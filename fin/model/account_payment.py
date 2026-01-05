from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    ref = fields.Char(string="Memo", store=True, copy=False, readonly=False, related="memo")
    communication = fields.Char(
        string="Memo - Comunicación",
        store=True,
        copy=False,
        readonly=False,
        states={"posted": [("readonly", True)]},
    )
    extracto_conciliado = fields.Boolean(
        string="Extracto Conciliado",
        store=True,
        readonly=True,
        compute="_onchange_reconciled_statement_line_ids",
    )

    cuenta_destino_id = fields.Many2one('account.account', string='Cuenta Contable', store=True)

    destination_account_id = fields.Many2one('account.account', string='Cuenta Destino', store=True, domain="[]")

    @api.depends("reconciled_statement_line_ids")
    def _onchange_reconciled_statement_line_ids(self):
        for record in self:
            if len(record.reconciled_statement_line_ids) > 0:
                record.extracto_conciliado = True
            else:
                record.extracto_conciliado = False

    def get_date(self):
        date = fields.Date.from_string(self.date)
        formatted_date = date.strftime("%d/%m/%Y")
        return formatted_date

    def write(self, vals):
        res = super(AccountPayment, self).write(vals)
        for record in self:
            # Detecta si se realizó algún cambio relevante
            if record.state == "posted" and record.move_id and record.ref:
                record.move_id.write({"ref": record.ref})
        return res

    @api.onchange('cuenta_destino_id')
    def _onchange_cuenta_destino_id(self):
        if self.cuenta_destino_id:
            self.destination_account_id = self.cuenta_destino_id
