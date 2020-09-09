# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from codecs import BOM_UTF8
from time import mktime
from datetime import date

from lxml import objectify
from odoo import _, api, fields, models
from odoo.exceptions import UserError

BOM_UTF8U = BOM_UTF8.decode('UTF-8')


class ResCompany(models.Model):
    _inherit = 'res.company'

    xunnel_last_sync = fields.Date(
        string='Last Sync with Xunnel',
        default=lambda _: date.today())

    @api.model
    def _cron_xunnel_sync(self):
        """Sync all the attachments from all companies that have xunnel_provider
        """
        for rec in self.search([('xunnel_token', '!=', False)]):
            rec._sync_xunnel_attachments()

    @api.multi
    def _sync_xunnel_attachments(self):
        """Requests https://wwww.xunnel.com/ to retrive all invoices
        related to the current company and check them in the database
        to create them if they're not. After refresh xunnel_last_sync
        """
        self.ensure_one()
        if not self.vat and self.xunnel_token:
            raise UserError(
                _('You need to define the VAT of your company.'))
        values = dict(
            last_sync=False,
            vat=self.vat,
            xunnel_testing=self.xunnel_testing)
        if self.xunnel_last_sync:
            values.update(last_sync=mktime(
                self.xunnel_last_sync.timetuple()))
        response = self._xunnel('get_invoices_sat', values)
        err = response.get('error')
        if err:
            raise UserError(err)
        if response.get('response') is None:
            return True
        dates = []
        created = 0
        for item in response.get('response'):
            xml = item.lstrip(BOM_UTF8U).encode("UTF-8")
            xml_obj = objectify.fromstring(xml)
            dates.append(xml_obj.get('Fecha', ' '))
            uuid = self.env['account.invoice'].l10n_mx_edi_get_tfd_etree(
                xml_obj).get('UUID')
            name = 'Xunnel_' + uuid
            attachment = self.env['ir.attachment'].search([
                ('name', '=', name)])
            if not attachment:
                created += 1
                attachment.create({
                    'name': name,
                    'datas_fname': (
                        name + '.xml'),
                    'type': 'binary',
                    'datas': base64.encodestring(bytes(xml)),
                    'index_content': xml,
                    'mimetype': 'text/plain',
                })
        self.xunnel_last_sync = max(dates) if dates else self.xunnel_last_sync
        return created
