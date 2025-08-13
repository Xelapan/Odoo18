from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.http import request


class AccountPaymentV(models.Model):
    _name = "account.payment.v"
    _description = "Visor Pagos"

    payment_id = fields.Many2one(
        "account.payment", string="Pago", readonly=True, store=True
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Proveedor Pago",
        readonly=True,
        related="payment_id.partner_id",
    )
    currency_id = fields.Many2one(
        "res.currency", string="Moneda", readonly=True, related="payment_id.currency_id"
    )
    amount = fields.Monetary(
        string="Monto a pagar",
        readonly=True,
        related="payment_id.amount",
        currency_field="currency_id",
    )
    date = fields.Date(
        string="Fecha de Pago", readonly=True, related="payment_id.date", store=True
    )
    move_id = fields.Many2one(
        "account.move", string="Asiento", readonly=True, related="payment_id.move_id"
    )
    ref = fields.Char(
        string="Circular", readonly=True, related="payment_id.ref", store=True
    )
    no_liquidacion = fields.Integer(
        string="Orden Mix P",
        readonly=True,
        related="move_id.no_liquidacion",
        store=True,
    )
    factura_id = fields.Many2one(
        "account.move", string="Factura", readonly=True, store=True
    )
    factura_fecha = fields.Date(
        string="Fecha Factura", readonly=True, related="factura_id.date", store=True
    )
    factura_no_liquidacion = fields.Integer(
        string="Orden Mix F",
        readonly=True,
        related="factura_id.no_liquidacion",
        store=True,
    )
    factura_tipo_documento = fields.Selection(
        string="Tipo Documento",
        readonly=True,
        related="factura_id.tipo_documento",
        store=True,
    )
    factura_numero_fel = fields.Char(
        string="Número FEL", readonly=True, related="factura_id.numero_fel"
    )
    factura_serie_fel = fields.Char(
        string="Serie FEL", readonly=True, related="factura_id.serie_fel"
    )
    factura_nit = fields.Char(
        string="NIT", readonly=True, related="factura_partner_id.vat", store=True
    )
    factura_partner_id = fields.Many2one(
        "res.partner",
        string="Proveedor Factura",
        readonly=True,
        related="factura_id.partner_id",
        store=True,
    )
    factura_amount_total = fields.Monetary(
        string="Total",
        readonly=True,
        related="factura_id.amount_total",
        currency_field="currency_id",
    )
    factura_iva_credito = fields.Monetary(
        string="IVA Crédito",
        readonly=True,
        compute="compute_taxes",
        currency_field="currency_id",
    )
    factura_isr_retenido = fields.Monetary(
        string="ISR Retenido",
        readonly=True,
        compute="compute_taxes",
        currency_field="currency_id",
    )
    factura_iva_retenido = fields.Monetary(
        string="IVA Retenido",
        readonly=True,
        compute="compute_taxes",
        currency_field="currency_id",
    )
    factura_arbitrios = fields.Monetary(
        string="Arbitrios",
        readonly=True,
        compute="compute_taxes",
        currency_field="currency_id",
    )
    session_identifier = fields.Char(
        string="Session Token", required=True
    )  # Campo para el token de sesión

    def compute_taxes(self):
        for record in self:
            record.factura_iva_credito = 0.0
            record.factura_isr_retenido = 0.0
            record.factura_iva_retenido = 0.0
            record.factura_arbitrios = 0.0
            for line in record.factura_id.invoice_line_ids:
                for impuesto in line.tax_ids:
                    if "IVA por Cobrar" in impuesto.name:
                        record.factura_iva_credito += impuesto.amount
                    if "ISR Retención" in impuesto.name:
                        record.factura_isr_retenido += impuesto.amount
                    if "Retenciones IVA" in impuesto.name:
                        record.factura_iva_retenido += impuesto.amount
                    if "IDP" in impuesto.name or "Timbre" in impuesto.name:
                        record.factura_arbitrios += impuesto.amount

    @api.model
    def get_session_identifier(self, fields_list):
        res = super(AccountPaymentV, self).get_session_identifier(fields_list)
        session_identifier = request.session.sid
        if session_identifier:
            res["domain"] = [("session_identifier", "=", session_identifier)]
        return res

    @api.model
    def action_open_account_payment_v(self):
        session_identifier = request.session.sid
        return {
            "name": "Visor Pagos Facturas",
            "type": "ir.actions.act_window",
            "res_model": "account.payment.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_payment_v_view_tree").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    @api.model
    def create_or_update_records(self, results):
        session_identifier = self.get_session_identifier()
        self.search([("session_identifier", "=", session_identifier)]).unlink()
        for result in results:
            for factura in result.reconciled_bill_ids:
                self.create(
                    {
                        "payment_id": result.id,
                        "factura_id": factura.id,
                        "session_identifier": session_identifier,
                    }
                )

    @api.model
    def delete_old_payment_records(self):
        # Define el umbral de 24 horas
        time_threshold = datetime.now() - timedelta(hours=24)
        # Busca los registros que son más antiguos de 24 horas
        old_records = self.search([("create_date", "<", time_threshold)])
        if old_records:
            old_records.unlink()
