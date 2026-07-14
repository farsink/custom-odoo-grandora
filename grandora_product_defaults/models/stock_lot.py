from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    supplier_lot_name = fields.Char(
        string="Supplier Lot/Batch",
        copy=False,
        help="Supplier-provided batch number. Grandora's internal batch ID remains the Lot/Serial Number.",
    )
