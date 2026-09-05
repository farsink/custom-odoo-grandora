from odoo import _, models

from odoo.addons.report_xlsx_helper.report.report_xlsx_format import FORMATS


LEDGER_HEADERS = ["Date", "Invoice No.", "Description", "Debit", "Credit", "Balance"]


def _description(line):
    name = line.get("name", "")
    reference = line.get("ref", "")
    return reference if name in ("", "/") else name


class LedgerStatementXlsx(models.AbstractModel):
    _inherit = "report.p_s.report_statement_common_xlsx"

    def _get_ledger_header_row_data(self):
        return [
            {
                "col_pos": position,
                "sheet_func": "write",
                "args": (_(header), FORMATS["format_theader_yellow_center"]),
            }
            for position, header in enumerate(LEDGER_HEADERS)
        ]

    def _get_ledger_line_row_data(self, line):
        date_format = FORMATS["format_tcell_date_left"]
        text_format = FORMATS["format_tcell_left"]
        money_format = FORMATS["current_money_format"]
        return [
            {
                "col_pos": position,
                "sheet_func": "write",
                "args": value,
            }
            for position, value in enumerate(
                [
                    (line.get("date", ""), date_format),
                    (line.get("move_id", ""), text_format),
                    (_description(line), text_format),
                    (line.get("debit", 0.0), money_format),
                    (line.get("credit", 0.0), money_format),
                    (line.get("balance", 0.0), money_format),
                ]
            )
        ]

    def _get_currency_footer_row_data(self, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id, {})
        return [
            {
                "col_pos": 0,
                "sheet_func": "write",
                "args": (
                    partner_data.get("end"),
                    FORMATS["format_tcell_date_left"],
                ),
            },
            {
                "col_pos": 1,
                "sheet_func": "merge_range",
                "span": 3,
                "args": (_("Ending Balance"), FORMATS["format_tcell_left"]),
            },
            {
                "col_pos": 5,
                "sheet_func": "write",
                "args": (
                    currency_data.get("amount_due"),
                    FORMATS["current_money_format"],
                ),
            },
        ]


class ActivityStatementXlsx(models.AbstractModel):
    _inherit = "report.p_s.report_activity_statement_xlsx"

    def _get_currency_header_row_data(self, partner, currency, data):
        return self._get_ledger_header_row_data()

    def _get_currency_subheader_row_data(self, partner, currency, data):
        partner_data = data.get("data", {}).get(partner.id, {})
        currency_data = partner_data.get("currencies", {}).get(currency.id, {})
        return [
            {
                "col_pos": 0,
                "sheet_func": "write",
                "args": (
                    partner_data.get("prior_day"),
                    FORMATS["format_tcell_date_left"],
                ),
            },
            {
                "col_pos": 1,
                "sheet_func": "merge_range",
                "span": 3,
                "args": (_("Opening Balance"), FORMATS["format_tcell_left"]),
            },
            {
                "col_pos": 5,
                "sheet_func": "write",
                "args": (
                    currency_data.get("balance_forward"),
                    FORMATS["current_money_format"],
                ),
            },
        ]

    def _get_currency_line_row_data(self, partner, currency, data, line):
        return self._get_ledger_line_row_data(line)


class OutstandingStatementXlsx(models.AbstractModel):
    _inherit = "report.p_s.report_outstanding_statement_xlsx"

    def _get_currency_header_row_data(self, partner, currency, data):
        return self._get_ledger_header_row_data()

    def _get_currency_line_row_data(self, partner, currency, data, line):
        return self._get_ledger_line_row_data(line)
