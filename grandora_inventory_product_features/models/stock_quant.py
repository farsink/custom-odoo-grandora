from odoo import fields, models


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def _grandora_empty_lot_quants(self):
        """Return new lot-tracked quant rows whose lot can safely be assigned."""
        return self.filtered(
            lambda quant: (
                quant.product_id.tracking == "lot"
                and not quant.lot_id
                and fields.Float.is_zero(
                    quant.quantity,
                    precision_rounding=quant.product_uom_id.rounding,
                )
            )
        )

    def _grandora_quants_requiring_lots(self):
        """Return positive lot-tracked inventory adjustments without a lot.

        Update Quantity creates an empty quant first, then records the entered
        counted quantity in ``inventory_quantity``. Core Odoo stops at that
        point with a tracked-product confirmation if no lot was selected. For
        lot-tracked products, Grandora instead assigns the next product batch.
        Serial-tracked products keep Odoo's normal confirmation because one
        generated lot cannot represent multiple serial units.
        """
        return self._grandora_empty_lot_quants().filtered(
            lambda quant: fields.Float.compare(
                quant.inventory_diff_quantity,
                0.0,
                precision_rounding=quant.product_uom_id.rounding,
            )
            > 0
        )

    def _grandora_assign_inventory_lots(self):
        """Create and assign a product-sequenced lot to each new quant row."""
        for quant in self:
            company = quant.company_id or quant.location_id.company_id or self.env.company
            lot = self.env["stock.lot"].create(
                {
                    "product_id": quant.product_id.id,
                    "company_id": company.id,
                }
            )
            # Odoo deliberately blocks direct lot changes while inventory mode
            # is active. This is an internal assignment before core Apply, so
            # bypass only that UI-edit restriction.
            quant.with_context(inventory_mode=False).write({"lot_id": lot.id})
        return True

    def _grandora_generate_inventory_lots(self):
        """Generate lots only for positive adjustments being applied."""
        return self._grandora_quants_requiring_lots()._grandora_assign_inventory_lots()

    def action_generate_inventory_lot(self):
        """Generate a batch from the inline Update Quantity suggestion link."""
        self._grandora_empty_lot_quants()._grandora_assign_inventory_lots()
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_apply_inventory(self):
        """Generate missing lots before core applies an inventory adjustment."""
        self._grandora_generate_inventory_lots()
        return super().action_apply_inventory()
