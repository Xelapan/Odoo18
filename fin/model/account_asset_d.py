from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.http import request


class AccountAssetD(models.Model):
    _name = "account.asset.d"
    _description = "Visor Activos y Depreciación"

    asset_id = fields.Many2one("account.asset", string="Activo", readonly=True)
    model_id = fields.Many2one("account.account", string="Tipo de bien", readonly=True)
    asiento_id = fields.Many2one(
        "account.move", string="Asiento Contable", readonly=True
    )
    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True
    )
    acquisition_date = fields.Date(string="Fecha de ingreso", readonly=True)
    marca = fields.Char(string="Marca", readonly=True, related="asset_id.marca")
    no_placa = fields.Char(
        string="No. Placa", readonly=True, related="asset_id.no_placa"
    )
    original_move_line = fields.Many2one(
        "account.move.line", string="Entradas de diario", readonly=True
    )
    serie_fel = fields.Char(string="Serie", readonly=True, compute="_compute_serie_fel")
    numero_fel = fields.Char(string="Número Factura", readonly=True)
    original_value = fields.Monetary(
        string="Valor Original", readonly=True, related="asset_id.original_value"
    )
    book_value = fields.Monetary(string="Valor Libro", readonly=True, store=True)
    depreciacion_acumulada = fields.Monetary(
        string="Depreciación Acumulada", readonly=True
    )
    session_identifier = fields.Char(string="Identificador de sesión", readonly=True)
    registro_interno = fields.Char(string="Registro Interno", readonly=True)
    descripcion = fields.Char(
        string="Descripción", readonly=True, related="original_move_line.name"
    )

    @api.onchange("original_move_line")
    def _compute_serie_fel(self):
        for rec in self:
            for record in rec:
                record.serie_fel = ""
                record.numero_fel = ""
                if record.original_move_line:
                    move = record.original_move_line.move_id
                    if move:
                        # record.model_id = move.account_id.id or False
                        record.serie_fel = move.serie_fel if move.serie_fel else ""
                        record.numero_fel = move.numero_fel if move.numero_fel else ""
                        break
                    else:
                        record.serie_fel = ""
                        record.numero_fel = ""
                else:
                    record.serie_fel = ""
                    record.numero_fel = ""

    @api.model
    def get_session_identifier(self, fields_list):
        res = super(AccountAssetD, self).get_session_identifier(fields_list)
        session_identifier = request.session.sid
        if session_identifier:
            res["domain"] = [("session_identifier", "=", session_identifier)]
        return res

    @api.model
    def action_open_account_asset_d(self):
        session_identifier = request.session.sid
        return {
            "name": "Reporte de Depreciaciones",
            "type": "ir.actions.act_window",
            "res_model": "account.asset.d",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_asset_d_view_tree").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    @api.model
    def create_or_update_records(self, results):
        session_identifier = self.get_session_identifier()
        self.search([("session_identifier", "=", session_identifier)]).unlink()
        for result in results:
            self.create(
                {
                    "asset_id": result.id,
                    "session_identifier": session_identifier,
                }
            )

    @api.model
    def delete_old_account_asset_v_records(self):
        # Define el umbral de 24 horas
        time_threshold = datetime.now() - timedelta(hours=24)
        # Busca los registros que son más antiguos de 24 horas
        old_records = self.search([("create_date", "<", time_threshold)])
        if old_records:
            old_records.unlink()

    def open_wizard(self):
        return {
            "name": "Visor Activos y Depreciación",
            "type": "ir.actions.act_window",
            "res_model": "account.asset.d.wizard",
            "view_mode": "form",
            "view_id": self.env.ref("fin.account_asset_d_wizard_view_form").id,
            "target": "new",
            "context": {
                "default_session_identifier": request.session.sid,
            },
        }
