from odoo import models, fields


class HrJobCompetenciaPuesto(models.Model):
    _name = "hr.job.competencia.puesto"
    _description = "Competencias en Puestos"
    _import_enabled = True

    competencia_id = fields.Many2one(
        "hr.job.competencia", string="Competencia", required=True, store=True
    )
    competencia_descripcion = fields.Many2one(
        "hr.job.competencia.description",
        string="Descripción",
        required=True,
        store=True,
    )
    grado = fields.Selection(
        related="competencia_descripcion.grado",
        string="Grado",
        readonly=True,
        store=True,
    )
    puesto_id = fields.Many2one(
        "hr.job", string="Puesto", store=True
    )  # Este es el campo relevante
    punteo = fields.Integer(
        string="Punteo",
        store=True,
        related="competencia_descripcion.punteo",
        readonly=True,
    )
    publicar_web = fields.Boolean(string="Publicar en la Web", store=True)
