# -*- coding: utf-8 -*-

from odoo import fields, models


class HrPayroll(models.Model):
    """Payroll"""
    _name = 'hr.payroll'
    _description = __doc__

    smgvdf = fields.Float('Salario Minimo', required=True)
    date_start = fields.Date('Fecha de Inicio', required=True)
    date_end = fields.Date('Fecha de Finalizacion', required=False)
    actual = fields.Boolean()


class ImssTable(models.Model):
    _name = 'imss.table'
    _description = 'IMSS table'

    name = fields.Char(required=True)
    c_patronal = fields.Float('Cuota Patronal', required=True)
    c_obrera = fields.Float('Cuota Obrera', required=True)
    c_total = fields.Float('Cuota Total', required=True)
    base = fields.Char('Base Salarial', required=True)
    description = fields.Char()


class IsrTable(models.Model):
    _name = 'isr.table'
    _description = 'Tabla de ISR'

    type_id = fields.Many2one('isr.table.type', 'Tipo', required=True)
    limite_min = fields.Float('Limite Minimo', required=True)
    limite_max = fields.Float('Limite Maximo', required=True)
    cuota_fija = fields.Float(required=True)
    excedente = fields.Float('Porcentaje sobre excedente', required=True)


class IsrSubcidioTable(models.Model):
    _name = 'isr.subcidio.table'
    _description = 'Tabla de Subcidios de ISR'

    type_id = fields.Many2one('isr.table.type', 'Tipo', required=True)
    limite_min = fields.Float('Limite Minimo', required=True)
    limite_max = fields.Float('Limite Maximo', required=True)
    subcidio = fields.Float(required=True)


class EmployeeIncapacity(models.Model):
    _name = 'employee.incapacity'

    name = fields.Char('Descripcion', required=False)
    clave = fields.Char()


class FactorIntegrationImss(models.Model):
    _name = 'factor.integration.imss'
    _description = 'Factor de Integracion'

    name = fields.Integer(
        type='integer',
        relation='factor.integration.imss', string='Worked Years',
    )
    yearsworking = fields.Integer('Años Trabajados')
    holidays = fields.Integer('Dias de vacaciones')
    vacation = fields.Float('Prima Vacacional')
    porcentaje = fields.Float('Porcentaje')
    day_years = fields.Integer('Dias del año')
    factor_vacation = fields.Float('Factor por Vacaciones')
    aguinaldo = fields.Integer('Aguinaldo')
    factor = fields.Float('Factor por Aguinaldo')
    factor_integration = fields.Float('Factor de Integracion')


class HrVacations(models.Model):
# TODO: Why are we creating a new model when we can reuse the hr.holiday
    _name = 'hr.vacations'
    _description = 'Vacaciones del empleado'
    _inherit = ['mail.thread']

    name = fields.Char()
    employee_id = fields.Many2one(
        'hr.employee', string='Empleado', required=True,
        help='Empleado que toma vacaciones.',
    )
    vacations_ids = fields.One2many(
        'hr.vacations.line', 'employee_vacation_id',
    )


class HrVacationsLine(models.Model):
    # TODO: Why are we creating a new model when we can reuse
    # the hr.holiday.line
    _name = 'hr.vacations.line'
    _description = 'Linea, Vacaciones del empleado'
    _inherit = ['mail.thread']

    name = fields.Char(default=None)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee',
        help='Empleado que toma vacaciones.',
    )
    begin = fields.Date('Desde')
    end = fields.Date('Hasta')
    days = fields.Float('Days')
    employee_vacation_id = fields.Many2one(
        'hr.vacations', string='Employee',
        help='Empleado que toma vacaciones.',
    )


class ResetWorkDays(models.Model):
    # TODO: Why not reuse the hr.holiday model?
    _name = 'hr.reset.work'
    _inherit = ['mail.thread']

    name = fields.Date(
        'Day', required=True, help='Holiday date',
    )
    year = fields.Integer(
        help='Año en que este día esta vigente.'
    )
