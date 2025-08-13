from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class HrApplicant(models.Model):
    _inherit = "hr.applicant"
    primer_nombre_Candidato = fields.Char(string="Primer Nombre", store=True)
    segundo_nombre_Candidato = fields.Char(string="Segundo Nombre", store=True)
    primer_apellido_Candidato = fields.Char(string="Primer Apellido", store=True)
    segundo_apellido_Candidato = fields.Char(string="Segundo Apellido", store=True)
    apellido_casada_Candidato = fields.Char(string="Apellido de Casada", store=True)

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(HrApplicant, self).fields_get(allfields, attributes)
        # Lista de campos a desmarcar de la lista negra
        fields_to_update = [
            "primer_nombre_Candidato",
            "segundo_nombre_Candidato",
            "primer_apellido_Candidato",
            "segundo_apellido_Candidato",
            "apellido_casada_Candidato",
        ]
        for field_name in fields_to_update:
            if field_name in fields:
                fields[field_name]["website_form_blacklisted"] = False
        return fields

    @api.model
    def create(self, vals):
        _logger.info("Valores recibidos: %s", vals)
        return super(HrApplicant, self).create(vals)
