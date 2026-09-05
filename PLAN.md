# Plan: Sync Grandora Odoo Invoice with the Approved Browser Template

## Context
The static reference at `docs/Company/report-template.html` now uses a light-maroon `#e8ccce` table/remarks background and the `30302234` header phone. The live QWeb invoice retains older styling and automatically invokes the browser print dialog when Odoo opens the report.

## Approach
Make one focused QWeb-template change. Preserve the existing report action and dynamic invoice bindings; remove only the page-load call to `window.print()` so the Odoo print action opens the custom report page, and the page toolbar remains the sole explicit route to the browser dialog.

## Files to modify
- `grandora_invoice_report/report/grandora_sales_invoice.xml`

## Reuse
- Existing browser-report action and new-tab routing in `grandora_invoice_report/models/account_move.py::action_print_pdf`.
- Existing `Print / Save as PDF` toolbar button in `grandora_sales_invoice.xml`, which already calls `window.print()` on an explicit click.
- Reference values from `docs/Company/report-template.html` (`#e8ccce`, centered title, `30302234`).

## Steps
- [ ] Update `.grandora-table-head` to `background: #e8ccce` so table headers and the remarks strip match the approved template.
- [ ] Center `.grandora-meta-title` content and change the fallback company phone to `30302234`.
- [ ] Remove the page-load `window.print()` script; retain the toolbar Print and Close controls unchanged.
- [ ] Confirm no report action or `account.move` override change is needed.

## Verification
- Parse `grandora_sales_invoice.xml` as XML.
- Upgrade `grandora_invoice_report` in Odoo.
- From a customer invoice, use Print and confirm the browser page opens without a native print dialog.
- Click **Print / Save as PDF** and confirm the dialog opens.
- Check a populated invoice for dynamic company/customer/delivery details, invoice lines, totals, and remarks, plus the centered title and light-maroon table/remarks backgrounds.
