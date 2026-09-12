# Custom Odoo addons

Custom business modules for the local Odoo 18 Community development setup.

## Custom module state

`__manifest__.py` is the canonical version. This table is a compact index; update its row whenever a custom module changes.

| Addon | Version | Latest functional change |
|---|---|---|
| [`grandora_inventory_product_features`](grandora_inventory_product_features/README.md) | 18.0.1.0.0 | Product list defaults |
| [`sale_lot_margin`](sale_lot_margin/README.md) | 18.0.1.0.0 | Percentage landing-cost entry |
| [`grandora_onhand_batch_dashboard`](grandora_onhand_batch_dashboard/README.md) | 18.0.1.0.0 | Batch dashboard improvements |
| [`grandora_invoice_report`](grandora_invoice_report/README.md) | 18.0.1.0.0 | Title-case amount words |
| [`grandora_partner_statement`](grandora_partner_statement/README.md) | 18.0.1.0.1 | Payment memo descriptions in statements |
| [`custom_admin_home`](custom_admin_home/README.md) | 18.0.1.0.0 | Admin home access check |
| [`business_inventory_sales`](business_inventory_sales/README.md) | 18.0.1.0.0 | Inventory/Sales starter fields |

See root `AGENTS.md` → "Custom Addon Reference Docs" for dependency and field-reuse rules.

## Vendored OCA modules

- `partner_statement`
- `report_xlsx`
- `report_xlsx_helper`

See [THIRD_PARTY_ADDONS.md](THIRD_PARTY_ADDONS.md) for upstream provenance and update rules.
