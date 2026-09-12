from odoo import _, fields, models


class ReportStatementCommon(models.AbstractModel):
    _inherit = "statement.common"

    def _set_payment_descriptions(self, lines_by_partner):
        line_ids = {
            line_id
            for lines in lines_by_partner.values()
            for line in lines
            for line_id in line.get("ids") or [line.get("id")]
            if line_id
        }
        payments = {
            line.id: line.payment_id
            for line in self.env["account.move.line"].browse(line_ids)
            if line.payment_id
        }
        for lines in lines_by_partner.values():
            for line in lines:
                payment = next(
                    (
                        payments[line_id]
                        for line_id in line.get("ids") or [line.get("id")]
                        if line_id in payments
                    ),
                    False,
                )
                if not payment:
                    continue
                line["name"] = "/"
                line["ref"] = (payment.memo or "").strip() or _(
                    "Payment %(direction)s – %(journal)s",
                    direction=(
                        _("Received")
                        if payment.payment_type == "inbound"
                        else _("Sent")
                    ),
                    journal=payment.journal_id.name,
                )
        return lines_by_partner

    def _get_report_values(self, docids, data=None):
        values = super()._get_report_values(docids, data)
        docs = values.get("docs")
        if docs:
            # ponytail: single-partner title; multi-partner falls back to first partner
            kind = "Activity" if "activity" in (self._name or "") else "Outstanding"
            partner_name = (docs[0].name or "statement").replace("/", "-")
            today = fields.Date.context_today(self).isoformat()
            values["title"] = "%s - %s Statement - %s" % (partner_name, kind, today)
        if self._name != "report.partner_statement.activity_statement":
            return values

        for partner_data in values["data"].values():
            for currency_data in partner_data["currencies"].values():
                balance_forward = currency_data["balance_forward"]
                for line in currency_data["lines"]:
                    line["balance"] += balance_forward
        return values


class ActivityStatementPaymentDescription(models.AbstractModel):
    _inherit = "report.partner_statement.activity_statement"

    def _get_account_display_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        return self._set_payment_descriptions(
            super()._get_account_display_lines(
                company_id, partner_ids, date_start, date_end, account_type
            )
        )


class OutstandingStatementPaymentDescription(models.AbstractModel):
    _inherit = "report.partner_statement.outstanding_statement"

    def _get_account_display_lines(
        self, company_id, partner_ids, date_start, date_end, account_type
    ):
        return self._set_payment_descriptions(
            super()._get_account_display_lines(
                company_id, partner_ids, date_start, date_end, account_type
            )
        )
