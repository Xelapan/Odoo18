from odoo import models, fields, api
from odoo.http import request, _logger


class AccountAssetViaceq(models.TransientModel):
    _name = "account.asset.viaceq.wizard"
    _description = "Visor Activos Wizard"

    account_ids = fields.Many2many(
        "account.account",
        string="Cuenta",
        default=lambda self: self._get_default_accounts(),
    )
    date_from = fields.Date(string="Fecha de inicio", required=True)
    date_to = fields.Date(string="Fecha de fin", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    account_name = [
        "Maquinaria",
        "Mobiliario y Equipo",
        "Vehiculos",
        "Equipo de Computacion",
        "Activos Intangibles",
        "Equipo Fungible Fabrica",
        "Equipo Fungible Operativos",
        "Equipo Fungible Administracion",
    ]

    @api.model
    def _get_default_accounts(self):
        """Obtain default account IDs based on `account_name` and the active company."""
        company = self.env.company
        accounts = self.env["account.account"].search(
            [("name", "in", self.account_name), ("company_id", "=", company.id)]
        )
        return accounts.ids  # Devuelve una lista de IDs

    @api.onchange("company_id")
    def _onchange_company_id(self):
        """Update the domain and reset `account_ids` when the company changes."""
        self.account_ids = False
        return {
            "domain": {
                "account_ids": [
                    ("name", "in", self.account_name),
                    ("company_id", "=", self.company_id.id),
                ]
            }
        }

    def open_account_asset_viaceq_at_date(self):
        self.ensure_one()
        session_identifier = request.session.sid

        # Archive previous data for this session instead of deleting
        self.env["account.asset.viaceq"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()
        # previous_records.write({'active': False})

        domain = [
            ("company_id", "=", self.company_id.id),
            ("date", ">=", self.date_from),
            ("date", "<=", self.date_to),
        ]

        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        else:
            domain.append(("account_id.name", "in", self.account_name))

        results = self.env["account.move.line"].search(domain)
        visor_activos = self.env["account.asset.viaceq"]
        for result in results:
            if result.move_id.state == "posted":
                visor_activos.create(
                    {
                        "product_id": (
                            result.product_id.id if result.product_id else False
                        ),
                        "session_identifier": session_identifier,
                        "product_model_id": (
                            result.product_id.id if result.product_id else False
                        ),
                        "model_id": (
                            result.account_id.id if result.account_id else False
                        ),
                        "asiento_id": result.move_id.id if result.move_id else False,
                        "acquisition_date": result.date,
                        "descripcion": result.name,
                        "no_placa": (
                            result.asset_ids[0].no_placa if result.asset_ids else False
                        ),
                        "original_move_line": result.id if result else False,
                        "asiento_contable": (
                            result.account_id.name if result.account_id else False
                        ),
                        "serie_fel": (
                            result.move_id.serie_fel if result.move_id else False
                        ),
                        "numero_fel": (
                            result.move_id.numero_fel if result.move_id else False
                        ),
                        "partner_name": (
                            result.move_id.partner_id.name if result.move_id else False
                        ),
                        "original_value": result.price_subtotal,
                        "company_id": result.company_id.id,
                        "currency_id": result.company_id.currency_id.id,
                    }
                )
        return {
            "name": "Reporte de Equipo Fungible",
            "type": "ir.actions.act_window",
            "res_model": "account.asset.viaceq",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_asset_viaceq_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_asset_viaceq_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }
