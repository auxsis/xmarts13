# -*- coding: utf-8 -*-

from odoo import fields, models


class SinceRisk(models.Model):
    """Object used to hold occupational risk for CFDI
    """

    _name = 'since.risk'
    _description = __doc__
    _order = 'clave ASC'

    name = fields.Char('Description', required=True)
    clave = fields.Char('Code', size=2, required=True)
    prime = fields.Float('Risk Pay', required=True)
