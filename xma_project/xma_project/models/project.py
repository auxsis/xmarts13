# -*- coding: utf-8 -*-

from odoo import fields, models


class Project(models.Model):
    _inherit = "project.project"

    xmasubscription_id = fields.Many2one(
        "xmarts.subscription", string="Subscription",

    )
    module_ids = fields.Many2many(
        "crm.lead.tag", string="Modules", related="xmasubscription_id.tag_ids"
    )
    develop_modules = fields.Char(string="Develop Modules")
    thirdpart_modules = fields.Char(string="Third Part Modules")
    reports = fields.Char(string="Reports Include")
    user_number = fields.Integer(string="User Number",)
    metodology = fields.Selection(
        [
            ("pmp", "PMP"),
            ("qs", "QuickStart"),
            ("upd", "Update"),
            ("sup", "Support")
        ], string="Metodology"
    )
    consultant_hours = fields.Integer(string="Consultant Hours")
    develop_hours = fields.Integer(string="Develop Hours")
    companies = fields.Integer(string="Companies")
    description = fields.Char(string="Description")
    # partner_id = fields.Many2one(
    #     "res.partner", string="Contact"
    # )
