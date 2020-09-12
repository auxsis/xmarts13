# -*- coding: utf-8 -*-

from odoo import fields, models


class ResourceCalendar(models.Model):
    """Object used to hold the resource calendar type that going to be
    mapped into the c_TipoJornada field for payroll 1.2 CFDI
    """

    _name = 'resource.calendar.type'
    _description = __doc__
    _order = 'code ASC'

    name = fields.Char('Description', required=True)
    code = fields.Char(size=2, required=True)
