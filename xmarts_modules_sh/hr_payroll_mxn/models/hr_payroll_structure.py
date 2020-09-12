# -*- coding: utf-8 -*-

from odoo import fields, models


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    payslip_type_id = fields.Many2one(
        'hr.payslip.type', string='Payslip Type', required=True,
    )
