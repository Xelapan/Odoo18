from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request


class AccountPaymentVWizard(models.TransientModel):
    _name = "account.payment.v.wizard"
    _description = "Visor Pagos Wizard"

    date_from = fields.Date(string="Fecha del")
    date_to = fields.Date(string="Fecha al", required=True)
    journal_ids = fields.Many2many("account.journal", string="Diario")
    payment_ids = fields.Many2many("account.payment", string="Pagos")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    def open_account_payment_v_at_date(self):
        self.ensure_one()
        # Obtener el session_id de la sesión HTTP actual
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual
        domain = [("company_id", "=", self.company_id.id)]
        if not self.date_to:
            raise UserError(_("Debe seleccionar al menos fecha al"))
            domain.append(("date", "<=", self.date_to))

        if self.date_from:
            if self.date_from > self.date_to:
                raise UserError(_("La fecha del debe ser menor a la fecha al"))
            else:
                domain.append(("date", ">=", self.date_from))

        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))

        if self.payment_ids:
            domain.append(("id", "in", self.payment_ids.ids))

        # Eliminar datos anteriores para esta sesión
        self.env["account.payment.v"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        pagos = self.env["account.payment"].search(domain)
        visor_activos = self.env["account.payment.v"]
        datos = []
        for pago in pagos:
            for factura in pago.reconciled_bill_ids:
                datos.append(
                    {
                        "payment_id": pago.id,
                        "factura_id": factura.id if factura else False,
                        "session_identifier": session_identifier,
                    }
                )
                # visor_activos.create({
                #     'payment_id': pago.id,
                #     'factura_id': factura.id if factura else False,
                #     'session_identifier': session_identifier
                # })
            if not pago.reconciled_bill_ids:
                datos.append(
                    {"payment_id": pago.id, "session_identifier": session_identifier}
                )
        visor_activos.create(datos)

        return {
            "name": "Visor Pagos",
            "type": "ir.actions.act_window",
            "res_model": "account.payment.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_payment_v_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_payment_v_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }
