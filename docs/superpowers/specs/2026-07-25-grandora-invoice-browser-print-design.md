# Grandora Invoice Browser Print Design

## Goal
Make the live Grandora Odoo invoice report match `docs/Company/report-template.html` while retaining the existing dynamic invoice data. Opening the report from Odoo must show the custom browser page without immediately opening the native print dialog; the dialog opens only after the page's **Print / Save as PDF** button is clicked.

## Scope
- Update the QWeb report template in `grandora_invoice_report/report/grandora_sales_invoice.xml`.
- Apply the reference template's light-maroon table/remarks background (`#e8ccce`).
- Center the **SALES INVOICE** title.
- Use `30302234` as the fallback company phone number when the Odoo company phone is not configured.
- Remove the page-load JavaScript call to `window.print()`.

## Data and behavior
- Keep the existing dynamic QWeb bindings for company data, customer and delivery details, invoice metadata, product lines, totals, remarks, and print timestamp.
- Keep `AccountMove.action_print_pdf()` opening the browser report URL in a new tab for customer invoices.
- Keep the browser toolbar's explicit `window.print()` button and Close button.
- Do not change report actions, the account-move print override, or the static reference template.

## Verification
- Validate the updated XML parses successfully.
- Upgrade `grandora_invoice_report` in Odoo.
- From a customer invoice, use Odoo's Print action and confirm the custom report opens without a dialog.
- Click **Print / Save as PDF** on that page and confirm the browser print dialog opens.
- Confirm rendered invoice data remains dynamic and the centered title, light-maroon backgrounds, and fallback phone match the reference template.
