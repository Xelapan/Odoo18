from odoo import models, fields, api
from datetime import datetime, time, timedelta


class InventoryAtDateWizard(models.TransientModel):
    _name = "inventory.at.date.wizard"
    _description = "Wizard para reporte de inventario a la fecha"

    # warehouse_id = fields.Many2one('stock.warehouse', string='Almacén', required=False)
    location_id = fields.Many2one("stock.location", string="Ubicación", required=True)
    # date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string="Fecha Hasta", required=True)
    product_id = fields.Many2one("product.product", string="Producto", required=False)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    def generate_report(self):
        self.ensure_one()

        # Aquí debes llamar a un método que realice el cálculo y cree los registros del reporte
        self.env["stock.inventory.at.date"].open_inventory_report(
            datetime.combine(self.date_to, time(23, 59, 59)) + timedelta(hours=6),
            self.location_id,
            self.product_id,
            self.company_id,
        )

        # Retornar la vista de reporte
        return {
            "type": "ir.actions.act_window",
            "name": "Reporte de Inventario a la Fecha",
            "view_mode": "tree,form",
            "res_model": "stock.inventory.at.date",
            "domain": [],
            "context": {"search_default_group_by_product": 1},
        }
