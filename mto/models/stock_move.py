from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = "stock.move"

    standard_price = fields.Float(
        string="Costo de Venta",
        related="product_id.standard_price",
        store=True,
        readonly=True,
    )
    lst_price = fields.Float(
        string="Precio de Venta",
        compute="_compute_lst_price",
        store=True,
        readonly=False,
    )
    monto = fields.Float(
        string="Monto", compute="_compute_monto", store=True, readonly=True
    )
    id_odoo_13 = fields.Integer(string="ID Odoo 13", store=True)

    api.depends("product_id", "product_id.lst_price")

    def _compute_lst_price(self):
        for record in self:
            if record.lst_price:
                continue
            record.lst_price = record.product_id.lst_price

    @api.depends("product_uom_qty", "lst_price")
    def _compute_monto(self):
        for record in self:
            record.monto = record.product_uom_qty * record.lst_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.lst_price = self.product_id.lst_price
            if self.raw_material_production_id.proyecto:
                self.location_id = (
                    self.raw_material_production_id.proyecto.location_dest_id.id
                )
        return super(StockMove, self)._onchange_product_id()


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    id_odoo_13 = fields.Integer(string="ID Odoo 13", store=True)
