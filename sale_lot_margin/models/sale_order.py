from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        self.order_line._check_lot_required_rules()
        self.order_line._check_selected_lot_availability()
        return super().action_confirm()
