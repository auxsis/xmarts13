# -*- coding: utf-8 -*-
from odoo import http

# class HrPayrollMxn(http.Controller):
#     @http.route('/hr_payroll_mxn/hr_payroll_mxn/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_payroll_mxn/hr_payroll_mxn/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_payroll_mxn.listing', {
#             'root': '/hr_payroll_mxn/hr_payroll_mxn',
#             'objects': http.request.env['hr_payroll_mxn.hr_payroll_mxn'].search([]),
#         })

#     @http.route('/hr_payroll_mxn/hr_payroll_mxn/objects/<model("hr_payroll_mxn.hr_payroll_mxn"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_payroll_mxn.object', {
#             'object': obj
#         })