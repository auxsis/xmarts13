# -*- coding: utf-8 -*-

from odoo import models, fields

class TypeOfSubject(models.Model):
    _name = 'type.of.subject'
    
    name = fields.Char(
        'Name',
        required=True,
    )
