from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseLotAutomation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "product_lot_sequence.policy", "global"
        )
        cls.seq = cls.env["ir.sequence"].search([("code", "=", "stock.lot.serial")], limit=1)
        cls.seq.write({"prefix": "LOT-", "padding": 7})
        cls.partner = cls.env["res.partner"].create({"name": "Batch Vendor"})
        cls.uom = cls.env.ref("uom.product_uom_unit")

    def _create_product(self, name, **extra):
        vals = {
            "name": name,
            "type": "consu",
            "is_storable": True,
            "purchase_ok": True,
            "tracking": "lot",
            "uom_id": self.uom.id,
            "uom_po_id": self.uom.id,
        }
        vals.update(extra)
        return self.env["product.product"].create(vals)

    def _create_po_receipt(self, lines):
        order_lines = []
        for product, qty in lines:
            order_lines.append(
                (
                    0,
                    0,
                    {
                        "name": product.display_name,
                        "product_id": product.id,
                        "product_qty": qty,
                        "product_uom": product.uom_po_id.id,
                        "price_unit": 10.0,
                        "date_planned": fields.Datetime.now(),
                    },
                )
            )
        po = self.env["purchase.order"].create(
            {"partner_id": self.partner.id, "order_line": order_lines}
        )
        po.button_confirm()
        picking = po.picking_ids.filtered(lambda p: p.picking_type_code == "incoming")[:1]
        picking.action_generate_batch_lines()
        return po, picking

    def test_goods_product_defaults_to_lot(self):
        product = self.env["product.product"].create(
            {"name": "Default Lot Product", "type": "consu", "is_storable": True}
        )
        self.assertEqual(product.tracking, "lot")

    def test_service_product_remains_untracked(self):
        product = self.env["product.product"].create(
            {"name": "Default Service", "type": "service"}
        )
        self.assertEqual(product.tracking, "none")

    def test_explicit_tracking_is_not_overwritten(self):
        product = self.env["product.product"].create(
            {
                "name": "Explicit No Tracking Product",
                "type": "consu",
                "is_storable": True,
                "tracking": "none",
            }
        )
        self.assertEqual(product.tracking, "none")

    def test_one_batch_receipt_creates_lot_and_metadata(self):
        product = self._create_product("Butter 200g")
        po, picking = self._create_po_receipt([(product, 10)])
        line = picking.batch_line_ids.filtered(lambda l: l.product_id == product)
        line.write(
            {
                "received_qty": 10,
                "supplier_lot": "BT-QA-7109",
                "expiry_date": fields.Date.today() + timedelta(days=365),
            }
        )
        picking.action_generate_lots()
        picking._assign_lots_to_move_lines()
        self.assertEqual(len(line.internal_lot_id), 1)
        self.assertTrue(line.internal_lot_id.name.startswith("LOT-"))
        self.assertEqual(line.internal_lot_id.supplier_lot, "BT-QA-7109")
        self.assertEqual(line.internal_lot_id.purchase_order_id, po)
        self.assertEqual(line.internal_lot_id.receipt_id, picking)
        self.assertEqual(picking.move_line_ids.lot_id, line.internal_lot_id)
        self.assertEqual(picking.move_line_ids.quantity, 10)

    def test_multiple_products_each_get_distinct_lot(self):
        butter = self._create_product("Multi Butter")
        bread = self._create_product("Multi Bread")
        _po, picking = self._create_po_receipt([(butter, 12), (bread, 8)])
        for line in picking.batch_line_ids:
            line.write(
                {
                    "received_qty": line.ordered_qty,
                    "supplier_lot": f"SUP-{line.product_id.id}",
                    "expiry_date": fields.Date.today() + timedelta(days=365),
                }
            )
        picking.action_generate_lots()
        lots = picking.batch_line_ids.mapped("internal_lot_id")
        self.assertEqual(len(lots), 2)
        self.assertEqual(len(set(lots.mapped("name"))), 2)
        self.assertEqual(set(lots.mapped("product_id").ids), {butter.id, bread.id})

    def test_split_batches_create_distinct_lots(self):
        product = self._create_product("Split Butter")
        po, picking = self._create_po_receipt([(product, 100)])
        line = picking.batch_line_ids.filtered(lambda l: l.product_id == product)
        line.write(
            {
                "received_qty": 60,
                "supplier_lot": "BT-QA-7109",
                "expiry_date": fields.Date.today() + timedelta(days=365),
            }
        )
        self.env["grandora.receipt.batch.line"].create(
            {
                "picking_id": picking.id,
                "move_id": line.move_id.id,
                "received_qty": 40,
                "supplier_lot": "BT-QA-7110",
                "expiry_date": fields.Date.today() + timedelta(days=380),
            }
        )
        picking.action_generate_lots()
        self.assertEqual(len(picking.batch_line_ids.mapped("internal_lot_id")), 2)
        self.assertEqual(len(set(picking.batch_line_ids.mapped("lot_name"))), 2)

    def test_expirable_product_without_expiry_is_blocked(self):
        product = self._create_product("Expirable Butter", use_expiration_date=True)
        _po, picking = self._create_po_receipt([(product, 10)])
        line = picking.batch_line_ids.filtered(lambda l: l.product_id == product)
        line.write({"received_qty": 10, "supplier_lot": "BT-NO-EXP"})
        with self.assertRaises(ValidationError):
            picking.action_generate_lots()

    def test_duplicate_lot_name_is_blocked_across_products(self):
        product_1 = self._create_product("Duplicate Lot Product 1")
        product_2 = self._create_product("Duplicate Lot Product 2")
        self.env["stock.lot"].create(
            {"name": "LOT-DUPLICATE", "product_id": product_1.id, "company_id": self.env.company.id}
        )
        with self.assertRaises(ValidationError):
            self.env["stock.lot"].create(
                {"name": "LOT-DUPLICATE", "product_id": product_2.id, "company_id": self.env.company.id}
            )

    def test_partial_receipt_is_allowed_for_backorder_flow(self):
        product = self._create_product("Partial Butter")
        _po, picking = self._create_po_receipt([(product, 100)])
        line = picking.batch_line_ids.filtered(lambda l: l.product_id == product)
        line.write(
            {
                "received_qty": 90,
                "supplier_lot": "BT-PARTIAL",
                "expiry_date": fields.Date.today() + timedelta(days=365),
            }
        )
        picking.action_generate_lots()
        picking._assign_lots_to_move_lines()
        move = picking.move_ids.filtered(lambda m: m.product_id == product)
        self.assertEqual(move.quantity, 90)
        self.assertEqual(move.product_uom_qty, 100)
