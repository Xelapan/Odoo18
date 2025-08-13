from datetime import timedelta

from odoo import fields, models, _, api
from odoo.exceptions import UserError


class StockInventoryAdjustmentName(models.TransientModel):
    _inherit = "stock.inventory.adjustment.name"

    inventory_adjustment_name = fields.Char(
        default=lambda self: self._default_inventory_adjustment_name()
    )

    def action_apply(self):
        # que solo permita ajustes de una sola bodega
        thQuants = self.quant_ids.filtered("inventory_quantity_set")
        if (
            len(self.quant_ids.filtered("inventory_quantity_set").mapped("location_id"))
            > 1
        ):
            raise UserError(_("Solamente se admiten ajustes de una sola bodega."))
        return super().action_apply()

    @api.model
    def _default_inventory_adjustment_name(self):

        current_date = (fields.Datetime.now() - timedelta(hours=6)).strftime(
            "%d-%m-%Y %H:%M:%S"
        )

        # Obtener los quants desde el contexto (porque self.quant_ids aún no tiene datos)
        quant_ids = self.env.context.get("default_quant_ids", [])
        if not quant_ids:
            raise UserError(_("No se han encontrado cantidades para ajustar."))

        # Filtrar solo los quants con `inventory_quantity_set`
        quants = (
            self.env["stock.quant"].browse(quant_ids).filtered("inventory_quantity_set")
        )
        if len(quants.mapped("location_id")) > 1:
            raise UserError(
                _("Solamente se admiten ajustes de una sola bodega a la vez.")
            )

        # Obtener la ubicación más frecuente
        location = quants.mapped("location_id.name")[:1] or ["Sin Ubicación"]
        parent_location = quants.mapped("location_id.location_id.name")[:1] or [
            "Sin Ubicación"
        ]

        return f"{parent_location[0]}/{location[0]} {current_date} Ajuste de Inventario"
