# -*- coding: utf-8 -*-

from odoo import fields, models


class XmartsSubscription(models.Model):
    _name = "xmarts.subscription"
    _description = "Xmarts Subscription"
    _inherit = "mail.thread"
    _order = "name"

    name = fields.Char(
        string="Name", index=True, required=True, help="Name of subscription"
    )
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(
        string="Sequence", default=10,
        help="Gives the sequence order when displaying a list of Projects."
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer", auto_join=True,
        track_visibility="onchange"
    )
    logo = fields.Binary(related="partner_id.image")
    description = fields.Char(string="Description")
    gigas = fields.Integer(string="Gigas")
    workers = fields.Integer(string="Workers")
    odoo_order_id = fields.Many2one("odoo.order", string="Odoo Order")
    code = fields.Char(
        string="Reference", required=True,
        help="Odoo subscription reference or Opensource subscription"
    )
    stage_id = fields.Many2one(
        "sale.subscription.stage", string="Stage"
    )
    template_id = fields.Many2one(
        "sale.subscription.template",
        string="Subscription Template",
        related="subscription_id.template_id"
    )
    subscription_id = fields.Many2one(
        "sale.subscription", string="Subscription", required=True
    )
    date_start = fields.Date(
        string="Start Date", default=fields.Date.today, required=True
    )
    success_history = fields.Boolean(
        string="Success History", default=False, required=True
    )
    tag_ids = fields.Many2many(
        "crm.lead.tag", string="Tags",
        help="Classify and analyze your lead/opportunity "
             "categories like: Training, Service"
    )
    server_id = fields.Many2one("xmarts.server", string="Server")
    account_manager_id = fields.Many2one(
        "res.partner", string="Account Manager"
    )
    initial_users = fields.Integer(string="Initial Users", required=True)
    users = fields.Integer(
        string="Users", track_visibility="onchange", required=True
    )



