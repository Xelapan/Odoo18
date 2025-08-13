from datetime import datetime

from odoo import models, fields, api
from odoo.http import request


class AccountAssetD(models.TransientModel):
    _name = "account.asset.d.wizard"
    _description = "Visor Activos y Depresiación Wizard"

    asset_ids = fields.Many2many("account.asset", string="Activo")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    # mes_de = fields.Selection([
    #     ('1', 'Enero'),
    #     ('2', 'Febrero'),
    #     ('3', 'Marzo'),
    #     ('4', 'Abril'),
    #     ('5', 'Mayo'),
    #     ('6', 'Junio'),
    #     ('7', 'Julio'),
    #     ('8', 'Agosto'),
    #     ('9', 'Septiembre'),
    #     ('10', 'Octubre'),
    #     ('11', 'Noviembre'),
    #     ('12', 'Diciembre')
    # ], string='Mes De')
    mes_a = fields.Selection(
        [
            ("1", "Enero"),
            ("2", "Febrero"),
            ("3", "Marzo"),
            ("4", "Abril"),
            ("5", "Mayo"),
            ("6", "Junio"),
            ("7", "Julio"),
            ("8", "Agosto"),
            ("9", "Septiembre"),
            ("10", "Octubre"),
            ("11", "Noviembre"),
            ("12", "Diciembre"),
        ],
        string="Mes A",
        required=True,
    )
    anio = fields.Integer(string="Año", required=True)

    def open_account_asset_d_at_date(self):
        self.ensure_one()
        # Obtener el session_id de la sesión HTTP actual
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual

        # Eliminar datos anteriores para esta sesión
        self.env["account.asset.d"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        domain = [("company_id", "=", self.company_id.id)]

        if self.asset_ids:
            domain.append(("id", "in", self.asset_ids.ids))
        dia_mes = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

        domain.append(
            (
                "acquisition_date",
                "<=",
                datetime(
                    self.anio if self.anio else datetime.now().year,
                    int(self.mes_a),
                    dia_mes[int(self.mes_a) - 1],
                ),
            )
        )

        # cuando solo se selecciona el año
        # if self.anio:
        # domain.append(('acquisition_date', '>=', datetime(self.anio, 1, 1)))
        #    domain.append(('acquisition_date', '<=', datetime(self.anio, 12, 31)))
        # cuando se selecciona el año y el mes de y el mes al
        # elif self.anio and self.mes_de and self.mes_a:
        #     domain.append(('acquisition_date', '>=', datetime(self.anio, int(self.mes_de), 1)))
        #     domain.append(('acquisition_date', '<=', datetime(self.anio, int(self.mes_a), dia_mes[int(self.mes_a)-1])))
        # cuando no se selecciona el año pero el mes si
        # elif self.mes_de and self.mes_a:
        #     domain.append(('acquisition_date', '>=', datetime(datetime.now().year, int(self.mes_de), 1)))
        #     domain.append(('acquisition_date', '<=', datetime(datetime.now().year, int(self.mes_a), dia_mes[int(self.mes_a)-1])))
        # elif self.mes_de:
        #     domain.append(('acquisition_date', '>=', datetime(self.anio if self.anio else datetime.now().year, int(self.mes_de), 1)))
        #     domain.append(('acquisition_date', '<=', datetime(self.anio if self.anio else datetime.now().year, int(self.mes_de), dia_mes[int(self.mes_a)-1])))
        # elif self.mes_a:
        #     domain.append(('acquisition_date', '>=', datetime(self.anio if self.anio else datetime.now().year, 1, 1)))
        #     domain.append(('acquisition_date', '<=', datetime(self.anio if self.anio else datetime.now().year, int(self.mes_a), dia_mes[int(self.mes_a)-1])))

        results = self.env["account.asset"].search(domain)
        visor_activos = self.env["account.asset.d"]

        for result in results:
            depreciacion = 0
            valor_libros = 0
            registrados = []
            # no puedo comparar date contra datetime
            xDepreciaciones = result.depreciation_move_ids.filtered(
                lambda x: x.state == "posted"
                and x.date
                <= datetime(
                    self.anio if self.anio else datetime.now().year,
                    int(self.mes_a),
                    dia_mes[int(self.mes_a) - 1],
                ).date()
            )
            x_PrimerValor = sum(
                result.depreciation_move_ids.mapped("depreciation_value")
            )
            for line in xDepreciaciones:
                if line.state == "posted" or line.state != "posted":
                    registrados.append(
                        {
                            "id": line.id,
                            "referencia": line.ref,
                            "valor": line.depreciation_value,
                        }
                    )
                    depreciacion += line.depreciation_value
            valor_libros = (
                x_PrimerValor - depreciacion
            )  # result.original_value - depreciacion
            visor_activos.create(
                {
                    "asset_id": result.id if result else False,
                    "session_identifier": session_identifier,  # Asociar los datos a la cookie de sesión
                    "model_id": (
                        result.original_move_line_ids.account_id.id
                        if result.original_move_line_ids.account_id
                        else False
                    ),
                    "acquisition_date": (
                        result.acquisition_date if result.acquisition_date else False
                    ),
                    "marca": result.marca if result.marca else "",
                    # 'descripcion': result.descripcion,
                    "no_placa": result.no_placa if result.no_placa else "",
                    "original_move_line": (
                        result.original_move_line_ids[0].id
                        if result.original_move_line_ids
                        else False
                    ),
                    "asiento_id": (
                        result.original_move_line_ids.move_id.id
                        if result.original_move_line_ids.move_id
                        else False
                    ),
                    #'serie_fel': result.serie_fel,
                    #'numero_fel': result.numero_fel,
                    "original_value": (
                        result.original_value if result.original_value else 0
                    ),
                    # 'book_value': result.book_value,
                    "book_value": valor_libros if valor_libros else 0,
                    "company_id": result.company_id.id,
                    "currency_id": result.company_id.currency_id.id,
                    "depreciacion_acumulada": (depreciacion)
                    + (
                        result.already_depreciated_amount_import
                        if result.already_depreciated_amount_import
                        else 0
                    ),
                }
            )

        return {
            "name": "Reporte de Depreciaciones",
            "type": "ir.actions.act_window",
            "res_model": "account.asset.d",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_asset_d_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_asset_d_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }
