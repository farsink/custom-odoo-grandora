from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    minimum_shelf_life_days = fields.Integer(
        string="Minimum Shelf Life (Days)",
        default=0,
        help="Minimum number of days from receipt date to expiry date. "
             "Validation will block receipt if remaining shelf life is below this threshold.",
    )
