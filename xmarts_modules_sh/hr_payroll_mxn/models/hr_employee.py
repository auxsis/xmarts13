# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    work_number = fields.Char(
        'Employee Number', required=True, size=15,
    )
    vat = fields.Char(required=True)
    curp = fields.Char('CURP', required=True)
    address_fiscal_id = fields.Many2one(
        'res.partner', string='Fiscal Address', required=True,
    )
    syndicated = fields.Boolean(
        help='Helper field to indicate if employee is syndicated or not',
    )
    # Other employee benefits
    infonavit_loan_type = fields.Selection(
        selection=(['none', 'None'], ['percent', 'Percent'],
                   ['fixed', 'Fixed Amount'], ['smvdf', 'Minimal Wage Times']),
        default='none',
        help='Select the Infonavit loan that employee is currently paying.'
        'The amount will be deducted from paysilp automatically according'
        'with loan type you selected on this field\n'
        'Use none for employees with no active infonavit loan to pay.',
    )
    infonavit_loan_qty = fields.Float(
        string='Amount',
        help='For loan percent the decimal percent amount.\n'
        'For Minimal Wage the qty of Minimal Wage',
    )
    infonavit_loan_amount = fields.Float(
        help='Amount per day to deduct when employee have an active credit',
    )

    @api.constrains('work_number')
    def _check_work_number(self):
        pattern = re.compile(
            '([A-Z]|[a-z]|[0-9]|Ñ|ñ|!|"|%|&|\'|´|-|:|;|>|=|<|@|_|,|{|}|`|~|á'
            '|é|í|ó|ú|Á|É|Í|Ó|Ú|ü|Ü){1,15}',
        )
        wrong = self.mapped(
            lambda r: not bool(pattern.match(r.work_number)),
        )
        if any(wrong):
            raise ValidationError(
                _('Invalid Employee Number'),
            )
        return

    @api.constrains('ssnid')
    def _check_medical_insurance(self):
        pattern = re.compile('[0-9]{1,15}')
        wrong = self.mapped(
            lambda r: not bool(pattern.match(r.work_number)),
        )
        if any(wrong):
            raise ValidationError(
                _('Invalid Social Security Number'),
            )
        return
