from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    require_supplier_batch = fields.Boolean(
        string="Require Supplier Batch",
        default=False,
        help="If enabled, products in this category must have a supplier batch number on receipt.",
    )
    require_expiry_date = fields.Boolean(
        string="Require Expiry Date",
        default=False,
        help="If enabled, products in this category must have an expiry date on receipt.",
    )
    minimum_shelf_life_days = fields.Integer(
        string="Minimum Shelf Life (Days)",
        default=0,
        help="Minimum number of days from receipt date to expiry date. "
             "Validation will block receipt if remaining shelf life is below this threshold.",
    )
