from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    razon_social = fields.Char(string="Nombre Fiscal", store=True)
    nombre_comercial = fields.Char(string="Nombre Comercial", store=True)
