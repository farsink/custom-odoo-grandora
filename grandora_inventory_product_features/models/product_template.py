import re

from odoo import api, fields, models
from odoo.tools import str2bool


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
            if (
                "tracking" in fields_list
                and "default_tracking" not in self.env.context
                and self._grandora_should_default_lot_tracking()
            ):
                # Odoo's stock default is 'none', so setdefault() would not
                # update the Product form to show the configured lot default.
                values["tracking"] = "lot"
        return values

    @api.model
    def _grandora_should_default_lot_tracking(self):
        value = self.env["ir.config_parameter"].sudo().get_param(
            "grandora_inventory_product_features.default_new_storable_products_to_lots",
            default=True,
        )
        return value if isinstance(value, bool) else str2bool(value, default=True)

    @api.model
    def _grandora_product_lot_acronym(self, name):
        """Return the normalized acronym used in automatic lot prefixes."""
        tokens = re.findall(r"[^\W_]+", name or "", flags=re.UNICODE)
        if not tokens:
            return "PRD"
        if len(tokens) == 1:
            return tokens[0][:3].upper()
        return "".join(token[0] for token in tokens).upper()

    def _grandora_lot_sequence_prefix(self):
        """Derive the current product prefix, adding the ID after an acronym clash."""
        self.ensure_one()
        acronym = self._grandora_product_lot_acronym(self.name)
        lower_templates = self.with_context(active_test=False).search(
            [
                ("id", "<", self.id),
                ("tracking", "in", ("lot", "serial")),
            ]
        )
        has_lower_clash = any(
            self._grandora_product_lot_acronym(template.name) == acronym
            for template in lower_templates
        )
        product_prefix = f"{acronym}-{self.id}" if has_lower_clash else acronym
        return f"BTCH-{product_prefix}-"

    def _grandora_ensure_lot_sequence(self, initialize=False):
        """Create/synchronize OCA product sequences without resetting used counters."""
        for template in self.filtered(lambda product: product.tracking in ("lot", "serial")):
            should_initialize = initialize
            desired_prefix = template._grandora_lot_sequence_prefix()
            sequence = template.lot_sequence_id
            if not sequence:
                sequence = template.sudo()._create_lot_sequence(
                    {
                        "name": template.display_name,
                        "lot_sequence_prefix": desired_prefix,
                        "lot_sequence_padding": 3,
                        "lot_sequence_number_next": 100,
                    }
                )
                template.with_context(grandora_skip_lot_sequence_sync=True).write(
                    {"lot_sequence_id": sequence.id}
                )
                should_initialize = True

            sequence_values = {
                "name": f"Lot Sequence - {template.display_name}",
                "implementation": "no_gap",
                "prefix": desired_prefix,
                "padding": 3,
                "number_increment": 1,
                "use_date_range": False,
            }
            sequence.sudo().write(sequence_values)
            if should_initialize:
                current_sequence = sequence.sudo()._get_current_sequence()
                if current_sequence.number_next_actual < 100:
                    current_sequence.number_next = 100
        return True

    @api.model
    def _grandora_sync_existing_lot_sequences(self):
        """Upgrade hook: initialize tracked products in deterministic ID order."""
        templates = self.with_context(active_test=False).search(
            [("tracking", "in", ("lot", "serial"))],
            order="id",
        )
        for template in templates:
            template._grandora_ensure_lot_sequence()
        return True

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
                if (
                    "tracking" not in vals
                    and vals.get("is_storable")
                    and self._grandora_should_default_lot_tracking()
                ):
                    vals["tracking"] = "lot"
            else:
                # A product.product creation can instantiate a template with
                # form defaults before its service type is propagated. Services
                # must remain untracked even when the UI lot default is enabled.
                vals["tracking"] = "none"
            if not vals.get("default_code"):
                vals["default_code"] = self._grandora_next_product_reference()
            if "standard_price" in vals and "base_cost" not in vals:
                vals["base_cost"] = vals.get("standard_price") or 0.0
        templates = super().create(vals_list)
        templates._grandora_sync_standard_price_from_total()
        templates._grandora_ensure_lot_sequence(initialize=True)
        return templates

    def write(self, vals):
        if self.env.context.get("grandora_skip_total_cost_sync"):
            return super().write(vals)
        vals = dict(vals)
        skip_lot_sequence_sync = self.env.context.get(
            "grandora_skip_lot_sequence_sync"
        )
        sequence_initialize_ids = set()
        if not skip_lot_sequence_sync and {"name", "tracking"} & set(vals):
            sequence_initialize_ids = set(
                self.filtered(lambda template: not template.lot_sequence_id).ids
            )

        # Do NOT overwrite tracking on write for existing products.
        # The default tracking is only set on creation.
        if "standard_price" in vals and "base_cost" not in vals:
            vals["base_cost"] = vals.get("standard_price") or 0.0
        res = super().write(vals)
        if {"base_cost", "landing_cost", "standard_price"} & set(vals):
            self._grandora_sync_standard_price_from_total()
        if not skip_lot_sequence_sync and {"name", "tracking"} & set(vals):
            for template in self:
                template._grandora_ensure_lot_sequence(
                    initialize=template.id in sequence_initialize_ids
                )
        return res

    def _grandora_sync_standard_price_from_total(self):
        for template in self:
            template.with_context(grandora_skip_total_cost_sync=True).standard_price = template.base_cost + template.landing_cost
