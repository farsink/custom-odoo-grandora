# grandora_onhand_batch_dashboard

Batch-level on-hand stock, expiry, cost, sale price, and margin reporting.

## Purpose
SQL-materialized dashboard (`init()` view) showing one row per lot/location: on-hand qty, expiry, landed unit cost, latest sale price, and margin %.

## Models
| Model | Type | File |
|---|---|---|
| `grandora.onhand.batch.dashboard` | New (SQL view) | `models/onhand_batch_dashboard.py` |

## Fields added
All readonly view fields: `product_id`, `product_default_code`, `brand_id`, `item_group_id`, `lot_id`, `batch_number`, `supplier_batch`, `warehouse_id`, `location_id`, `quantity`, `reserved_quantity`, `available_quantity`, `receipt_date`, `expiry_date`, `days_to_expiry`, `landed_unit_cost`, `batch_value`, `latest_sale_price`, `unit_margin_percent`, `status`, `is_low_stock`, `negative_margin`.

Cost fields are group-restricted (`_COST_GROUPS`) — keep that protection when editing.

## Cross-addon links
- Depends on `grandora_inventory_product_features`: the SQL in `init()` reads `product.template` columns `brand_id`, `item_group_id`, `total_cost` directly. Any schema change there requires updating this SQL and re-upgrading both modules.
- `supplier_batch` mirrors `grandora.receipt.batch.line.supplier_lot` / `stock.lot.supplier_lot`.

## Depends on
`stock`, `stock_account`, `account`, `sale_management`, `product_expiry`, `grandora_inventory_product_features`.
