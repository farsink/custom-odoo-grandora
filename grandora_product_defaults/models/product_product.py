from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    brand_id = fields.Many2one(related="product_tmpl_id.brand_id", store=True, readonly=True)
    item_group_id = fields.Many2one(related="product_tmpl_id.item_group_id", store=True, readonly=True)

    @api.model
    def _grandora_product_defaults_enabled(self):
        return self.env["grandora.product.defaults.toggle"]._grandora_product_defaults_enabled()

    @api.model_create_multi
    def create(self, vals_list):
        if not self._grandora_product_defaults_enabled():
            return super().create(vals_list)
        for vals in vals_list:
            if vals.get("default_code"):
                continue
            template = self.env["product.template"].browse(vals.get("product_tmpl_id")) if vals.get("product_tmpl_id") else False
            if template and template.default_code:
                vals["default_code"] = template.default_code
            elif template and template.categ_id:
                vals["default_code"] = template.categ_id._grandora_next_product_sku()
        return super().create(vals_list)
