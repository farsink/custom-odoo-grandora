# grandora_invoice_report

Grandora commercial invoice layout (browser-print) and sales invoice metadata.

## Models
| Model | Type | File |
|---|---|---|
| `sale.order` | Inherit | `models/sale_order.py` |
| `account.move` | Inherit | `models/account_move.py` |

## Fields added
| Model | Field | Type | Notes |
|---|---|---|---|
| `sale.order` | `division_name` | Char, default `RESTAURANT` | Copied to invoice via `_prepare_invoice` |
| `sale.order` | `delivery_time` | Char | Copied to invoice via `_prepare_invoice` |
| `account.move` | `division_name` | Char | Printed on Grandora layout |
| `account.move` | `delivery_time` | Char | Printed on Grandora layout |
| `account.move` | `sale_order_number` | Char | Source SO reference |
| `account.move` | `grandora_remarks` | Text | Free-text remarks block on the report |

## Reports
- `report/grandora_sales_invoice.xml` — A4 browser-print layout and the inkjet QWeb template.
- `report/invoice_report.xml` — report definitions and paper formats.
- `report/grandora_sales_invoice_inkjet_preview.html` — standalone US Letter (8.5 × 11 in) mock-data overlay used to calibrate the production template. It prints field labels and values, but no logos, borders, or other form artwork. Its position variables—including each line column's X position—match the final report.
- **Default customer invoice Print** — opens the US Letter (8.5 × 11 in) inkjet form inside Odoo, not a new browser tab. It prints invoice/delivery field labels and values, up to 19 invoice lines, totals, remarks, and delivery details at the calibrated positions; the physical form supplies all borders, artwork, and footer labels.
- The existing A4 browser layout remains available as `report_invoice_browser_print` but is no longer the default customer-invoice print output.

## Depends on
`account`, `sale_management`, `stock`. No Grandora module dependencies.
