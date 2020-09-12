# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


legend = '''
# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories
# (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days
# inputs: object containing the computed inputs
# smgvdf: float object containing the current Minimal Wage

# Note: returned value have to be set in the variable 'result'

result = rules.NET > categories.NET * 0.10'''

tax_select_options = [
    ('none', 'Never'),
    ('always', 'Always'),
    ('python', 'Python Expression'),
]


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    code_sat = fields.Char('Sat code')
    salary_payment_type_id = fields.Many2one(
        'salary.payment.type', string='Payment type',
    )
    overtime_type_id = fields.Many2one(
        'overtime.type', string='Overtime type',
    )
    tax_select = fields.Selection(
        tax_select_options, 'Taxable Based on', required=True, default='none',
    )
    tax_python_compute = fields.Text(
        'Tax compute code', default=legend,
        help='Tax python compute code',
    )

    @api.multi
    def _satisfy_condition(self, localdict):
        """ :return: True if the given rule match the condition.
        False otherwise.
        """
        self.ensure_one()

        if self.condition_select == 'none':
            return True
        else:
            try:
                safe_eval(
                    self.condition_python,
                    localdict, mode='exec', nocopy=True,
                )
                return localdict.get('result', False)
            except Exception as err:
                raise ValidationError(
                    _('Wrong python condition defined for salary '
                      'rule %s (%s): %s') %
                    (self.name, self.code, err),
                )

    @api.multi
    def compute_tax(self, localdict):
        """
        Eval amount tax based on tax_select rule defined for salary rule
        :param localdict: dictionary containing the environement in which to
        compute the rule
        :return: returns a float as the tax amount computed
        :rtype: float
        """
        self.ensure_one()
        # Date from payslip to ensure use the proper Min wage
        date_from = localdict['payslip'].date_from

        rule = localdict['rule']

        if rule.tax_select == 'none':
            taxable_amount = 0
        elif rule.tax_select == 'always':
            taxable_amount = localdict[rule.code]
        else:
            # python code
            try:
                # Get current Minimum Wage
                smgvdf = self.env['hr.payroll'].search(
                    [('date_start', '<=', date_from)], limit=1,
                    order='date_start desc',
                ).smgvdf
                localdict['smgvdf'] = smgvdf
                safe_eval(
                    self.tax_python_compute,
                    localdict, mode='exec', nocopy=True,
                )
                return float(localdict['result'])
            except Exception as e:
                raise ValidationError(
                    _('Wrong python code defined for compute tax amount '
                      'for salary rule %s (%s): %s') % (
                          rule.name, rule.code, e),
                )

        return taxable_amount
