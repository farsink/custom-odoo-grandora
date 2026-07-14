from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    supplier_lot_name = fields.Char(
        string="Supplier Lot/Batch",
        copy=False,
        help="Supplier-provided batch number. The Lot/Serial Number field is Grandora's generated internal batch ID.",
    )
    best_before_date = fields.Datetime(
        string="Best Before Date",
        copy=False,
        help="Best-before date copied to the created lot/serial number.",
    )
    brand_id = fields.Many2one(
        related="product_id.brand_id",
        string="Brand",
        store=True,
        readonly=True,
    )
    item_group_id = fields.Many2one(
        related="product_id.item_group_id",
        string="Item Group",
        store=True,
        readonly=True,
    )
    grandora_product_defaults_enabled = fields.Boolean(
        compute="_compute_grandora_product_defaults_enabled",
        string="Grandora Product Defaults Enabled",
    )

    def _compute_grandora_product_defaults_enabled(self):
        enabled = self.env["grandora.product.defaults.toggle"]._grandora_product_defaults_enabled()
        for line in self:
            line.grandora_product_defaults_enabled = enabled

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        if self.supplier_lot_name:
            vals["supplier_lot_name"] = self.supplier_lot_name
        if self.best_before_date:
            vals["use_date"] = self.best_before_date
        return vals
