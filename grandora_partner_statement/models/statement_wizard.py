from odoo import fields, models


class ActivityStatementWizard(models.TransientModel):
    _inherit = "activity.statement.wizard"

    def _get_current_month_start(self):
        return fields.Date.context_today(self).replace(day=1)

    date_start = fields.Date(default=_get_current_month_start)
