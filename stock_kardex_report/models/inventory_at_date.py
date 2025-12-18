import logging

from odoo import models, fields, api, _
from datetime import datetime, timedelta


class StockInventoryAtDate(models.TransientModel):
    _name = "stock.inventory.at.date"
    _description = "Inventory at Date"

    product_id = fields.Many2one("product.product", string="Producto")
    # warehouse_id = fields.Many2one('stock.warehouse', string='Almacén')
    location_id = fields.Many2one("stock.location", string="Ubicación")
    location_dest_id = fields.Many2one("stock.location", string="Ubicación Destino")
    date = fields.Date(string="Fecha")
    quantity = fields.Float(string="Cantidad")
    value = fields.Float(string="Valor")
    unit_cost = fields.Float(string="Costo Unitario")
    total_cost = fields.Float(string="Costo Total")
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )
    categ_id = fields.Many2one(
        "product.category", string="Categoría", related="product_id.categ_id"
    )
    uom_id = fields.Many2one(
        "uom.uom", string="Unidad de Medida", related="product_id.uom_id"
    )
    precio = fields.Float(string="Precio", related="product_id.lst_price")
    total_precio = fields.Float(string="Total Precio", compute="_compute_total_precio")

    def _compute_total_precio(self):
        for record in self:
            record.total_precio = record.quantity * record.precio

    def open_inventory_report(self, date_to, location_id, product_id, company_id):
        self.env["stock.inventory.at.date"].search([]).unlink()

        # Configurar el dominio para filtrar los movimientos de stock en el rango de fechas
        domain = [
            # ('date', '>=', date_from),
            ("date", "<=", date_to),
            ("state", "=", "done"),
            ("company_id", "=", company_id.id),
        ]

        if product_id:
            domain.append(("product_id", "=", product_id.id))
        # if warehouse_id:
        #     domain.append(('move_id.warehouse_id', '=', warehouse_id.id))
        if location_id:
            domain += [
                "|",
                ("location_id", "=", location_id.id),
                ("location_dest_id", "=", location_id.id),
            ]

        # Buscar los movimientos de stock
        stock_moves = self.env["stock.move.line"].search(domain, order="date desc")

        # Crear un diccionario para consolidar la información por producto
        product_data = {}
        thMovs = []
        for move in stock_moves:

            product_id = move.product_id.id
            if product_id not in product_data:
                product_data[product_id] = {
                    "total_quantity": 0,
                    "total_cost": 0,
                    "quantity": 0,
                    "calc_total_quantity": 0,
                    "calc_total_cost": 0,
                    "unit_cost": 0,
                }

            # Obtener el costo unitario del movimiento desde stock.valuation.layer
            cost = 0
            qty = 0
            value = 0
            # valuation = self.env['stock.valuation.layer'].search([('product_id', '=', move.product_id.id), ('create_date','<=',date_to)], order='id asc')
            # if len(valuation)>1:
            #     ddd = []
            #     for val in valuation:
            #         ddd.append(val)
            #     auxa = 1
            # if valuation:
            #     cost = valuation[0].unit_cost
            #     qty = valuation[0].quantity
            #     value = valuation[0].value
            # for val in valuation:
            #     qty += val.quantity
            #     value += val.value
            # thMovs.append({
            #     'move_id': move.id,
            #     'cost': value / qty if qty != 0 and cost != 0 else 0,
            #     'origin': move.origin
            # })
            # Sumar o restar según la ubicación
            if location_id:
                if move.location_dest_id.id == location_id.id:
                    # Si la ubicación de destino es la seleccionada, es una entrada
                    product_data[product_id]["total_quantity"] += move.quantity
                    product_data[product_id][
                        "total_cost"
                    ] += value  # move.quantity * cost
                    if (
                        (move.picking_type_id.code != "internal")
                        or (
                            move.picking_type_id.code == "internal"
                            and move.location_id.usage == "supplier"
                        )
                        or not move.picking_type_id
                    ):
                        product_data[product_id]["calc_total_quantity"] += move.quantity
                        product_data[product_id][
                            "calc_total_cost"
                        ] += value  # move.quantity * cost
                        product_data[product_id]["unit_cost"] = cost
                elif move.location_id.id == location_id.id:
                    # Si la ubicación de origen es la seleccionada, es una salida
                    product_data[product_id]["total_quantity"] -= move.quantity
                    product_data[product_id][
                        "total_cost"
                    ] -= value  # move.quantity * cost
                    if (
                        (move.picking_type_id.code != "internal")
                        or (
                            move.picking_type_id.code == "internal"
                            and move.location_dest_id.usage == "customer"
                        )
                        or not move.picking_type_id
                    ):
                        product_data[product_id]["calc_total_quantity"] -= move.quantity
                        product_data[product_id][
                            "calc_total_cost"
                        ] -= value  # move.quantity * cost
                        product_data[product_id]["unit_cost"] = cost
            else:
                # Si no se especifica una ubicación, se hace el cálculo general
                if self.env["stock.location"].browse(move.location_id.id).usage in [
                    "internal",
                    "transit",
                ] and self.env["stock.location"].browse(
                    move.location_dest_id.id
                ).usage not in [
                    "internal",
                    "transit",
                ]:
                    # Movimiento interno o en tránsito a externo
                    product_data[product_id]["total_quantity"] -= move.quantity
                    product_data[product_id][
                        "total_cost"
                    ] -= value  # move.quantity * cost
                    if move.picking_type_id.code != "internal":
                        product_data[product_id]["calc_total_quantity"] -= move.quantity
                        product_data[product_id][
                            "calc_total_cost"
                        ] -= value  # move.quantity * cost
                        product_data[product_id]["unit_cost"] = cost
                else:
                    # Movimiento general
                    product_data[product_id]["total_quantity"] += move.quantity
                    product_data[product_id][
                        "total_cost"
                    ] += value  # move.quantity * cost
                    if move.picking_type_id.code != "internal":
                        product_data[product_id]["calc_total_quantity"] += move.quantity
                        product_data[product_id][
                            "calc_total_cost"
                        ] += value  # move.quantity * cost
                        product_data[product_id]["unit_cost"] = cost

        # Crear los registros consolidados en stock.inventory.at.date
        last_cost = 0

        for product_id, data in product_data.items():
            # last_cost = 0
            # last_cost = sum(self.env['stock.valuation.layer'].search([('product_id', '=', product_id), ('unit_cost', '!=', 0), ('quantity', '!=', 0),('stock_move_id.date', '<=', date_to)], order='id desc', limit=1).mapped('unit_cost'))
            valuation = self.env["stock.valuation.layer"].search(
                [("product_id", "=", product_id), ("create_date", "<=", date_to)],
                order="id asc",
            )
            thValue = 0
            thQty = 0

            for val in valuation:
                thValue += val.value
                thQty += val.quantity
            last_cost = thValue / thQty if thValue != 0 and thQty != 0 else 0
            self.env["stock.inventory.at.date"].create(
                {
                    "product_id": product_id,
                    "location_id": location_id.id if location_id else False,
                    "quantity": data["total_quantity"],
                    "unit_cost": last_cost,  # data['calc_total_cost'] / data['calc_total_quantity'] if data['calc_total_quantity'] != 0 and data['calc_total_cost'] != 0 else 0.0,
                    "total_cost": data["total_quantity"]
                    * last_cost,  # (data['calc_total_cost'] / data['calc_total_quantity']),
                    "date": date_to,  # Fecha del reporte
                }
            )

        # Retornar la acción para mostrar la vista del reporte
        tree_view_id = self.env.ref(
            "stock_kardex_report.stock_inventory_at_date_tree_view"
        ).id
        action = {
            "type": "ir.actions.act_window",
            "views": [(tree_view_id, "list")],
            "view_id": tree_view_id,
            "view_mode": "list",
            "name": _("Inventory at Date"),
            "res_model": "stock.inventory.at.date",
        }
        return action

    def action_open_kardex_report(self):

        # Ejecutar la lógica para abrir el reporte Kardex directamente
        action = (
            self.env["stock.kardex.report.wiz"]
            .with_context(
                default_product=self.product_id.id,
                default_location=self.location_id.id,
                default_date_to=datetime.combine(self.date, datetime.min.time())
                + timedelta(hours=5),
                default_company_id=self.company_id.id,
                # Agregar otros datos necesarios aquí
            )
            .open_table()
        )  # Este es el método que generaría el reporte
        return action
