# -*- coding: utf-8 -*-

from datetime import datetime, date

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = 'hr.contract'

    isr_table = fields.Many2one(
        'isr.table.type', 'Tipo de Pago', required=True,
        help='Utilizado para calculo de ISR',
    )
    vacaciones = fields.Integer('Vacation Days', required=True)
    prima_v = fields.Float('Prima Vacacional %', required=True)
    aguinaldo = fields.Integer('Dias de Aguinaldo', required=True)
    tipo_regimen = fields.Many2one(
        'regimen.employee', 'Tipo de Regimen', required=True,
    )
    riesgo_puesto = fields.Many2one('since.risk', 'Since risk')
    integrated_wage = fields.Float(
        compute='_compute_integrated_wage', store=True,
        help='Utilizado para calculo de cuotas IMSS',
    )
    daily_wage = fields.Float(compute='_compute_wages', store=True)
    hourly_wage = fields.Float(compute='_compute_wages', store=True)
    infonavit_loan_amount = fields.Float(
        compute='_compute_infonavit_loan_amount', sotore=True,
        help='Daily amount to discount employee because of infonavit loan',
    )
    working_hours = fields.Many2one(
        'resource.calendar', 'Working Schedule',
    )
    worked_days_on_year = fields.Integer(
        compute='_compute_days_on_year',
        help='Helper field to compute days worked on current year for use'
        'in Christmas box calculations',
    )
    days_on_year = fields.Integer(
        compute='_compute_days_on_year',
        help='Helper field to compute days for current year for use'
        'in Christmas box calculations',
    )
    label_isr_table = fields.Char(compute='_compute_isr_table')

    @api.one
    @api.depends('wage', 'isr_table', 'working_hours')
    def _compute_wages(self):
        worked_days = self.isr_table.number_of_days
        working_hours = self.working_hours.hours_day
        try:
            self.daily_wage = self.wage / worked_days
            self.hourly_wage = self.daily_wage / working_hours
        except ZeroDivisionError:
            pass
    @api.one
    @api.depends('isr_table')
    def _compute_isr_table(self):
        self.label_isr_table = self.isr_table.name

    @api.one
    @api.depends('wage', 'vacaciones', 'prima_v', 'aguinaldo')
    def _compute_integrated_wage(self):
        factor = (365 + self.aguinaldo + self.vacaciones * self.prima_v) / 365
        try:
            daily_wage = self.wage / self.isr_table.number_of_days
        except ZeroDivisionError:
            daily_wage = 0
        self.integrated_wage = daily_wage * factor

    @api.one
    @api.depends('integrated_wage', 'employee_id')
    def _compute_infonavit_loan_amount(self):
        amount = 0
        if self.employee_id.infonavit_loan_type == 'fixed':
            # Fixed amount is deduction per month. For calculate the daily
            # deduction we divide between 30.4 (standard days per month)
            amount = self.employee_id.infonavit_loan_qty / 30.4
        elif self.employee_id.infonavit_loan_type == 'percent':
            # When percent amount, simply multiply Base Wage (Integrated Wage)
            # per percentage indicated on field
            amount = self.integrated_wage * self.employee_id.infonavit_loan_qty
        elif self.employee_id.infonavit_loan_type == 'smvdf':
            # For this we need to get current Minimal Wage first
            min_wage = self.env['hr.payroll'].search(
                [('date_start', '<=', self.date_from)], limit=1,
                order='date_start desc',
            ).smgvdf
            # Then multiply the wage per qty on employee loan and divide
            # between 30.4 (standard days per month)
            amount = min_wage * self.employee_id.infonavit_loan_qty / 30.4
        self.infonavit_loan_amount = amount

    @api.one
    def _compute_days_on_year(self):
        first = date(datetime.today().year, 1, 1)
        last = date(datetime.today().year, 12, 31)
        begin = self.date_start
        # If contracts begins on past years, begin becomes first day
        # for this year
        if first > self.date_start:
            begin = first

        if not self.date_end:
            end = last
        else:
            end = self.date_end

        self.worked_days_on_year = (end - begin).days + 1
        self.days_on_year = (last - first).days + 1

class HrContractType(models.Model):
    _inherit = 'hr.contract.type'

    code = fields.Char(help='Code that will be used in the CFDI generation')
