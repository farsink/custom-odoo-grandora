import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductCategory(models.Model):
    _inherit = "product.category"

    grandora_sku_prefix = fields.Char(
        string="SKU Prefix",
        help="Prefix used for automatic product Internal References in this category, e.g. BUT.",
    )
    grandora_product_sequence_id = fields.Many2one(
        "ir.sequence",
        string="Product SKU Sequence",
        readonly=True,
        copy=False,
        help="Private sequence used to generate product Internal References for this category.",
    )

    @api.constrains("grandora_sku_prefix")
    def _check_grandora_sku_prefix(self):
        for category in self:
            if category.grandora_sku_prefix and not re.fullmatch(r"[A-Z0-9]{2,8}", category.grandora_sku_prefix):
                raise ValidationError(_("SKU Prefix must contain 2-8 uppercase letters or digits, e.g. PRD or BUT."))

    def _grandora_sanitized_prefix(self):
        self.ensure_one()
        prefix = (self.grandora_sku_prefix or "").upper().strip()
        prefix = re.sub(r"[^A-Z0-9]", "", prefix)
        return prefix or "PRD"

    def _grandora_ensure_product_sequence(self):
        for category in self:
            if category.grandora_product_sequence_id:
                continue
            prefix = category._grandora_sanitized_prefix()
            sequence = self.env["ir.sequence"].sudo().create({
                "name": _("Grandora Product SKU - %(category)s", category=category.display_name),
                "code": "grandora.product.sku.%s" % category.id,
                "prefix": "%s-" % prefix,
                "padding": 6,
                "number_next": 1,
                "number_increment": 1,
                "company_id": False,
            })
            category.sudo().grandora_product_sequence_id = sequence.id

    def _grandora_next_product_sku(self):
        self.ensure_one()
        self._grandora_ensure_product_sequence()
        sequence = self.grandora_product_sequence_id.sudo()
        prefix = self._grandora_sanitized_prefix()
        if sequence.prefix != "%s-" % prefix:
            sequence.prefix = "%s-" % prefix
        return sequence.next_by_id()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("grandora_sku_prefix"):
                vals["grandora_sku_prefix"] = vals["grandora_sku_prefix"].upper().strip()
        categories = super().create(vals_list)
        categories.filtered("grandora_sku_prefix")._grandora_ensure_product_sequence()
        return categories

    def write(self, vals):
        if vals.get("grandora_sku_prefix"):
            vals = dict(vals, grandora_sku_prefix=vals["grandora_sku_prefix"].upper().strip())
        res = super().write(vals)
        if "grandora_sku_prefix" in vals:
            self.filtered("grandora_sku_prefix")._grandora_ensure_product_sequence()
            for category in self.filtered("grandora_product_sequence_id"):
                category.grandora_product_sequence_id.sudo().prefix = "%s-" % category._grandora_sanitized_prefix()
        return res
