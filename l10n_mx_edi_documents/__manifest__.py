# -*- coding: utf-8 -*-
{
    'name': 'Create Invoices from XML',
    'summary': 'Create Invoices from XML',
    'version': '12.0.1.0.0',
    'category': 'Localization/Mexico',
    'author': 'Vauxoo,Jarsa',
    'website': 'https://www.git.vauxoo.com/vauxoo/vendor-bills',
    'depends': [
        'l10n_mx_edi',
        'documents_account',
        'account_predictive_bills',
    ],
    'data': [
        'data/data.xml',
        'views/account_invoice.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': True,
}
