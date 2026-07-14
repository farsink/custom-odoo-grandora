from odoo import fields, models


class ProductItemGroup(models.Model):
    _name = "product.item.group"
    _description = "Product Item Group"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    note = fields.Text()

    _sql_constraints = [
        ("name_unique", "unique(name)", "The item group name must be unique."),
    ]
