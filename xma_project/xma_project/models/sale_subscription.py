# -*- coding: utf-8 -*-

from odoo import fields, models


class SaleSubscription(models.Model):
    _inherit = "sale.subscription"

    odoo_subscription_id = fields.Many2one(
        "xmarts.subscription", string='Odoo subscription'
    )
