# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    'name': 'Xunnel Invoice',
    'summary': '''
        Use Xunnel Invoice to retrieve invoices from SAT.
    ''',
    'version': '12.0.1.0.31',
    'author': 'Jarsa Sistemas,Vauxoo',
    'category': 'Accounting',
    'website': 'http://www.jarsa.com.mx',
    'license': 'LGPL-3',
    'depends': [
        'account_xunnel',
        'l10n_mx_edi_vendor_bills',
    ],
    'data': [
        'data/ir_cron.xml',
        'views/account_config_settings.xml',
    ],
    'demo': [
        'demo/res_company.xml',
    ],
    'installable': True,
}
