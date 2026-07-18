from odoo import api, fields, models


class GrandoraReceiptBatchLine(models.Model):
    _name = "grandora.receipt.batch.line"
    _description = "Receipt Batch Line"
    _rec_name = "display_name"
    _order = "picking_id, move_id, id"

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=False,
    )

    picking_id = fields.Many2one(
        "stock.picking",
        string="Receipt",
        required=True,
        ondelete="cascade",
        index=True,
    )
    move_id = fields.Many2one(
        "stock.move",
        string="Stock Move",
        required=True,
        ondelete="cascade",
        index=True,
        domain="[('picking_id', '=', picking_id)]",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        related="move_id.product_id",
        readonly=True,
        store=False,
    )
    ordered_qty = fields.Float(
        string="Ordered Quantity",
        related="move_id.product_uom_qty",
        readonly=True,
    )
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Unit of Measure",
        related="move_id.product_uom",
        readonly=True,
    )
    received_qty = fields.Float(
        string="Received Quantity",
        required=True,
        digits="Product Unit of Measure",
        help="Quantity being received in this batch.",
    )
    supplier_lot = fields.Char(
        string="Supplier Batch",
        help="Batch number assigned by the supplier (e.g. BT-QA-7109).",
    )
    expiry_date = fields.Date(
        string="Expiry Date",
        help="Expiration date of this batch.",
    )
    manufacture_date = fields.Date(
        string="Manufacture Date",
        help="Date this product was manufactured.",
    )
    quality_status = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail"), ("pending", "Pending")],
        string="Quality Status",
        default="pass",
    )
    internal_lot_id = fields.Many2one(
        "stock.lot",
        string="Internal Lot",
        readonly=True,
        copy=False,
        help="Generated internal lot assigned to this batch.",
    )
    lot_name = fields.Char(
        string="Lot Number",
        copy=False,
        help=(
            "Enter a manual lot number or leave blank to generate the next "
            "product lot number automatically."
        ),
    )

    @api.model
    def _grandora_backfill_lot_names(self):
        """Backfill the new stored field for receipt rows created before upgrade."""
        self.env.cr.execute(
            """
            UPDATE grandora_receipt_batch_line AS line
               SET lot_name = lot.name
              FROM stock_lot AS lot
             WHERE line.internal_lot_id = lot.id
               AND COALESCE(line.lot_name, '') = ''
            """
        )
        self.env.invalidate_all()
        return True

    @api.depends("move_id", "supplier_lot", "lot_name")
    def _compute_display_name(self):
        for line in self:
            parts = []
            if line.product_id:
                parts.append(line.product_id.display_name)
            if line.supplier_lot:
                parts.append(f"Supplier: {line.supplier_lot}")
            if line.lot_name:
                parts.append(f"Lot: {line.lot_name}")
            line.display_name = " / ".join(parts) if parts else f"Batch #{line.id}"
