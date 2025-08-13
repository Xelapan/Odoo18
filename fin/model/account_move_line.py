from odoo import models, fields, api


class YourModel(models.Model):
    _inherit = "account.move.line"  # O el modelo donde esté `analytic_distribution`

    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Cuenta Analítica",
        compute="_compute_analytic_account",
        # store=True,
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_account(self):
        for record in self:
            if record.analytic_distribution:
                analytic_ids = list(record.analytic_distribution.keys())
                if analytic_ids:
                    record.analytic_account_id = int(
                        analytic_ids[0]
                    )  # Toma el primer ID
                else:
                    record.analytic_account_id = False
            else:
                record.analytic_account_id = False

    @api.model_create_multi
    def create(self, vals):
        if "analytic_distribution" in vals and vals["analytic_distribution"]:
            analytic_ids = list(vals["analytic_distribution"].keys())
            if analytic_ids:
                vals["analytic_account_id"] = int(analytic_ids[0])
        return super().create(vals)

    def write(self, vals):
        if "analytic_distribution" in vals and vals["analytic_distribution"]:
            analytic_ids = list(vals["analytic_distribution"].keys())
            if analytic_ids:
                vals["analytic_account_id"] = int(analytic_ids[0])
        # if self.move_id.move_type == 'out_invoice' and self.move_id.state != 'posted' and 'name' in vals and ('price_unit' not in vals and 'quantity' not in vals and 'tax_ids' not in vals and 'product_id' not in vals):
        #     for line in self:
        #         vals['price_unit'] = line.price_unit
        return super().write(vals)
