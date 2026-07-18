from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class StockPicking(models.Model):
    _inherit = "stock.picking"

    batch_line_ids = fields.One2many(
        "grandora.receipt.batch.line",
        "picking_id",
        string="Receipt Batches",
        copy=False,
        help="Batch-level receipt details for lot-tracked products.",
    )
    show_batch_entry = fields.Boolean(
        compute="_compute_show_batch_entry",
        help="Technical field to show/hide the batch entry section.",
    )

    @api.depends("picking_type_code", "purchase_id")
    def _compute_show_batch_entry(self):
        for picking in self:
            picking.show_batch_entry = (
                picking.picking_type_code == "incoming"
                and bool(picking.purchase_id)
            )

    def action_generate_batch_lines(self):
        """Populate batch lines from moves for lot-tracked products."""
        self.ensure_one()
        if not self.show_batch_entry:
            return
        existing_move_ids = set(self.batch_line_ids.move_id.ids)
        for move in self.move_ids.filtered(
            lambda m: m.product_id.tracking == "lot" and m.state not in ("done", "cancel")
        ):
            if move.id not in existing_move_ids:
                self.env["grandora.receipt.batch.line"].create(
                    {
                        "picking_id": self.id,
                        "move_id": move.id,
                        "received_qty": move.quantity or move.product_uom_qty,
                    }
                )

    def action_generate_lots(self):
        """Generate internal lots for batch lines that don't have one yet.

        For each batch line without an internal_lot_id, create a stock.lot
        and assign it.
        """
        self.ensure_one()
        self._check_batch_lines()
        for line in self.batch_line_ids:
            if line.internal_lot_id:
                continue
            if float_is_zero(line.received_qty, precision_rounding=line.product_uom_id.rounding):
                continue
            lot = self._resolve_lot_for_batch_line(line)
            line.write({"internal_lot_id": lot.id, "lot_name": lot.name})

    def _grandora_receipts_requiring_lot_automation(self):
        return self.filtered(
            lambda picking: picking.show_batch_entry
            and any(move.product_id.tracking == "lot" for move in picking.move_ids)
        )

    def button_validate(self):
        """Prepare and assign receipt lots before Odoo runs its sanity checks."""
        qualifying_pickings = self._grandora_receipts_requiring_lot_automation()
        for picking in qualifying_pickings:
            picking.action_generate_batch_lines()
            picking._check_batch_lines()
            picking.action_generate_lots()
            picking._assign_lots_to_move_lines()
        return super().button_validate()

    def action_validate_with_lots(self):
        """Compatibility entry point; standard Validate now performs automation."""
        return self.button_validate()

    def action_add_batch(self):
        """Add another batch line for the same receipt."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "grandora.receipt.batch.line",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_picking_id": self.id,
                "default_move_id": self.move_ids.filtered(
                    lambda m: m.product_id.tracking == "lot"
                    and m.state not in ("done", "cancel")
                )[:1].id,
            },
        }

    def _get_batch_lines_for_move(self, move):
        """Get all batch lines for a specific stock move."""
        return self.batch_line_ids.filtered(lambda l: l.move_id == move)

    def _lot_values_from_batch_line(self, line):
        return {
            "product_id": line.product_id.id,
            "company_id": self.company_id.id,
            "supplier_lot": line.supplier_lot or "",
            "purchase_order_id": self.purchase_id.id,
            "receipt_id": self.id,
            "expiration_date": line.expiry_date,
            "manufacture_date": line.manufacture_date,
        }

    def _check_reused_lot_metadata(self, line, lot):
        """Block conflicting non-empty metadata on a reused manual lot."""
        conflicts = []
        if line.supplier_lot and lot.supplier_lot and line.supplier_lot != lot.supplier_lot:
            conflicts.append(_("Supplier Batch"))
        lot_expiry = fields.Date.to_date(lot.expiration_date)
        if line.expiry_date and lot_expiry and line.expiry_date != lot_expiry:
            conflicts.append(_("Expiry Date"))
        if (
            line.manufacture_date
            and lot.manufacture_date
            and line.manufacture_date != lot.manufacture_date
        ):
            conflicts.append(_("Manufacture Date"))
        if conflicts:
            raise ValidationError(
                _(
                    "Lot '%(lot)s' already exists for product '%(product)s' with "
                    "different metadata: %(fields)s.",
                    lot=lot.name,
                    product=line.product_id.display_name,
                    fields=", ".join(conflicts),
                )
            )

    def _fill_blank_reused_lot_metadata(self, line, lot):
        """Enrich blank metadata without overwriting the lot's existing history."""
        values = {}
        if line.supplier_lot and not lot.supplier_lot:
            values["supplier_lot"] = line.supplier_lot
        if line.expiry_date and not lot.expiration_date:
            values["expiration_date"] = line.expiry_date
        if line.manufacture_date and not lot.manufacture_date:
            values["manufacture_date"] = line.manufacture_date
        if self.purchase_id and not lot.purchase_order_id:
            values["purchase_order_id"] = self.purchase_id.id
        if not lot.receipt_id:
            values["receipt_id"] = self.id
        if values:
            lot.write(values)

    def _resolve_lot_for_batch_line(self, line):
        """Reuse/create a manual lot, or generate one when the name is blank."""
        manual_name = (line.lot_name or "").strip()
        if not manual_name:
            return self.env["stock.lot"].create(self._lot_values_from_batch_line(line))

        lot = self.env["stock.lot"].search(
            [
                ("name", "=", manual_name),
                "|",
                ("company_id", "=", self.company_id.id),
                ("company_id", "=", False),
            ],
            limit=1,
        )
        if lot:
            if lot.product_id != line.product_id:
                raise ValidationError(
                    _(
                        "Lot '%(lot)s' belongs to '%(lot_product)s', not '%(product)s'.",
                        lot=manual_name,
                        lot_product=lot.product_id.display_name,
                        product=line.product_id.display_name,
                    )
                )
            self._check_reused_lot_metadata(line, lot)
            self._fill_blank_reused_lot_metadata(line, lot)
            return lot

        values = self._lot_values_from_batch_line(line)
        values["name"] = manual_name
        return self.env["stock.lot"].create(values)

    def _grandora_receipt_date(self):
        self.ensure_one()
        return fields.Date.to_date(self.scheduled_date) or fields.Date.context_today(self)

    def _check_batch_lines(self):
        """Validate batch line data before lot creation and validation."""
        self.ensure_one()
        lot_moves = self.move_ids.filtered(
            lambda m: m.product_id.tracking == "lot" and m.state not in ("done", "cancel")
        )
        if not lot_moves:
            return
        if not self.batch_line_ids:
            raise UserError(
                _("No batch lines entered. Please add batch details before validating.")
            )

        receipt_date = self._grandora_receipt_date()

        # Group batch lines by move to check quantity totals.
        for move in lot_moves:
            batch_lines = self._get_batch_lines_for_move(move)
            if not batch_lines:
                raise ValidationError(
                    _(
                        "Batch details are required for lot-tracked product '%(product)s'.",
                        product=move.product_id.display_name,
                    )
                )

            total_received = sum(batch_lines.mapped("received_qty"))
            demand_qty = move.product_uom_qty

            if float_compare(
                total_received,
                demand_qty,
                precision_rounding=move.product_uom.rounding,
            ) > 0:
                raise ValidationError(
                    _(
                        "Received quantity (%(total)s %(uom)s) for product %(product)s "
                        "cannot exceed the ordered quantity (%(ordered)s %(uom)s).",
                        total=total_received,
                        uom=move.product_uom.name,
                        product=move.product_id.display_name,
                        ordered=demand_qty,
                    )
                )

            for line in batch_lines:
                product = line.product_id
                categ = product.categ_id

                if line.internal_lot_id and line.internal_lot_id.product_id != product:
                    raise ValidationError(
                        _(
                            "Internal lot %(lot)s belongs to %(lot_product)s, not %(product)s.",
                            lot=line.internal_lot_id.name,
                            lot_product=line.internal_lot_id.product_id.display_name,
                            product=product.display_name,
                        )
                    )

                product_tmpl = product.product_tmpl_id

                # Expiry before receipt date
                if line.expiry_date and line.expiry_date < receipt_date:
                    raise ValidationError(
                        _(
                            "Expiry date (%(expiry)s) for product '%(product)s' "
                            "is before the receipt date (%(receipt)s).",
                            expiry=line.expiry_date,
                            product=product.display_name,
                            receipt=receipt_date,
                        )
                    )

                # Manufacture date consistency checks (all dates remain optional).
                if line.manufacture_date and line.manufacture_date > receipt_date:
                    raise ValidationError(
                        _(
                            "Manufacture date (%(manufacture)s) for product '%(product)s' "
                            "cannot be after the receipt date (%(receipt)s).",
                            manufacture=line.manufacture_date,
                            product=product.display_name,
                            receipt=receipt_date,
                        )
                    )
                if (
                    line.manufacture_date
                    and line.expiry_date
                    and line.manufacture_date > line.expiry_date
                ):
                    raise ValidationError(
                        _(
                            "Manufacture date (%(manufacture)s) for product '%(product)s' "
                            "cannot be after its expiry date (%(expiry)s).",
                            manufacture=line.manufacture_date,
                            product=product.display_name,
                            expiry=line.expiry_date,
                        )
                    )

                # Minimum shelf-life check applies only when expiry is supplied.
                minimum_shelf_life_days = max(
                    product_tmpl.minimum_shelf_life_days,
                    categ.minimum_shelf_life_days,
                )
                if minimum_shelf_life_days > 0 and line.expiry_date:
                    remaining_days = (line.expiry_date - receipt_date).days
                    if remaining_days < minimum_shelf_life_days:
                        raise ValidationError(
                            _(
                                "Minimum shelf life of %(min_days)s days is required for "
                                "product '%(product)s'. Only %(remaining)s days remaining until expiry.",
                                min_days=minimum_shelf_life_days,
                                product=product.display_name,
                                remaining=remaining_days,
                            )
                        )

    def _assign_lots_to_move_lines(self):
        """Assign generated lots to stock.move.line records.
        
        This creates move lines if they don't exist, and assigns the
        proper lot and quantity for each batch.
        """
        self.ensure_one()
        for move in self.move_ids.filtered(
            lambda m: m.product_id.tracking == "lot"
            and m.state not in ("done", "cancel")
        ):
            batch_lines = self._get_batch_lines_for_move(move)
            if not batch_lines:
                continue

            # Replace draft/non-done move lines with the exact batch split.
            move.move_line_ids.filtered(lambda ml: ml.state not in ("done", "cancel")).unlink()

            for line in batch_lines:
                if float_is_zero(
                    line.received_qty,
                    precision_rounding=line.product_uom_id.rounding,
                ):
                    continue
                if not line.internal_lot_id:
                    continue

                # Create or update move line
                move_line_vals = {
                    "move_id": move.id,
                    "picking_id": self.id,
                    "product_id": move.product_id.id,
                    "product_uom_id": move.product_uom.id,
                    "location_id": move.location_id.id,
                    "location_dest_id": move.location_dest_id.id,
                    "lot_id": line.internal_lot_id.id,
                    "quantity": line.received_qty,
                    "company_id": self.company_id.id,
                    "picked": True,
                }
                self.env["stock.move.line"].create(move_line_vals)

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        # Auto-generate batch lines for qualified pickings.
        for picking in pickings:
            if picking.show_batch_entry:
                picking.action_generate_batch_lines()
        return pickings

    def write(self, vals):
        res = super().write(vals)
        if "state" in vals and vals.get("state") not in ("draft", "cancel"):
            for picking in self:
                if picking.show_batch_entry and not picking.batch_line_ids:
                    picking.action_generate_batch_lines()
        return res
