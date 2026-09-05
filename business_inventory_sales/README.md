# business_inventory_sales

Starter/sandbox module for testing the Inventory/Sales customization workflow. Not part of the Grandora production dependency chain.

## Models
| Model | Type | File |
|---|---|---|
| `business.inventory.sales.note` | New | `models/inventory_sales_note.py` |
| `product.template` | Inherit | `models/product_template.py` |

## Fields added
### On `business.inventory.sales.note`
`name`, `product_id` (→ `product.product`), `sale_order_id` (→ `sale.order`), `priority` (`0/1/2`), `note`, `active`.

### On `product.template`
| Field | Type | Notes |
|---|---|---|
| `x_business_sku` | Char | Test business reference (uses `x_` prefix — sandbox only) |
| `x_reorder_note` | Text | Internal replenishment note |

## Depends on
`sale_management`, `stock`. No other custom addon depends on this module.
