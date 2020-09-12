# -*- coding: utf-8 -*-

from odoo import fields, models


class SalaryPaymentType(models.Model):
    """Object that holds the payment type catalog used for field
    c_TipoOtroPago on SAT specifications
    """

    _name = 'salary.payment.type'
    _description = __doc__
    _order = 'code ASC'

    code = fields.Char(size=3, required=True)
    name = fields.Char('Description', required=True)
