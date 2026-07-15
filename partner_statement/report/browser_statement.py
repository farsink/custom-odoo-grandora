# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class ActivityStatementBrowser(models.AbstractModel):
    _inherit = "report.partner_statement.activity_statement"
    _name = "report.partner_statement.activity_statement_browser"
    _description = "Partner Activity Statement Browser Preview"


class OutstandingStatementBrowser(models.AbstractModel):
    _inherit = "report.partner_statement.outstanding_statement"
    _name = "report.partner_statement.outstanding_statement_browser"
    _description = "Partner Outstanding Statement Browser Preview"
