# -*- coding: utf-8 -*

from odoo import models, fields, api

class CustomerPrice(models.Model):
    _inherit = 'res.partner'

    product_id_helpdesk = fields.Many2one(
        'product.product',
        string='Product',
    )
    
    @api.multi
    @api.depends('ticket_ids')
    def _ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)

    price_rate = fields.Float(
        string='Price / Rate (Company Currency)',
        default=0.0,
        copy=False,
    )

    ticket_count = fields.Integer(
        compute = '_ticket_count',
        store=True,
     )
    ticket_ids = fields.One2many(
        'helpdesk.support',
        'partner_id',
        string='Helpdesk Ticket',
        readonly=True,
    )
     
    @api.multi
    def show_ticket(self):
        for rec in self:
            res = self.env.ref('website_helpdesk_support_ticket.action_helpdesk_support')
            res = res.read()[0]
            res['domain'] = str([('partner_id','=',rec.id)])
        return res
