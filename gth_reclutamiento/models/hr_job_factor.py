from odoo import models, fields, api, exceptions


class HrJobFactor(models.Model):
    _name = "hr.job.factor"
    _description = "Factore"
    _import_enabled = True

    name = fields.Char(string="Nombre", required=True, store=True)

    # @api.model
    # def default_get(self, fields):
    #     res = super(HrJobFactor, self).default_get(fields)
    #     # Aquí puedes agregar valores predeterminados para los campos
    #     res['name'] = 'Nuevo Factor'
    #     return res
