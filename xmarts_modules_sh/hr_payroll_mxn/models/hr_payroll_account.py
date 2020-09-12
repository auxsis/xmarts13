# -*- encoding: utf-8 -*-
# © <2018> <Quadit, S.A. de C.V.>
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import api, fields, models


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    analytic_account_id = fields.Many2one(
        'account.analytic.account')
    account_tax_id = fields.Many2one(
        'account.tax.code', 'Tax Code')
    account_debit = fields.Many2one('account.account')
    account_credit = fields.Many2one('account.account')


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    analytic_account_id = fields.Many2one('account.analytic.account')
    journal_id = fields.Many2one('account.journal', 'Salary Journal')


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Run'

    @api.returns('self')
    def _get_default_journal(self):
        model_data = self.env['ir.model.data']
        res = model_data.search([('name', '=', 'expenses_journal')])
        if res:
            return res.res_id
        return False

    journal_id = fields.Many2one(
        'account.journal', 'Salary Journal',
        states={'draft': [('readonly', False)]}, readonly=True, required=True,
        default=_get_default_journal)
