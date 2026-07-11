from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    x_business_sku = fields.Char(
        string="Business SKU",
        copy=False,
        help="Local business reference used while testing Inventory/Sales customizations.",
    )
    x_reorder_note = fields.Text(
        string="Reorder Note",
        help="Internal note for replenishment or sales availability discussions.",
    )
