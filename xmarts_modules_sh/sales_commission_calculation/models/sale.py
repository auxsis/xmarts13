# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import UserError, ValidationError
import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    commission_manager_id = fields.Many2one(
        'sales.commission.line',
        string='Sales Commission for Manager'
    )
    commission_person_id = fields.Many2one(
        'sales.commission.line',
        string='Sales Commission for Member'
    )
    
    @api.multi
    def get_categorywise_commission(self):
        sum_line_manager = []
        sum_line_person = []
        for order in self:
            for line in order.order_line:
                sum_line_manager.append((line.price_subtotal * line.product_id.categ_id.sales_manager_commission)/100)
                sum_line_person.append((line.price_subtotal * line.product_id.categ_id.sales_person_commission)/100)
            amount_manager = sum(sum_line_manager)
            amount_person = sum(sum_line_person)
        return amount_person, amount_manager
    
    @api.multi
    def get_productwise_commission(self):
        sum_line_manager = []
        sum_line_person = []
        for order in self:
            for line in order.order_line:
                sum_line_manager.append((line.price_subtotal * line.product_id.sales_manager_commission)/100)
                sum_line_person.append((line.price_subtotal * line.product_id.sales_person_commission)/100)
            amount_manager = sum(sum_line_manager)
            amount_person = sum(sum_line_person)
        return amount_person, amount_manager
    
    @api.multi
    def get_teamwise_commission(self):
        sum_line_manager = []
        sum_line_person = []
        for order in self:
            amount_manager = (order.amount_untaxed * order.team_id.sales_manager_commission)/100
            amount_person = (order.amount_untaxed * order.team_id.sales_person_commission)/100

        return amount_person, amount_manager

    @api.multi
    def create_commission(self, amount,commission,type):
        commission_obj = self.env['sales.commission.line']
        product = self.env['product.product'].search([('is_commission_product','=',1)],limit=1)
        for order in self:
            #Salesperson
            if amount != 0.0:
                commission_value = {
                    #'sales_team_id': order.team_id.id,
                    #'commission_user_id': order.user_id.id,
                    'amount': amount,
                    'origin': order.name,
                    'type':type,
                    'product_id': product.id,
                    'date' : order.confirmation_date,
                    'src_order_id': order.id,
                    'sales_commission_id':commission.id,
                    'sales_team_id': order.team_id and order.team_id.id or False,
                }
                commission_id = commission_obj.create(commission_value)
                if type == 'sales_person':
                    order.commission_person_id = commission_id.id
                if type == 'sales_manager':
                    order.commission_manager_id = commission_id.id

        return True

    @api.multi
    def create_base_commission(self, type):
        commission_obj = self.env['sales.commission']
        product = self.env['product.product'].search([('is_commission_product','=',1)],limit=1)
        for order in self:
            if type == 'sales_person':
                user = order.user_id.id
            if type == 'sales_manager':
                user = order.team_id.user_id.id

            today = date.today()
            first_day = today.replace(day=1)
            last_day = datetime.datetime(today.year,today.month,1)+relativedelta(months=1,days=-1)
            commission_value = {
                    'start_date' : first_day,
                    'end_date': last_day,
                    'product_id':product.id,
                    'commission_user_id': user,
                }
            commission_id = commission_obj.create(commission_value)
        return commission_id

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

#         when_to_pay = self.env['ir.values'].get_default('sale.config.settings', 'when_to_pay')
        when_to_pay = self.env['ir.config_parameter'].sudo().get_param('sales_commission_calculation.when_to_pay') #odoo11
        if  when_to_pay == 'sales_confirm':
#             commission_based_on = self.env['ir.values'].get_default('sale.config.settings', 'commission_based_on')
            commission_based_on = self.env['ir.config_parameter'].sudo().get_param('sales_commission_calculation.commission_based_on') #odoo11
            for order in self:
                if commission_based_on == 'sales_team':
                    amount_person, amount_manager = order.get_teamwise_commission()
                elif commission_based_on == 'product_category':
                    amount_person, amount_manager = order.get_categorywise_commission()
                elif commission_based_on == 'product_template':
                    amount_person, amount_manager = order.get_productwise_commission()

                #Sale Person
                commission = self.env['sales.commission'].search([
                    ('commission_user_id', '=', order.user_id.id),
                    ('start_date', '<', order.date_order),
                    ('end_date', '>', order.date_order),
                    ('state','=','draft')], limit=1)
                if not commission:
                    commission = order.create_base_commission(type='sales_person')
                order.create_commission(amount_person, commission, type='sales_person')

                #Sale Manager
                if not order.user_id.id == order.team_id.user_id.id and order.team_id.user_id:
                    commission = self.env['sales.commission'].search([
                        ('commission_user_id', '=', order.team_id.user_id.id),
                        ('start_date', '<', order.date_order),
                        ('end_date', '>', order.date_order),
                        ('state','=','draft')],limit=1)
                    if not commission:
                        commission = order.create_base_commission(type='sales_manager')
                    order.create_commission(amount_manager,commission, type='sales_manager')

                #order.create_commission(amount_person, amount_manager)

        return res
    
    @api.multi
    def action_cancel(self):
        res = super(SaleOrder, self).action_cancel()
        for rec in self:
            if rec.commission_manager_id:
                rec.commission_manager_id.state = 'exception'
            if rec.commission_person_id:
                rec.commission_person_id.state = 'exception'
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
