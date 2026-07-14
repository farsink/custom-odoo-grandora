from odoo import fields, models


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    note = fields.Text()

    _sql_constraints = [
        ("name_unique", "unique(name)", "The brand name must be unique."),
    ]
