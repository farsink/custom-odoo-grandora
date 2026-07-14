from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Keep the model extension file for module stability. Sale confirmation now
    # follows standard Odoo behavior and no longer requires manual lot selection.
