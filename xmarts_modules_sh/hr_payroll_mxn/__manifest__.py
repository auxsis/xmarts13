# -*- coding: utf-8 -*-
{
    'name': "hr_payroll_mxn",

    'summary': """
        Modulo de Nomina mexicana para odoo12 enterprise""",

    'description': """
        Nomina MXN
    """,

    'author': "Xmarts",
    'collaborators':'BIOFHE',
    'website': "xmarts.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','resource','hr_attendance','hr_payroll','account','hr_expense','l10n_mx_edi','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_imss_table.xml',
        'views/hr_salary_rule.xml',
        'views/hr_payroll.xml',
        'views/hr_payroll_structure.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_type.xml',
        'views/overtime_type.xml',
        'views/res_company_view.xml',
        'views/resource_calendar.xml',
        'views/salary_payment_type.xml',
        'views/hr_payslip_report.xml',
        #vista de hr_payroll_account
        'views/hr_payroll_account_view.xml',
        'data/hr_contract_type_data.xml',
        'data/hr_factor_integration_data.xml',
        'data/hr_payroll_data.xml',
        'data/hr_payroll_imss_data.xml',
        'data/hr_payslip_type_data.xml',
        'data/hr_salary_rule_category.xml',
        'data/isr_table_type_data.xml',
        'data/l10n_mx_hr_ausent_data.xml',
        'data/l10n_mx_hr_incapacity_data.xml',
        'data/l10n_mx_hr_reset_work_data.xml',
        'data/overtime_type_data.xml',
        'data/regimen_employee_data.xml',
        'data/resource_calendar_type_data.xml',
        'data/resource_calendar_data.xml',
        'data/since_risk_data.xml',
        'data/salary_payment_type_data.xml',
        # This must be at the end because use the data from previous files
        'data/catalogo_TipoPercepcion.xml',
        'data/catalogo_OtrosPagos.xml',
        'data/catalogo_TipoDeduccion.xml',
        'data/catalogo_TipoRetenciones.xml',
        'data/catalogo_Obligaciones.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_payroll_isr_data.xml',
        'data/hr_payroll_isr_subcidio_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
        #'demo/hr_payroll_account_demo.xml',
    ],
}