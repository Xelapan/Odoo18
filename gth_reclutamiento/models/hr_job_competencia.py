from odoo import models, fields


class HrJobCompetencia(models.Model):
    _name = "hr.job.competencia"
    _description = "Competencia"
    _import_enabled = True

    name = fields.Char(string="Nombre", required=True, store=True)
