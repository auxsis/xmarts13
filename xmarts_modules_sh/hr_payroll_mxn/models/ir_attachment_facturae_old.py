# -*- coding: utf-8 -*-

from odoo.osv import orm


class IrAttachmentFacturaeMx(orm.Model):
    _inherit = 'ir.attachment.facturae.mx'

    # Extend _get_signed_xml to be able to sign a payroll
    def _get_signed_xml(self, cr, uid, ids, context):
        context = dict(context or {})
        hr_paysilp_obj = self.pool.get('hr.payslip')
        result = super(IrAttachmentFacturaeMx, self)._get_signed_xml(
            cr, uid, ids, context=context,
        )
        for attachment in self.browse(cr, uid, ids, context=context):
            if attachment.type_attachment == 'hr.payslip':
                result = hr_paysilp_obj._get_signed_xml(
                    cr, uid, [attachment.res_id], context=context,
                )
        return result
