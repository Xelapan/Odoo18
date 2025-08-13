# visor de ajustes de inventario
from datetime import datetime, time, timedelta

from odoo import models, fields, api, _
from odoo.http import request


class StockInventoryAdjustment(models.Model):
    _name = "stock.inventory.adjustment"
    _description = "Visor de Ajustes de Inventario Consolidado"

    date = fields.Date(string="Fecha", required=True, store=True)
    ref = fields.Char(string="Referencia", required=True, store=True)
    location_id = fields.Many2one(
        "stock.location", string="Ubicación", required=True, store=True
    )
    cost = fields.Float(string="Costo", required=True, store=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
        store=True,
    )
    session_identifier = fields.Char(
        string="Session Token", required=True
    )  # Campo para el token de sesión
    created_by = fields.Many2one(
        "res.users", string="Creado por", default=lambda self: self.env.user, store=True
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockInventoryAdjustment, self).default_get(fields_list)
        session_id = request.session.sid
        if session_id:
            defaults["session_identifier"] = session_id
        return defaults

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super(StockInventoryAdjustment, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == "list":  # Aseguramos que solo aplica a la vista tree
            session_id = request.session.sid
            if session_id:
                res["arch"] = res["arch"].replace(
                    "<tree>",
                    f'<tree domain="[(&#39;session_identifier&#39;, &#39;=&#39;, {session_id})]">',
                )
        return res

    def open_adjustment_inventory_report(
        self,
        date_to,
        date_starte,
        location_id,
        product_id,
        company_id,
        session_identifiere,
    ):
        date_start = False
        if date_starte:
            date_start = datetime.combine(self.date_end, time(23, 59, 59)) + timedelta(
                hours=6
            )

        session_identifier = session_identifiere  # Identificador de sesión
        self.env["stock.inventory.adjustment"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        # Configurar el dominio para filtrar los movimientos de stock en el rango de fechas
        domain = [
            # ('date', '>=', date_from),
            ("date", "<=", date_to),
            ("state", "=", "done"),
            ("company_id", "=", company_id.id),
            ("move_id.picking_type_id", "=", False),
        ]

        if product_id:
            domain.append(("product_id", "=", product_id.id))
        if date_starte:
            domain.append(("date", ">=", date_start))
        if location_id:
            domain += [
                "|",
                ("location_id", "=", location_id.id),
                ("location_dest_id", "=", location_id.id),
            ]
        # Buscar los movimientos de stock
        stock_moves = self.env["stock.move.line"].search(domain, order="reference asc")
        # Crear un diccionario para consolidar la información por producto
        product_data = {}
        for move in stock_moves:
            product_id = move.product_id.id
            # Verificar si tanto product_id como reference están en product_data
            if product_id not in product_data:
                product_data[product_id] = {}

            if move.reference not in product_data[product_id]:  # reference es un string
                product_data[product_id][move.reference] = {
                    "date": move.date,
                    "created_by": move.create_uid.id,
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

            if location_id:
                if move.location_dest_id.id == location_id.id:
                    # Si la ubicación de destino es la seleccionada, es una entrada
                    product_data[product_id][move.reference][
                        "total_quantity"
                    ] += move.qty_done
                    product_data[product_id][move.reference][
                        "total_cost"
                    ] += value  # move.qty_done * cost
                    if move.picking_type_id.code != "internal":
                        product_data[product_id][move.reference][
                            "calc_total_quantity"
                        ] += move.qty_done
                        product_data[product_id][move.reference][
                            "calc_total_cost"
                        ] += value  # move.qty_done * cost
                        product_data[product_id][move.reference]["unit_cost"] = cost
                elif move.location_id.id == location_id.id:
                    # Si la ubicación de origen es la seleccionada, es una salida
                    product_data[product_id][move.reference][
                        "total_quantity"
                    ] -= move.qty_done
                    product_data[product_id][move.reference][
                        "total_cost"
                    ] -= value  # move.qty_done * cost
                    if move.picking_type_id.code != "internal":
                        product_data[product_id][move.reference][
                            "calc_total_quantity"
                        ] -= move.qty_done
                        product_data[product_id][move.reference][
                            "calc_total_cost"
                        ] -= value  # move.qty_done * cost
                        product_data[product_id][move.reference]["unit_cost"] = cost
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
                    product_data[product_id]["total_quantity"] -= move.qty_done
                    product_data[product_id][
                        "total_cost"
                    ] -= value  # move.qty_done * cost
                    if move.picking_type_id.code != "internal":
                        product_data[product_id]["calc_total_quantity"] -= move.qty_done
                        product_data[product_id][
                            "calc_total_cost"
                        ] -= value  # move.qty_done * cost
                        product_data[product_id]["unit_cost"] = cost
                else:
                    # Movimiento general
                    product_data[product_id]["total_quantity"] += move.qty_done
                    product_data[product_id][
                        "total_cost"
                    ] += value  # move.qty_done * cost
                    if move.picking_type_id.code != "internal":
                        product_data[product_id]["calc_total_quantity"] += move.qty_done
                        product_data[product_id][
                            "calc_total_cost"
                        ] += value  # move.qty_done * cost
                        product_data[product_id]["unit_cost"] = cost

        # Crear los registros consolidados en stock.inventory.adjustment
        last_cost = 0
        costos = []
        for product_id, references in product_data.items():
            for thReference, data in references.items():
                thInventory = None
                thInventory = self.env["stock.inventory.adjustment"].search(
                    [
                        ("ref", "=", thReference),
                        ("session_identifier", "=", session_identifier),
                    ],
                    order="id desc",
                    limit=1,
                )
                if not thInventory:
                    valuation = self.env["stock.valuation.layer"].search(
                        [
                            ("product_id", "=", product_id),
                            ("reference", "=", thReference),
                        ],
                        order="create_date desc",
                        limit=1,
                    )  # , ('create_date', '<=', data['date'])
                    thValue = 0
                    thQty = 0
                    for val in valuation:
                        thValue += val.value
                        thQty += val.quantity
                    last_cost = thValue / thQty if thValue != 0 and thQty != 0 else 0
                    self.env["stock.inventory.adjustment"].create(
                        {
                            "date": data["date"],  # Fecha del reporte
                            "ref": thReference,
                            "location_id": location_id.id if location_id else False,
                            "cost": data["total_quantity"]
                            * last_cost,  # (data['calc_total_cost'] / data['calc_total_quantity']),
                            "session_identifier": session_identifier,
                            "created_by": data["created_by"],
                            "company_id": company_id.id,
                        }
                    )
                else:
                    valuation = self.env["stock.valuation.layer"].search(
                        [
                            ("product_id", "=", product_id),
                            ("reference", "=", thReference),
                        ],
                        order="create_date desc",
                        limit=1,
                    )  # , ('create_date', '<=', data['date'])
                    thValue = 0
                    thQty = 0
                    for val in valuation:
                        thValue += val.value
                        thQty += val.quantity
                    last_cost = thValue / thQty if thValue != 0 and thQty != 0 else 0
                    thCost = data["total_quantity"] * last_cost
                    thCost += thInventory.cost
                    thInventory.cost = thCost
                costos.append(data["total_quantity"] * last_cost)
        self.env["stock.inventory.adjustment"].search(
            [("session_identifier", "=", request.session.sid)]
        )
        tree_view_id = self.env.ref(
            "stock_kardex_report.view_stock_inventory_adjustment_tree"
        ).id
        action = {
            "type": "ir.actions.act_window",
            "views": [(tree_view_id, "list")],
            "view_id": tree_view_id,
            "view_mode": "list",
            "name": _("Historial Ajustes Inventario"),
            "res_model": "stock.inventory.adjustment",
            "domain": [("session_identifier", "=", request.session.sid)],
            "context": {
                "search_default_session_identifier": request.session.sid
            },  # Contexto para filtrar
        }
        return action

    def action_open_stock_inventory_adjustment_line_report(self):
        # Ejecutar la lógica para abrir el reporte Kardex directamente
        action = (
            self.env["stock.inventory.adjustment.line.wizard"]
            .with_context(
                default_location=self.location_id.id,
                default_ref=self.ref,
                default_company_id=self.company_id.id,
                default_date_to=datetime.combine(self.date, datetime.min.time())
                + timedelta(hours=6),
                default_session_identifier=self.session_identifier,
            )
            .open_table_adjustment()
        )
        return action


class StockInventoryAdjustmentLine(models.Model):
    _name = "stock.inventory.adjustment.line"
    _description = "Detalle de Ajustes de Inventario Consolidado"

    account_move_id = fields.Many2one(
        "account.move",
        readonly=True,
        string="Movimiento Contable",
        compute="_compute_account_move_id",
    )
    stock_move_line_id = fields.Many2one(
        "stock.move.line", string="Movimiento de Stock", required=True
    )
    product_id = fields.Many2one("product.product", string="Producto", store=True)
    product_uom_id = fields.Many2one("uom.uom", string="Unidad de Medida", store=True)
    qty_done = fields.Float(string="Cantidad", store=True)
    location_id = fields.Many2one("stock.location", string="Ubicación", store=True)
    location_dest_id = fields.Many2one("stock.location", string="Destino", store=True)
    tipo_mov = fields.Char(string="Tipo Movimiento", store=True)
    date = fields.Datetime(readonly=True, string="Fecha")
    origin = fields.Char(
        readonly=True, string="Movimiento", related="stock_move_line_id.move_id.origin"
    )
    reference = fields.Char(readonly=True, string="Referencia")
    balance = fields.Float(readonly=True, string="Saldo")
    user_id = fields.Many2one("res.users", readonly=True, string="Usuario")
    update_at = fields.Datetime(readonly=True, string="Fecha Modificacion")
    cost = fields.Float("Costo", readonly=True)
    total_cost = fields.Float("Costo Total", readonly=True)
    session_identifier = fields.Char(
        string="Session Token"
    )  # Campo para el token de sesión
    company_id = fields.Many2one("res.company", string="Compañía", store=True)

    @api.depends("stock_move_line_id.move_id")
    def _compute_account_move_id(self):
        for record in self:
            thSVL = self.env["stock.valuation.layer"].search(
                [
                    ("stock_move_id", "=", record.stock_move_line_id.move_id.id),
                    ("company_id", "=", record.company_id.id),
                ],
                order="create_date desc",
                limit=1,
            )
            record.account_move_id = thSVL.account_move_id if thSVL else False
            # if thSVL:
            #     for svl in thSVL:
            #         record.account_move_id = svl.account_move_id
        auxa = 0
