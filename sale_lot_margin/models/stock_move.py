from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    sale_lot_id = fields.Many2one(
        "stock.lot",
        string="Selected Sale Lot",
        copy=True,
        check_company=True,
        help="Lot selected on the originating sale order line. Reservation is restricted to this lot.",
    )

    def _update_reserved_quantity_vals(self, need, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        self.ensure_one()
        if self.sale_lot_id:
            if lot_id and lot_id != self.sale_lot_id:
                return [], 0.0
            lot_id = self.sale_lot_id
        return super()._update_reserved_quantity_vals(need, location_id, lot_id, package_id, owner_id, strict)
