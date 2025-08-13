from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = "res.partner"

    metodo_pago = fields.Selection(
        [
            ("Efectivo", "Efectivo"),
            ("Cheque", "Cheque"),
            ("Transferencia", "Transferencia"),
        ],
        string="Método de Pago",
    )


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends("partner_id")
    @api.onchange("partner_id")
    def _compute_payment_method(self):
        for record in self:
            if record.payment_method_line_id:
                for method in record.payment_method_line_id:
                    if record.partner_id.metodo_pago:
                        if method.name == record.partner_id.metodo_pago:
                            record.payment_method_line_id = method
