# -*- coding: utf-8 -*-

from odoo import fields, models


class OvertimeType(models.Model):
    """Object used to hold overtime type catalog
    """
    _name = 'overtime.type'
    _description = __doc__
    _order = 'code ASC'

    name = fields.Char('Description', required=True)
    code = fields.Char(size=2, required=True)
