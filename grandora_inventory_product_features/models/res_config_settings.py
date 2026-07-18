from odoo import api, fields, models


_LOT_TRACKING_DEFAULT_PARAM = (
    "grandora_inventory_product_features.default_new_storable_products_to_lots"
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    new_storable_products_lot_tracking = fields.Boolean(
        string="Default New Storable Products to By Lots",
        default=True,
        help=(
            "When enabled, new storable goods default to lot tracking. "
            "An explicit tracking choice on a product always takes precedence."
        ),
    )

    @api.model
    def get_values(self):
        values = super().get_values()
        values["new_storable_products_lot_tracking"] = self.env[
            "product.template"
        ]._grandora_should_default_lot_tracking()
        return values

    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].sudo().set_param(
            _LOT_TRACKING_DEFAULT_PARAM,
            "True" if self.new_storable_products_lot_tracking else "False",
        )
