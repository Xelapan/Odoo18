from odoo import models, fields, api, exceptions


class HrJobFactorPuesto(models.Model):
    _name = "hr.job.factor.puesto"
    _description = "Factores en Puestos"
    _import_enabled = True

    factor_descripcion = fields.Many2one(
        "hr.job.factor.description", string="Descripción", required=True, store=True
    )
    factor_id = fields.Many2one(
        "hr.job.factor", string="Factor", required=True, store=True
    )
    grado = fields.Selection(
        [], string="Grado", readonly=True, related="factor_descripcion.grado"
    )
    job_id = fields.Many2one("hr.job", string="Puesto", required=True, store=True)
    publicar_en_web = fields.Boolean(string="Publicar en Web", store=True)
    punteo = fields.Integer(
        string="Punteo", readonly=True, related="factor_descripcion.punteo"
    )

    @api.onchange("factor_descripcion")
    def _onchange_factor_description(self):
        if self.factor_descripcion:
            self.punteo = self.factor_descripcion.punteo
            self.grado = self.factor_descripcion.grado
        else:
            self.punteo = 0
            self.grado = ""

    @api.depends("factor_descripcion")
    def _compute_related_fields(self):
        for record in self:
            if record.factor_descripcion:
                record.punteo = record.factor_descripcion.punteo
                record.grado = record.factor_descripcion.grado
            else:
                record.punteo = 0
                record.grado = ""
