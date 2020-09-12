# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ResCompany(models.Model):
    _inherit = 'res.company'

    patron_registration = fields.Char()
    risk_company = fields.Float(string='Prima de Riesgo')
    curp = fields.Char('CURP')

    @api.one
    @api.constrains('partner_id', 'curp')
    def _check_curp(self):
        """When company is "persona física" we need curp for payslips
        """
        if self.partner_id.property_account_position.code in ['612']:
            if not self.curp:
                raise ValidationError(
                    _('CURP is needed for the fiscal position you selected.'),
                )
