from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockLot(models.Model):
    _inherit = "stock.lot"

    supplier_lot = fields.Char(
        string="Supplier Batch",
        index=True,
        copy=False,
        help="Batch/serial number assigned by the supplier.",
    )
    purchase_order_id = fields.Many2one(
        "purchase.order",
        string="Source Purchase Order",
        readonly=True,
        copy=False,
        help="Purchase Order that this lot was received from.",
    )
    receipt_id = fields.Many2one(
        "stock.picking",
        string="Source Receipt",
        readonly=True,
        copy=False,
        help="Receipt picking that this lot was received from.",
    )
    manufacture_date = fields.Date(
        string="Manufacture Date",
        copy=False,
        help="Date this product was manufactured.",
    )
    quality_status = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail"), ("pending", "Pending")],
        string="Quality Status",
        default="pass",
        copy=False,
        help="Quality inspection status for this lot.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Keep product sequences current for every automatic lot creation path."""
        product_ids = [values.get("product_id") for values in vals_list if values.get("product_id")]
        if product_ids:
            self.env["product.product"].browse(product_ids).mapped(
                "product_tmpl_id"
            )._grandora_ensure_lot_sequence()
        return super().create(vals_list)

    @api.constrains("name", "company_id")
    def _check_unique_lot_name_per_company(self):
        """Enforce globally unique internal lot names per company.

        Odoo core only enforces uniqueness per product/name/company. Grandora
        internal lots are generated from one global sequence, so future manual
        duplicates across products should be blocked as well.
        """
        for lot in self:
            if not lot.name:
                continue
            company_domain = []
            if lot.company_id:
                company_domain = ["|", ("company_id", "=", lot.company_id.id), ("company_id", "=", False)]
            duplicates = self.sudo().search(
                [("id", "!=", lot.id), ("name", "=", lot.name)] + company_domain,
                limit=1,
            )
            if duplicates:
                raise ValidationError(
                    _(
                        "Lot number '%(lot)s' already exists for company '%(company)s'. "
                        "Please generate a new internal lot number.",
                        lot=lot.name,
                        company=lot.company_id.display_name or _("Global"),
                    )
                )
