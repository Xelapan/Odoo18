from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.http import request


class AccountAssetViaceq(models.Model):
    _name = "account.asset.viaceq"
    _description = "Visor Activos y Equipos"

    # asset_id = fields.Many2one('account.asset', string="Activo", readonly=True)
    # model_id = fields.Many2one('account.asset', string="Tipo de bien", readonly=True)
    product_id = fields.Many2one("product.product", string="Activo", readonly=True)
    product_model_id = fields.Many2one(
        "product.product", string="Tipo de Bien", readonly=True
    )
    acquisition_date = fields.Date(string="Fecha de ingreso", readonly=True)

    serie_fel = fields.Char(string="Serie", readonly=True)
    numero_fel = fields.Char(string="Número Factura", readonly=True)
    # partner_id = fields.Many2one('res.partner', string="Proveedor", readonly=True)
    partner_name = fields.Char(
        string="Proveedor",
        readonly=True,
    )
    descripcion = fields.Char(string="Descripción", readonly=True)
    original_value = fields.Monetary(string="Valor Original", readonly=True)
    model_id = fields.Many2one("account.account", string="Tipo de bien", readonly=True)

    # move_id = fields.Many2one('account.move', string="Asiento Contable", readonly=True)
    asiento_contable = fields.Char(string="Asiento Contable", readonly=True)
    asiento_id = fields.Many2one(
        "account.move", string="Asiento Contable", readonly=True
    )

    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)
    original_move_line = fields.Many2one(
        "account.move.line", string="Entradas de diario", readonly=True
    )
    session_identifier = fields.Char(string="Identificador de sesión", readonly=True)

    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True
    )
    no_placa = fields.Char(string="No. Placa", readonly=True)

    def get_session_identifier(self, fields_list):
        res = super(AccountAssetViaceq, self).get_session_identifier(fields_list)
        session_identifier = request.session.sid
        if session_identifier:
            res["domain"] = [("session_identifier", "=", session_identifier)]
        return res

    @api.model
    def action_open_account_asset_viaceq(self):
        session_identifier = request.session.sid
        return {
            "name": "Reporte de Equipo Fungible",
            "type": "ir.actions.act_window",
            "res_model": "account.asset.viaceq",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_asset_viaceq_view_tree").id,
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
                    # 'product_id': result.id,
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

            # def _busqueda_asiento_contable(self):
            #     for record in self:
            #         record.asiento_contable = record.asset_id.original_move_line_ids[0].move_id.name if record.asset_id.original_move_line_ids else False

            # def _busqueda_diario(self):
            #     for record in self:
            #         record.original_move_line = record.asset_id.original_move_line_ids[0].id if record.asset_id.original_move_line_ids else False

            # @api.onchange('original_move_line')
            # def _compute_serie_fel(self):
            #     for record in self:
            #         if record.original_move_line:
            #             move = record.original_move_line.move_id
            #             if move:
            #                 record.serie_fel = move.serie_fel
            #                 record.numero_fel = move.numero_fel
            #                 # record.partner_id = move.partner_id
            #                 # record.move_id = move.id
            #                 break
            #             else:
            #                 record.serie_fel = False
            #         else:
            #             record.serie_fel = False
