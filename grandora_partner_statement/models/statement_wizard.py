from odoo import fields, models


class StatementCommonWizard(models.AbstractModel):
    _inherit = "statement.common.wizard"

    def _print_browser_report(self, report_xmlid):
        self.ensure_one()
        data = self._prepare_statement()
        partners = self.env["res.partner"].browse(data["partner_ids"])
        return self.env.ref(report_xmlid).report_action(partners, data=data)


class ActivityStatementWizard(models.TransientModel):
    _inherit = "activity.statement.wizard"

    def _get_current_month_start(self):
        return fields.Date.context_today(self).replace(day=1)

    date_start = fields.Date(default=_get_current_month_start)

    def _export(self, report_type):
        if report_type == "qweb-html":
            return self._print_browser_report(
                "partner_statement.action_print_activity_statement_browser"
            )
        return super()._export(report_type)


class OutstandingStatementWizard(models.TransientModel):
    _inherit = "outstanding.statement.wizard"

    def _export(self, report_type):
        if report_type == "qweb-html":
            return self._print_browser_report(
                "partner_statement.action_print_outstanding_statement_browser"
            )
        return super()._export(report_type)
