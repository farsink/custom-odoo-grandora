from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product_type = vals.setdefault("type", "consu")
            if product_type == "consu":
                vals.setdefault("is_storable", True)
                if "tracking" not in vals and vals.get("is_storable"):
                    vals["tracking"] = "lot"
        return super().create(vals_list)
