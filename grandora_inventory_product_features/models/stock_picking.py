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
        existing = self.batch_line_ids
        existing_product_move = {
            (l.move_id.id, l.supplier_lot, l.expiry_date): l
            for l in existing
        }
        for move in self.move_ids.filtered(
            lambda m: m.product_id.tracking == "lot" and m.state not in ("done", "cancel")
        ):
            key = (move.id, False, False)
            if key not in existing_product_move:
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
            lot = self._create_lot_for_batch_line(line)
            line.internal_lot_id = lot.id

    def action_validate_with_lots(self):
        """Validate the receipt, creating lots and assigning to move lines.
        
        1. Generate lots for any batch lines that don't have them.
        2. Validate batch line data (quantities, required fields).
        3. Assign lots to stock.move.line records.
        4. Call standard validation.
        """
        self.ensure_one()
        self._check_batch_lines()
        self.action_generate_lots()
        self._assign_lots_to_move_lines()
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

    def _create_lot_for_batch_line(self, line):
        """Create a stock.lot record for a batch line."""
        lot_vals = {
            "product_id": line.product_id.id,
            "company_id": self.company_id.id,
            "supplier_lot": line.supplier_lot or "",
            "purchase_order_id": self.purchase_id.id,
            "receipt_id": self.id,
            "expiration_date": line.expiry_date,
            "manufacture_date": line.manufacture_date,
        }
        # The OCA product_lot_sequence module will auto-assign the
        # next global sequence number to the name field.
        lot = self.env["stock.lot"].create(lot_vals)
        return lot

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

                # Supplier batch requirement check
                if (
                    product_tmpl.require_supplier_batch
                    or categ.require_supplier_batch
                    or product.tracking == "lot"
                ) and not line.supplier_lot:
                    raise ValidationError(
                        _(
                            "Supplier batch is required for product '%(product)s' but none was provided.",
                            product=product.display_name,
                        )
                    )

                # Expiry date requirement
                if product_tmpl.require_expiry_date or categ.require_expiry_date or product.use_expiration_date:
                    if not line.expiry_date:
                        raise ValidationError(
                            _(
                                "Expiry date is required for product '%(product)s' but none was provided.",
                                product=product.display_name,
                            )
                        )

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

                # Minimum shelf-life check
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
