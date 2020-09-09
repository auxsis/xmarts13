import base64
from codecs import BOM_UTF8
from os.path import splitext

from lxml import objectify
from odoo import _, api, fields, models
from odoo.tools import DEFAULT_SERVER_TIME_FORMAT, float_round

BOM_UTF8U = BOM_UTF8.decode('UTF-8')

DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%S'


class WorkflowActionRuleAccount(models.Model):
    _inherit = ['documents.workflow.rule']

    create_model = fields.Selection(
        selection_add=[
            ('account.invoice.l10n_mx_edi', "Invoices from CFDI")])

    def create_record(self, attachments=None):
        xml = attachments.filtered(
            lambda a: splitext(a.name)[1].lower() == '.xml')
        res = super(WorkflowActionRuleAccount, self).create_record(
            attachments=attachments - xml)
        if self.create_model.startswith('account.invoice'):
            invoice_ids = res['domain'][0][2]
            result = self.process_xml(xml)
            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'account.invoice',
                'name': "Invoices",
                'view_id': False,
                'view_type': 'list',
                'view_mode': 'tree',
                'views': [(False, "list"), (False, "form")],
                'domain': [('id', 'in', result['invoice_ids'])],
                'context': self._context,
            }
            if len(attachments) == 1 and invoice_ids:
                view_id = self.env['account.invoice'].get_formview_id()
                action.update({
                    'view_type': 'form',
                    'view_mode': 'form',
                    'views': [(view_id, "form")],
                    'res_id': result['invoice_ids'][0],
                    'view_id': view_id,
                })
            return action
        return res

    @api.model
    def get_tax_data(self, taxes_xml):
        taxes = []
        tax_codes = {'001': 'ISR', '002': 'IVA', '003': 'IEPS'}
        for rec in taxes_xml:
            tax_code = rec.get('Impuesto')
            tax_name = tax_codes.get(tax_code)
            amount_xml = float(rec.get('Importe', '0.0'))
            rate_xml = float_round(
                float(rec.get('TasaOCuota', '0.0')) * 100, 4)
            if 'Retenciones' in rec.getparent().tag:
                amount_xml = amount_xml * -1
                rate_xml = rate_xml * -1
            taxes.append({
                'rate': rate_xml,
                'name': tax_name,
                'amount': amount_xml
            })
        return taxes

    @api.model
    def validate_taxes(self, xml, inv_type):
        if not hasattr(xml, 'Impuestos'):
            return {}
        tax_obj = self.env['account.tax']
        tax_group_obj = self.env['account.tax.group']
        errors = []
        tax_ids = {}
        type_tax_use = 'purchase'
        if inv_type in ['out_invoice', 'out_refund']:
            type_tax_use = 'sale'
        for index, rec in enumerate(xml.Conceptos.Concepto):
            if not hasattr(rec, 'Impuestos'):
                continue
            taxes_xml = rec.Impuestos
            if hasattr(taxes_xml, 'Traslados'):
                taxes = self.get_tax_data(taxes_xml.Traslados.Traslado)
            if hasattr(taxes_xml, 'Retenciones'):
                taxes += self.get_tax_data(taxes_xml.Retenciones.Retencion)
            for tax in taxes:
                tax_group = tax_group_obj.search([
                    ('name', 'ilike', tax['name'])])
                domain = [
                    ('tax_group_id', 'in', tax_group.ids),
                    ('type_tax_use', '=', type_tax_use),
                    ('amount', '=', tax['rate'])]
                name = '%s(%s%%)' % (tax['name'], tax['rate'])
                tax_get = tax_obj.search(domain, limit=1)
                if not tax_group or not tax_get:
                    errors.append(
                        _('The tax %s do not exist in the system') % name)
                    continue
                if not tax_get.account_id.id:
                    errors.append(
                        _('The tax %s do not have an account defined') % name)
                    continue
                tax.update({
                    'id': tax_get.id,
                    'account_id': tax_get.account_id.id,
                    'name': name,
                })
                tax_ids.setdefault(index, []).append(tax)
        return {
            'errors': errors,
            'tax_ids': tax_ids,
        }

    @api.model
    def validate_xml_attachments(self, attachments):
        invoices = {}
        inv_obj = self.env['account.invoice']
        error_invoices = {}
        for attachment in attachments:
            errors = []
            filename = attachment.name
            xml_str = base64.b64decode(attachment.datas)
            # Fix the CFDIs emitted by the SAT
            xml_str = xml_str.replace(
                b'xmlns:schemaLocation', b'xsi:schemaLocation')
            try:
                xml = objectify.fromstring(xml_str)
            except SyntaxError:
                errors.append(
                    _('The XML file could not be processed'))
                error_invoices[filename] = errors
                continue
            if xml.get('Version') and xml.get('Version') != '3.3':
                errors.append(
                    _('The XML file is not CFDI 3.3'))
                error_invoices[filename] = errors
                continue
            tfd = inv_obj.l10n_mx_edi_get_tfd_etree(xml)
            uuid = False if tfd is None else tfd.get('UUID', '')
            if not uuid:
                errors.append(
                    _('This XML is not signed.'))
                error_invoices[filename] = errors
                continue
            edi_type = xml.get('TipoDeComprobante')
            if xml.get('TipoDeComprobante') not in ['I', 'E']:
                errors.append(
                    _('The XML is not of type "I" or "E".'))
                error_invoices[filename] = errors
                continue
            company_vat = self.env.user.company_id.vat
            emitter_vat = xml.Emisor.get('Rfc', '')
            receiver_vat = xml.Receptor.get('Rfc', '')
            inv_type = 'in_invoice'
            if edi_type == 'E' and receiver_vat == company_vat:
                inv_type = 'in_refund'
            elif edi_type == 'I' and emitter_vat == company_vat:
                inv_type = 'out_invoice'
            elif edi_type == 'E' and emitter_vat == company_vat:
                inv_type = 'out_refund'
            domain = [
                ('l10n_mx_edi_cfdi_name', '!=', False),
                ('type', '=', inv_type)]
            if uuid in inv_obj.search(domain).mapped('l10n_mx_edi_cfdi_uuid'):
                errors.append(
                    _('This UUID is already registered. (%s)' % uuid))
                error_invoices[filename] = errors
                continue
            if (inv_type in ['in_invoice', 'in_refund'] and
                    receiver_vat != company_vat):
                errors.append(
                    _('The VAT (%s) do not match with the company VAT(%s)') % (
                        receiver_vat, company_vat))
            if (inv_type in ['out_invoice', 'out_refund'] and
                    emitter_vat != company_vat):
                errors.append(
                    _('The VAT (%s) do not match with the company VAT(%s)') % (
                        emitter_vat, company_vat))
            currency = self.env['res.currency'].search([
                ('name', '=', xml.get('Moneda'))], limit=1)
            if not currency:
                errors.append(
                    _('The currency %s is not in the system.'))
            taxes = self.validate_taxes(xml, inv_type)
            if taxes['errors']:
                errors.extend(taxes['errors'])
            if not errors:
                invoices.update({
                    filename: {
                        'xml': xml,
                        'taxes': taxes['tax_ids'],
                        'invoice_type': inv_type,
                        'attachment': attachment,
                    },
                })
                continue
            error_invoices[filename] = errors
        return {
            'errors': error_invoices,
            'invoices': invoices,
        }

    @api.model
    def create_invoice_with_error(self, errors):
        inv_obj = self.env['account.invoice']
        invoices = inv_obj
        for filename, error_list in errors.items():
            body = ''
            for error in error_list:
                body += '<li>%s</li><br/>' % error
            invoice = inv_obj.create({})
            invoice.message_post(subject=_('Error in creation'), body=body)
            invoices |= invoice
        return invoices

    @api.model
    def process_xml(self, attachments, error_message=False, params={}):
        res = self.validate_xml_attachments(attachments)
        invoice_dict = self.prepare_invoices(res['invoices'], params)
        invoices = self.create_invoices(invoice_dict)
        if res['errors'] and not error_message:
            error_invoices = self.create_invoice_with_error(res['errors'])
            return {'invoice_ids': invoices.ids + error_invoices.ids}
        if res['errors'] and error_message:
            return {
                'invoice_ids': invoices.ids,
                'errors': res['errors']
            }
        return {'invoice_ids': invoices.ids}

    @api.model
    def prepare_invoices(self, invoices, params):
        res = []
        for invoice in invoices.values():
            invoice_lines = self.prepare_invoice_lines(invoice, params)
            invoice_dict = self.prepare_invoice_dict(
                invoice, invoice_lines, params)
            res.append(invoice_dict)
        return res

    @api.model
    def prepare_invoice_lines(self, values, params):
        xml = values['xml']
        taxes = values['taxes']
        invoice_type = values['invoice_type']
        invoice_lines = []
        sat_code_obj = self.env['l10n_mx_edi.product.sat.code']
        ail_obj = self.env['account.invoice.line']
        uom_obj = self.env['uom.uom']
        if params.get('account_id'):
            account_id = params.get('account_id')
        else:
            journal_id = self.env['account.invoice'].with_context(
                type=invoice_type)._default_journal().id
            account_id = ail_obj.with_context({
                'journal_id': journal_id,
                'type': invoice_type})._default_account()
        account_analytic_id = False
        if params.get('account_analytic_id'):
            account_analytic_id = params.get('account_analytic_id')
        analytic_tag_ids = False
        if params.get('analytic_tag_ids'):
            analytic_tag_ids = [(6, 0, params.get('analytic_tag_ids'))]
        if params.get('product_id'):
            product_id = params.get('product_id')
        partner = self.get_partner(xml, invoice_type)
        for index, rec in enumerate(xml.Conceptos.Concepto):
            if not params.get('product_id'):
                product_id = self.search_product(rec, invoice_type)
            description = rec.get('Descripcion')
            pred_account = ail_obj._predict_account(description, partner)
            if params.get('account_id'):
                pred_account = False
            amount = float(rec.get('Importe', '0.0'))
            discount = 0.0
            if rec.get('Descuento') and amount:
                discount = (float(rec.get('Descuento', '0.0')) / amount) * 100
            uom = rec.get('Unidad', '')
            uom_code = rec.get('ClaveUnidad', '')
            domain_uom = [('name', '=ilike', uom)]
            line_taxes = [tax['id'] for tax in taxes.get(index, [])]
            code_sat = sat_code_obj.search([('code', '=', uom_code)], limit=1)
            domain_uom += [('l10n_mx_edi_code_sat_id', '=', code_sat.id)]
            uom_id = uom_obj.with_context(
                lang='es_MX').search(domain_uom, limit=1)

            # If there is a Fuel invoice the IPES must be manually computed
            # and added one extra line.
            sat_code = rec.get('ClaveProdServ')
            if sat_code in self._get_fuel_codes():
                tax = taxes.get(index)[0] if taxes.get(index, []) else {}
                price = tax.get('amount') / (tax.get('rate') / 100)
                invoice_lines.append((0, 0, {
                    'account_id': pred_account if pred_account else account_id,
                    'name': _('FUEL - IEPS'),
                    'quantity': 1.0,
                    'uom_id': uom_id.id,
                    'price_unit': float(rec.get('Importe', 0)) - price,
                }))
            invoice_lines.append((0, 0, {
                'product_id': product_id,
                'account_id': pred_account if pred_account else account_id,
                'name': description,
                'quantity': float(rec.get('Cantidad', '')),
                'uom_id': uom_id.id,
                'invoice_line_tax_ids': [(6, 0, line_taxes)],
                'price_unit': float(rec.get('ValorUnitario')),
                'discount': discount,
                'account_analytic_id': account_analytic_id,
                'analytic_tag_ids': analytic_tag_ids,
            }))
        return invoice_lines

    @api.model
    def prepare_invoice_dict(self, values, invoice_lines, params):
        xml = values['xml']
        invoice_type = values['invoice_type']
        partner = self.get_partner(xml, invoice_type)
        if params.get('journal_id'):
            journal_id = params.get('journal_id')
        else:
            journal_id = self.env['account.invoice'].with_context(
                type=invoice_type)._default_journal().id
        date = fields.datetime.strptime('2018-03-01T19:18:32', DATETIME_FORMAT)
        currency = self.env['res.currency'].search([
            ('name', '=', xml.get('Moneda', 'MXN'))], limit=1)
        payment_method_id = self.env['l10n_mx_edi.payment.method'].search(
            [('code', '=', xml.get('FormaPago'))], limit=1)
        payment_condition = xml.get('CondicionesDePago') or False
        acc_pay_term = self.env['account.payment.term']
        if payment_condition:
            acc_pay_term = acc_pay_term.search([
                ('name', '=', payment_condition)], limit=1)

        attachment = values['attachment']
        xml_tfd = self.env['account.invoice'].l10n_mx_edi_get_tfd_etree(xml)
        uuid = False if xml_tfd is None else xml_tfd.get('UUID', '')
        invoice_dict = {
            'partner_id': partner.id,
            'reference': '%s|%s' % (xml.get('Folio', ''), uuid.split('-')[0]),
            'payment_term_id': acc_pay_term.id,
            'l10n_mx_edi_payment_method_id': payment_method_id.id,
            'l10n_mx_edi_usage': xml.Receptor.get('UsoCFDI'),
            'date_invoice': date.strftime('%Y-%m-%d'),
            'currency_id': currency.id,
            'type': invoice_type,
            'l10n_mx_edi_time_invoice': date.strftime(
                DEFAULT_SERVER_TIME_FORMAT),
            'journal_id': journal_id,
            'invoice_line_ids': invoice_lines,
            'l10n_mx_edi_cfdi_name': attachment.name,
            'attachment': attachment,
        }
        if invoice_type in ['out_refund', 'in_refund']:
            invoice_dict.update({
                'related_uuid':
                    xml.CfdiRelacionados.CfdiRelacionado.get('UUID')
            })
        return invoice_dict

    @api.model
    def create_invoices(self, invoice_list):
        invoices = self.env['account.invoice']
        for rec in invoice_list:
            attachment = rec.pop('attachment')
            related_uuid = (
                rec.pop('related_uuid') if rec.get('related_uuid') else False)
            invoice = invoices.create(rec)
            if related_uuid:
                invoice._set_cfdi_origin('01', [related_uuid])
            attachment.write({
                'res_id': invoice.id,
                'res_model': invoice._name,
            })
            invoice.l10n_mx_edi_update_sat_status()
            invoices |= invoice
            body = "<p>created with DMS</p>"
            invoice.message_post(body=body)
        return invoices

    @api.model
    def search_product(self, concept, invoice_type):
        xml = concept.getparent().getparent()
        partner = self.get_partner(xml, invoice_type)
        code = concept.get('NoIdentificacion')
        name = concept.get('Descripcion')
        supplierinfo = self.env['product.supplierinfo'].search([
            ('name', '=', partner.id), '|',
            ('product_code', '=ilike', code), ('product_name', '=ilike', name)
        ])
        if len(supplierinfo) == 1:
            return supplierinfo.product_tmpl_id.product_variant_id.id
        product = self.env['product.product'].search([
            '|', ('default_code', '=ilike', code),
            ('name', '=ilike', name)])
        if len(product) == 1:
            return product.id
        pred_product = self.env['account.invoice.line']._predict_product(name)
        if pred_product:
            return pred_product
        return False

    @api.model
    def get_partner(self, xml, invoice_type):
        vat = xml.Emisor.get('Rfc')
        name = xml.Emisor.get('Nombre')
        if invoice_type in ['out_invoice', 'out_refund']:
            vat = xml.Receptor.get('Rfc')
            name = xml.Receptor.get('Nombre')
        domain = [('vat', '=', vat)]
        if vat in ['XEXX010101000', 'XAXX010101000']:
            domain.append(('name', '=ilike', name))
        partner = self.env['res.partner'].search(domain)
        if partner:
            return partner.commercial_partner_id
        return self.create_partner(xml, invoice_type)

    @api.model
    def create_partner(self, xml, invoice_type):
        """ It creates the partner from xml object. """
        # Default Mexico because only in Mexico are emitted CFDIs
        folio = xml.get('Folio', '')
        vat = xml.Emisor.get('Rfc')
        name = xml.Emisor.get('Nombre')
        if invoice_type in ['out_invoice', 'out_refund']:
            vat = xml.Receptor.get('Rfc')
            name = xml.Receptor.get('Nombre')
        partner = self.env['res.partner'].create({
            'name': name,
            'company_type': 'company',
            'vat': vat,
            'country_id': self.env.ref('base.mx').id,
            'supplier':
                True if invoice_type in ['in_refund', 'in_invoice'] else False,
            'customer':
                False if invoice_type in ['in_invoice', 'in_refund'] else True,
        })
        msg = _('This partner was created when invoice %s was added from '
                'a XML file. Please verify that the data of partner is '
                'correct.') % folio
        partner.message_post(subject=_('Info'), body=msg)
        return partner

    @api.model
    def _get_fuel_codes(self):
        """Return the codes that could be used in FUEL"""
        return [str(r) for r in range(15101500, 15101513)]
