import re

from odoo import _, fields, models
from odoo.tools import format_datetime


_GRANDORA_LEADING_PRODUCT_CODE_RE = re.compile(r"^\s*\[[^\]]+\]\s*")


class AccountMove(models.Model):
    _inherit = "account.move"

    division_name = fields.Char(string="Division Name", copy=False)
    delivery_time = fields.Char(string="Delivery Time", copy=False)
    sale_order_number = fields.Char(string="SO Number", copy=False)
    grandora_remarks = fields.Text(string="Grandora Invoice Remarks", copy=False)

    def _grandora_printed_at(self):
        self.ensure_one()
        return format_datetime(
            self.env,
            fields.Datetime.now(),
            tz=self.env.user.tz or "UTC",
            dt_format="dd/MM/yyyy 'at' h:mm a",
        )

    def _grandora_delivery_partner(self):
        self.ensure_one()
        return self.partner_shipping_id or self.partner_id

    def _grandora_report_lines(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered(lambda line: line.display_type == "product")

    def _grandora_line_description(self, line):
        """Return customer-facing line description without leading Odoo SKU.

        Odoo often stores product lines as "[SKU] Product Name". Grandora keeps
        the SKU visible internally and in the dedicated CODE column, but removes
        the bracketed prefix from the customer-facing DESCRIPTION column.
        """
        self.ensure_one()
        description = line.name or line.product_id.display_name or ""
        default_code = line.product_id.default_code
        if default_code:
            exact_prefix = "[%s]" % default_code
            if description.lstrip().startswith(exact_prefix):
                return description.lstrip()[len(exact_prefix):].lstrip()
        return _GRANDORA_LEADING_PRODUCT_CODE_RE.sub("", description)

    def action_print_pdf(self):
        """Show the customer invoice form inside the Odoo client."""
        self.ensure_one()
        if self.move_type in ("out_invoice", "out_refund", "out_receipt"):
            return {
                "type": "ir.actions.client",
                "tag": "grandora_invoice_report.invoice_preview",
                "name": _("Invoice Preview"),
                "params": {"invoice_id": self.id},
            }
        return super().action_print_pdf()
