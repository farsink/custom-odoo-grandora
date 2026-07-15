from odoo import fields, models, tools


_COST_GROUPS = "stock.group_stock_manager,account.group_account_user"


class GrandoraOnhandBatchDashboard(models.Model):
    _name = "grandora.onhand.batch.dashboard"
    _description = "On-hand Batch Cost Dashboard"
    _auto = False
    _rec_name = "product_id"
    _order = "product_default_code, batch_number, location_id"

    product_id = fields.Many2one("product.product", string="Product", readonly=True)
    product_tmpl_id = fields.Many2one("product.template", string="Product Template", readonly=True)
    product_default_code = fields.Char(string="Product SKU / Internal ID", readonly=True)
    product_name = fields.Char(string="Product Name", readonly=True)
    product_barcode = fields.Char(string="Barcode", readonly=True)
    brand_id = fields.Many2one("product.brand", string="Brand", readonly=True)
    item_group_id = fields.Many2one("product.item.group", string="Item Group", readonly=True)
    categ_id = fields.Many2one("product.category", string="Product Category", readonly=True)
    lot_id = fields.Many2one("stock.lot", string="Batch Number", readonly=True)
    batch_number = fields.Char(string="Batch Number", readonly=True)
    supplier_batch = fields.Char(string="Supplier Batch", readonly=True)
    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", readonly=True)
    location_id = fields.Many2one("stock.location", string="Location", readonly=True)
    company_id = fields.Many2one("res.company", string="Company", readonly=True)
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True)
    uom_id = fields.Many2one("uom.uom", string="UoM", readonly=True)

    quantity = fields.Float(string="On-hand Quantity", readonly=True)
    reserved_quantity = fields.Float(string="Reserved Quantity", readonly=True)
    available_quantity = fields.Float(string="Available Quantity", readonly=True)

    receipt_date = fields.Date(string="Receipt Date", readonly=True)
    expiry_date = fields.Date(string="Expiry Date", readonly=True)
    days_to_expiry = fields.Integer(string="Days to Expiry", readonly=True)

    landed_unit_cost = fields.Monetary(
        string="Landed Unit Cost",
        currency_field="currency_id",
        readonly=True,
        groups=_COST_GROUPS,
    )
    batch_value = fields.Monetary(
        string="Batch Value",
        currency_field="currency_id",
        readonly=True,
        groups=_COST_GROUPS,
    )
    latest_sale_price = fields.Monetary(
        string="Latest Sale Price",
        currency_field="currency_id",
        readonly=True,
    )
    unit_margin_percent = fields.Float(
        string="Unit Margin %",
        readonly=True,
        groups=_COST_GROUPS,
    )

    status = fields.Selection(
        [
            ("available", "Available"),
            ("low_stock", "Low Stock"),
            ("expiring_soon", "Expiring Soon"),
            ("expired", "Expired"),
            ("depleted", "Depleted"),
        ],
        string="Status",
        readonly=True,
    )
    is_low_stock = fields.Boolean(string="Low Stock", readonly=True)
    has_batch_cost = fields.Boolean(string="Has Batch Cost", readonly=True, groups=_COST_GROUPS)
    has_sale_price = fields.Boolean(string="Has Previous Sale Price", readonly=True)
    negative_margin = fields.Boolean(string="Negative Margin", readonly=True, groups=_COST_GROUPS)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            f"""
            CREATE OR REPLACE VIEW {self._table} AS (
                WITH quant_base AS (
                    SELECT
                        MIN(q.id) AS id,
                        q.product_id,
                        q.lot_id,
                        q.location_id,
                        COALESCE(q.company_id, loc.company_id, lot.company_id) AS company_id,
                        SUM(q.quantity) AS quantity,
                        SUM(q.reserved_quantity) AS reserved_quantity,
                        SUM(q.quantity - q.reserved_quantity) AS available_quantity,
                        MIN(q.in_date)::date AS quant_in_date
                    FROM stock_quant q
                    JOIN stock_location loc ON loc.id = q.location_id
                    LEFT JOIN stock_lot lot ON lot.id = q.lot_id
                    WHERE loc.usage = 'internal'
                    GROUP BY
                        q.product_id,
                        q.lot_id,
                        q.location_id,
                        COALESCE(q.company_id, loc.company_id, lot.company_id)
                ),
                valuation AS (
                    SELECT
                        svl.product_id,
                        svl.lot_id,
                        svl.company_id,
                        SUM(svl.remaining_qty) AS remaining_qty,
                        SUM(svl.remaining_value) AS remaining_value,
                        (MIN(svl.create_date) FILTER (WHERE svl.quantity > 0))::date AS receipt_date
                    FROM stock_valuation_layer svl
                    GROUP BY svl.product_id, svl.lot_id, svl.company_id
                ),
                latest_sale AS (
                    SELECT DISTINCT ON (aml.product_id, aml.company_id)
                        aml.product_id,
                        aml.company_id,
                        (
                            -aml.balance / NULLIF(
                                aml.quantity / NULLIF(COALESCE(uom_line.factor, 1.0) / COALESCE(uom_template.factor, 1.0), 0.0),
                                0.0
                            )
                        ) AS latest_sale_price
                    FROM account_move_line aml
                    JOIN account_move move ON move.id = aml.move_id
                    JOIN product_product product ON product.id = aml.product_id
                    JOIN product_template template ON template.id = product.product_tmpl_id
                    LEFT JOIN uom_uom uom_line ON uom_line.id = aml.product_uom_id
                    LEFT JOIN uom_uom uom_template ON uom_template.id = template.uom_id
                    WHERE move.state = 'posted'
                        AND move.move_type = 'out_invoice'
                        AND aml.display_type = 'product'
                        AND aml.product_id IS NOT NULL
                        AND aml.quantity > 0
                        AND aml.price_unit > 0
                        AND -aml.balance > 0
                    ORDER BY aml.product_id, aml.company_id, move.invoice_date DESC NULLS LAST, move.id DESC, aml.id DESC
                ),
                orderpoint AS (
                    SELECT
                        product_id,
                        location_id,
                        company_id,
                        MIN(product_min_qty) AS product_min_qty
                    FROM stock_warehouse_orderpoint
                    WHERE active = TRUE
                    GROUP BY product_id, location_id, company_id
                ),
                row_data AS (
                    SELECT
                        qb.id,
                        qb.product_id,
                        pp.product_tmpl_id,
                        COALESCE(pp.default_code, pt.default_code, '') AS product_default_code,
                        COALESCE(pt.name->>'en_US', '') AS product_name,
                        pp.barcode AS product_barcode,
                        pt.brand_id,
                        pt.item_group_id,
                        pt.categ_id,
                        qb.lot_id,
                        lot.name AS batch_number,
                        ''::varchar AS supplier_batch,
                        wh.id AS warehouse_id,
                        qb.location_id,
                        qb.company_id,
                        company.currency_id,
                        pt.uom_id,
                        qb.quantity,
                        qb.reserved_quantity,
                        qb.available_quantity,
                        COALESCE(val.receipt_date, lot.create_date::date, qb.quant_in_date) AS receipt_date,
                        lot.expiration_date::date AS expiry_date,
                        CASE
                            WHEN lot.expiration_date IS NOT NULL THEN lot.expiration_date::date - CURRENT_DATE
                            ELSE NULL
                        END AS days_to_expiry,
                        cost.landed_unit_cost,
                        qb.quantity * cost.landed_unit_cost AS batch_value,
                        COALESCE(ls.latest_sale_price, 0.0) AS latest_sale_price,
                        CASE
                            WHEN COALESCE(ls.latest_sale_price, 0.0) > 0
                                THEN (ls.latest_sale_price - cost.landed_unit_cost) / ls.latest_sale_price
                            ELSE 0.0
                        END AS unit_margin_percent,
                        CASE
                            WHEN op.product_min_qty IS NOT NULL THEN qb.available_quantity <= op.product_min_qty
                            ELSE qb.available_quantity <= 0
                        END AS is_low_stock,
                        cost.landed_unit_cost > 0 AS has_batch_cost,
                        COALESCE(ls.latest_sale_price, 0.0) > 0 AS has_sale_price,
                        COALESCE(ls.latest_sale_price, 0.0) > 0 AND cost.landed_unit_cost > COALESCE(ls.latest_sale_price, 0.0) AS negative_margin
                    FROM quant_base qb
                    JOIN product_product pp ON pp.id = qb.product_id
                    JOIN product_template pt ON pt.id = pp.product_tmpl_id
                    LEFT JOIN stock_lot lot ON lot.id = qb.lot_id
                    LEFT JOIN stock_location loc ON loc.id = qb.location_id
                    LEFT JOIN stock_warehouse wh ON loc.parent_path::text LIKE CONCAT('%%/', wh.view_location_id, '/%%')
                    LEFT JOIN res_company company ON company.id = qb.company_id
                    LEFT JOIN valuation val
                        ON val.product_id = qb.product_id
                        AND val.company_id IS NOT DISTINCT FROM qb.company_id
                        AND val.lot_id IS NOT DISTINCT FROM qb.lot_id
                    LEFT JOIN latest_sale ls
                        ON ls.product_id = qb.product_id
                        AND ls.company_id IS NOT DISTINCT FROM qb.company_id
                    LEFT JOIN orderpoint op
                        ON op.product_id = qb.product_id
                        AND op.location_id = qb.location_id
                        AND op.company_id IS NOT DISTINCT FROM qb.company_id
                    LEFT JOIN LATERAL (
                        SELECT CASE
                            WHEN COALESCE(val.remaining_qty, 0.0) > 0
                                THEN COALESCE(val.remaining_value, 0.0) / NULLIF(val.remaining_qty, 0.0)
                            ELSE COALESCE(pt.total_cost, 0.0)
                        END AS landed_unit_cost
                    ) cost ON TRUE
                )
                SELECT
                    row_data.*,
                    CASE
                        WHEN row_data.quantity <= 0 THEN 'depleted'
                        WHEN row_data.expiry_date IS NOT NULL AND row_data.expiry_date < CURRENT_DATE THEN 'expired'
                        WHEN row_data.expiry_date IS NOT NULL AND row_data.expiry_date <= CURRENT_DATE + INTERVAL '30 days' THEN 'expiring_soon'
                        WHEN row_data.is_low_stock THEN 'low_stock'
                        ELSE 'available'
                    END AS status
                FROM row_data
            )
            """
        )
