# Grandora Plain Invoice HTML Design

## Goal
Provide an independent, branded A4 invoice template that can be opened and printed without Odoo report data.

## Scope
- Add `grandora_invoice_report/report/grandora_sales_invoice_plain.html`.
- Keep every existing QWeb XML template, report action, and manifest entry unchanged.
- Use the existing Grandora logo and lettermark assets through their module URLs.

## Layout
The new HTML document will use embedded CSS for an A4 portrait page and print-safe styling. It will retain:
- Grandora header and bilingual branding
- Sales Invoice title
- Invoice, customer, and delivery labels with blank writing areas
- Item table column headings and an empty ruled body
- Total/in-words and remarks labels without values
- Terms, customer receipt, signature lines, and delivery section

## Data boundary
The file will contain no Odoo/QWeb directives (`t-*`), record references, addresses, product lines, invoice numbers, totals, dates, customer details, or print-time values.

## Verification
- Parse the document as XML-compatible XHTML to catch malformed markup.
- Confirm the existing `grandora_sales_invoice.xml` and `invoice_report.xml` are unmodified.
