from odoo.tests.common import TransactionCase


class TestInvoicePreview(TransactionCase):
    def test_customer_invoice_print_uses_in_odoo_preview(self):
        partner = self.env["res.partner"].create({"name": "Invoice Preview Partner"})
        invoice = self.env["account.move"].create(
            {"move_type": "out_invoice", "partner_id": partner.id}
        )

        self.assertEqual(
            invoice.action_print_pdf(),
            {
                "type": "ir.actions.client",
                "tag": "grandora_invoice_report.invoice_preview",
                "name": "Invoice Preview",
                "params": {"invoice_id": invoice.id},
            },
        )
        html = self.env["ir.actions.report"]._render_qweb_html(
            "grandora_invoice_report.report_invoice_inkjet_print", invoice.ids
        )[0].decode()
        self.assertIn("grandora_invoice_report.close_preview", html)
