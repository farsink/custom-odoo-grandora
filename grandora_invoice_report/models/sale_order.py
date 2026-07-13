from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    division_name = fields.Char(string="Division Name", default="RESTAURANT", copy=True)
    delivery_time = fields.Char(string="Delivery Time", copy=True)

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        values.update({
            "division_name": self.division_name,
            "delivery_time": self.delivery_time,
            "sale_order_number": self.name,
        })
        return values
