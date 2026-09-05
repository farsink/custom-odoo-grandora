# sale_lot_margin

Batch-specific sale margins and lot-locked delivery reservation.

## Purpose
Copies Grandora product costs onto sale order lines and computes margin from `total_cost` (not Odoo's standard cost), so margins reflect landed cost per product.

## Models
| Model | Type | File |
|---|---|---|
| `sale.order.line` | Inherit | `models/sale_order_line.py` |
| `sale.order` | Inherit | `models/sale_order.py` |

## Fields added by this addon
### On `sale.order.line`
| Field | Type | Notes |
|---|---|---|
| `landing_cost` | Monetary, computed+stored | Copied from `product_tmpl_id.landing_cost_actual` (from **grandora_inventory_product_features**) |
| `total_cost` | Monetary, computed+stored | Copied from `product_tmpl_id.total_cost`; used as the margin cost basis |
| `unit_margin_percent` | Float, computed+stored | `(net price − total_cost) / net price` |

## Cross-addon links
- Depends on `grandora_inventory_product_features` — its compute depends on `product_id.product_tmpl_id.landing_cost_actual` and `.total_cost`. Renaming/changing those fields breaks this module's stored computes.
- Currency conversion to line company currency via `_convert_to_sol_currency`.

## Depends on
`sale_management`, `sale_stock`, `stock_account`, `sale_margin`, `grandora_inventory_product_features`.
