# grandora_inventory_product_features

Core inventory customization module. **Other Grandora modules depend on this one** — changes here have downstream impact (see AGENTS.md → Dependency Map).

## Purpose
Product references (auto SKU), brand/item-group classification, base/landing cost model, receipt batch entry with automatic internal lot generation, and lot-tracking defaults.

## Models
| Model | Type | File |
|---|---|---|
| `product.brand` | New | `models/product_brand.py` |
| `product.item.group` | New | `models/product_item_group.py` |
| `grandora.receipt.batch.line` | New | `models/receipt_batch_line.py` |
| `product.template` | Inherit | `models/product_template.py` |
| `product.product`, `product.category`, `stock.lot`, `stock.picking`, `stock.quant` | Inherit | respective files |
| `res.config.settings` | Inherit | `models/res_config_settings.py` |

## Fields added by this addon
### On `product.template` (referenced by other addons)
| Field | Type | Notes |
|---|---|---|
| `brand_id` | Many2one → `product.brand` | Used by `grandora_onhand_batch_dashboard` |
| `item_group_id` | Many2one → `product.item.group` | Used by `grandora_onhand_batch_dashboard` |
| `base_cost` | Float, tracked | Base cost before landing cost; synced with `standard_price` |
| `landing_cost` | Float, tracked | Entered as fixed QAR or % of base cost |
| `landing_cost_type` | Selection `fixed`/`percentage` | Required, default `fixed` |
| `landing_cost_actual` | Float, computed+stored | Effective landing cost in company currency. **Consumed by `sale_lot_margin`** |
| `total_cost` | Float, computed+stored | `base_cost + landing_cost_actual`; synced back to Odoo's `standard_price`. **Consumed by `sale_lot_margin` and dashboard SQL** |
| `minimum_shelf_life_days` | Integer | Shelf-life rule used in expiry checks |

### On `grandora.receipt.batch.line`
`picking_id`, `move_id`, `received_qty`, `supplier_lot`, `expiry_date`, `manufacture_date`, `quality_status` (`pass`/`fail`/`pending`), `internal_lot_id` (→ `stock.lot`), `lot_name`.

### On other inherited models
- `stock.picking`: `batch_line_ids` (One2many to receipt batch lines), `show_batch_entry`.
- `stock.lot`: `supplier_lot`, `purchase_order_id`, `receipt_id`, `manufacture_date`, `quality_status`.
- `stock.quant`, `product.product`, `product.category`: minor extensions (`minimum_shelf_life_days` on category).

## Key behaviors
- **Inventory landing page**: the Inventory app opens the storable Product Templates list by default; the standard Overview menu remains available.
- **Product list defaults**: Base Cost and Grandora Total Cost are shown; duplicate Odoo standard cost and landing-cost columns are hidden.
- **Auto product SKU**: `create()` assigns next reference from sequence code `grandora.product.reference` when `default_code` is empty.
- **Cost sync**: `total_cost` ↔ Odoo `standard_price` kept in sync via `_grandora_sync_standard_price_from_total()`; guard context keys `grandora_skip_total_cost_sync` / `grandora_skip_lot_sequence_sync` must be preserved.
- **Lot tracking defaults**: new storable products default to `tracking = "lot"` (configurable via `default_new_storable_products_to_lots` system parameter).
- **Lot sequences**: builds on OCA `product_lot_sequence`; per-product prefix `BTCH-{ACRONYM}-` with ID disambiguation on acronym clash.
- **Receipt batches**: validating a picking creates `stock.lot` records from batch lines.

## Depends on
`stock`, `purchase_stock`, `product_expiry`, `product_lot_sequence` (vendored OCA).

## Downstream dependents
- `grandora_onhand_batch_dashboard` (reads brand, item group, total_cost in its SQL view)
- `sale_lot_margin` (reads `landing_cost_actual`, `total_cost`)

⚠️ Changing any field above requires `-u` on all three modules and doc updates in their READMEs.
