# -*- coding: utf-8 -*-

from odoo import fields, models


class OdooOrder(models.Model):
    _name = "odoo.order"

    name = fields.Char(string="Odoo Order")
    subscription_ids = fields.One2many(
        "xmarts.subscription", "odoo_order_id", string="Subscription"
    )