from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lot_id = fields.Many2one(
        "stock.lot",
        string="Lot / Batch",
        copy=False,
        check_company=True,
        domain="[('id', 'in', available_lot_ids)]",
        help="Batch selected for this sale line. Delivery reservation is restricted to this lot.",
    )
    available_lot_ids = fields.Many2many(
        "stock.lot",
        compute="_compute_available_lot_ids",
        string="Available Lots",
    )
    batch_cost = fields.Monetary(
        string="Batch Cost",
        currency_field="currency_id",
        readonly=True,
        copy=False,
        help="Unit cost copied from the selected lot average cost; falls back to product cost when lot average cost is zero.",
    )
    actual_lot_id = fields.Many2one(
        "stock.lot",
        string="Actual Delivered Lot",
        readonly=True,
        copy=False,
        check_company=True,
    )
    actual_batch_cost = fields.Monetary(
        string="Actual Batch Cost",
        currency_field="currency_id",
        readonly=True,
        copy=False,
        help="Cost snapshot saved when the delivery is completed.",
    )
    unit_margin_percent = fields.Float(
        string="Unit Margin %",
        compute="_compute_unit_margin_percent",
        store=True,
        readonly=True,
        copy=False,
        help="Unit margin based on selected batch cost and selling unit price.",
    )

    def _requires_lot_selection(self):
        self.ensure_one()
        return bool(
            not self.display_type
            and not self.is_downpayment
            and self.product_id
            and self.product_id.type == "consu"
        )

    def _get_lot_available_qty(self, lot):
        self.ensure_one()
        if not self.product_id or not lot or not self.order_id.warehouse_id:
            return 0.0
        return self.env["stock.quant"]._get_available_quantity(
            self.product_id,
            self.order_id.warehouse_id.lot_stock_id,
            lot_id=lot,
            strict=False,
        )

    def _get_available_lots(self):
        self.ensure_one()
        if not self.product_id or not self.order_id.warehouse_id:
            return self.env["stock.lot"]
        domain = [
            ("product_id", "=", self.product_id.id),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", self.company_id.id or self.env.company.id),
        ]
        lots = self.env["stock.lot"].search(domain)
        return lots.filtered(lambda lot: self._get_lot_available_qty(lot) > 0)

    def _get_available_lot_domain(self):
        self.ensure_one()
        return [("id", "in", self._get_available_lots().ids)]

    @api.depends("product_id", "order_id.warehouse_id", "company_id")
    def _compute_available_lot_ids(self):
        for line in self:
            line.available_lot_ids = line._get_available_lots() if line.product_id else False

    def _get_lot_batch_cost(self, lot):
        self.ensure_one()
        if not lot or not self.product_id:
            return 0.0
        company = self.company_id or self.order_id.company_id or self.env.company
        lot = lot.sudo().with_company(company)
        product = self.product_id.sudo().with_company(company)
        company_currency = company.currency_id
        lot_avg_cost = lot.avg_cost or 0.0
        cost = lot_avg_cost if lot_avg_cost > 0 else product.standard_price or 0.0
        return self._convert_to_sol_currency(cost, company_currency)

    def _refresh_batch_cost_from_lot(self):
        for line in self:
            if line.lot_id:
                line.batch_cost = line._get_lot_batch_cost(line.lot_id)
            else:
                line.batch_cost = 0.0

    @api.depends("price_unit", "discount", "batch_cost")
    def _compute_unit_margin_percent(self):
        for line in self:
            selling_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.unit_margin_percent = selling_price and (selling_price - line.batch_cost) / selling_price or 0.0

    @api.onchange("product_id", "order_id.warehouse_id", "product_uom_qty", "product_uom")
    def _onchange_lot_product_or_warehouse(self):
        for line in self:
            if not line.product_id:
                line.lot_id = False
                line.batch_cost = 0.0
                continue
            if line.lot_id and (
                line.lot_id.product_id != line.product_id
                or (line.lot_id.company_id and line.lot_id.company_id != line.company_id)
                or line._get_lot_available_qty(line.lot_id) <= 0
            ):
                line.lot_id = False
                line.batch_cost = 0.0
        return {"domain": {"lot_id": self[:1]._get_available_lot_domain() if len(self) == 1 else []}}

    @api.onchange("lot_id")
    def _onchange_lot_id(self):
        self._refresh_batch_cost_from_lot()

    @api.constrains("lot_id", "product_id", "company_id")
    def _check_lot_product_company(self):
        for line in self:
            if not line.lot_id:
                continue
            if line.lot_id.product_id != line.product_id:
                raise ValidationError(_("Lot %(lot)s does not belong to product %(product)s.", lot=line.lot_id.display_name, product=line.product_id.display_name))
            if line.lot_id.company_id and line.lot_id.company_id != line.company_id:
                raise ValidationError(_("Lot %(lot)s belongs to another company.", lot=line.lot_id.display_name))

    def _check_lot_required_rules(self):
        for line in self:
            if not line._requires_lot_selection():
                continue
            if line.product_id.tracking == "none":
                raise ValidationError(_(
                    "Product %(product)s must be tracked by lots/batches before it can be sold.",
                    product=line.product_id.display_name,
                ))
            if not line.lot_id:
                raise ValidationError(_(
                    "Select a Lot / Batch for product %(product)s on order %(order)s.",
                    product=line.product_id.display_name,
                    order=line.order_id.name,
                ))

    def _check_selected_lot_availability(self):
        grouped = defaultdict(lambda: {"qty": 0.0, "lines": self.env["sale.order.line"]})
        for line in self:
            if not line._requires_lot_selection() or not line.lot_id:
                continue
            qty = line.product_uom._compute_quantity(
                line.product_uom_qty,
                line.product_id.uom_id,
                rounding_method="HALF-UP",
            )
            key = (line.order_id.warehouse_id.id, line.product_id.id, line.lot_id.id)
            grouped[key]["qty"] += qty
            grouped[key]["lines"] |= line

        for (warehouse_id, product_id, lot_id), data in grouped.items():
            line = data["lines"][:1]
            warehouse = self.env["stock.warehouse"].browse(warehouse_id)
            product = self.env["product.product"].browse(product_id)
            lot = self.env["stock.lot"].browse(lot_id)
            available_qty = self.env["stock.quant"]._get_available_quantity(
                product,
                warehouse.lot_stock_id,
                lot_id=lot,
                strict=False,
            )
            if float_compare(data["qty"], available_qty, precision_rounding=product.uom_id.rounding) > 0:
                raise ValidationError(_(
                    "Not enough quantity for lot %(lot)s of %(product)s in warehouse %(warehouse)s. Needed %(needed)s %(uom)s, available %(available)s %(uom)s.",
                    lot=lot.display_name,
                    product=product.display_name,
                    warehouse=warehouse.display_name,
                    needed=data["qty"],
                    available=available_qty,
                    uom=product.uom_id.name,
                ))
            data["lines"]._refresh_batch_cost_from_lot()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._refresh_batch_cost_from_lot()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if {"lot_id", "product_id", "product_uom", "currency_id", "order_id"} & set(vals):
            self.filtered(lambda line: not line.actual_lot_id)._refresh_batch_cost_from_lot()
        return res

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id=group_id)
        if self.lot_id:
            values["sale_lot_id"] = self.lot_id.id
        return values
