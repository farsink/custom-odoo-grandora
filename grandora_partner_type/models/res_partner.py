from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_customer = fields.Boolean(
        string="Is a Customer",
        default=lambda self: self.env.context.get("res_partner_search_mode") != "supplier",
    )
    is_vendor = fields.Boolean(
        string="Is a Vendor",
        default=lambda self: self.env.context.get("res_partner_search_mode") == "supplier",
    )

    @api.model_create_multi
    def create(self, vals_list):
        partners = super().create(vals_list)
        partners._sync_partner_ranks()
        return partners

    def write(self, vals):
        result = super().write(vals)
        if "is_customer" in vals or "is_vendor" in vals:
            self._sync_partner_ranks()
        return result

    def _sync_partner_ranks(self):
        self.filtered(lambda partner: partner.is_customer and not partner.customer_rank).write(
            {"customer_rank": 1}
        )
        self.filtered(lambda partner: partner.is_vendor and not partner.supplier_rank).write(
            {"supplier_rank": 1}
        )
