from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(
        "product.brand",
        string="Brand",
        ondelete="restrict",
        help="Optional brand or manufacturer for this product.",
    )
    item_group_id = fields.Many2one(
        "product.item.group",
        string="Item Group",
        ondelete="restrict",
        help="Optional operational product group for reporting and filtering.",
    )
    base_cost = fields.Float(
        string="Cost",
        min_display_digits="Product Price",
        tracking=True,
        help="Base product cost before landing cost.",
    )
    landing_cost = fields.Float(
        string="Landing Cost",
        min_display_digits="Product Price",
        tracking=True,
        help="Additional landing/import/freight cost per unit.",
    )
    total_cost = fields.Float(
        string="Total Cost",
        compute="_compute_total_cost",
        store=True,
        min_display_digits="Product Price",
        help="Computed as Cost + Landing Cost. Odoo's official Cost is synchronized to this value.",
    )
    require_supplier_batch = fields.Boolean(
        string="Require Supplier Batch",
        default=False,
        help="If enabled, this product must have a supplier batch number on receipt.",
    )
    require_expiry_date = fields.Boolean(
        string="Require Expiry Date",
        default=False,
        help="If enabled, this product must have an expiry date on receipt.",
    )
    minimum_shelf_life_days = fields.Integer(
        string="Minimum Shelf Life (Days)",
        default=0,
        help="Minimum number of days from receipt date to expiry date for this product.",
    )

    @api.depends("base_cost", "landing_cost")
    def _compute_total_cost(self):
        for template in self:
            template.total_cost = template.base_cost + template.landing_cost

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if "type" in fields_list:
            values.setdefault("type", "consu")
        # Default new goods to stock-tracked + lot-tracked.
        # Service/non-storable products get 'none' via stock._compute_tracking.
        product_type = values.get("type", "consu")
        if product_type == "consu":
            if "is_storable" in fields_list:
                values.setdefault("is_storable", True)
            if "tracking" in fields_list:
                values.setdefault("tracking", "lot")
        return values

    @api.model
    def _grandora_next_product_reference(self):
        return self.env["ir.sequence"].sudo().next_by_code("grandora.product.reference")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            product_type = vals.setdefault("type", "consu")
            # Default new goods to stock-tracked + lot-tracked.
            # Only set tracking if not explicitly provided.
            if product_type == "consu":
                vals.setdefault("is_storable", True)
                if "tracking" not in vals and vals.get("is_storable"):
                    vals["tracking"] = "lot"
            # For non-consu types, the stock._compute_tracking method
            # will set tracking to 'none' during precompute if is_storable is False.
            if not vals.get("default_code"):
                vals["default_code"] = self._grandora_next_product_reference()
            if "standard_price" in vals and "base_cost" not in vals:
                vals["base_cost"] = vals.get("standard_price") or 0.0
        templates = super().create(vals_list)
        templates._grandora_sync_standard_price_from_total()
        return templates

    def write(self, vals):
        if self.env.context.get("grandora_skip_total_cost_sync"):
            return super().write(vals)
        vals = dict(vals)
        # Do NOT overwrite tracking on write for existing products.
        # The default tracking is only set on creation.
        if "standard_price" in vals and "base_cost" not in vals:
            vals["base_cost"] = vals.get("standard_price") or 0.0
        res = super().write(vals)
        if {"base_cost", "landing_cost", "standard_price"} & set(vals):
            self._grandora_sync_standard_price_from_total()
        return res

    def _grandora_sync_standard_price_from_total(self):
        for template in self:
            template.with_context(grandora_skip_total_cost_sync=True).standard_price = template.base_cost + template.landing_cost
