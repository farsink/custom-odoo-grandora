from odoo import fields, models


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"
    _order = "name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    supplier_id = fields.Many2one(
        "res.partner",
        string="Supplier / Manufacturer",
        domain="['|', ('supplier_rank', '>', 0), ('is_company', '=', True)]",
    )
    website = fields.Char()
    logo = fields.Image(max_width=512, max_height=512)

    _sql_constraints = [
        ("name_unique", "unique(name)", "Brand names must be unique."),
    ]
