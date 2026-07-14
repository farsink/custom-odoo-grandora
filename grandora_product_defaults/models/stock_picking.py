from odoo import _, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _grandora_is_incoming_receipt(self):
        self.ensure_one()
        return self.picking_type_id.code == "incoming"

    def _grandora_requires_auto_batch(self, move_line):
        product = move_line.product_id
        return bool(
            self._grandora_is_incoming_receipt()
            and product
            and product.type == "consu"
            and product.is_storable
            and product.tracking == "lot"
        )

    def _grandora_lot_date_token(self):
        self.ensure_one()
        base_date = fields.Date.to_date(self.scheduled_date or fields.Datetime.now())
        return base_date.strftime("%Y%m%d")

    def _grandora_next_internal_batch_name(self, product):
        self.ensure_one()
        sku = product.default_code or product.product_tmpl_id.default_code
        if not sku:
            sku = product.categ_id._grandora_next_product_sku()
            product.write({"default_code": sku})
            if not product.product_tmpl_id.default_code:
                product.product_tmpl_id.default_code = sku
        sequence = self.env["ir.sequence"].sudo()
        date_token = self._grandora_lot_date_token()
        Lot = self.env["stock.lot"].sudo()
        company = self.company_id or self.env.company
        while True:
            suffix = sequence.next_by_code("grandora.purchase.lot") or "001"
            name = "LOT-%s-%s-%s" % (sku, date_token, suffix)
            duplicate = Lot.search_count([
                ("product_id", "=", product.id),
                ("name", "=", name),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", company.id),
            ])
            if not duplicate:
                return name

    def _grandora_prepare_incoming_batches(self):
        for picking in self:
            if not picking._grandora_is_incoming_receipt():
                continue
            for move_line in picking.move_line_ids.filtered(lambda line: line.quantity > 0):
                if not picking._grandora_requires_auto_batch(move_line):
                    continue
                if move_line.lot_id:
                    raise UserError(_(
                        "Do not reuse an existing lot for incoming product %(product)s. Clear the Lot/Serial Number; Grandora will generate a new internal batch ID.",
                        product=move_line.product_id.display_name,
                    ))
                if not move_line.supplier_lot_name and move_line.lot_name:
                    move_line.supplier_lot_name = move_line.lot_name
                missing = []
                if not move_line.supplier_lot_name:
                    missing.append(_("Supplier Lot/Batch"))
                expiration_is_placeholder = False
                if move_line.expiration_date and not move_line.product_id.expiration_time:
                    expiration_is_placeholder = fields.Date.to_date(move_line.expiration_date) <= fields.Date.to_date(picking.scheduled_date or fields.Datetime.now())
                if not move_line.expiration_date or expiration_is_placeholder:
                    missing.append(_("Expiry Date"))
                if not move_line.best_before_date:
                    missing.append(_("Best Before Date"))
                if missing:
                    raise UserError(_(
                        "Receipt %(receipt)s for %(product)s is missing: %(fields)s.",
                        receipt=picking.name,
                        product=move_line.product_id.display_name,
                        fields=", ".join(missing),
                    ))
                if move_line.best_before_date and move_line.expiration_date and move_line.best_before_date > move_line.expiration_date:
                    raise UserError(_(
                        "Best Before Date cannot be later than Expiry Date for %(product)s on receipt %(receipt)s.",
                        product=move_line.product_id.display_name,
                        receipt=picking.name,
                    ))
                move_line.lot_name = picking._grandora_next_internal_batch_name(move_line.product_id)

    def button_validate(self):
        self._grandora_prepare_incoming_batches()
        return super().button_validate()

    def _action_done(self):
        self._grandora_prepare_incoming_batches()
        return super()._action_done()
