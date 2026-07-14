from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("default_code"):
                continue
            template = self.env["product.template"].browse(vals.get("product_tmpl_id")) if vals.get("product_tmpl_id") else False
            if template and template.default_code:
                vals["default_code"] = template.default_code
            elif template and template.categ_id:
                vals["default_code"] = template.categ_id._grandora_next_product_sku()
        return super().create(vals_list)
