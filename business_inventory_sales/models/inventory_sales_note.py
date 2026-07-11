from odoo import fields, models


class BusinessInventorySalesNote(models.Model):
    _name = "business.inventory.sales.note"
    _description = "Business Inventory/Sales Note"
    _order = "priority desc, id desc"

    name = fields.Char(required=True, default="Inventory/Sales note")
    product_id = fields.Many2one("product.product", string="Product", ondelete="set null")
    sale_order_id = fields.Many2one("sale.order", string="Sales Order", ondelete="set null")
    priority = fields.Selection(
        [("0", "Normal"), ("1", "Important"), ("2", "Urgent")],
        default="0",
        required=True,
    )
    note = fields.Text()
    active = fields.Boolean(default=True)
