from odoo.tests.common import TransactionCase


class TestPartnerType(TransactionCase):
    def test_flags_set_partner_ranks(self):
        partner = self.env["res.partner"].create(
            {"name": "Partner Type Test", "is_customer": False, "is_vendor": False}
        )
        self.assertFalse(partner.customer_rank)
        self.assertFalse(partner.supplier_rank)

        partner.write({"is_customer": True, "is_vendor": True})

        self.assertEqual(partner.customer_rank, 1)
        self.assertEqual(partner.supplier_rank, 1)

        partner.write({"is_customer": False, "is_vendor": False})
        self.assertEqual(partner.customer_rank, 1)
        self.assertEqual(partner.supplier_rank, 1)
