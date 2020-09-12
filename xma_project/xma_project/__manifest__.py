# -*- coding: utf-8 -*-
{
    'name': "Xmarts Project",
    'summary': """ """,
    'description': """ """,
    'author': "Xmarts",
    'website': "http://www.xmarts.com",
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['crm', 'mail', 'sale_subscription', 'project'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale_subscription_view.xml',
        'views/xmarts_subscription_view.xml',
        'views/xmarts_server_view.xml',
        'views/project_inherit_view.xml',
        'views/report.xml',
        'views/odoo_order.xml',
    ],

}
