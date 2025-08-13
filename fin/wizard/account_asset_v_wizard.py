from odoo import models, fields, api
from odoo.http import request


class AccountAssetV(models.TransientModel):
    _name = "account.asset.v.wizard"
    _description = "Visor Activos Wizard"

    asset_ids = fields.Many2many("account.asset", string="Activo")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    def open_account_asset_v_at_date(self):
        self.ensure_one()
        # Obtener el session_id de la sesión HTTP actual
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual

        # Eliminar datos anteriores para esta sesión
        self.env["account.asset.v"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        domain = [("company_id", "=", self.company_id.id)]

        if self.asset_ids:
            domain.append(("id", "in", self.asset_ids.ids))

        results = self.env["account.asset"].search(domain)
        visor_activos = self.env["account.asset.v"]
        for result in results:
            visor_activos.create(
                {
                    "asset_id": result.id if result else False,
                    "session_identifier": session_identifier,  # Asociar los datos a la cookie de sesión
                    "model_id": result.model_id.id if result.model_id else False,
                    "acquisition_date": result.acquisition_date,
                    "marca": result.marca,
                    "descripcion": result.descripcion,
                    "no_placa": result.no_placa,
                    "original_move_line": (
                        result.original_move_line_ids[0].id
                        if result.original_move_line_ids
                        else False
                    ),
                    #'serie_fel': result.serie_fel,
                    #'numero_fel': result.numero_fel,
                    "original_value": result.original_value,
                    "book_value": result.book_value,
                    "company_id": result.company_id.id,
                    "currency_id": result.company_id.currency_id.id,
                }
            )

        return {
            "name": "Visor Activos",
            "type": "ir.actions.act_window",
            "res_model": "account.asset.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_asset_v_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_asset_v_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }
