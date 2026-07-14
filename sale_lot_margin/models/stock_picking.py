from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _check_sale_lot_delivery(self):
        for picking in self:
            for move in picking.move_ids.filtered(lambda m: m.sale_lot_id and m.state != "cancel"):
                move_lines = move.move_line_ids.filtered(lambda ml: ml.quantity > 0)
                for move_line in move_lines:
                    if not move_line.lot_id:
                        raise UserError(_(
                            "Delivery %(picking)s must use selected lot %(lot)s for product %(product)s.",
                            picking=picking.name,
                            lot=move.sale_lot_id.display_name,
                            product=move.product_id.display_name,
                        ))
                    if move_line.lot_id != move.sale_lot_id:
                        raise UserError(_(
                            "You cannot validate delivery %(picking)s with lot %(actual)s for %(product)s. The sale order line selected lot %(expected)s.",
                            picking=picking.name,
                            actual=move_line.lot_id.display_name,
                            product=move.product_id.display_name,
                            expected=move.sale_lot_id.display_name,
                        ))

    def button_validate(self):
        self._check_sale_lot_delivery()
        return super().button_validate()

    def _action_done(self):
        self._check_sale_lot_delivery()
        res = super()._action_done()
        for move in self.move_ids.filtered(lambda m: m.sale_lot_id and m.sale_line_id and m.state == "done"):
            sale_line = move.sale_line_id
            actual_lots = move.move_line_ids.filtered(lambda ml: ml.quantity > 0).lot_id
            if move.sale_lot_id not in actual_lots:
                continue
            values = {}
            if not sale_line.actual_lot_id:
                values["actual_lot_id"] = move.sale_lot_id.id
            if not sale_line.actual_batch_cost:
                values["actual_batch_cost"] = sale_line._get_lot_batch_cost(move.sale_lot_id)
            if values:
                sale_line.sudo().write(values)
        return res
