from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product_type = vals.setdefault("type", "consu")
            if product_type == "consu":
                vals.setdefault("is_storable", True)
                if (
                    "tracking" not in vals
                    and vals.get("is_storable")
                    and self.env["product.template"]._grandora_should_default_lot_tracking()
                ):
                    vals["tracking"] = "lot"
        products = super().create(vals_list)
        products.product_tmpl_id._grandora_sync_standard_price_from_total()
        return products
