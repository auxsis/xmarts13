from odoo import models

class ThemeCommon(models.AbstractModel):
    _inherit = 'theme.utils'

    def _theme_common_post_copy(self, mod):
        self.disable_view('website_theme_install.customize_modal')

        # For compatibility
        # self.enable_view('theme_common.compatibility-saas-11-4-variables')
        # self.enable_view('theme_common.compatibility-saas-11-4')
