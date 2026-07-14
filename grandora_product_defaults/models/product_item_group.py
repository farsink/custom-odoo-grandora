from odoo import fields, models


class ProductItemGroup(models.Model):
    _name = "product.item.group"
    _description = "Product Item Group"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(help="Short operational code, e.g. FRZ, DRY, BAK.")
    active = fields.Boolean(default=True)
    default_categ_id = fields.Many2one(
        "product.category",
        string="Default Product Category",
        help="Optional default accounting/inventory category for products in this item group.",
    )

    _sql_constraints = [
        ("name_unique", "unique(name)", "Item Group names must be unique."),
        ("code_unique", "unique(code)", "Item Group codes must be unique."),
    ]
