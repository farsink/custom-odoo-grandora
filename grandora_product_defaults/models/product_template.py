from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _grandora_default_category(self):
        return self.env.ref("grandora_product_defaults.product_category_grandora_food", raise_if_not_found=False)

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if "type" in fields_list:
            values.setdefault("type", "consu")
        if "is_storable" in fields_list:
            values.setdefault("is_storable", True)
        if "tracking" in fields_list:
            values.setdefault("tracking", "lot")
        if "lot_valuated" in fields_list:
            values.setdefault("lot_valuated", True)
        if "use_expiration_date" in fields_list:
            values.setdefault("use_expiration_date", True)
        if "categ_id" in fields_list and not values.get("categ_id"):
            category = self._grandora_default_category()
            if category:
                values["categ_id"] = category.id
        return values

    @api.model_create_multi
    def create(self, vals_list):
        default_category = self._grandora_default_category()
        for vals in vals_list:
            vals.setdefault("type", "consu")
            vals.setdefault("is_storable", True)
            vals.setdefault("tracking", "lot")
            vals.setdefault("lot_valuated", True)
            vals.setdefault("use_expiration_date", True)
            if default_category and not vals.get("categ_id"):
                vals["categ_id"] = default_category.id
            if not vals.get("default_code"):
                category = self.env["product.category"].browse(vals.get("categ_id")) if vals.get("categ_id") else default_category
                if category:
                    vals["default_code"] = category._grandora_next_product_sku()
        templates = super().create(vals_list)
        for template in templates:
            if template.default_code:
                template.product_variant_ids.filtered(lambda variant: not variant.default_code).write({"default_code": template.default_code})
        return templates

    def write(self, vals):
        res = super().write(vals)
        if vals.get("default_code"):
            for template in self:
                template.product_variant_ids.filtered(lambda variant: not variant.default_code).write({"default_code": template.default_code})
        return res
