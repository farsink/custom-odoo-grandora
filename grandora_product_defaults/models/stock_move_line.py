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

    def _prepare_new_lot_vals(self):
        vals = super()._prepare_new_lot_vals()
        if self.supplier_lot_name:
            vals["supplier_lot_name"] = self.supplier_lot_name
        if self.best_before_date:
            vals["use_date"] = self.best_before_date
        return vals
