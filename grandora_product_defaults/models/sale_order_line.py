from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

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
