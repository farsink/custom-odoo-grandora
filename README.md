# Custom Odoo addons

Custom business modules for the local Odoo 18 Community development setup.

## Grandora modules

Each module has its own `README.md` documenting implementation and fields — read it before changing that module.

- `grandora_inventory_product_features` — core: product references, brand/item group, base/landing cost, receipt batches with auto lot generation. **Other Grandora modules depend on it.** ([README](grandora_inventory_product_features/README.md))
- `sale_lot_margin` — batch-specific sale margins from Grandora product total cost. ([README](sale_lot_margin/README.md))
- `grandora_onhand_batch_dashboard` — on-hand batch cost dashboard (SQL view). ([README](grandora_onhand_batch_dashboard/README.md))
- `grandora_invoice_report` — Grandora browser-print invoice layout + SO/invoice metadata. ([README](grandora_invoice_report/README.md))
- `custom_admin_home` — admin-only apps grid home screen. ([README](custom_admin_home/README.md))
- `business_inventory_sales` — sandbox starter module for workflow testing. ([README](business_inventory_sales/README.md))

See root `AGENTS.md` → "Custom Addon Reference Docs" for the dependency map and rules for adding fields / linking addons.

## Vendored OCA modules

- `partner_statement`
- `report_xlsx`
- `report_xlsx_helper`

See [THIRD_PARTY_ADDONS.md](THIRD_PARTY_ADDONS.md) for upstream provenance and update rules.
