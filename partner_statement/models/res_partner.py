# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_preview_activity_statement(self):
        """Open the default activity statement in the browser print preview."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/report/html/partner_statement.activity_statement_browser/{self.id}",
            "target": "new",
        }

    def action_preview_outstanding_statement(self):
        """Open the default outstanding statement in the browser print preview."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": f"/report/html/partner_statement.outstanding_statement_browser/{self.id}",
            "target": "new",
        }
