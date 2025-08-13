from odoo import fields, models, api


class StockMove(models.Model):
    _inherit = "stock.move"

    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Cuenta analítica", store=True
    )

    @api.onchange("analytic_account_id")
    def _onchange_analytic_account_id(self):
        for line in self.move_line_ids:
            line.analytic_account_id = self.analytic_account_id


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Cuenta analítica", store=True
    )

    # @api.depends('move_id.analytic_account_id')
    # def _compute_analytic_account_id(self):
    #     for line in self:
    #         if line.move_id and line.move_id.analytic_account_id:
    #             line.analytic_account_id = line.move_id.analytic_account_id
