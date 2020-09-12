# -*- coding: utf-8 -*-

from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    hours_day = fields.Integer(required=True)
    calendar_type_id = fields.Many2one(
        'resource.calendar.type', string='Calendar type', required=True,
    )
