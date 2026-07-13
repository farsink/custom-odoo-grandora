from odoo import fields, models
from odoo.tools import format_datetime


class AccountMove(models.Model):
    _inherit = "account.move"

    division_name = fields.Char(string="Division Name", copy=False)
    delivery_time = fields.Char(string="Delivery Time", copy=False)
    sale_order_number = fields.Char(string="SO Number", copy=False)

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

    def action_print_pdf(self):
        """Use Grandora's browser-native print view for customer invoices.

        The standard Odoo button name is still ``action_print_pdf``; returning an
        HTML report URL here makes the existing Invoice Print button open the
        browser print layout instead of generating a wkhtmltopdf PDF.
        """
        self.ensure_one()
        if self.move_type in ("out_invoice", "out_refund", "out_receipt"):
            return {
                "type": "ir.actions.act_url",
                "url": f"/report/html/grandora_invoice_report.report_invoice_browser_print/{self.id}",
                "target": "new",
            }
        return super().action_print_pdf()
