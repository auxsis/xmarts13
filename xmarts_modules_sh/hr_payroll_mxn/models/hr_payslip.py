import base64
import logging
import time
from datetime import datetime, timedelta
from os import path
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pytz import timezone
from lxml import etree, objectify
from suds.client import Client

from odoo import _, api, fields, models
from odoo.addons.l10n_mx_edi.models import account_invoice
from odoo import _, api, fields, models, tools
from odoo.exceptions import ValidationError

from .safe_eval import ast, Transformer
from .jinja_extension import RaiseExtension
from itertools import groupby
from odoo.addons.l10n_mx_edi.tools.run_after_commit import run_after_commit
from lxml.objectify import fromstring

CFDI_XSLT_CADENA = 'hr_payroll_mxn/SAT/cadenaoriginal_3_3.xslt'

_logger = logging.getLogger(__name__)

_errors = {
    'bank_account': _('Missing bank account for employee.'),
    'employer_number': _('Missing employer number.'),
    'social_security': _('Missing social security number for employee.'),
    'payslip_type': _('Missing payslip type on payroll structure.'),
    'contract_type': _('Missing code for contract type.'),
    'company_curp': _('CURP is required when company is a Person.'),
    'tipo_regimen_tipo_contrato': _(
        'When Contract Type code is between 01 and 08, '
        'then Employee Regime must be 02, 03 or 04.',
    ),
}

def create_list_html(array):
    '''Convert an array of string to a html list.
    :param array: A list of strings
    :return: an empty string if not array, an html list otherwise.
    '''
    if not array:
        return ''
    msg = ''
    for item in array:
        msg += '<li>' + item + '</li>'
    return '<ul>' + msg + '</ul>'

def _domain2statement(domain):
    statement = ''
    operator = False
    for d in domain:
        if not operator:
            if isinstance(d, str):
                if d == '|':
                    operator = ' or'
                continue
            else:
                operator = False
        statement += ' o.' + str(d[0]) + ' '
        statement += (d[1] == '=' and '==' or d[1]) + ' '
        statement += (
            (isinstance(d[2], str) and '\'' + d[2] + '\'' or str(d[2]))
        )
        if d != domain[-1]:
            statement += operator or ' and'
        operator = False


def required_field(value, error):
    """Filter used to enforce a required value on template

    @param value: Value to evaluate and enforce presence
    @type value: any
    @param error: Error message to display if value not present
    @type error: str
    @raise ValidationError: if value is not set
    """
    if not value:
        raise ValidationError(error)
    return value

class InheritAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @classmethod
    def generate_cadena_original(self, xml, context=None):
        xlst_file = tools.file_open(context.get('path_cadena', '')).name
        dom = etree.fromstring(xml)
        xslt = etree.parse(xlst_file)
        transform = etree.XSLT(xslt)
        return str(transform(dom))


class HrPayslip(models.Model):
    _name = 'hr.payslip'
    _inherit = ['hr.payslip', 'mail.thread']

    @api.model
    def _default_currency_id(self):
        return self.env.user.company_id.currency_id

    no_certificado = fields.Char(
        'No. Certificate', size=64, copy=False,
        help='Number of serie of certificate used for the invoice',
    )
    certificado = fields.Text(
        'Certificate', size=64, copy=False,
        help='Certificate used in the invoice',
    )
    sello = fields.Text('Stamp', size=512, copy=False, help='Digital Stamp')
    cadena_original = fields.Text(
        'String Original', size=512, copy=False,
        help='Data stream with the information contained in the electronic'
        ' invoice',
    )
    cfdi_folio_fiscal = fields.Char(
        'CFD-I Folio Fiscal', size=64, copy=False,
        help='Folio used in the electronic invoice',
        related="l10n_mx_edi_cfdi_uuid"
    )
    date_payroll = fields.Datetime(
        'Payroll Date', readonly=True,
        states={'draft': [('readonly', False)]}, index=True,
        help='Keep empty to use the current date',
        default=(fields.Datetime.now)
    )
    payment_type = fields.Many2one(
        'l10n_mx_edi.payment.method',
        help='Indicates the way it was paid or will be paid the invoice,'
        'where the options could be: check, bank transfer, reservoir in '
        'account bank, credit card, cash etc. If not know as will be '
        'paid the invoice, leave empty and the XML show “Unidentified”.',
    default=lambda self: self.env['l10n_mx_edi.payment.method'].search([('code','=','01')],limit=1) or ''
    )
    currency_id = fields.Many2one(
        'res.currency', 'Currency', required=True, readonly=True,
        states={'draft': [('readonly', False)]}, track_visibility='always',
        default=lambda self: self._default_currency_id(),
    )
    cfdi_fecha_timbrado = fields.Datetime(
        'CFD-I Date Stamping', copy=False,
        help='Date when is stamped the electronic invoice',
    )
    cfdi_sello = fields.Text(
        'CFD-I Stamp', copy=False, help='Sign assigned by the SAT',
    )
    cfdi_cadena_original = fields.Text(
        'CFD-I Original String', copy=False,
        help='Original String used in the electronic invoice',
    )
    cfdi_no_certificado = fields.Char(
        'SAT CFDI Certificado', copy=False,
        help='SAT Certificate used for sign current file',
    )
    date_tz = fields.Datetime(
        compute='_compute_date_tz', string='Date Payroll with TZ',
        help='Date of Invoice with Time Zone',
    )
    antiquity = fields.Integer(
        compute='_compute_antiquity', help='Antiquity in weeks',
    )
    total_days = fields.Integer(
        compute='_compute_total_days',
        help='Helper field to compute the total days included in payslip',
    )
    cfdi_nomina = fields.Binary()
    cfdi_nomina_file_name = fields.Char()
    #name = vat + '_' + payslip.number + '.' + mimetype
    source_resource = fields.Selection([
        ('IP', 'Own income'),
        ('IF', 'Federal income'),
        ('IM', 'Mixed income')],
        help='Used in XML to identify the source of the resource used '
        'for the payment of payroll of the personnel that provides or '
        'performs a subordinate or assimilated personal service to salaries '
        'in the dependencies. This value will be set in the XML attribute '
        '"OrigenRecurso" to node "EntidadSNCF".')
    amount_sncf = fields.Float(
        'Own resource', help='When the attribute in "Source Resource" is "IM" '
        'this attribute must be added to set in the XML attribute '
        '"MontoRecursoPropio" in node "EntidadSNCF", and must be less that '
        '"TotalPercepciones" + "TotalOtrosPagos"')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('cancel', 'Rejected'),
        ('canceled', 'Cancelado'),
    ], string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")
    l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, readonly=True,
        help='Folio in electronic invoice, is returned by SAT when send to stamp.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi = fields.Binary(string='Cfdi content', copy=False, readonly=True,
        help='The cfdi xml content encoded in base64.',
        related='cfdi_nomina')
    l10n_mx_edi_cfdi_supplier_rfc = fields.Char(string='Supplier RFC', copy=False, readonly=True,
        help='The supplier tax identification number.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_customer_rfc = fields.Char(string='Customer RFC', copy=False, readonly=True,
        help='The customer tax identification number.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_amount = fields.Monetary(string='Total Amount', copy=False, readonly=True,
        help='The total amount reported on the cfdi.',
        compute='_compute_cfdi_values')
    l10n_mx_edi_cfdi_certificate_id = fields.Many2one('l10n_mx_edi.certificate',
        string='Certificate', copy=False, readonly=True,
        help='The certificate used during the generation of the cfdi.')

    @api.onchange('cfdi_nomina')
    def onchange_cfdi_nomina_name(self):
        data = {
            'model': 'hr.payslip',
            'id': payslip.id,
            'report_type': 'aeroo',
        }
        result, mimetype = self.render_report(
            self._cr, self._uid, [payslip.id],
            'payroll_report_aeroo', data, context=self._context,
        )
        vat = payslip.company_id.partner_id.vat_split
        name = vat + '_' + payslip.number + '.' + mimetype
        self.cfdi_nomina_file_name = name

    @api.onchange('cfdi_nomina')
    def onchange_read_xml_uuid(self):
        if self.cfdi_nomina:
            result = self.cfdi_nomina.encode('utf-8')
            data = base64.decodestring(result)
            fobj = tempfile.NamedTemporaryFile(delete=False)
            fname = fobj.name
            fobj.write(data)
            fobj.close()
            file_xml = open(fname, "r")
            tree = objectify.fromstring(file_xml.read().encode())
            if self._get_stamp_data(tree) == None:
                self.l10n_mx_edi_cfdi_uuid = ''
            else:
                tfd = self._get_stamp_data(tree)
                xml = tfd.get('UUID')
                tfd = self._get_stamp_data(tree)
                self.l10n_mx_edi_cfdi_uuid = tfd.get('UUID')

        else:
            self.l10n_mx_edi_cfdi_uuid = ''

    @api.model
    def l10n_mx_edi_get_xml_etree(self, cfdi=None):
        '''Get an objectified tree representing the cfdi.
        If the cfdi is not specified, retrieve it from the attachment.

        :param cfdi: The cfdi as string
        :return: An objectified tree
        '''
        #TODO helper which is not of too much help and should be removed
        self.ensure_one()
        if cfdi is None and self.l10n_mx_edi_cfdi:
            cfdi = base64.decodestring(self.l10n_mx_edi_cfdi)
        return fromstring(cfdi) if cfdi else None


    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        '''Get the TimbreFiscalDigital node from the cfdi.

        :param cfdi: The cfdi as etree
        :return: the TimbreFiscalDigital node
        '''
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None


    @api.multi
    @api.depends('cfdi_nomina','l10n_mx_edi_cfdi')
    def _compute_cfdi_values(self):
        '''Fill the invoice fields from the cfdi values.
        '''
        for inv in self:
            attachment_id = inv.l10n_mx_edi_retrieve_last_attachment()
            if not attachment_id:
                continue
            # At this moment, the attachment contains the file size in its 'datas' field because
            # to save some memory, the attachment will store its data on the physical disk.
            # To avoid this problem, we read the 'datas' directly on the disk.
            datas = attachment_id._file_read(attachment_id.store_fname)
            inv.cfdi_nomina = datas
            cfdi = base64.decodestring(datas).replace(
                b'xmlns:schemaLocation', b'xsi:schemaLocation')
            tree = inv.l10n_mx_edi_get_xml_etree(cfdi)
            # if already signed, extract uuid
            tfd_node = inv.l10n_mx_edi_get_tfd_etree(tree)
            if tfd_node is not None:
                inv.l10n_mx_edi_cfdi_uuid = tfd_node.get('UUID')
            inv.l10n_mx_edi_cfdi_amount = tree.get('Total', tree.get('total'))
            inv.l10n_mx_edi_cfdi_supplier_rfc = tree.Emisor.get(
                'Rfc', tree.Emisor.get('rfc'))
            inv.l10n_mx_edi_cfdi_customer_rfc = tree.Receptor.get(
                'Rfc', tree.Receptor.get('rfc'))
            certificate = tree.get('noCertificado', tree.get('NoCertificado'))
            inv.l10n_mx_edi_cfdi_certificate_id = self.env['l10n_mx_edi.certificate'].sudo().search(
                [('serial_number', '=', certificate)], limit=1)

    @api.multi
    def _compute_date_tz(self):
        for record in self.filtered('date_payroll'):
            record.date_tz = timezone('America/Mexico_City').localize(
                record.date_payroll).strftime('%Y-%m-%d %H:%M:%S')

    @api.multi
    def _compute_antiquity(self):
        for record in self.filtered('contract_id.date_start'):
            begin = record.contract_id.date_start
            end = record.date_to + timedelta(days=1)
            record.antiquity = (end - begin).days / 7

    @api.multi
    def _compute_total_days(self):
        for record in self:
            total_days = 0
            for days in record.worked_days_line_ids:
                total_days += days.number_of_days
            record.total_days = total_days

    @api.multi
    def _get_imss(self, fee_name='c_obrera'):
        # Calculate amount to pay for IMSS according to actual IMSS tables
        # pylint: disable=eval-used,unused-variable
        result = 0
        transformer = Transformer()
        smgvdf = self.env['hr.payroll'].search(  # noqa: F841
            [('date_start', '<=', self.date_from)], limit=1,
            order='date_start desc',
        ).smgvdf
        sbc = self.contract_id.integrated_wage  # noqa: F841
        total_days = self.contract_id.isr_table.number_of_days
        imss_table = self.env['imss.table'].search([])

        for row in imss_table:
            tree = ast.parse(row.base, mode='eval')
            # raises RuntimeError on invalid code
            transformer.visit(tree)

            # compile the ast into a code object
            clause = compile(tree, '<AST>', 'eval')

            # and eval the compiled object
            base = eval(clause)
            if base > 0:
                fee = getattr(row, fee_name)
                result = result + base * (fee / 100) * total_days
        return result

    @api.multi
    def cancel_done_sheet(self):
        """ Cancel payslip on SAT and also cancel payslip """
        #cfdi_obj =self.env['account.invoice']
        cfdi_obj =self.env['ir.attachment']
        for payslip in self:
            # First we are going to try cancel the payslip, and only when
            # the payslip is properly cancelled then we try to cancel the
            # cfdi on SAT

            #Se comento la siguiente linea para corregir error al cancelar status
            #payslip.cancel_sheet()

            #Se agrega lo siguiente en lugar de la linea anterior
            self.write({'state': 'canceled'})

            # Search for cfdis to cancel on SAT
            cfdis = cfdi_obj.search([
                ('res_id', '=', payslip.id),
                ('res_model', '=', 'hr.payslip'),
            ])
            #for cfdi in cfdis:
                #if cfdi.state != 'cancel':
                    #cfdi.signal_cancel([cfdi.id])
            #self.action_cancel_cfdi()
            self._l10n_mx_edi_call_service('cancel')
            
    def action_cancel_cfdi(self):
        msg = ''
        folio_cancel = ''
        uuids = []
        pac_params_obj = self.env['params.pac']
        for inv in self:
            certificate_id = inv.company_id.certificate_id
            if not certificate_id:
                inv.message_post(body=_(
                    'No tienes definido certificado para esta compañia!'))
                continue
            pac_params = pac_params_obj.search([
                ('method_type', '=', 'cancelar'),
                ('company_id', '=', inv.company_id.id),
            ], limit=1)
            if not pac_params:
                inv.message_post(body=_(
                    'No tienes parametros del PAC configurados para '
                    'cancelar'))
                continue
            pac_usr = pac_params.user
            pac_pwd = pac_params.password
            wsdl_url = pac_params.url_webservice
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.cer_file)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key_file, certificate_id.password)).decode('UTF-8')
            try:
                client = Client(wsdl_url, cache=None)
            except:
                inv.message_post(body=_(
                    'Revisa tu conexion a internet y los datos del PAC'))
                continue
            taxpayer_id = inv.company_id.partner_id.vat
            folio_cancel = inv.cfdi_folio_fiscal
            uuids.append(folio_cancel)
            uuids_list = client.factory.create("UUIDS")
            uuids_list.uuids.string = uuids
            result = client.service.cancel(
                uuids_list, pac_usr, pac_pwd, taxpayer_id, cer_pem, key_pem)
            time.sleep(1)
            if 'Folios' not in result:
                msg += _('%s' % result)
                inv.message_post(body=_('Mensaje %s') % (msg))
                continue
            estatus_uuid = result.Folios[0][0].EstatusUUID
            if estatus_uuid in ('201', '202'):
                msg += _(
                    '\n- El proceso de cancelación se ha completado '
                    'correctamente.\n El uuid cancelado es: ') + folio_cancel
                self.cfdi_fecha_cancelacion = time.strftime(
                    '%Y-%m-%d %H:%M:%S')
            else:
                inv.message_post(body=_('Mensaje %s %s Code: %s') % (
                    msg, result.Folios[0][0].EstatusCancelacion,
                    estatus_uuid))
            inv.message_post(body=msg)
            if 'Acuse' in result:
                cname = 'ACUSE_CANCELACION_' + inv.move_id.name + '.xml'
                self.env['ir.attachment'].create({
                    'name': cname,
                    'datas_fname': cname,
                    'datas': base64.encodestring(str(
                        result.Acuse).encode()),
                    'res_model': 'hr.payslip',
                    'res_id': inv.id,
                })

    @api.multi
    def action_printable(self):
        attachment_obj = self.env['ir.attachment']
        ir_attach_obj = self.env['ir.attachment.facturae.mx']
        for payslip in self:
            # the value of data is in this way because the report is aeroo
            data = {
                'model': 'hr.payslip',
                'id': payslip.id,
                'report_type': 'aeroo',
            }
            result, mimetype = self.render_report(
                self._cr, self._uid, [payslip.id],
                'payroll_report_aeroo', data, context=self._context,
            )
            vat = payslip.company_id.partner_id.vat_split
            name = vat + '_' + payslip.number + '.' + mimetype
            attachment = attachment_obj.create({
                'name': name,
                'datas_fname': name,
                'datas': base64.encodestring(result),
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
            })
            ir_attach_obj.write({
                'file_xml_sign': attachment.id,
                'state': 'signed',
                'last_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            })
        return

    @api.model
    def create_ir_attachment_facturae(self):
        for payslip in self:
            payslip._get_signed_xml()
            vat = payslip.company_id.partner_id.vat
            name = vat + '_' + payslip.number + '.xml'
            attachment = self.env['ir.attachment'].create({
                'name': name,
                'res_model': 'hr.payslip',
                'res_id': payslip.id,
                'datas': self.cfdi_nomina,
                'datas_fname': name,
            })
            payslip.message_post(
                body=_('CFDI generated'),
                attachment_ids=[attachment.id])
            # call the function which creates pdf report
            # payslip.action_printable()
        return

    def action_payslip_done(self):
        for payslip in self:
            if not payslip.date_payroll:
                payslip.date_payroll = fields.Datetime.now()
            payslip.create_ir_attachment_facturae()
        return super().action_payslip_done()

    @api.multi
    def _get_cfdi_dict_data(self):
        self.ensure_one()
        # Crate an environment of jinja in the templates directory
        env = Environment(
            loader=FileSystemLoader(
                path.join(
                    path.dirname(path.abspath(__file__)), '../templates',),),
            extensions=[RaiseExtension],
            undefined=StrictUndefined, autoescape=True,
        )
        # Add custom filters
        env.filters['required_field'] = required_field
        template = env.get_template('nomina1_2.mako')

        total_percepciones_grav = 0.0
        total_percepciones_ex = 0.0
        # Iterate in each line_ids to get importeGravado and importeExento
        for line in self.line_ids:
            if line.category_id.code == 'PERGRA':
                percepcion = {
                    'tipo': line.salary_rule_id.code_sat,
                    'concepto': line.name,
                    'importegravado': line.taxable_amount,
                    'importeexento': line.total - line.taxable_amount,
                    'clave': line.code,
                }
                total_percepciones_grav += percepcion['importegravado']
                total_percepciones_ex += percepcion['importeexento']
        emitter = self.company_id
        # Covert date to a date with time zone
        date_payroll_tz = datetime.now(timezone(
            'America/Mexico_City')).strftime('%Y-%m-%dT%H:%M:%S')
        # Covert date to an adequate date
        payment_day = self.date_tz.strftime('%Y-%m-%d')
        # Create a template and pass a context
        total_percepciones = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'PERGRA').mapped('total'))
        total_deducciones = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'DEDC').mapped('total'))
        total_otrospagos = sum(self.line_ids.filtered(
            lambda l: l.category_id.code == 'OTROS').mapped('total'))
        total_impuestos_retenidos = sum(self.line_ids.filtered(
            lambda l: l.salary_rule_id.code_sat == '002' and l.category_id.code == 'DEDC').mapped('total'))  # noqa
        days_overtime = lambda l: sum([w.number_of_days for w in l.payslip.id.worked_days_line_ids if w.code == l.code])  # noqa
        hours_overtime = lambda l: sum([w.number_of_hours for w in l.payslip.id.worked_days_line_ids if w.code == l.code])  # noqa
        total_other_ded = sum(self.line_ids.filtered(
            lambda l: l.salary_rule_id.code_sat != '002' and l.category_id.code == 'DEDC').mapped('total'))  # noqa
        has_other = self.line_ids.filtered(
            lambda l: l.category_id.code == 'OTROS')
        # certificate_id = self.company_id.certificate_id
        # print("DATA CERTIFICADO :: ",certificate_id.sudo().get_data()[0].decode())
        certificate_ids = self.company_id.l10n_mx_edi_certificate_ids
        certificate_id = certificate_ids.sudo().get_valid_certificate()
        self.l10n_mx_edi_cfdi_certificate_id = certificate_id
        print(certificate_id.sudo().get_data()[0].decode())
        if not certificate_id:
            raise ValidationError(_(
                'No tienes definido certificado para esta compañia !'))
        xml_data = template.render(
            payslip=self, emitter=emitter,
            percepciones_totalgravado=total_percepciones_grav,
            percepciones_totalexento=total_percepciones_ex,
            date=date_payroll_tz,
            payment_day=payment_day,
            errors=_errors, total_percepciones=total_percepciones,
            total_deducciones=total_deducciones,
            total_otrospagos=total_otrospagos,
            TotalImpuestosRetenidos=total_impuestos_retenidos,
            days_overtime=days_overtime, hours_overtime=hours_overtime,
            total_other_ded=total_other_ded, has_other=has_other,
            certificate=certificate_id,
            cer_data=certificate_id.sudo().get_data()[0].decode(),
        )
        _logger.warn('Jinja XML result: %s', xml_data)
        self.cfdi_nomina = base64.b64encode(xml_data.encode())
        return True

    @api.multi
    def _get_signed_xml(self):
        for payroll in self:
            payroll._get_cfdi_dict_data()
            payroll.set_sign_data()
            company_id = payroll.company_id.id
            copy_context = dict(self._context)
            copy_context.update({'company_id': company_id})
            #self.sign_cfdi()
            self._l10n_mx_edi_call_service('sign')
            return True

    @api.model
    def l10n_mx_edi_retrieve_attachments(self):
        """Retrieve all the cfdi attachments generated for this payment.

        :return: An ir.attachment recordset
        """
        self.ensure_one()
        if not self.cfdi_nomina:
            return []
        vat = self.company_id.partner_id.vat
        name = vat + '_' + (self.number or '') + '.xml'
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', '=', name)]
        return self.env['ir.attachment'].search(domain)

    @api.model
    def l10n_mx_edi_retrieve_last_attachment(self):
        attachment_ids = self.l10n_mx_edi_retrieve_attachments()
        return attachment_ids and attachment_ids[0] or None

    @run_after_commit
    @api.multi
    def _l10n_mx_edi_call_service(self, service_type):
        """Call the right method according to the pac_name, it's info returned
        by the '_l10n_mx_edi_%s_info' % pac_name'
        method and the service_type passed as parameter.
        :param service_type: sign or cancel"""
        invoice_obj = self.env['account.invoice']
        # Regroup the invoices by company (= by pac)
        comp_x_records = groupby(self, lambda r: r.company_id)
        for company_id, records in comp_x_records:
            pac_name = company_id.l10n_mx_edi_pac
            if not pac_name:
                continue
            # Get the informations about the pac
            pac_info_func = '_l10n_mx_edi_%s_info' % pac_name
            service_func = '_l10n_mx_edi_%s_%s' % (pac_name, service_type)
            pac_info = getattr(invoice_obj, pac_info_func)(company_id, service_type)
            # Call the service with invoices one by one or all together according to the 'multi' value.
            # TODO - Check multi
            for record in records:
                getattr(record, service_func)(pac_info)

    @api.model
    def _l10n_mx_edi_solfact_info(self, company_id, service_type):
        test = company_id.l10n_mx_edi_pac_test_env
        username = company_id.l10n_mx_edi_pac_username
        password = company_id.l10n_mx_edi_pac_password
        url = 'https://testing.solucionfactible.com/ws/services/Timbrado?wsdl'\
            if test else 'https://solucionfactible.com/ws/services/Timbrado?wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'testing@solucionfactible.com' if test else username,
            'password': 'timbrado.SF.16672' if test else password,
        }

    @api.multi
    def _l10n_mx_edi_solfact_sign(self, pac_info):
        '''SIGN for Solucion Factible.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for rec in self:
            cfdi = rec.cfdi_nomina.decode('UTF-8')
            try:
                client = Client(url, timeout=20)
                response = client.service.timbrar(username, password, cfdi, False)
            except Exception as e:
                rec.l10n_mx_edi_log_error(str(e))
                continue
            msg = getattr(response.resultados[0], 'mensaje', None)
            code = getattr(response.resultados[0], 'status', None)
            xml_signed = getattr(response.resultados[0], 'cfdiTimbrado', None)
            rec._l10n_mx_edi_post_sign_process(xml_signed, code, msg)

    @api.multi
    def _l10n_mx_edi_solfact_cancel(self, pac_info):
        '''CANCEL for Solucion Factible.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for rec in self:
            uuids = [self.cfdi_folio_fiscal]
            certificate_id = self.l10n_mx_edi_cfdi_certificate_id.sudo()
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.content)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key, certificate_id.password)).decode('UTF-8')
            key_password = certificate_id.password
            try:
                client = Client(url, timeout=20)
                response = client.service.cancelar(username, password, uuids, cer_pem, key_pem, key_password)
            except Exception as e:
                rec.l10n_mx_edi_log_error(str(e))
                continue
            code = getattr(response.resultados[0], 'statusUUID', None)
            cancelled = code in ('201', '202')  # cancelled or previously cancelled
            # no show code and response message if cancel was success
            msg = '' if cancelled else getattr(response.resultados[0], 'mensaje', None)
            code = '' if cancelled else code
            rec._l10n_mx_edi_post_cancel_process(cancelled, code, msg)

    @api.multi
    def _l10n_mx_edi_finkok_info(self, company_id, service_type):
        test = company_id.l10n_mx_edi_pac_test_env
        username = company_id.l10n_mx_edi_pac_username
        password = company_id.l10n_mx_edi_pac_password
        if service_type == 'sign':
            url = 'http://demo-facturacion.finkok.com/servicios/soap/stamp.wsdl'\
                if test else 'http://facturacion.finkok.com/servicios/soap/stamp.wsdl'
        else:
            url = 'http://demo-facturacion.finkok.com/servicios/soap/cancel.wsdl'\
                if test else 'http://facturacion.finkok.com/servicios/soap/cancel.wsdl'
        return {
            'url': url,
            'multi': False,  # TODO: implement multi
            'username': 'cfdi@vauxoo.com' if test else username,
            'password': 'vAux00__' if test else password,
            }

    @api.multi
    def _l10n_mx_edi_finkok_sign(self, pac_info):
        """SIGN for Finkok."""
        # TODO - Duplicated with the invoice one
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for rec in self:
            cfdi = rec.cfdi_nomina.decode('UTF-8')
            try:
                client = Client(url, timeout=20)
                response = client.service.stamp(cfdi, username, password)
            except Exception as e:
                rec.l10n_mx_edi_log_error(str(e))
                continue
            code = 0
            msg = None
            if response.Incidencias:
                code = getattr(response.Incidencias[0][0], 'CodigoError', None)
                msg = getattr(response.Incidencias[0][0], 'MensajeIncidencia', None)
            xml_signed = getattr(response, 'xml', None)
            if xml_signed:
                xml_signed = base64.b64encode(xml_signed.encode('utf-8'))
            rec._l10n_mx_edi_post_sign_process(xml_signed, code, msg)

    @api.multi
    def _l10n_mx_edi_finkok_cancel(self, pac_info):
        '''CANCEL for Finkok.
        '''
        url = pac_info['url']
        username = pac_info['username']
        password = pac_info['password']
        for inv in self:
            uuid = inv.cfdi_nomina
            certificate_id = inv.l10n_mx_edi_cfdi_certificate_id.sudo()
            company_id = self.company_id
            cer_pem = base64.encodestring(certificate_id.get_pem_cer(
                certificate_id.content)).decode('UTF-8')
            key_pem = base64.encodestring(certificate_id.get_pem_key(
                certificate_id.key, certificate_id.password)).decode('UTF-8')
            cancelled = False
            code = False
            try:
                client = Client(url, timeout=20)
                invoices_list = client.factory.create("UUIDS")
                invoices_list.uuids.string = [uuid]
                response = client.service.cancel(invoices_list, username, password, company_id.vat, cer_pem, key_pem)
            except Exception as e:
                inv.l10n_mx_edi_log_error(str(e))
                continue
            if not hasattr(response, 'Folios'):
                msg = _('A delay of 2 hours has to be respected before to cancel')
            else:
                code = getattr(response.Folios[0][0], 'EstatusUUID', None)
                cancelled = code in ('201', '202')  # cancelled or previously cancelled
                # no show code and response message if cancel was success
                code = '' if cancelled else code
                msg = '' if cancelled else _("Cancelling got an error")
            inv._l10n_mx_edi_post_cancel_process(cancelled, code, msg)

    @api.multi
    def _l10n_mx_edi_post_sign_process(self, xml_signed, code=None, msg=None):
        """Post process the results of the sign service.

        :param xml_signed: the xml signed datas codified in base64
        :param code: an eventual error code
        :param msg: an eventual error msg
        """
        # TODO - Duplicated
        self.ensure_one()
        if xml_signed:
            body_msg = _('The sign service has been called with success')
            # Update the pac status
            self.l10n_mx_edi_pac_status = 'signed'
            self.l10n_mx_edi_cfdi = xml_signed
            self.cfdi_nomina = xml_signed
            # Update the content of the attachment
            attachment_id = self.l10n_mx_edi_retrieve_last_attachment()
            attachment_id.write({
                'datas': xml_signed,
                'mimetype': 'application/xml'
            })
            post_msg = [_('The content of the attachment has been updated')]
        else:
            body_msg = _('The sign service requested failed')
            post_msg = []
        if code:
            post_msg.extend([_('Code: %s') % code])
        if msg:
            post_msg.extend([_('Message: %s') % msg])
        self.message_post(
            body=body_msg + account_invoice.create_list_html(post_msg))

    @api.multi
    def sign_cfdi(self):
        invoice = self.env['account.invoice']
        for record in self.filtered('cfdi_nomina'):
            pac_usr = ''
            pac_pwd = ''
            pac_url = ''
            pac_params_ids = self.env['params.pac'].search([
                ('method_type', '=', 'firmar'),
                ('company_id', '=', record.company_id.id),
                ('active', '=', True)], limit=1)
            if not pac_params_ids:
                raise ValidationError(_(
                    'No tienes parametros del PAC configurados'))
            pac_usr = pac_params_ids.user
            pac_pwd = pac_params_ids.password
            pac_url = pac_params_ids.url_webservice
            client = Client(pac_url, cache=None)
            xml = [self.cfdi_nomina.decode('utf-8')]
            resultado = client.service.stamp(xml, pac_usr, pac_pwd)
            if resultado.Incidencias:
                code = getattr(resultado.Incidencias[0][0], 'CodigoError',
                               None)
                msg = getattr(resultado.Incidencias[0][0],
                              'MensajeIncidencia' if code != '301' else 'ExtraInfo', None)  # noqa
                raise ValidationError(_(' %s - %s ' % (code, msg)))

            if not resultado.Incidencias or None:
                folio_fiscal = resultado.UUID or False

                original_string = invoice._create_original_str(resultado)
                self.cfdi_nomina = base64.b64encode(resultado.xml.encode())
                self.l10n_mx_edi_cfdi = base64.b64encode(resultado.xml.encode())
                data_cfdi = {
                    'cfdi_folio_fiscal': folio_fiscal,
                    'cfdi_cadena_original': original_string,
                }
                self.write(data_cfdi)

    @api.multi
    def _l10n_mx_edi_post_cancel_process(self, cancelled, code=None, msg=None):
        '''Post process the results of the cancel service.

        :param cancelled: is the cancel has been done with success
        :param code: an eventual error code
        :param msg: an eventual error msg
        '''

        self.ensure_one()
        if cancelled:
            body_msg = _('The cancel service has been called with success')
            self.l10n_mx_edi_pac_status = 'cancelled'
        else:
            body_msg = _('The cancel service requested failed')
        post_msg = []
        if code:
            post_msg.extend([_('Code: %s') % code])
        if msg:
            post_msg.extend([_('Message: %s') % msg])
        self.message_post(
            body=body_msg + create_list_html(post_msg),
            subtype='account.mt_invoice_validated')

    def set_sign_data(self):
        invoice_obj = self.env['account.invoice']
        for payroll in self:
            company = payroll.company_id
            certificate_ids = self.company_id.l10n_mx_edi_certificate_ids
            certificate_id = certificate_ids.sudo().get_valid_certificate()
            if not certificate_id:
                raise ValidationError(_(
                    'No tienes definido certificado para esta compañia !'))
            xml = base64.decodestring(payroll.cfdi_nomina)
            cadena = invoice_obj.generate_cadena_original(
                xml, {'path_cadena': CFDI_XSLT_CADENA})
            #sello = certificate_id.get_sello(cadena)
            sello = certificate_id.get_encrypted_cadena(cadena)
            tree = objectify.fromstring(xml)
            tree.attrib['Sello'] = sello
            xml = etree.tostring(
                tree, pretty_print=True,
                xml_declaration=True, encoding='UTF-8')
            self.cfdi_nomina = base64.b64encode(xml)
            self.l10n_mx_edi_cfdi = base64.b64encode(xml)

    @api.model
    def _get_xml_etree(self):
        self.ensure_one()
        if self.cfdi_nomina:
            cfdi = base64.decodebytes(self.cfdi_nomina)
            return objectify.fromstring(cfdi)

    @api.model
    def _get_stamp_data(self, cfdi):
        self.ensure_one()
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
    #  Anexo hr_payroll_account/hr_apayslip  #
    ##########################################
    def _default_journal_id(self):
        # TODO: Add a way to set a journal type for payslips
        res = self.env['account.journal'].search(
            [('type', '=', 'purchase')], limit=1,
        )
        return res.id and res or False

    journal_id = fields.Many2one(
        'account.journal', 'Salary Journal',
        states={'draft': [('readonly', False)]}, readonly=True,
        required=True, default=lambda self: self._default_journal_id(),
    )
    move_id = fields.Many2one(
        'account.move', 'Accounting Entry', readonly=True, copy=False,
    )

    @api.model
    def create(self, vals):
        if 'journal_id' in self._context:
            vals.update({'journal_id': self._context.get('journal_id')})
        return super(HrPayslip, self).create(vals)

    @api.onchange('contract_id')
    def onchange_contract(self):
        self.journal_id = self.contract_id.journal_id.id or False
        return super(HrPayslip, self).onchange_contract()

#     def cancel_sheet(self, cr, uid, ids, context=None):
#         context = dict(context or {})
#         move_pool = self.pool.get('account.move')
#         move_ids = []
#         move_to_cancel = []
#         for slip in self.browse(cr, uid, ids, context=context):
#             if slip.move_id:
#                 move_ids.append(slip.move_id.id)
#                 if slip.move_id.state == 'posted':
#                     move_to_cancel.append(slip.move_id.id)
#         move_pool.button_cancel(cr, uid, move_to_cancel, context=context)
#         move_pool.unlink(cr, uid, move_ids, context=context)
#         return super(HrPayslip, self).cancel_sheet(cr, uid, ids, context=context)

#     def process_sheet(self, cr, uid, ids, context=None):
#         move_pool = self.pool.get('account.move')
#         period_pool = self.pool.get('account.period')
#         precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Payroll')

#         for slip in self.browse(cr, uid, ids, context=context):
#             line_ids = []
#             debit_sum = 0.0
#             credit_sum = 0.0
#             if not slip.period_id:
#                 ctx = dict(context or {}, account_period_prefer_normal=True)
#                 search_periods = period_pool.find(cr, uid, slip.date_to, context=ctx)
#                 period_id = search_periods[0]
#             else:
#                 period_id = slip.period_id.id

#             default_partner_id = slip.employee_id.address_home_id.id
#             name = _('Payslip of %s') % (slip.employee_id.name)
#             move = {
#                 'name': slip.number,
#                 'narration': name,
#                 'date': slip.date_to,
#                 'ref': slip.number.replace('/', ''),
#                 'journal_id': slip.journal_id.id,
#                 'period_id': period_id,
#             }
#             for line in slip.details_by_salary_rule_category:
#                 amt = slip.credit_note and -line.total or line.total
#                 if float_is_zero(amt, precision_digits=precision):
#                     continue
#                 partner_id = line.salary_rule_id.register_id.partner_id and line.salary_rule_id.register_id.partner_id.id or default_partner_id
#                 debit_account_id = line.salary_rule_id.account_debit.id
#                 credit_account_id = line.salary_rule_id.account_credit.id

#                 if debit_account_id:
#                     vals = {
#                         'name': line.name,
#                         'date': slip.date_to,
#                         'partner_id': partner_id or False,
#                         'account_id': debit_account_id,
#                         'journal_id': slip.journal_id.id,
#                         'period_id': period_id,
#                         'debit': amt > 0.0 and amt or 0.0,
#                         'credit': amt < 0.0 and -amt or 0.0,
#                         'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
#                         'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
#                         'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
#                     }
#                     debit_line = (0, 0, vals)
#                     line_ids.append(debit_line)
#                     debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

#                 if credit_account_id:
#                     vals = {
#                         'name': line.name,
#                         'date': slip.date_to,
#                         'partner_id': partner_id or False,
#                         'account_id': credit_account_id,
#                         'journal_id': slip.journal_id.id,
#                         'period_id': period_id,
#                         'debit': amt < 0.0 and -amt or 0.0,
#                         'credit': amt > 0.0 and amt or 0.0,
#                         'analytic_account_id': line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False,
#                         'tax_code_id': line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False,
#                         'tax_amount': line.salary_rule_id.account_tax_id and amt or 0.0,
#                     }
#                     credit_line = (0, 0, vals)
#                     line_ids.append(credit_line)
#                     credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

#             if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
#                 acc_id = slip.journal_id.default_credit_account_id.id
#                 if not acc_id:
#                     raise ValidationError(
#                         _('The Expense Journal "%s" has not properly '
#                           'configured the Credit Account!') %
#                         (slip.journal_id.name),
#                     )
#                 adjust_credit = (0, 0, {
#                     'name': _('Adjustment Entry'),
#                     'date': slip.date_to,
#                     'partner_id': False,
#                     'account_id': acc_id,
#                     'journal_id': slip.journal_id.id,
#                     'period_id': period_id,
#                     'debit': 0.0,
#                     'credit': debit_sum - credit_sum,
#                 })
#                 line_ids.append(adjust_credit)

#             elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
#                 acc_id = slip.journal_id.default_debit_account_id.id
#                 if not acc_id:
#                     raise ValidationError(
#                         _('The Expense Journal "%s" has not properly '
#                           'configured the Debit Account!') %
#                         (slip.journal_id.name),
#                     )
#                 adjust_debit = (0, 0, {
#                     'name': _('Adjustment Entry'),
#                     'date': slip.date_to,
#                     'partner_id': False,
#                     'account_id': acc_id,
#                     'journal_id': slip.journal_id.id,
#                     'period_id': period_id,
#                     'debit': credit_sum - debit_sum,
#                     'credit': 0.0,
#                 })
#                 line_ids.append(adjust_debit)

#             move.update({'line_id': line_ids})
#             move_id = move_pool.create(cr, uid, move, context=context)
#             self.write(
#                 cr, uid, [slip.id],
#                 {'move_id': move_id, 'period_id': period_id},
#                 context=context,
#             )
#             if slip.journal_id.entry_posted:
#                 move_pool.post(cr, uid, [move_id], context=context)
#         return super(HrPayslip, self).process_sheet(cr, uid, [slip.id], context=context)

    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!#
    #  Anexo hr_payroll_attendance/hr_apayslip#
    ##########################################


    @api.model
    def _have_worked(self, working_calendar, employee, day):
        """
        Determine if employee have worked on a given day

        Search in hr.attendance records in order to see if employee have
        arrive to work on a given day.

        @param working_calendar: The calendar that define working days
        @type working_calendar: resource.calendar
        @param employee: The employee to test
        @type employee: hr.employee
        @param day: The day to test
        @type day: Datetime
        @return: True if employee have worked False otherwise
        @rtype: bool
        """
        have_worked = self.env['hr.attendance'].have_worked(
            working_calendar, employee, day,
        )
        return have_worked

    @api.model
    def _late_hours(self, working_calendar, employee, day):
        """
        Determine if employee arrive late to work on a given day

        @param working_calendar: The calendar that define working days
        @type working_calendar: resource.calendar
        @param employee: The employee to test
        @type employee: hr.employee
        @param day: The day to test
        @type day: Datetime
        @return: Hours employee arrives late
        @rtype: int
        """
        late_hours = self.env['hr.attendance'].late_hours(
            working_calendar, employee, day,
        )
        return late_hours

    @api.model
    def _overtime_hours(self, working_calendar, employee, day):
        """
        Determine if employee do overtime on a given day
        The function in this module is just a placeholder, other modules must
        inherit and extend.

        @param working_calendar: The calendar that define working days
        @type working_calendar: resource.calendar
        @param employee: The employee to test
        @type employee: hr.employee
        @param day: The day to test
        @type day: Datetime
        @return: Hours employee do on overtime
        @rtype: int
        """
        overtime_hours = self.env['hr.attendance'].overtime_hours(
            working_calendar, employee, day,
        )
        return overtime_hours


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def action_payslips_done(self):
        self.ensure_one()
        for payslip in self.slip_ids.filtered(lambda p: p.state == 'draft'):
            try:
                payslip.source_resource = self.source_resource
                payslip.action_payslip_done()
            except ValidationError as ex:
                payslip.message_post(body=ex.name)

    source_resource = fields.Selection([
        ('IP', 'Own income'),
        ('IF', 'Federal income'),
        ('IM', 'Mixed income')],
        help='If this value is set will be assigned in all the payslips '
        'related.')
