# -*- coding: utf-8 -*-

from odoo import models, fields, api

# import odoo.addons.decimal_precision as dp
# import pyzbar.pyzbar as pyzbar
# from PIL import Image
# import io
# import base64


class MaterialPurchaseRequisitionLine(models.Model):
    _name = "material.purchase.requisition.line"
    _description = "Linea de Requisición de Materiales"

    requisition_id = fields.Many2one(
        "material.purchase.requisition",
        string="Requisitions",
    )
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        required=True,
    )
    #     layout_category_id = fields.Many2one(
    #         'sale.layout_category',
    #         string='Section',
    #     )
    description = fields.Char(
        string="Description",
        required=True,
    )
    qty = fields.Float(
        string="Cantidad",
        default=1,
        required=True,
    )

    uom = fields.Many2one(
        "uom.uom",  # product.uom in odoo11
        string="Unidad de Medida",
        required=True,
    )
    partner_id = fields.Many2many(
        "res.partner",
        string="Vendors",
    )
    requisition_type = fields.Selection(
        selection=[
            ("internal", "Internal Picking"),
            ("purchase", "Purchase Order"),
        ],
        string="Tipo de Requisición",
        default="internal",
        required=True,
    )

    x_costo = fields.Float(string="Costo", readonly=True, store=True)

    x_monto = fields.Float(
        string="Monto",
        readonly=True,
        #store=True,
        compute="_compute_monto",
    )

    x_price = fields.Float(string="Precio", store=True)

    @api.depends("product_id", "qty")
    @api.onchange("product_id", "qty")
    def _compute_price(self):
        for rec in self:
            rec.x_price = rec.product_id.list_price

    @api.depends("qty", "x_price")
    def _compute_monto(self):
        for rec in self:
            rec.x_monto = rec.qty * rec.x_price

    # @api.onchange('x_qr')
    # def obtener_contenido_codigo_qr(self):
    #   if self.x_qr:
    #      imagen = Image.open(io.BytesIO(self.x_qr))
    #     codigo_qr = pyzbar.decode(imagen)
    #    if codigo_qr:
    #       contenido = codigo_qr[0].data.decode('utf-8')
    #  self.x_qr_code = contenido

    @api.onchange("product_id")
    def onchange_product_id(self):
        for rec in self:
            rec.description = rec.product_id.name
            rec.uom = rec.product_id.uom_id.id
            rec.x_costo = rec.product_id.standard_price
            # if (rec.product_id.product_tmpl_id.last_purchase_price/1.12)>rec.product_id.standard_price:
            # rec.x_coti=(rec.product_id.product_tmpl_id.last_purchase_price/1.12)
            # else:
            # rec.x_coti=rec.product_id.standard_price
            # rec.x_coti = rec.product_id.standard_price


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
