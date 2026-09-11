from freezegun import freeze_time

from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase
from odoo.tools.safe_eval import safe_eval, time


class TestPartnerStatement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Statement Test Partner"})

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
        self.assertEqual(
            wizard.button_export_html()["report_name"],
            "partner_statement.activity_statement_browser",
        )

        data = wizard._prepare_statement()
        report = self.env["report.partner_statement.activity_statement"]._get_report_values(
            self.partner.ids, data
        )
        lines = report["data"][self.partner.id]["currencies"][
            current_invoice.currency_id.id
        ]["lines"]
        current_line = next(line for line in lines if line["move_id"] == current_invoice.name)
        self.assertEqual(current_line["balance"], 200.0)

    def test_outstanding_statement_view_uses_browser_template(self):
        wizard = self.env["outstanding.statement.wizard"].with_context(
            active_ids=self.partner.ids
        ).create({})
        self.assertEqual(
            wizard.button_export_html()["report_name"],
            "partner_statement.outstanding_statement_browser",
        )

    @freeze_time("2026-02-15 08:00")
    def test_statement_filename_uses_customer_and_generated_date(self):
        wizard = self.env["activity.statement.wizard"].with_context(
            active_ids=self.partner.ids
        ).create({})
        values = self.env[
            "report.partner_statement.activity_statement"
        ]._get_report_values(self.partner.ids, wizard._prepare_statement())
        self.assertEqual(
            values["title"],
            "Statement Test Partner - Activity Statement - 2026-02-15",
        )
        report = self.env.ref("partner_statement.action_print_activity_statement")
        self.assertIn("object.name", report.print_report_name)
        filename = safe_eval(
            report.print_report_name, {"object": self.partner, "time": time}
        )
        # ponytail: print_report_name uses the real server clock, not frozen time
        self.assertTrue(
            filename.startswith("Statement-Activity-Statement Test Partner-")
        )
