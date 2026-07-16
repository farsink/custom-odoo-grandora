# Traceability Lot-Tracking Default Design

## Goal

Make automatic lot tracking for newly created storable products controllable from **Inventory → Settings → Traceability**.

## Current behavior and diagnosis

`grandora_inventory_product_features` currently sets `tracking = 'lot'` in both `product.template.create()` and `product.product.create()` for newly created storable consumable goods. A direct reproduction of the Product form's template creation flow confirms that it produces a storable product tracked **By Lots**. Odoo's core Lots & Serial Numbers setting is enabled.

The requested change is therefore a configurable business default, not automatic creation of a `stock.lot` record when a product master is saved. Lots remain created during receipt processing.

## Approved behavior

Add **Default New Storable Products to By Lots** to the existing **Inventory → Settings → Traceability** block.

- It is visible only when Odoo's core **Lots & Serial Numbers** setting is enabled.
- It is stored globally in `ir.config_parameter`.
- Its initial default is enabled to preserve the current system behavior.
- When enabled, a new storable good without an explicit `tracking` value defaults to `lot`.
- When disabled, creation uses Odoo's standard default (`none`).
- An explicit `tracking` value always wins, including `none` and `serial`.
- Existing products and existing lots are never changed when the setting changes.

## Implementation shape

1. Extend `res.config.settings` in `grandora_inventory_product_features` with a Boolean field backed by `ir.config_parameter`.
2. Inherit `stock.res_config_settings_view_form` and add the setting inside `block#production_lot_info` after the core lots setting.
3. Centralize the configuration lookup in a helper used by both product create overrides, avoiding divergent behavior between template creation, variant creation, imports, and API callers.
4. Keep the existing default of `is_storable=True` for new consumable goods; only the tracking default becomes configurable.

## Validation

- Settings view XML parses and module upgrades successfully.
- Tests cover setting enabled, setting disabled, explicit `none`, and explicit `serial` through both product-template and product-variant creation paths.
- Manual UAT confirms the setting appears in Inventory → Settings → Traceability and affects only products created after the setting is saved.
