# product_lot_sequence (vendored OCA)

Vendored OCA module: per-product lot sequence configuration.

## Purpose
Adds lot-number sequencing to `product.template`: each tracked product can own an `ir.sequence` used when generating `stock.lot` names.

## Fields added
### On `product.template`
| Field | Type | Notes |
|---|---|---|
| `lot_sequence_id` | Many2one → `ir.sequence` | Per-product lot sequence. **Consumed by `grandora_inventory_product_features`** (`_grandora_ensure_lot_sequence`) |
| `lot_sequence_prefix` | Char | Sequence prefix |
| `lot_sequence_padding` | Integer | Padding |
| `lot_sequence_number_next` | Integer | Next number |
| `display_lot_sequence_fields` | Boolean, computed | View visibility helper |

### Other
- `res.company`, `res.config.settings`, `stock.move`, `stock.lot` extensions for automatic lot naming.

## Cross-addon links
This is an upstream OCA module — **do not modify it**. `grandora_inventory_product_features` builds its `BTCH-{ACRONYM}-` prefixes and no-gap sequences on top of `_create_lot_sequence()` here. Custom logic belongs in `grandora_inventory_product_features`.

See [THIRD_PARTY_ADDONS.md](../THIRD_PARTY_ADDONS.md) for upstream provenance.
