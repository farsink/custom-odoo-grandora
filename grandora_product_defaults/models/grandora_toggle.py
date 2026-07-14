from odoo import api, models


class GrandoraProductDefaultsToggle(models.AbstractModel):
    _name = "grandora.product.defaults.toggle"
    _description = "Grandora Product Defaults Toggle"

    @api.model
    def _grandora_product_defaults_enabled(self):
        value = self.env["ir.config_parameter"].sudo().get_param(
            "grandora_product_defaults.enabled",
            "True",
        )
        return value not in (False, "False", "false", "0", "no", "No")
