# -*- coding: utf-8 -*-
# Copyright 2023 Alex Martinez <baterodedios3@gmail.com>
# License AGPL-3.0 or later

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMesBloqueado(models.Model):
    _name = "account.mes.bloqueado"
    _description = "Account Mes Bloqueado"
    _order = "create_date desc"

    user_id = fields.Many2one(
        "res.users",
        string="Usuario",
        required=True,
        default=lambda self: self.env.user,
        store=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        required=True,
        default=lambda self: self.env.user.company_id,
        store=True,
    )
    anio = fields.Integer(string="Año", required=True, store=True)
    mes = fields.Selection(
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
        store=True,
    )


class AccountMove(models.Model):
    _inherit = "account.move"
    x_asiento_bloqueado = fields.Boolean(
        string="Asiento Bloqueado", default=False, store=True, readonly=True
    )
