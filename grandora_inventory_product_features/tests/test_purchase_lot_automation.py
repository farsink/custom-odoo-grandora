from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseLotAutomation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Batch Vendor"})
        cls.uom = cls.env.ref("uom.product_uom_unit")

    def setUp(self):
        super().setUp()
        self.env["ir.config_parameter"].sudo().set_param(
            "product_lot_sequence.policy", "product"
        )
        self.env["ir.config_parameter"].sudo().set_param(
            "grandora_inventory_product_features.default_new_storable_products_to_lots",
            "True",
        )

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
        picking = po.picking_ids.filtered(
            lambda picking: picking.picking_type_code == "incoming"
        )[:1]
        picking.action_generate_batch_lines()
        return po, picking

    def _batch_line(self, picking, product):
        return picking.batch_line_ids.filtered(
            lambda line: line.product_id == product
        )[:1]

    def _create_inventory_quant(self, product, quantity, lot=False):
        warehouse = self.env["stock.warehouse"].search(
            [("company_id", "=", self.env.company.id)], limit=1
        )
        return self.env["stock.quant"].with_context(inventory_mode=True).create(
            {
                "product_id": product.id,
                "location_id": warehouse.lot_stock_id.id,
                "lot_id": lot.id if lot else False,
                "inventory_quantity": quantity,
            }
        )

    def test_product_form_defaults_to_lot_when_enabled(self):
        values = self.env["product.template"].default_get(
            ["type", "is_storable", "tracking"]
        )
        self.assertEqual(values["tracking"], "lot")

    def test_product_form_keeps_explicit_tracking_context(self):
        values = self.env["product.template"].with_context(
            default_tracking="serial"
        ).default_get(["type", "is_storable", "tracking"])
        self.assertEqual(values["tracking"], "serial")

    def test_saved_disabled_lot_default_keeps_new_goods_untracked(self):
        settings = self.env["res.config.settings"].create(
            {"new_storable_products_lot_tracking": False}
        )
        settings.execute()
        product = self.env["product.product"].create(
            {"name": "Disabled Lot Default Product", "type": "consu", "is_storable": True}
        )
        self.assertEqual(product.tracking, "none")

    def test_service_product_remains_untracked(self):
        product = self.env["product.product"].create(
            {"name": "Default Service", "type": "service"}
        )
        self.assertEqual(product.tracking, "none")

    def test_explicit_tracking_is_not_overwritten(self):
        product = self.env["product.product"].create(
            {
                "name": "Explicit Serial Tracking Product",
                "type": "consu",
                "is_storable": True,
                "tracking": "serial",
            }
        )
        self.assertEqual(product.tracking, "serial")

    def test_obsolete_batch_requirement_fields_are_removed(self):
        self.assertNotIn("require_supplier_batch", self.env["product.template"]._fields)
        self.assertNotIn("require_expiry_date", self.env["product.template"]._fields)
        self.assertNotIn("require_supplier_batch", self.env["product.category"]._fields)
        self.assertNotIn("require_expiry_date", self.env["product.category"]._fields)

    def test_optional_metadata_generates_product_lot_from_100(self):
        product = self._create_product("Beef Burger Plate", use_expiration_date=True)
        po, picking = self._create_po_receipt([(product, 10)])
        line = self._batch_line(picking, product)
        line.write({"received_qty": 10})

        picking.action_generate_lots()

        self.assertEqual(line.internal_lot_id.name, "BTCH-BBP-100")
        self.assertFalse(line.internal_lot_id.supplier_lot)
        self.assertFalse(line.internal_lot_id.expiration_date)
        self.assertFalse(line.internal_lot_id.manufacture_date)
        self.assertEqual(line.internal_lot_id.purchase_order_id, po)
        self.assertEqual(line.internal_lot_id.receipt_id, picking)

    def test_split_batches_increment_the_product_sequence(self):
        product = self._create_product("Split Butter")
        _po, picking = self._create_po_receipt([(product, 100)])
        line = self._batch_line(picking, product)
        line.write({"received_qty": 60})
        self.env["grandora.receipt.batch.line"].create(
            {
                "picking_id": picking.id,
                "move_id": line.move_id.id,
                "received_qty": 40,
            }
        )

        picking.action_generate_lots()

        self.assertEqual(
            set(picking.batch_line_ids.mapped("lot_name")),
            {"BTCH-SB-100", "BTCH-SB-101"},
        )

    def test_manual_lot_is_created_and_then_reused(self):
        product = self._create_product("Manual Lot Product")
        _po, first_picking = self._create_po_receipt([(product, 2)])
        first_line = self._batch_line(first_picking, product)
        first_line.write({"received_qty": 2, "lot_name": "VENDOR-MANUAL-01"})
        first_picking.action_generate_lots()
        lot = first_line.internal_lot_id

        _po, second_picking = self._create_po_receipt([(product, 3)])
        second_line = self._batch_line(second_picking, product)
        second_line.write({"received_qty": 3, "lot_name": "VENDOR-MANUAL-01"})
        second_picking.action_generate_lots()

        self.assertEqual(second_line.internal_lot_id, lot)
        self.assertEqual(second_line.lot_name, "VENDOR-MANUAL-01")

    def test_manual_lot_rejects_wrong_product_and_metadata_conflicts(self):
        first_product = self._create_product("First Manual Product")
        second_product = self._create_product("Second Manual Product")
        lot = self.env["stock.lot"].create(
            {
                "name": "MANUAL-CONFLICT",
                "product_id": first_product.id,
                "company_id": self.env.company.id,
                "supplier_lot": "SUP-A",
                "expiration_date": fields.Date.today() + timedelta(days=60),
            }
        )
        _po, picking = self._create_po_receipt([(second_product, 1)])
        line = self._batch_line(picking, second_product)
        line.write({"received_qty": 1, "lot_name": lot.name})
        with self.assertRaises(ValidationError):
            picking.action_generate_lots()

        _po, picking = self._create_po_receipt([(first_product, 1)])
        line = self._batch_line(picking, first_product)
        line.write(
            {
                "received_qty": 1,
                "lot_name": lot.name,
                "supplier_lot": "SUP-B",
            }
        )
        with self.assertRaises(ValidationError):
            picking.action_generate_lots()

        _po, picking = self._create_po_receipt([(first_product, 1)])
        line = self._batch_line(picking, first_product)
        line.write(
            {
                "received_qty": 1,
                "lot_name": lot.name,
                "expiry_date": fields.Date.today() + timedelta(days=90),
            }
        )
        with self.assertRaises(ValidationError):
            picking.action_generate_lots()

    def test_optional_dates_enforce_full_consistency(self):
        product = self._create_product("Date Checked Product", minimum_shelf_life_days=30)
        _po, picking = self._create_po_receipt([(product, 1)])
        receipt_date = picking._grandora_receipt_date()
        line = self._batch_line(picking, product)
        line.write(
            {
                "received_qty": 1,
                "manufacture_date": receipt_date - timedelta(days=10),
                "expiry_date": receipt_date + timedelta(days=40),
            }
        )
        picking.action_generate_lots()

        _po, picking = self._create_po_receipt([(product, 1)])
        line = self._batch_line(picking, product)
        line.write(
            {
                "received_qty": 1,
                "manufacture_date": picking._grandora_receipt_date() + timedelta(days=1),
            }
        )
        with self.assertRaises(ValidationError):
            picking.action_generate_lots()

        _po, picking = self._create_po_receipt([(product, 1)])
        line = self._batch_line(picking, product)
        line.write(
            {
                "received_qty": 1,
                "expiry_date": picking._grandora_receipt_date() - timedelta(days=1),
            }
        )
        with self.assertRaises(ValidationError):
            picking.action_generate_lots()

    def test_product_lot_acronym_normalization(self):
        template = self.env["product.template"]
        self.assertEqual(template._grandora_product_lot_acronym("Milk"), "MIL")
        self.assertEqual(
            template._grandora_product_lot_acronym("Beef-Burger 2kg"), "BB2"
        )
        self.assertEqual(template._grandora_product_lot_acronym("---"), "PRD")

    def test_acronym_collision_and_product_rename_refresh_prefix(self):
        first = self._create_product("Beef Burger Plate")
        second = self._create_product("Baked Bean Paste")
        self.assertEqual(first.product_tmpl_id.lot_sequence_id.prefix, "BTCH-BBP-")
        self.assertEqual(
            second.product_tmpl_id.lot_sequence_id.prefix,
            f"BTCH-BBP-{second.product_tmpl_id.id}-",
        )

        first.product_tmpl_id.write({"name": "Chicken Burger Plate"})
        self.assertEqual(first.product_tmpl_id.lot_sequence_id.prefix, "BTCH-CBP-")

    def test_stock_lot_create_uses_synchronized_product_sequence(self):
        product = self._create_product("Direct Generation Product")
        product.product_tmpl_id.write({"name": "Renamed Direct Product"})
        lot = self.env["stock.lot"].create(
            {"product_id": product.id, "company_id": self.env.company.id}
        )
        self.assertEqual(lot.name, "BTCH-RDP-100")

    def test_update_quantity_generates_lot_for_lot_tracked_product(self):
        product = self._create_product("Update Quantity Product")
        quant = self._create_inventory_quant(product, 12)

        self.assertFalse(quant.lot_id)
        self.assertFalse(quant.action_apply_inventory())

        self.assertEqual(quant.lot_id.name, "BTCH-UQP-100")
        self.assertEqual(quant.quantity, 12)

    def test_update_quantity_inline_action_generates_lot_before_apply(self):
        product = self._create_product("Inline Quantity Product")
        quant = self._create_inventory_quant(product, 0)

        result = quant.action_generate_inventory_lot()

        self.assertEqual(result, {"type": "ir.actions.client", "tag": "reload"})
        self.assertEqual(quant.lot_id.name, "BTCH-IQP-100")
        self.assertEqual(quant.quantity, 0)

    def test_update_quantity_preserves_manually_selected_lot(self):
        product = self._create_product("Manual Quantity Product")
        manual_lot = self.env["stock.lot"].create(
            {
                "name": "MANUAL-QUANTITY-LOT",
                "product_id": product.id,
                "company_id": self.env.company.id,
            }
        )
        quant = self._create_inventory_quant(product, 8, lot=manual_lot)

        self.assertFalse(quant.action_apply_inventory())

        self.assertEqual(quant.lot_id, manual_lot)
        self.assertEqual(quant.quantity, 8)

    def test_update_quantity_keeps_untracked_products_lot_free(self):
        product = self._create_product("Untracked Quantity Product", tracking="none")
        quant = self._create_inventory_quant(product, 4)

        self.assertFalse(quant.action_apply_inventory())

        self.assertFalse(quant.lot_id)
        self.assertEqual(quant.quantity, 4)

    def test_update_quantity_view_shows_inline_batch_generator(self):
        view = self.env.ref(
            "grandora_inventory_product_features.view_stock_quant_tree_inventory_generate_lot"
        )
        self.assertIn('name="action_generate_inventory_lot"', view.arch_db)
        self.assertIn('string="Generate Batch Number"', view.arch_db)
        self.assertIn("tracking == 'lot' and not lot_id", view.arch_db)

    def test_standard_validate_generates_and_assigns_missing_lots(self):
        product = self._create_product("Validate Receipt Product")
        _po, picking = self._create_po_receipt([(product, 5)])
        line = self._batch_line(picking, product)
        line.write({"received_qty": 5})

        result = picking.button_validate()

        self.assertTrue(result)
        self.assertEqual(picking.state, "done")
        self.assertEqual(line.internal_lot_id.name, "BTCH-VRP-100")
        self.assertEqual(picking.move_line_ids.lot_id, line.internal_lot_id)

    def test_partial_receipt_keeps_standard_backorder_flow(self):
        product = self._create_product("Partial Receipt Product")
        _po, picking = self._create_po_receipt([(product, 100)])
        line = self._batch_line(picking, product)
        line.write({"received_qty": 90})

        result = picking.button_validate()

        self.assertEqual(result["res_model"], "stock.backorder.confirmation")
        self.assertEqual(line.internal_lot_id.name, "BTCH-PRP-100")
        move = picking.move_ids.filtered(lambda candidate: candidate.product_id == product)
        self.assertEqual(move.quantity, 90)

    def test_receipt_view_keeps_only_generate_lots_as_custom_action(self):
        view = self.env.ref(
            "grandora_inventory_product_features.view_picking_form_inherit_batch_entry"
        )
        self.assertIn('name="action_generate_lots"', view.arch_db)
        self.assertNotIn('name="action_validate_with_lots"', view.arch_db)
        self.assertNotIn('name="action_add_batch"', view.arch_db)
        self.assertNotIn('name="action_generate_batch_lines"', view.arch_db)
        self.assertNotIn('name="batch_buttons"', view.arch_db)
