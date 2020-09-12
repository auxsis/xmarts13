# -*- coding: utf-8 -*-

from odoo import fields, models


class RegimenEmployee(models.Model):
    """Object use to hold catalog for employee regimen
    """
    _name = 'regimen.employee'
    _description = __doc__
    _order = 'clave ASC'

    name = fields.Char('Description', required=True)
    clave = fields.Char('Code', size=2, required=True)
