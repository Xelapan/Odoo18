from odoo import models, fields


class HrJobCompetenciaDescription(models.Model):
    _name = "hr.job.competencia.description"
    _description = "Descripción de Competencia"

    name = fields.Char(string="Nombre", required=True, store=True)
    competencia_id = fields.Many2one(
        "hr.job.competencia", string="Competencia", required=True, store=True
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
            "unique_competencia_description",
            "unique(name, competencia_id)",
            "La descripción de la competencia debe ser única por competencia.",
        )
    ]
