# -*- coding: utf-8 -*-

from odoo import api, fields, models


class HrPayslipType(models.Model):
    """Object used to define payslip type according to SAT specifications for
    Payslip CFDI version 1.2
    """

    _name = 'hr.payslip.type'
    _description = __doc__

    name = fields.Char(
        'Description', required=True, translate=True,
    )
    code = fields.Char(required=True, size=2)
    default = fields.Boolean(
        'Use as default?',
        help='The record whose being selected here will be used as default'
        'payslip type when user create a new salary structure.',
    )

    @api.model
    def create(self, vals):
        """
        Extend create function in order to update default record
        """
        if vals.get('default'):
            self._delete_default()
        return super(HrPayslipType, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        Extend write function in order to update default record
        """
        if vals.get('default'):
            self._delete_default()
        return super(HrPayslipType, self).write(vals)

    @api.model
    def _delete_default(self):
        """
        Delete default mark previous to save the record
        """
        marked_records = self.search([('default', '=', True)])
        marked_records.write({'default': False})
        return
