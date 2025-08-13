# Copyright 2020, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models, api
from datetime import date
from odoo.exceptions import UserError


class StockKardexReport(models.Model):
    _name = "stock.kardex.report"
    _description = "This model creates a kardex report for stock moves"
    _order = "date desc"

    account_move_id = fields.Many2one(
        "account.move",
        readonly=True,
        string="Movimiento Contable",
        compute="_compute_account_move_id",
    )
    move_id = fields.Many2one("stock.move", readonly=True, string="Movimiento")
    product_id = fields.Many2one("product.product", readonly=True, string="Producto")
    product_uom_id = fields.Many2one(
        "uom.uom", readonly=True, string="Unidad de Medida"
    )
    # lot_id = fields.Many2one('stock.production.lot', readonly=True)
    owner_id = fields.Many2one("res.partner", readonly=True, string="Propietario")
    package_id = fields.Many2one("stock.quant.package", readonly=True, string="Paquete")
    location_id = fields.Many2one("stock.location", readonly=True, string="Origen")
    location_dest_id = fields.Many2one(
        "stock.location", readonly=True, string="Destino"
    )
    qty_done = fields.Float("Cantidad", readonly=True)
    date = fields.Datetime(readonly=True, string="Fecha")
    origin = fields.Char(readonly=True, string="Movimiento", related="move_id.origin")
    reference = fields.Char(readonly=True, string="Referencia")
    balance = fields.Float(readonly=True, string="Saldo")
    user_id = fields.Many2one("res.users", readonly=True, string="Usuario")
    update_at = fields.Datetime(readonly=True, string="Fecha Modificacion")
    picking_type_id = fields.Many2one(
        "stock.picking.type", readonly=True, string="Tipo de Movimiento"
    )
    tipo_mov = fields.Char(readonly=True, string="Tipo Movimiento")
    cost = fields.Float("Costo", readonly=True)
    total_cost = fields.Float("Costo Total", readonly=True)

    # @api.depends('move_id')
    # def _compute_account_move_id(self):
    #     for record in self:
    #         thSVL = self.env['stock.valuation.layer'].search([('stock_move_id', '=', record.move_id.id)], order='create_date desc', limit=1)
    #         if thSVL:
    #             for svl in thSVL:
    #                 if svl.account_move_id:
    #                     record.account_move_id = svl.account_move_id

    @api.depends("move_id")
    def _compute_account_move_id(self):
        for record in self:
            account_move = False
            if record.move_id:
                thSVL = self.env["stock.valuation.layer"].search(
                    [("stock_move_id", "=", record.move_id.id)],
                    order="create_date desc",
                    limit=1,
                )

                if thSVL and thSVL.account_move_id:
                    account_move = thSVL.account_move_id

            record.account_move_id = account_move

    def action_open_reference(self):
        """Open the form view of the move's reference document, if one exists, otherwise open form view of self"""
        self.ensure_one()
        source = self.move_id
        if source and source.check_access_rights("read", raise_exception=False):
            return {
                "res_model": source._name,
                "type": "ir.actions.act_window",
                "views": [[False, "form"]],
                "res_id": source.id,
            }
        return {
            "res_model": self._name,
            "type": "ir.actions.act_window",
            "views": [[False, "form"]],
            "res_id": self.id,
        }

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        if "unit_cost" in fields:
            fields.remove("unit_cost")

        if "product_id" in groupby and "unit_cost" not in fields:
            fields.append("product_id")

        result = super().read_group(
            domain, fields, groupby, offset, limit, orderby, lazy
        )

        if "product_id" in groupby:
            product_obj = self.env["product.product"]
            todo = (
                self.env["stock.kardex.report"]
                .search([])
                .sorted(key=lambda r: r.date, reverse=True)
            )
            for group in result:
                product_ids = group.get("product_id")
                if product_ids:
                    # Asegúrate de que `product_ids` es un solo ID
                    # if isinstance(product_ids, list):
                    product_id = product_ids[0]
                    # else:
                    #    product_id = product_ids

                    product = product_obj.browse(product_id)

                    if len(product) == 1:
                        if product.categ_id.property_cost_method == "average":
                            total_cost = 0.00
                            total_cost_real = 0.00
                            total_qty = 0.00
                            total_qty_real = 0.00
                            last_saldo = 0.00
                            last_costo = 0.00
                            layers = self.search(
                                [
                                    ("product_id", "=", product.id),
                                    ("date", "<=", todo[0].date),
                                ]
                            )
                            a = 0
                            for layer in layers:
                                if a == 0:
                                    a = 1
                                    last_saldo = layer.balance
                                    last_costo = layer.cost
                                if (
                                    layer.tipo_mov != "Transferencia Interna"
                                    or "Transferencia" not in layer.tipo_mov
                                ):
                                    total_qty += layer.qty_done
                                    total_cost += layer.cost * layer.qty_done
                                total_cost_real += layer.cost * layer.qty_done
                                total_qty_real += layer.qty_done
                            if total_qty:
                                group["cost"] = total_cost / total_qty
                                group["total_cost"] = (
                                    last_costo  # group['cost'] * last_saldo
                                )
                                group["balance"] = last_saldo
                            else:
                                group["cost"] = 0
                            xt = total_cost
                            xtt = total_cost_real
                            xq = total_qty
                            xqr = total_qty_real
                            xcp = total_cost / total_qty
                            xcr = total_cost_real / total_qty_real
                    else:
                        # Maneja el caso en que hay múltiples productos o ninguno
                        raise UserError(
                            "Expected singleton product, got %d records" % len(product)
                        )

        return result
