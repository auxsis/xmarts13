# -*- coding: utf-8 -*-

from odoo import fields, models


class IsrTableType(models.Model):
    """Object used to hold payment periods catalog
    """

    _name = 'isr.table.type'
    _description = __doc__

    active = fields.Boolean(
        'Active', default=True,
        help='If the active field is set to False, it will allow you to hide '
        'the isr type without removing it.',
    )
    name = fields.Char('Description', required=True)
    code = fields.Char(required=True)
    number_of_days = fields.Float(
        help='Internal field used for indicate number of days covered by this'
        'payment period',
    )
