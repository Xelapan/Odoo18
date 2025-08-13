# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2023 Alex Martínez
#
##############################################################################
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime, date
from calendar import monthrange
import locale


class WizarMesBloqueado(models.TransientModel):
    _name = "wizard.mes.bloqueado"
    _description = "FIN Contabilidad"
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company.id
    )
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    anio = fields.Integer(
        string="Año", default=lambda self: datetime.now().year, required=True
    )
    mes_de = fields.Selection(
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
        string="Mes",
        required=True,
    )
    state = fields.Selection(
        [("choose", "choose"), ("get", "get"), ("pre", "pre")], default="choose"
    )
    name = fields.Char(string="File Name", readonly=True)
    data = fields.Binary(string="File", readonly=True)

    @api.onchange("company_id")
    def onchange_company_id(self):
        domain = [("id", "in", self.env.user.company_ids.ids)]
        return {"domain": {"company_id": domain}}

    def go_back(self):
        self.state = "choose"
        return {
            "name": "Bloquear Mes",
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "target": "new",
        }

    def cerrar_mes(self):
        self.write(
            {
                "state": "pre",
                "name": "Bloquear Mes",
            }
        )
        return {
            "name": "Bloquear Mes",
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "target": "new",
        }

    def bloquear_mes(self):
        # Mensaje de advertencia esperando que el usuario acepte o cancele
        self.start_date = date(self.anio, int(self.mes_de), 1)
        self.end_date = date(
            self.anio, int(self.mes_de), monthrange(self.anio, int(self.mes_de))[1]
        )
        if int(self.mes_de) > 1:
            mes_actual = int(self.mes_de) - 1
            aux_mes = 1
            while aux_mes <= mes_actual:
                thMeseAbiertos = self.env["account.mes.bloqueado"].search(
                    [
                        ("anio", "=", self.anio),
                        ("mes", "=", aux_mes),
                        ("company_id", "=", self.company_id.id),
                    ]
                )
                if not thMeseAbiertos:
                    raise ValidationError(
                        _(
                            "El mes "
                            + str(
                                dict(self._fields["mes_de"].selection).get(str(aux_mes))
                            )
                            + " del año "
                            + str(self.anio)
                            + ", se encuentra abierto para la compañia "
                            + str(
                                self.company_id.name
                                + ". \nPor favor cierre el mes "
                                + str(
                                    dict(self._fields["mes_de"].selection).get(
                                        str(aux_mes)
                                    )
                                )
                                + " antes de cerrar el mes "
                                + str(
                                    dict(self._fields["mes_de"].selection).get(
                                        self.mes_de
                                    )
                                )
                                + "."
                            )
                        )
                    )
                aux_mes += 1
        else:
            if int(self.mes_de) == 1:
                self.env["ir.sequence"].search(
                    [
                        ("company_id", "=", self.company_id.id),
                        ("code", "=", "account.mes.bloqueado.seq"),
                    ]
                ).write(
                    {
                        "number_next_actual": 1,
                    }
                )

        thCuentaBloqueada = self.env["account.mes.bloqueado"].search(
            [
                ("anio", "=", self.anio),
                ("mes", "=", self.mes_de),
                ("company_id", "=", self.company_id.id),
            ]
        )
        if thCuentaBloqueada:
            raise ValidationError(
                _(
                    "El mes "
                    + str(dict(self._fields["mes_de"].selection).get(self.mes_de))
                    + " del año "
                    + str(self.anio)
                    + ", ya se encuentra bloqueado para la compañia "
                    + str(self.company_id.name + ".")
                )
            )
        else:
            thAsientos = self.env["account.move"].read_group(
                domain=[
                    ("date", ">=", self.start_date),
                    ("date", "<=", self.end_date),
                    ("state", "=", "posted"),
                    ("company_id", "=", self.company_id.id),
                ],
                fields=[
                    "date",
                    "x_name_partida",
                ],  # Campo 'date' para agrupar y contar registros
                groupby=["date:day"],  # Agrupar por campo 'date'
                orderby="date asc",
            )  # Ordenar por campo 'date' de forma ascendente
            if thAsientos:
                for asiento in thAsientos:
                    meses = {
                        "ene.": "01",
                        "feb.": "02",
                        "mar.": "03",
                        "abr.": "04",
                        "may.": "05",
                        "jun.": "06",
                        "jul.": "07",
                        "ago.": "08",
                        "sep.": "09",
                        "oct.": "10",
                        "nov.": "11",
                        "dic.": "12",
                    }

                    partes = str(asiento["date:day"]).split()
                    # Convierte el mes abreviado en número usando el diccionario
                    mes_numero = meses.get(partes[1])
                    fecha = datetime.strptime(
                        f"{partes[2]}-{mes_numero}-{partes[0]}", "%Y-%m-%d"
                    )
                    if self.env["account.move"].search(
                        [
                            ("date", "=", fecha),
                            ("state", "=", "posted"),
                            ("company_id", "=", self.company_id.id),
                            ("x_name_partida", "!=", False),
                            ("x_asiento_bloqueado", "=", True),
                        ]
                    ):
                        raise ValidationError(
                            _(
                                "Uno o mas asientos de fecha "
                                + str(fecha)
                                + " ya tiene numero de partida."
                            )
                        )
                    else:
                        self.env["account.move"].search(
                            [
                                ("date", "=", fecha),
                                ("state", "=", "posted"),
                                ("company_id", "=", self.company_id.id),
                            ]
                        ).write(
                            {
                                "x_name_partida": self.env["ir.sequence"].next_by_code(
                                    "account.mes.bloqueado.seq"
                                )
                                or "Error",
                                "x_asiento_bloqueado": True,
                            }
                        )
                self.env["account.mes.bloqueado"].create(
                    {
                        "anio": self.anio,
                        "mes": self.mes_de,
                        "company_id": self.company_id.id,
                    }
                )
                self.write(
                    {
                        "state": "get",
                        "name": "Bloquear Mes",
                    }
                )
                return {
                    "name": "Bloquear Mes",
                    "type": "ir.actions.act_window",
                    "res_model": self._name,
                    "view_mode": "form",
                    "view_type": "form",
                    "res_id": self.id,
                    "target": "new",
                }
            else:
                raise ValidationError(
                    _(
                        "No se encontraron asientos contables para el mes "
                        + str(dict(self._fields["mes_de"].selection).get(self.mes_de))
                        + " del año "
                        + str(self.anio)
                        + ", para la compañia "
                        + str(self.company_id.name)
                        + "."
                    )
                )


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
