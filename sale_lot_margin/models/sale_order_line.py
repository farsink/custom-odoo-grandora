from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    landing_cost = fields.Monetary(
        string="Landing Cost",
        currency_field="currency_id",
        compute="_compute_product_cost_fields",
        store=True,
        readonly=True,
        copy=False,
        help="Per-unit landing cost copied from the selected product.",
    )
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_product_cost_fields",
        store=True,
        readonly=True,
        copy=False,
        help="Per-unit total cost copied from the selected product. Margin uses this value.",
    )
    unit_margin_percent = fields.Float(
        string="Margin %",
        compute="_compute_unit_margin_percent",
        store=True,
        readonly=True,
        copy=False,
        help="Margin percentage based on selling price and product total cost.",
    )

    @api.depends("product_id", "product_id.product_tmpl_id.landing_cost", "product_id.product_tmpl_id.total_cost", "currency_id", "company_id", "order_id.company_id")
    def _compute_product_cost_fields(self):
        for line in self:
            product_template = line.product_id.product_tmpl_id
            if not product_template:
                line.landing_cost = 0.0
                line.total_cost = 0.0
                continue
            company = line.company_id or line.order_id.company_id or line.env.company
            company_currency = company.currency_id
            line.landing_cost = line._convert_to_sol_currency(product_template.landing_cost or 0.0, company_currency)
            line.total_cost = line._convert_to_sol_currency(product_template.total_cost or product_template.standard_price or 0.0, company_currency)

    @api.depends("price_unit", "discount", "total_cost")
    def _compute_unit_margin_percent(self):
        for line in self:
            selling_price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.unit_margin_percent = selling_price and (selling_price - line.total_cost) / selling_price or 0.0
