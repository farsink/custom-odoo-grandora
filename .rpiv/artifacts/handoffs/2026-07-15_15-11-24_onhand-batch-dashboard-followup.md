---
date: 2026-07-15T15:11:24+0300
author: farsink
commit: 1b5a470
branch: main
repository: custom-addons
topic: "On-hand Batch Cost Dashboard Follow-up Bug Fix"
tags: [bug-fix, odoo, inventory, stock, reporting, grandora-onhand-batch-dashboard]
status: complete
last_updated: 2026-07-15T15:11:24+0300
last_updated_by: farsink
type: bug_fix
---

# Handoff: On-hand dashboard missing zero-stock products

## Task(s)

- Completed: Created and installed new Odoo 18 addon `grandora_onhand_batch_dashboard`.
  - Menu: Inventory → Reporting → On-hand Batch Cost.
  - Commit: `1b5a470 Add on-hand batch cost dashboard`.
  - Local database `odoo18_dev` has module installed and Odoo was restarted successfully.
- Completed: Validated dashboard SQL report against local data:
  - Python compile OK.
  - XML parse OK.
  - Module install OK.
  - Quantity totals checked against `stock_quant`.
  - Landed unit cost checked against `stock.valuation.layer`.
  - Latest sale price checked against latest posted customer invoice line.
  - Sensitive cost/margin fields hidden from normal Inventory users.
- In progress / next bug fix: User reported some products are not visible and clarified: “all products should be listed on the report.”
  - Diagnosis reproduced locally: active storable products = 43; dashboard products visible = 10; missing = 33.
  - Root cause: report SQL view starts from `stock_quant`, and the default action applies `search_default_on_hand`. Products with no quant/no physical stock have no row, so they cannot appear.
  - Recommended fix already stated to user: change report base from `stock.quant only` to `all active stockable products LEFT JOIN stock.quant`, so zero-stock products appear with quantity/reserved/available = 0 and status = depleted/no stock.

## Critical References

- `plans/onhand-batch-dashboard.md` — approved implementation plan used for the initial addon.
- `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py` — SQL view model and root cause of missing zero-stock products.
- `grandora_onhand_batch_dashboard/views/onhand_batch_dashboard_views.xml` — action/search defaults controlling default visible rows.

## Recent changes

- `grandora_onhand_batch_dashboard/__manifest__.py:8` — addon dependencies include `stock`, `stock_account`, `account`, `sale_management`, `product_expiry`, and `grandora_inventory_product_features`.
- `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py:8` — added `_auto = False` model `grandora.onhand.batch.dashboard`.
- `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py:78-222` — `init()` creates SQL view; currently starts at `quant_base` from `stock_quant` (`FROM stock_quant q` around line 94).
- `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py:115-139` — latest sale price CTE uses most recent posted customer invoice line, company-wide.
- `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py:178-184` — calculates landed unit cost, batch value, latest sale price, and unit margin.
- `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py:223-231` — derives status (`depleted`, `expired`, `expiring_soon`, `low_stock`, `available`).
- `grandora_onhand_batch_dashboard/security/ir.model.access.csv:2` — read-only access for Inventory users.
- `grandora_onhand_batch_dashboard/views/onhand_batch_dashboard_views.xml:1-45` — list view with product, batch, location, quantity, expiry, cost/margin, sale price, and status columns.
- `grandora_onhand_batch_dashboard/views/onhand_batch_dashboard_views.xml:162-168` — window action currently uses context `{'search_default_on_hand': 1, ...}`.
- `grandora_onhand_batch_dashboard/views/onhand_batch_dashboard_views.xml:174-178` — menu item under Inventory → Reporting.

## Learnings

- Odoo’s `stock.quant` is not a product master list. It represents stock by product/location/lot/package/owner when stock/quant history exists. Products with no quants are invisible if a report is based only on quants.
- The approved first version intentionally used `stock.quant` as the source to make an on-hand batch report, but the user now expects a fuller product dashboard that includes zero-stock products too.
- Local diagnosis command showed:
  - `active_storable_products = 43`
  - `dashboard_products_any_qty = 10`
  - `missing_products = 33`
  - Examples: `[10000] Shrimbs`, `[10001] Falooda`, and many imported products, all with `qty_available = 0.0`.
- Sensitive fields are model-level group restricted (`landed_unit_cost`, `batch_value`, `unit_margin_percent`, `has_batch_cost`, `negative_margin`) and view restricted to `stock.group_stock_manager,account.group_account_user`.
- Product name is selected from translated JSONB with `pt.name->>'en_US'`; this worked locally.
- Supplier Batch is intentionally a blank placeholder in version 1 because no confirmed supplier-batch field exists in this project.

## Artifacts

- `plans/onhand-batch-dashboard.md` — implementation plan, approved and marked complete.
- `grandora_onhand_batch_dashboard/__init__.py`
- `grandora_onhand_batch_dashboard/__manifest__.py`
- `grandora_onhand_batch_dashboard/models/__init__.py`
- `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py`
- `grandora_onhand_batch_dashboard/security/ir.model.access.csv`
- `grandora_onhand_batch_dashboard/views/onhand_batch_dashboard_views.xml`
- Commit: `1b5a470 Add on-hand batch cost dashboard`

## Action Items & Next Steps

1. Confirm/assume scope: “all products” should mean all active stockable inventory products (`product.product.active = True`, `product.product.is_storable = True`). This was recommended to the user but not yet explicitly approved; likely safe based on wording.
2. Update `grandora_onhand_batch_dashboard/models/onhand_batch_dashboard.py` so SQL view includes zero-stock products:
   - Keep existing quant rows for products with quants.
   - Add fallback product rows for active storable products not represented by any internal-location quant row.
   - Recommended implementation: introduce a `product_base` CTE and a `quant_rows` CTE, then `UNION ALL` one product-level zero row for products with no quant row.
   - Zero row fields: quantity/reserved/available = 0, lot/location/warehouse = NULL, batch fields blank, receipt/expiry = NULL, status = `depleted` or possibly rename label to “No Stock”.
3. Update action/search behavior:
   - Current action has `search_default_on_hand: 1`, which hides zero-stock rows even if SQL includes them.
   - Remove this default filter or replace it with a default that includes all active stockable products.
   - Keep quick filters: On Hand, In Stock, Reserved, Show History / Depleted.
4. Consider renaming status label:
   - Existing key `depleted` label is “Depleted”. For products that never had stock, “No Stock” may be clearer. Could either change label to `Depleted / No Stock` or add a new `no_stock` status. Keep data/view simple unless user requests separate semantics.
5. Re-run validation:
   - `./odoo/venv/bin/python -m py_compile custom-addons/grandora_onhand_batch_dashboard/models/*.py`
   - XML parse for `views/onhand_batch_dashboard_views.xml`.
   - Update module: `./odoo/venv/bin/python ./odoo/odoo-bin -c ./odoo.conf -d odoo18_dev -u grandora_onhand_batch_dashboard --stop-after-init`.
6. Re-run diagnosis loop:
   - active storable products count should equal distinct dashboard products, or explain exceptions such as archived/non-storable variants.
   - Products like `[10000] Shrimbs` and `[10001] Falooda` should appear with zero quantities.
7. Restart Odoo and commit fix with required trailer:
   - `Co-Authored-By: GPT-5 Codex <noreply@openai.com>`.

## Other Notes

- Local Odoo path: `/Users/farsin/Freelance/odoo-dev`.
- Custom addons repo: `/Users/farsin/Freelance/odoo-dev/custom-addons`.
- Local database: `odoo18_dev`.
- Odoo URL: `http://127.0.0.1:8069`.
- Odoo command pattern:
  - compile: `./odoo/venv/bin/python -m py_compile custom-addons/<module>/models/*.py`
  - update: `./odoo/venv/bin/python ./odoo/odoo-bin -c ./odoo.conf -d odoo18_dev -u <module> --stop-after-init`
  - shell: `./odoo/venv/bin/python ./odoo/odoo-bin shell -c ./odoo.conf -d odoo18_dev`
  - restart: `./stop-odoo.sh || true && ./run-background.sh`
- Production status: not deployed by this session unless user manually deployed separately. The dashboard was installed only in local `odoo18_dev`.
