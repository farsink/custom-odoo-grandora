# grandora_partner_statement

Grandora contact-statement workflow and ledger-style output for the vendored `partner_statement` addon.

## Purpose

- Opens a date-selection wizard from the Activity Statement and Outstanding Statement buttons on a contact.
- Uses a current-month activity period and today's outstanding “as at” date by default.
- Presents statements as Date, Invoice no., Description, Debit, Credit, and Balance.
- Uses the existing branded browser-print template for the wizard’s View action.
- Names saved PDFs and browser Save-as-PDF files `<Customer> - <Activity|Outstanding> Statement - <YYYY-MM-DD>`.

## Partial payments, write-offs, and advances (audited)

- Partial payment: the invoice row keeps its full debit while the payment row
  carries the credit, so the running Balance settles on the residual; the
  outstanding statement shows the invoice with the residual open amount.
- Write-off: Odoo books the difference inside the payment entry, so it is
  absorbed into the payment row and the invoice closes fully.
- Unapplied advance: appears as a credit row (negative running balance) and as
  an open credit line on the outstanding statement.
- Known limitation: payment rows are labeled with the generic description
  “Payment” — a custom payment reference/memo is not shown (upstream OCA
  grouping labels all bank/cash lines that way).

## Models

| Model | Type | File |
|---|---|---|
| `res.partner` | Inherit | `models/res_partner.py` |
| `statement.common` | Inherit | `report/report_statement_common.py` |
| `report.p_s.report_activity_statement_xlsx` | Inherit | `report/statement_xlsx.py` |
| `report.p_s.report_outstanding_statement_xlsx` | Inherit | `report/statement_xlsx.py` |

## Fields added

None.

## Cross-addon links

- Depends on `partner_statement` and extends its contact actions, report data, QWeb templates, and XLSX report models.
- Does not alter the vendored addon.
