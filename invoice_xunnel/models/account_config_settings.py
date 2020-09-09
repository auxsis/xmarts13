# Copyright 2018, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models, _
from odoo.addons.account_xunnel.models.account_config_settings import \
    assert_xunnel_token


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    xunnel_last_sync = fields.Date(
        string='Last Sync with Xunnel',
        related='company_id.xunnel_last_sync',
        readonly=False)

    @api.model
    def get_values(self):
        res = super(AccountConfigSettings, self).get_values()
        company = self.company_id
        res.update(
            xunnel_last_sync=company.xunnel_last_sync,
        )
        return res

    @api.multi
    def set_values(self):
        res = super(AccountConfigSettings, self).set_values()
        company = self.company_id
        company.write({
            'xunnel_last_sync': self.xunnel_last_sync,
        })
        return res

    @api.multi
    @assert_xunnel_token
    def sync_xunnel_attachments(self):
        result = self.company_id._sync_xunnel_attachments()
        message = _(
            "Success! %s xml have been downloaded.") % result
        return {
            'type': 'ir.actions.client',
            'tag': 'account_xunnel.syncrhonized_accounts',
            'name': _('Xunnel invoice response.'),
            'target': 'new',
            'message': message,
            'message_class': 'success',
        }
