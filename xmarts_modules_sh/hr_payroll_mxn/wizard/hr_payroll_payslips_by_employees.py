# -*- coding: utf-8 -*-

from openerp import api, models
from openerp.exceptions import ValidationError
from openerp.tools.translate import _


class HrPayslipEmployees(models.TransientModel):

    _inherit = 'hr.payslip.employees'

    @api.multi
    def compute_sheet(self):
        self.ensure_one()

        active_id = self.env.context.get('active_id', False)
        payslip_run = self.env['hr.payslip.run'].browse(active_id)

        if not payslip_run.journal_id:
            raise ValidationError(
                _('The journal is not set on the payslip run.'),
            )

        ctx = dict(self.env.context)
        ctx['journal_id'] = payslip_run.journal_id.id
        self = self.with_context(ctx)

        return super(HrPayslipEmployees, self).compute_sheet()
