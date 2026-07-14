from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(
        "product.brand",
        string="Brand",
        ondelete="restrict",
        help="Supplier/manufacturer brand. This is product master data, not a variant attribute.",
    )
    item_group_id = fields.Many2one(
        "product.item.group",
        string="Item Group",
        ondelete="restrict",
        help="Operational product group such as Frozen, Dairy, or Bakery. This is not a variant attribute.",
    )

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
            product_type = vals.setdefault("type", "consu")
            if product_type == "consu":
                vals.setdefault("is_storable", True)
                vals.setdefault("tracking", "lot")
                vals.setdefault("lot_valuated", True)
                vals.setdefault("use_expiration_date", True)
            else:
                vals.setdefault("is_storable", False)
                vals.setdefault("tracking", "none")
                vals.setdefault("lot_valuated", False)
                vals.setdefault("use_expiration_date", False)
            if vals.get("item_group_id") and not vals.get("categ_id"):
                item_group = self.env["product.item.group"].browse(vals["item_group_id"])
                if item_group.default_categ_id:
                    vals["categ_id"] = item_group.default_categ_id.id
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
        if vals.get("item_group_id") and not vals.get("categ_id"):
            item_group = self.env["product.item.group"].browse(vals["item_group_id"])
            templates_using_default = self.filtered(lambda template: not template.categ_id or template.categ_id == template._grandora_default_category())
            if item_group.default_categ_id and templates_using_default:
                vals = dict(vals, categ_id=item_group.default_categ_id.id)
        res = super().write(vals)
        if vals.get("default_code"):
            for template in self:
                template.product_variant_ids.filtered(lambda variant: not variant.default_code).write({"default_code": template.default_code})
        return res

    def _grandora_requires_product_information(self):
        self.ensure_one()
        return self.type == "consu" and self.is_storable

    @api.constrains("type", "is_storable", "brand_id", "item_group_id", "categ_id")
    def _check_grandora_required_product_information(self):
        for template in self:
            if not template._grandora_requires_product_information():
                continue
            missing = []
            if not template.brand_id:
                missing.append(_("Brand"))
            if not template.item_group_id:
                missing.append(_("Item Group"))
            if not template.categ_id:
                missing.append(_("Product Category"))
            if missing:
                raise ValidationError(_(
                    "Product %(product)s is a stockable good and requires: %(fields)s.",
                    product=template.display_name,
                    fields=", ".join(missing),
                ))
