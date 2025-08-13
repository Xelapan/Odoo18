from odoo import api, fields, models


class PickingType(models.Model):
    _inherit = "stock.picking.type"

    display_name = fields.Char(
        string="Display Name", readonly=True, compute="_compute_display_name"
    )

    @api.depends("name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name
