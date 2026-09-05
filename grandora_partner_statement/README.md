# grandora_partner_statement

Grandora contact-statement workflow and ledger-style output for the vendored `partner_statement` addon.

## Purpose

- Opens a date-selection wizard from the Activity Statement and Outstanding Statement buttons on a contact.
- Uses a current-month activity period and today's outstanding “as at” date by default.
- Presents statements as Date, Invoice no., Description, Debit, Credit, and Balance.

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
