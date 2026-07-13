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
