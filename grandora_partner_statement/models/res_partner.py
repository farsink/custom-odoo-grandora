from odoo import _, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _open_statement_wizard(self, title, model, view_xmlid):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": model,
            "view_mode": "form",
            "views": [(self.env.ref(view_xmlid).id, "form")],
            "target": "new",
            "context": {
                "active_model": "res.partner",
                "active_id": self.id,
                "active_ids": self.ids,
            },
        }

    def action_preview_activity_statement(self):
        return self._open_statement_wizard(
            _("Activity Statement"),
            "activity.statement.wizard",
            "grandora_partner_statement.activity_statement_wizard_view",
        )

    def action_preview_outstanding_statement(self):
        return self._open_statement_wizard(
            _("Outstanding Statement"),
            "outstanding.statement.wizard",
            "grandora_partner_statement.outstanding_statement_wizard_view",
        )
