from freezegun import freeze_time

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestPartnerStatement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env.ref("base.res_partner_2")

    @freeze_time("2026-02-15 08:00")
    def test_contact_activity_statement_uses_current_month_and_running_balance(self):
        def post_invoice(invoice_date):
            form = Form(
                self.env["account.move"].with_context(default_move_type="out_invoice")
            )
            form.partner_id = self.partner
            form.invoice_date = invoice_date
            with form.invoice_line_ids.new() as line:
                line.name = "Statement test"
                line.price_unit = 100
            invoice = form.save()
            invoice.action_post()
            return invoice

        post_invoice(fields.Date.from_string("2026-01-31"))
        current_invoice = post_invoice(fields.Date.from_string("2026-02-01"))
        action = self.partner.action_preview_activity_statement()
        self.assertEqual(action["res_model"], "activity.statement.wizard")
        self.assertEqual(action["target"], "new")

        wizard = self.env["activity.statement.wizard"].with_context(
            active_ids=self.partner.ids
        ).create({"date_end": fields.Date.from_string("2026-02-15")})
        self.assertEqual(wizard.date_start, fields.Date.from_string("2026-02-01"))

        data = wizard._prepare_statement()
        report = self.env["report.partner_statement.activity_statement"]._get_report_values(
            self.partner.ids, data
        )
        lines = report["data"][self.partner.id]["currencies"][
            current_invoice.currency_id.id
        ]["lines"]
        current_line = next(line for line in lines if line["move_id"] == current_invoice.name)
        self.assertEqual(current_line["balance"], 200.0)
