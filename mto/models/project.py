from odoo import models, fields, api


class Project(models.Model):
    _inherit = "project.project"

    # custom_picking_type_id = fields.Many2one('stock.picking.type', string='Tipo de transferencia', store=True, help="Tipo de transferencia para el proyecto, estas deben ser configuradas en el módulo de inventario.")
    # location_id = fields.Many2one('stock.location', string='Ubicación Origen', related='custom_picking_type_id.default_location_src_id', readonly=True, help="Ubicación de origen para el proyecto, estas deben ser configuradas en el módulo de inventario.")
    # location_dest_id = fields.Many2one('stock.location', string='Ubicación Destino', store=True, related='custom_picking_type_id.default_location_dest_id', readonly=True, help="Ubicación de destino para el proyecto, estas deben ser configuradas en el módulo de inventario.")
    # presupuestado = fields.Boolean(string='Presupuesto', store=True, help="Indica si el proyecto tiene presupuesto, se este campo es verdadero todos los pedidos de venta se autorizaran automáticamente.")
    x_autorizador = fields.Many2one(
        "res.partner",
        string="Autorizador",
        store=True,
        help="Autorizador del proyecto.",
        context={"allowed_company_ids": False},
    )  # Permitir empleados de todas las empresas)
