# -*- coding: utf-8 -*-

from odoo import fields, models 


class XmartsServers(models.Model):
    _name = "xmarts.server"

    name = fields.Char(string="Name", index=True, required=True)
    active = fields.Boolean(string="Active", default=True)
    user = fields.Char(string="User", index=True, required=True)
    server_ip = fields.Char(string="Ip", required=True)
