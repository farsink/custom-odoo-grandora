from odoo import models


class ReportStatementCommon(models.AbstractModel):
    _inherit = "statement.common"

    def _get_report_values(self, docids, data=None):
        values = super()._get_report_values(docids, data)
        if self._name != "report.partner_statement.activity_statement":
            return values

        for partner_data in values["data"].values():
            for currency_data in partner_data["currencies"].values():
                balance_forward = currency_data["balance_forward"]
                for line in currency_data["lines"]:
                    line["balance"] += balance_forward
        return values
