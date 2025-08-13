from odoo import models, fields, api, exceptions


class HrJobFactorPuesto(models.Model):
    _name = "hr.job.factor.description"
    _description = "Decripcion de Factores en Puestos"
    _import_enabled = True

    name = fields.Char(string="Descripción", required=True, store=True)
    factor_id = fields.Many2one(
        "hr.job.factor", string="Factor", required=True, store=True
    )
    grado = fields.Selection(
        [
            ("I", "I"),
            ("II", "II"),
            ("III", "III"),
            ("IV", "IV"),
            ("V", "V"),
            ("VI", "VI"),
            ("VII", "VII"),
        ],
        string="Grado",
        required=True,
        store=True,
    )
    punteo = fields.Integer(string="Punteo", required=True, store=True)

    _sql_constraints = [
        (
            "unique_factor_description",
            "unique(name, factor_id)",
            "La descripción del factor debe ser única por factor.",
        )
    ]
