# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Project Scrum Portal Agile',
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'license': 'AGPL-3',
    'description': """This application respects the scrum.org protocol
    and has been developed and is maintained by ITIL Certified Member
    (in course of certification).

    """,
    'summary': """This application respects the scrum.org protocol.""",
    'category': 'Project',
    'website': 'http://www.serpentcs.com',
    'version': '12.0.1.0.1',
    'sequence': 1,
    'depends': [
        'website',
        'project',
        'project_scrum_agile',
        'portal'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/website_data.xml',
        'views/assets.xml',
        'views/meetings.xml',
        'views/templates.xml',
        'views/backlog.xml',
        'views/sprints.xml',
    ],
    'images': ['static/description/ProjectScrumBanner.png'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'price': 149,
    'currency': 'EUR',
}
