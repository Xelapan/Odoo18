import datetime
import logging

from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import html2text

from odoo.tools import groupby


class MrpProduction(models.Model):
    _inherit = "mrp.production"
    product_id = fields.Many2one(
        "product.product",
        "Product",
        domain="""[
                ('type', 'in', ['product', 'consu']),
                '|',
                    ('company_id', '=', False),
                    ('company_id', '=', company_id),
                ('bom_ids', '!=', False)
            ]
            """,
        compute="_compute_product_id",
        store=True,
        copy=True,
        precompute=True,
        readonly=True,
        required=True,
        check_company=True,
        states={"draft": [("readonly", False)]},
    )
    requisiciones = fields.One2many(
        "material.purchase.requisition",
        "orden_produccion",
        string="Requisiciones",
        store=True,
    )
    ventas = fields.One2many(
        "sale.order", "orden_produccion", string="Ventas", store=True
    )
    mesa_servicio = fields.Many2one(
        "x_mesa_servicio",
        string="Mesa de Servicio",
        store=True,
        domain="[('x_tipo_solicitud_id', '=', 5), ('x_fabricacion', '=', False),('x_ticket_odoo','=', False),('x_estado','not in',[5, 6, 7])]",
    )
    ticket = fields.Integer(
        string="Ticket", readonly=True, store=True, related="mesa_servicio.x_solicitud"
    )
    asignado = fields.Many2one(
        "hr.employee",
        string="Asignado",
        store=True,
        related="mesa_servicio.x_colaborador_id",
        readonly=True,
    )
    team_id = fields.Many2one(
        "helpdesk.team",
        string="Equipo",
        compute="_compute_ticket",
        readonly=True,
        store=True,
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Cuenta Analítica",
        related="mesa_servicio.x_lugar_ubicacion",
        store=True,
        readonly=True,
    )
    costo_total = fields.Float(
        string="Costo Total", compute="_compute_costo_total", store=True
    )
    proyecto = fields.Many2one(
        "project.project",
        string="Proyecto",
        store=True,
        related="mesa_servicio.x_proyecto",
        readonly=True,
    )
    servicio_fabricacion = fields.Float(string="Servicio Fabricación", store=True)
    costo_materiales = fields.Float(string="Costo Materiales", store=True)
    id_odoo_13 = fields.Integer(string="ID Odoo 13", store=True)
    unica_requisicion = fields.Boolean(
        string="Unica Requisición",
        store=True,
        readonly=True,
        default=False,
        help="Si se marca esta opción, se creará una sola requisición de materiales para la orden de producción",
    )
    multi_requisicion_materiales = fields.Boolean(
        string="Multi Requisición Materiales",
        store=True,
        readonly=True,
        default=False,
        help="Si se marca esta opción, es porque la orden de produccion tiene mas de una requisicion con materiales",
    )
    exportar = fields.Boolean(
        string="Exportar",
        store=True,
        readonly=True,
        default=False,
        help="Si se marca esta opción, es porque la orden de produccion se exportará a Odoo 13",
    )
    transaccion_proceso = fields.Boolean(
        string="Transaccion en Proceso", store=True, default=False
    )
    exportado_13 = fields.Datetime(string="ExpoOdoo 13", store=True)

    @api.depends("move_raw_ids")
    @api.onchange("move_raw_ids")
    def _compute_costo_total(self):
        for record in self:
            if record.product_id and record.bom_id:
                record.costo_materiales = sum(
                    [
                        lines.lst_price * lines.product_uom_qty
                        for lines in record.move_raw_ids
                    ]
                )
                thManoObra = self.env["ir.config_parameter"].search(
                    [("key", "=", "Porcentaje Mano de Obra")], order="id desc", limit=1
                )
                if thManoObra:
                    mano_de_obra = record.costo_materiales * (
                        float(thManoObra.value) / 100
                    )
                else:
                    mano_de_obra = 0

                thMargenGanancia = self.env["ir.config_parameter"].search(
                    [("key", "=", "Margen Ganancia")], order="id desc", limit=1
                )
                if thMargenGanancia:
                    margen_ganancia = mano_de_obra * (
                        float(thMargenGanancia.value) / 100
                    )
                else:
                    margen_ganancia = 0

                record.servicio_fabricacion = mano_de_obra + margen_ganancia
                record.costo_total = (
                    sum(
                        [
                            line.lst_price * line.product_uom_qty
                            for line in record.move_raw_ids
                        ]
                    )
                    + record.servicio_fabricacion
                )
                # if record.ticket > 0 and record.id:
                auxa2 = 0
                auxa = 0
                try:
                    auxa = int(record.id)
                    auxa2 = int(record.ticket)
                except Exception as e:
                    logging.warning(
                        "Error al calcular el costo total de la orden de produccion "
                        + str(e)
                    )
                if len(record.requisiciones) > 0 and auxa2 != 0 and auxa != 0:
                    thLinesReq = self.env["material.purchase.requisition.line"].search(
                        [
                            (
                                "requisition_id.state",
                                "in",
                                ["ir_approve", "approve", "stock", "receive"],
                            ),
                            ("requisition_id.x_no_ticket", "=", auxa2),
                            ("product_id.type", "=", "service"),
                            ("requisition_id.orden_produccion.id", "=", auxa),
                        ]
                    )
                    # if any(line.product_id.type == 'service' for line in rec.requisition_line_ids):
                    record.costo_total += (
                        sum(line.x_monto for line in thLinesReq) * 1.12
                    )

    @api.depends("mesa_servicio")
    @api.onchange("mesa_servicio")
    def _compute_ticket(self):
        for record in self:
            record.mesa_servicio.write({"x_fabricacion": record.id})
            thMesa = self.env["x_mesa_servicio"].search(
                [
                    ("id", "!=", record.mesa_servicio.id),
                    ("x_tipo_solicitud_id", "=", 5),
                    ("x_fabricacion", "=", record.id),
                    ("x_ticket_odoo", "=", False),
                ]
            )
            for mesa in thMesa:
                mesa.write({"x_fabricacion": False})
            thEquipo = self.env["helpdesk.team"].search(
                [("x_area.id", "=", record.asignado.x_area.id)], limit=1
            )
            if thEquipo:
                record.write({"team_id": thEquipo.id})

    @api.depends("mesa_servicio")
    @api.onchange("mesa_servicio")
    def _compute_bodegas(self):
        for record in self:
            if record.mesa_servicio:
                if record.proyecto:
                    record.write(
                        {
                            "picking_type_id": record.proyecto.custom_picking_type_id.warehouse_id.manu_type_id.id,
                            "location_src_id": record.proyecto.custom_picking_type_id.warehouse_id.manu_type_id.default_location_src_id.id,
                            "location_dest_id": record.proyecto.custom_picking_type_id.warehouse_id.manu_type_id.default_location_dest_id.id,
                        }
                    )
                record.write(
                    {
                        "origin": "Ticket "
                        + str(record.mesa_servicio.x_solicitud)
                        + " - "
                        + record.mesa_servicio.x_titulo,
                    }
                )

    def action_confirm(self):
        res = super(MrpProduction, self).action_confirm()
        for record in self:
            if record.state == "confirmed" and record.ticket != 0:
                if record.proyecto:
                    thTipoOperacion = record.proyecto.custom_picking_type_id.id
                    thOrigen = (
                        record.proyecto.custom_picking_type_id.default_location_src_id.id
                    )
                    thDestino = (
                        record.proyecto.custom_picking_type_id.default_location_dest_id.id
                    )
                else:
                    thTipoOperacion = 47
                    thOrigen = 56
                    thDestino = 24
                if len(record.requisiciones) == 0:
                    requisicion = self.env["material.purchase.requisition"].create(
                        {
                            "employee_id": record.asignado.id,
                            "department_id": record.asignado.sudo().department_id.id,
                            "analytic_account_id": record.analytic_account_id.id,
                            "requisiton_responsible_id": record.asignado.parent_id.id,
                            "orden_produccion": record.id,
                            "x_no_ticket": record.ticket,
                            "company_id": record.company_id.id,
                            "request_date": datetime.date(datetime.now()),
                            "custom_picking_type_id": thTipoOperacion,
                            "location_id": thOrigen,
                            "dest_location_id": thDestino,
                            "requisition_line_ids": [
                                (
                                    0,
                                    0,
                                    {
                                        "requisition_type": "internal",
                                        "product_id": line.product_id.id,
                                        "description": line.product_id.name,
                                        "qty": line.product_uom_qty,
                                        "uom": line.product_uom.id,
                                        "x_price": line.lst_price,
                                    },
                                )
                                for line in record.move_raw_ids
                            ],
                            "x_costo_total": record.costo_total,  # sum([line.lst_price * line.product_uom_qty for line in record.move_raw_ids]),
                            "reason": "Ticket No.: "
                            + str(record.mesa_servicio.x_solicitud)
                            + "\nDescripción: "
                            + str(
                                html2text.html2text(record.mesa_servicio.x_descripcion)
                            ),
                        }
                    )
                    requisicion.onchange_custom_picking_type_id()
                    requisicion.requisition_confirm()
                else:
                    for requisicion in record.requisiciones:
                        if requisicion.state == "dept_confirm":
                            requisicion.write(
                                {
                                    "custom_picking_type_id": thTipoOperacion,
                                    "location_id": thOrigen,
                                    "dest_location_id": thDestino,
                                    "x_costo_total": sum(
                                        [
                                            line.x_price * line.qty
                                            for line in record.requisicion.requisition_line_ids
                                        ]
                                    ),
                                }
                            )
                            requisicion.onchange_custom_picking_type_id()

    def _compute_ventas(self):
        for record in self:
            logging.warning("Entrando a compute ventas")
            if record.ventas.invoice_status == "invoiced":
                raise UserError(
                    "Ya no es permitido crear requisiciones, la orden de produccion ya tiene una factura asociada"
                )
            else:
                thMontoMaximo = self.env["ir.config_parameter"].search(
                    [("key", "=", "valor maximo cotizacion")], order="id desc", limit=1
                )
                if len(record.requisiciones) == 1 and len(record.ventas) > 0:
                    raise UserError(
                        "La orden de fabricacion, tiene una venta. Si necesita agregar mas items a la fabricacion cree una nueva requisicion, caso contrario borre el pedido de venta"
                    )
                if len(record.ventas) > 0 and len(record.requisiciones) > 1:
                    logging.warning(
                        "Entrando a compute ventas con requisiciones y con ventas"
                    )
                    # Esto debe irse para requisiciones

                    for sale in record.ventas:
                        if sale.state == "sale":
                            thSale = self.env["sale.order.cancel"].create(
                                {
                                    "order_id": sale.id,
                                }
                            )
                            thSale.with_context(
                                {"disable_cancel_warning": True}
                            ).action_cancel()
                            sale.action_draft()
                            # self.env.cr.commit()
                        for order_line in sale.order_line:
                            # record._compute_costo_total()
                            order_line.write(
                                {
                                    "product_uom_qty": record.product_qty,
                                    "qty_delivered": 1,
                                    "product_uom": record.product_uom_id.id,
                                    "price_unit": record.costo_total
                                    / order_line.product_uom_qty,
                                }
                            )
                else:
                    logging.warning(
                        "Entrando a compute ventas sin requisiciones o sin ventas"
                    )
                    thPrecio = (
                        record.costo_total
                    )  # sum([lines.monto for lines in record.move_raw_ids])
                    logging.warning("Record: " + str(record.id))
                    logging.warning(
                        "Record analicitc: " + str(record.analytic_account_id)
                    )
                    logging.warning("Record model: " + str(record._name))
                    logging.warning(
                        "Record partner: "
                        + str(record.analytic_account_id.partner_id.id)
                    )
                    record.write(
                        {
                            "ventas": [
                                (
                                    0,
                                    0,
                                    {
                                        "partner_id": record.analytic_account_id.partner_id.id,
                                        "user_id": self.env.user.id,
                                        "company_id": record.company_id.id,
                                        "analytic_account_id": record.analytic_account_id.id,
                                        "warehouse_id": 2,
                                        "team_id": 1,
                                        "date_order": datetime.now(),
                                        "origin": record.name,
                                        "state": "draft",
                                        "orden_produccion": record.id,
                                        "order_line": [
                                            (
                                                0,
                                                0,
                                                {
                                                    "product_id": record.product_id.id,
                                                    "product_uom_qty": record.product_qty,
                                                    "qty_delivered": 1,
                                                    "product_uom": record.product_uom_id.id,
                                                    "price_unit": thPrecio
                                                    / record.product_qty,
                                                    "price_subtotal": thPrecio,
                                                },
                                            )
                                        ],
                                    },
                                )
                            ]
                        }
                    )
                if record.mesa_servicio:
                    # if estado_original == 'done':
                    #     record.ventas.action_confirm()
                    #     thFabricar = self.env["mrp.consumption.warning"].create({
                    #         'mrp_production_ids': [(4, record.id)],
                    #     })
                    #     try:
                    #         thFabricar.action_confirm()
                    #     except Exception as e:
                    #         raise UserError('Error al confirmar fabricacion '+str(e))
                    #     record.sincroniza_fabricacion('Odoo 13', record)
                    # elif record.mesa_servicio.x_proyecto.presupuestado:
                    if record.mesa_servicio.x_proyecto.presupuestado:
                        record.ventas.action_confirm()
                    else:
                        thPrecio = (
                            record.costo_total
                        )  # sum([lines.monto for lines in record.move_raw_ids])
                        if thPrecio <= float(thMontoMaximo.value):
                            record.ventas.action_confirm()
                            # record.write({
                            #     'ventas': [(0, 0, {
                            #         'state': 'sale',
                            #     })],
                            # })
                        else:
                            base_web = "http://www.dimasagt.com"
                            data = (
                                self.env["sale.order"]
                                .browse(record.ventas[0].id)
                                .action_preview_sale_order()
                            )
                            url = data["url"]
                            proyecto = self.env["project.project"].search(
                                [
                                    (
                                        "analytic_account_id.id",
                                        "=",
                                        record.analytic_account_id.id,
                                    )
                                ],
                                order="id asc",
                                limit=1,
                            )
                            if not proyecto:
                                raise UserError(
                                    "La cuenta analitica "
                                    + record.analytic_account_id.name
                                    + " no tiene un proyecto asignado"
                                )
                            else:
                                empleado = self.env["hr.employee"].search(
                                    [
                                        (
                                            "work_contact_id",
                                            "=",
                                            proyecto.x_autorizador.id,
                                        )
                                    ],
                                    order="id asc",
                                    limit=1,
                                )
                            if not empleado:
                                raise UserError(
                                    "El contacto "
                                    + proyecto.x_autorizador.name
                                    + " autorizador de "
                                    + record.analytic_account_id.name
                                    + " no tiene un empleado relacionado"
                                )
                            else:
                                if not empleado.mobile_phone:
                                    raise UserError(
                                        "El empleado "
                                        + empleado.name
                                        + " no tiene registrado un numero de telefono corporativo"
                                    )
                                else:
                                    idchat = "+502" + empleado.mobile_phone
                                    # raise UserError('Datos: '+str(empleado.name)+' - '+str(record.id)+' - '+str(sale_order.x_ticket.x_ticket)+' - '+str(record.analytic_account_id.name)+' fin ')
                                    mensaje = (
                                        "AUTORIZACION REQUERIDA Saludos "
                                        + empleado.name
                                        + " se requiere autorización para la fabricación del ticket "
                                        + str(record.ticket)
                                        + " la tarea a realizar es "
                                        + record.mesa_servicio.x_titulo
                                        + " en "
                                        + record.analytic_account_id.name
                                    )
                                    urlimagen = False
                                    record.requisiciones.EnviarMensaje(
                                        idchat, mensaje, urlimagen
                                    )  # Llama al método EnviarMensaje de la instancia whatsapp_obj
                                    mensaje = str(base_web) + str(url)
                                    record.requisiciones.EnviarMensaje(
                                        idchat, mensaje, urlimagen
                                    )  # Llama al método EnviarMensaje de la instancia whatsapp_obj
                                    record.ventas[0].write(
                                        {
                                            "state": "sent",
                                        }
                                    )

    def button_mark_done(self):
        # si el pedido de venta que es one2many esta en estado sale entonces se marca como done
        for record in self:
            if record.ventas.state == "sale":
                if any(
                    line.state in ["draft", "dept_confirm", "ir_approve", "approve"]
                    for line in record.requisiciones
                ):
                    raise UserError(
                        "No se puede marcar como terminado si no se ha aprobado la requisicion de materiales"
                    )
                else:
                    botton = super(MrpProduction, record).button_mark_done()
                    # Sincroniza la fabricacion 02 05 2024
                    # if record.state == 'done':
                    #     if not record.id_odoo_13:
                    #         logging.warning('Llamada al proceso de sincronizacion de fabricacion desde boton hecho')
                    #         record.sincroniza_fabricacion('Odoo 13', record)
                    return botton
            else:
                raise UserError(
                    "No se puede marcar como terminado si no hay un pedio de venta confirmado"
                )

    @api.depends(
        "company_id",
        "bom_id",
        "product_id",
        "product_qty",
        "product_uom_id",
        "location_src_id",
        "date_planned_start",
    )
    def _compute_move_raw_ids(self):
        super(MrpProduction, self)._compute_move_raw_ids()
        if self.proyecto:
            for record in self:
                if (
                    record.proyecto.location_dest_id
                    and record.proyecto.custom_picking_type_id
                ):
                    # Buscamos el almacen
                    thAlmacen = self.env["stock.warehouse"].search(
                        [
                            ("company_id", "=", record.company_id.id),
                            ("lot_stock_id", "=", record.proyecto.location_dest_id.id),
                        ],
                        limit=1,
                        order="id asc",
                    )
                    if thAlmacen:
                        record.move_raw_ids.write(
                            {
                                "location_id": record.proyecto.location_dest_id.id,
                                "warehouse_id": thAlmacen.id,
                                "picking_type_id": thAlmacen.manu_type_id.id,
                            }
                        )

    @api.depends("state")
    def set_return_confirmed(self):
        for record in self:
            if record.state == "done":
                for line in record.move_raw_ids:
                    if line.state == "done":
                        line.write(
                            {
                                "state": "confirmed",
                            }
                        )
                moves_in_raw = self.env["stock.move"].search(
                    [("raw_material_production_id", "=", record.id)]
                )
                for line in moves_in_raw:
                    if line.state == "done":
                        line.write(
                            {
                                "state": "confirmed",
                            }
                        )
                for line in record.move_finished_ids:
                    if line.state == "done":
                        line.write(
                            {
                                "state": "confirmed",
                            }
                        )
                record.write(
                    {
                        "state": "to_close",
                    }
                )

    @api.depends("state")
    def set_to_draft(self):
        for record in self:
            if record.state not in ["done"]:
                for line in record.move_raw_ids:
                    if line.state == "done":
                        raise UserError(
                            "No se puede regresar a borrador si la orden de produccion tiene movimientos de inventario en estado hecho"
                        )
                moves_in_raw = self.env["stock.move"].search(
                    [("raw_material_production_id", "=", record.id)]
                )
                for line in moves_in_raw:
                    if line.state == "done":
                        raise UserError(
                            "No se puede regresar a borrador si la orden de produccion tiene movimientos de inventario en estado hecho"
                        )
                for line in record.move_finished_ids:
                    if line.state == "done":
                        raise UserError(
                            "No se puede regresar a borrador si la orden de produccion tiene movimientos de inventario (productos finalizados) en estado hecho"
                        )
                if len(record.requisiciones) > 0 and record.unica_requisicion:
                    raise UserError(
                        "No se puede regresar a borrador si ya tiene requisicion de materiales"
                    )
                elif len(record.ventas) > 0 and record.unica_requisicion:
                    raise UserError(
                        "No se puede regresar a borrador si ya tiene pedido de venta"
                    )
                else:
                    record.write(
                        {
                            "state": "draft",
                        }
                    )
                    record.do_unreserve()
                    moves_in_raw = self.env["stock.move"].search(
                        [("raw_material_production_id", "=", record.id)]
                    )
                    for line in moves_in_raw:
                        if line.state == "done":
                            raise UserError(
                                "No se puede regresar a borrador si la orden de produccion tiene movimientos de inventario en estado hecho"
                            )
                        logging.warning("Antes de borrador" + " " + str(line.state))
                        line.write(
                            {
                                "state": "draft",
                            }
                        )
                        logging.warning(
                            "Movimiento de inventario en estado borrador"
                            + " "
                            + str(line.state)
                        )
                    for line in record.move_finished_ids:
                        if line.state == "done":
                            raise UserError(
                                "No se puede regresar a borrador si la orden de produccion tiene movimientos de inventario en estado hecho"
                            )
                        line.write(
                            {
                                "state": "draft",
                            }
                        )
            else:
                raise UserError("Unicamente para ordenes que no esten en estado hecho")

    # @api.onchange('state')
    # @api.depends('state')
    # def _onchange_state_done(self):
    #     for record in self:
    #         if record.state == 'done':
    #             if not record.id_odoo_13:
    #                 logging.warning('Llamada al proceso de sincronizacion de fabricacion')
    #                 record.sincroniza_fabricacion('Odoo 13', record)

    def sincroniza_fabricacion(self, odoo_externo, record):
        # idchat = '+120363179270802732@g.us'
        idchat = "+50250205026"
        urlimagen = False
        logging.warning(
            "Entrando al proceso de sincronizacion de fabricacion " + str(self)
        )
        # odoo_execute_kw = self.env['datalayer']._eval_context_odoo2odoox(odoo_externo).get('odoo_execute_kw')

        odoo_execute_kw4 = 1
        if odoo_execute_kw4 == 1:
            # idchat = '+120363179270802732@g.us'
            idchat = "+50250205026"
            urlimagen = False

            thProduction = self.env["datalayer"].odoo_execute_kw(
                odoo_externo,
                "mrp.production",
                "search_read",
                [("x_id_odoo_16", "=", record.id)],
                fields=[
                    "id",
                    "product_id",
                    "qty_produced",
                    "product_uom_id",
                    "name",
                    "product_qty",
                ],
            )

            requisiciones_ids = [linea.id for linea in record.requisiciones]
            logging.warning(
                "------------------------------> Dentro de Fabricacion "
                + str(len(thProduction))
                + " requisiciones "
                + str(
                    self.env["material.purchase.requisition"].search_count(
                        [
                            ("orden_produccion", "=", record.id),
                            ("x_id_odoo_13", "!=", False),
                        ]
                    )
                )
                + " odoo13req "
                + str(
                    len(
                        self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "material.purchase.requisition",
                            "search_read",
                            [("x_id_odoo_16", "in", requisiciones_ids)],
                            fields=["id"],
                        )
                    )
                    > 0
                )
            )
            if thProduction:
                logging.warning(
                    "Fabricaciones encontrada en Odoo 13 " + str(len(thProduction))
                )

            # Aqui ya se sincronizo y solamente tiene una requisicion
            if (
                len(thProduction) > 0
                and self.env["material.purchase.requisition"].search_count(
                    [("orden_produccion", "=", record.id)]
                )
                == 1
            ):
                logging.warning(
                    "Ya se sincronizo la fabricacion y tiene una requisicion solamente"
                )
                mensaje = (
                    "Error - Ticket "
                    + str(record.ticket)
                    + " - ya tiene una orden de fabricacion en Odoo 13 debe borrarla. *¡No se realizó sincronización!.*"
                )
                self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                raise UserError(
                    "La orden de produccion " + str(record.id) + " ya existe en Odoo 13"
                )

            # Aqui no ha sincronizado la fabricacion y tiene requisiciones sincronizadas
            elif len(thProduction) == 0 and (
                self.env["material.purchase.requisition"].search_count(
                    [
                        ("orden_produccion", "=", record.id),
                        ("x_id_odoo_13", "!=", False),
                    ]
                )
                > 0
                or len(
                    self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "material.purchase.requisition",
                        "search_read",
                        [("x_id_odoo_16", "in", requisiciones_ids)],
                        fields=["id"],
                    )
                )
                > 0
            ):
                thAuxProducto_p = None
                thAuxProducto = None
                logging.warning(
                    "No se sincronizo la fabricacion y tiene requisiciones sincronizadas"
                )
                almacen_p = self.env["datalayer"].odoo_execute_kw(
                    odoo_externo,
                    "stock.warehouse",
                    "search_read",
                    [
                        ("name", "=", record.picking_type_id.warehouse_id.name),
                        ("code", "=", record.picking_type_id.warehouse_id.code),
                        ("company_id", "=", 1),
                    ],
                    fields=["id", "out_type_id"],
                )
                if not almacen_p:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - el almacen "
                        + str(record.picking_type_id.warehouse_id.name)
                        + " no existe en Odoo 13. *¡No se realizó sincronización!.*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "El almacen "
                        + str(record.picking_type_id.warehouse_id.name)
                        + " no existe en Odoo 13"
                    )
                # Esta condicion es para la bodega de ordenes en proceso de odoo13
                # Para que origen y destino sea B01/BD Central Dimasa
                if record.picking_type_id.id == 18:
                    tipo_operacion_p = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "stock.picking.type",
                        "search_read",
                        [("id", "=", 8)],
                        fields=[
                            "id",
                            "name",
                            "default_location_src_id",
                            "default_location_dest_id",
                        ],
                    )
                else:  # Caso contrario tome la configuracion del tipo de operacion de odoo13 que deberia ser igual a odoo16
                    tipo_operacion_p = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "stock.picking.type",
                        "search_read",
                        [
                            ("name", "=", record.picking_type_id.name),
                            ("warehouse_id", "=", almacen_p[0]["id"]),
                        ],
                        fields=[
                            "id",
                            "name",
                            "default_location_src_id",
                            "default_location_dest_id",
                        ],
                    )
                if not tipo_operacion_p:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - el tipo de operacion "
                        + str(record.picking_type_id.name)
                        + " no existe en Odoo 13 debe borrarla. *¡No se realizó sincronización!.*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "El tipo de operacion "
                        + str(record.picking_type_id.name)
                        + " no existe en Odoo 13"
                    )
                if (
                    record.picking_type_id.id == 18
                ):  # Aca cuando busque el tipo de operacion Central Dimasa nos de origen y destino B01/BD Central Dimasa
                    bodega_origen_p = tipo_operacion_p[0]["default_location_dest_id"][0]
                else:  # Aca caso contrario nos de las bodegas del tipo de operacion que deberian ser igual en odoo 13 y odoo 16
                    bodega_origen_p = tipo_operacion_p[0]["default_location_src_id"][0]
                if not bodega_origen_p:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - La bodega de origen del tipo de operacion de fabricacion en Odoo 13 no esta configurada, por favor revise que sea "
                        + record.location_id.name
                        + " *¡No se realizó sincronización!.*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "La bodega de origen no esta bien configurada en el tipo de operacion de fabricacion en Odoo 13"
                    )
                bodega_destino_p = tipo_operacion_p[0]["default_location_dest_id"][0]
                if not bodega_destino_p:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - La bodega destino del tipo de operacion de fabricacion en Odoo 13 no esta configurada, por favor revise que sea "
                        + record.location_dest_id.name
                        + " *¡No se realizó sincronización!.*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "La bodega de origen no esta bien configurada en el tipo de operacion de fabricacion en Odoo 13"
                    )
                if record.product_id.detailed_type == "service":
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - el producto "
                        + str(record.product_id.name)
                        + " es de tipo servicio. *¡No se realizó sincronización!*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "El producto "
                        + str(record.product_id.name)
                        + " es de tipo servicio"
                    )
                idUnidadMedida_p = 0
                UnidadMedida_p = None
                UnidadMedida_p = self.env["datalayer"].odoo_execute_kw(
                    odoo_externo,
                    "uom.uom",
                    "search_read",
                    [("name", "=", record.product_uom_id.name)],
                    fields=["id"],
                )
                if not UnidadMedida_p:
                    x_UnidadMedida_p = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "ir.translation",
                        "search_read",
                        [
                            ("name", "=", "uom.uom,name"),
                            ("lang", "=", "es_GT"),
                            "|",
                            ("value", "=", record.product_uom_id.name),
                            ("src", "=", record.product_uom_id.name),
                        ],
                        fields=["res_id"],
                    )
                    UnidadMedida_p = x_UnidadMedida_p
                    idUnidadMedida_p = x_UnidadMedida_p[0]["res_id"]
                else:
                    idUnidadMedida_p = UnidadMedida_p[0]["id"]
                if not UnidadMedida_p:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - La unidad de medida "
                        + str(record.product_uom_id.name)
                        + " no existe en Odoo 13 *¡No se realizó sincronización!*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "La unidad de medida "
                        + str(record.product_uom_id.name)
                        + " no existe en Odoo 13"
                    )
                producto_p = self.env["datalayer"].odoo_execute_kw(
                    odoo_externo,
                    "product.template",
                    "search_read",
                    [("name", "=", record.product_id.name), ("company_id", "=", 1)],
                    fields=["id", "name", "categ_id"],
                )
                if producto_p:
                    for linePro in producto_p:
                        thAuxProducto_p = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "product.product",
                            "search_read",
                            [
                                ("product_tmpl_id", "=", linePro["id"]),
                                ("bom_ids", "!=", False),
                            ],
                            fields=["id", "name", "bom_ids", "categ_id"],
                        )
                        if thAuxProducto_p:
                            # raise UserError('Desde product.product'+str(thAuxProducto))
                            up_categ = {
                                "property_valuation": "real_time",
                                "property_cost_method": "average",
                            }
                            upCateg = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "product.category",
                                "write",
                                [thAuxProducto_p[0]["categ_id"][0]],
                                up_categ,
                            )
                            continue
                else:
                    producto_p = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "ir.translation",
                        "search_read",
                        [
                            ("name", "=", "product.template,name"),
                            ("lang", "=", "es_GT"),
                            ("value", "=", record.product_id.name),
                        ],
                        fields=["res_id", "name"],
                    )
                    if producto_p:
                        for linePro in producto_p:
                            logging.warning("Desde traduccion " + str(producto_p))
                            thPT = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "product.template",
                                "search_read",
                                [
                                    ("id", "=", linePro["res_id"]),
                                    ("company_id", "=", 1),
                                ],
                                fields=["id"],
                            )
                            if not thPT:
                                mensaje = (
                                    "Error - Ticket "
                                    + str(record.ticket)
                                    + " - El producto "
                                    + str(record.product_id.name)
                                    + " no existe o no tiene lista de materiales en Odoo 13 *¡No se realizó sincronización!*"
                                )
                                self.env["sale.order"].EnviarMensaje(
                                    idchat, mensaje, urlimagen
                                )
                                raise UserError(
                                    "El producto "
                                    + str(record.product_id.name)
                                    + " no existe en Odoo 13"
                                )
                            thAuxProducto_p = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "product.product",
                                "search_read",
                                [
                                    ("product_tmpl_id", "=", thPT[0]["id"]),
                                    ("bom_ids", "!=", False),
                                ],
                                fields=["id", "name", "bom_ids", "categ_id"],
                            )
                            if thAuxProducto_p:
                                # raise UserError('Desde traduccion'+str(thAuxProducto))
                                up_categ = {
                                    "property_valuation": "real_time",
                                    "property_cost_method": "average",
                                }
                                upCateg = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "product.category",
                                    "write",
                                    [thAuxProducto_p[0]["categ_id"][0]],
                                    up_categ,
                                )
                                continue
                vals_componentes = []
                if not thAuxProducto_p:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - El producto "
                        + str(record.product_id.name)
                        + " no existe o no tiene lista de materiales en Odoo 13 *¡No se realizó sincronización!*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "El producto "
                        + str(record.product_id.name)
                        + " no existe en Odoo 13"
                    )
                    # For de componentes-----------------------------
                x_bd_o = 0
                x_bd_d = 0
                bodega_origen = None
                bodega_destino = None
                aux_UnidadMedida = 0
                productos = record.move_raw_ids
                if productos:
                    productos_ordenados = sorted(
                        productos, key=lambda x: x.product_id.name
                    )
                    primera_letra = productos_ordenados[0].product_id.name[0]
                    ultima_letra = productos_ordenados[-1].product_id.name[0]

                thProducto = self.env["datalayer"].odoo_execute_kw(
                    odoo_externo,
                    "product.product",
                    "search_read",
                    [
                        ("product_tmpl_id.company_id", "=", 1),
                        ("name", ">=", primera_letra),
                        ("name", "<=", ultima_letra),
                        ("categ_id", "not in", [1, 3, 12]),
                    ],
                    fields=["id", "name", "categ_id", "valuation"],
                )

                if thProducto:
                    productos_ordenados = sorted(
                        thProducto, key=lambda x: x["categ_id"]
                    )
                    # Agrupar los productos por categ_id
                    productos_agrupados = {}
                    up_categ = {
                        "property_valuation": "real_time",
                        "property_cost_method": "average",
                    }
                    for categ_id, group in groupby(
                        productos_ordenados, key=lambda x: x["categ_id"][0]
                    ):
                        productos_agrupados[categ_id] = list(group)
                        # logging.warning('Productos agrupados '+str(productos_agrupados))
                        logging.warning("Llamando a up categ " + str(categ_id))
                        upCateg = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "product.category",
                            "write",
                            [categ_id],
                            up_categ,
                        )

                for comp in record.move_raw_ids:
                    # Bodega de componentes
                    if x_bd_o != comp.location_id.id:
                        x_bd_o = comp.location_id.id
                        bodega_origen = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "stock.location",
                            "search_read",
                            [
                                ("name", "=", comp.location_id.name),
                                (
                                    "location_id.name",
                                    "=",
                                    comp.location_id.location_id.name,
                                ),
                            ],
                            fields=["id", "name", "location_id"],
                        )
                    if not bodega_origen:
                        mensaje = (
                            "Error - Ticket "
                            + str(record.ticket)
                            + " - La bodega "
                            + str(comp.location_id.location_id.name)
                            + "/"
                            + str(comp.location_id.name)
                            + " no existe en Odoo 13. *¡No se realizó sincronización!.*"
                        )
                        self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                        raise UserError(
                            "La bodega "
                            + str(comp.location_id.location_id.name)
                            + "/"
                            + str(comp.location_id.name)
                            + " no existe en Odoo 13"
                        )
                    if x_bd_d != comp.location_dest_id.id:
                        x_bd_d = comp.location_dest_id.id
                        bodega_destino = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "stock.location",
                            "search_read",
                            [
                                ("name", "=", comp.location_dest_id.name),
                                (
                                    "location_id.name",
                                    "=",
                                    comp.location_dest_id.location_id.name,
                                ),
                            ],
                            fields=["id", "name", "location_id"],
                        )
                    if not bodega_destino:
                        mensaje = (
                            "Error - Ticket "
                            + str(record.ticket)
                            + " - La bodega "
                            + str(comp.location_dest_id.location_id.name)
                            + "/"
                            + str(comp.location_dest_id.name)
                            + " no existe en Odoo 13. *¡No se realizó sincronización!*"
                        )
                        self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                        raise UserError(
                            "La bodega "
                            + str(comp.location_dest_id.location_id.name)
                            + "/"
                            + str(comp.location_dest_id.name)
                            + " no existe en Odoo 13"
                        )
                    if aux_UnidadMedida != comp.product_uom.id:
                        idUnidadMedida = 0
                        aux_UnidadMedida = comp.product_uom.id
                        UnidadMedida = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "uom.uom",
                            "search_read",
                            [("name", "=", comp.product_uom.name)],
                            fields=["id"],
                        )
                        if not UnidadMedida:
                            UnidadMedida = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "ir.translation",
                                "search_read",
                                [
                                    ("name", "=", "uom.uom,name"),
                                    ("lang", "=", "es_GT"),
                                    "|",
                                    ("value", "=", comp.product_uom.name),
                                    ("src", "=", comp.product_uom.name),
                                ],
                                fields=["res_id"],
                            )
                            if not UnidadMedida:
                                mensaje = (
                                    "Error - Ticket "
                                    + str(record.ticket)
                                    + " - La unidad de medida "
                                    + str(comp.product_uom.name)
                                    + " no existe en Odoo 13 *¡No se realizó sincronización!*"
                                )
                                self.env["sale.order"].EnviarMensaje(
                                    idchat, mensaje, urlimagen
                                )
                                raise UserError(
                                    "La unidad de medida "
                                    + str(comp.product_uom.name)
                                    + " no existe en Odoo 13"
                                )
                            idUnidadMedida = UnidadMedida[0]["res_id"]
                        else:
                            idUnidadMedida = UnidadMedida[0]["id"]
                    if not UnidadMedida:
                        mensaje = (
                            "Error - Ticket "
                            + str(record.ticket)
                            + " - La unidad de medida "
                            + str(comp.product_uom.name)
                            + " no existe en Odoo 13 *¡No se realizó sincronización!*"
                        )
                        self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                        raise UserError(
                            "La unidad de medida "
                            + str(comp.product_uom.name)
                            + " no existe en Odoo 13"
                        )
                    # producto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.template", "search_read",
                    #                           [('name', '=', comp.product_id.name), ('company_id', '=', 1)],
                    #                           fields=["id", "name"])
                    # producto = self.env['datalayer'].odoo_execute_kw(odoo_externo, "product.product", "search_read",
                    #                                                  [('product_tmpl_id.name', '=', comp.product_id.name),
                    #                                                   ('product_tmpl_id.company_id', '=', 1)],
                    #                                                  fields=["id", "name"], limit=1, order='id desc')
                    producto = None
                    producto = [
                        line
                        for line in thProducto
                        if line["name"] == comp.product_id.name
                    ]
                    if producto:
                        for linePro in producto:
                            # thAuxProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.product", "search_read",
                            #                                 [('product_tmpl_id', '=', linePro["id"])],
                            #                                 fields=["id", "name"])
                            thAuxProducto = None
                            thAuxProducto = linePro["id"]
                            if thAuxProducto:
                                break
                    else:
                        producto = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "ir.translation",
                            "search_read",
                            [
                                ("name", "=", "product.template,name"),
                                ("lang", "=", "es_GT"),
                                ("value", "=", comp.product_id.name),
                            ],
                            fields=["res_id", "name"],
                        )
                        if producto:
                            for linePro in producto:
                                logging.warning("Desde traduccion " + str(producto))
                                # thPT = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.template", "search_read",
                                #                        [('id', '=', linePro["res_id"]), ('company_id', '=', 1)],
                                #                        fields=["id"])
                                # thAuxProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.product", "search_read",
                                #                                 [('product_tmpl_id', '=', thPT[0]["id"])],
                                #                                 fields=["id", "name"])
                                thAuxProducto_t = None
                                thAuxProducto_t = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "product.product",
                                    "search_read",
                                    [
                                        ("product_tmpl_id.id", "=", linePro["res_id"]),
                                        ("product_tmpl_id.company_id", "=", 1),
                                    ],
                                    fields=["id", "name"],
                                    limit=1,
                                    order="id desc",
                                )

                                if thAuxProducto_t:
                                    thAuxProducto = thAuxProducto_t[0]["id"]
                                    # raise UserError('Desde traduccion'+str(thAuxProducto))
                                    break
                    if not thAuxProducto:
                        mensaje = (
                            "Error - Ticket "
                            + str(record.ticket)
                            + " - El producto "
                            + str(comp.product_id.name)
                            + " no existe en Odoo 13 *¡No se realizó sincronización!*"
                        )
                        self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                        raise UserError(
                            "El producto "
                            + str(comp.product_id.name)
                            + " no existe en Odoo 13"
                        )
                    vals_componentes.append(
                        {
                            "product_id": thAuxProducto,
                            "product_uom_qty": comp.product_uom_qty,
                            "quantity_done": comp.quantity_done,
                            "product_uom": int(idUnidadMedida),
                            "location_id": bodega_origen[0]["id"],
                            "location_dest_id": bodega_destino[0]["id"],
                            #'raw_material_production_id': False,
                            #'reference': thReference,
                            #'name': thName,
                            #'display_name': thDisplayName,
                            "company_id": 1,
                        }
                    )

                vals_production = {
                    "product_id": thAuxProducto_p[0]["id"],
                    "product_qty": record.product_qty,
                    "product_uom_id": int(idUnidadMedida_p),
                    "x_id_odoo_16": record.id,
                    "x_ticket_ms": record.ticket,
                    "bom_id": thAuxProducto_p[0]["bom_ids"][0],
                    "company_id": 1,
                    "user_id": 2,
                    "picking_type_id": tipo_operacion_p[0]["id"],
                    "location_src_id": bodega_origen_p,
                    "location_dest_id": bodega_destino_p,
                }
                try:
                    new_produccion = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo, "mrp.production", "create", vals_production
                    )
                    self.env.cr.commit()
                except Exception as e:
                    # if not new_stock_move > 0:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - la orden de fabricacion no se creo correctamente en Odoo 13 *¡No se realizó sincronización!*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "La orden de fabricacion no se creo correctamente en Odoo 13 "
                        + str(e)
                    )
                thName = self.env["datalayer"].odoo_execute_kw(
                    odoo_externo,
                    "mrp.production",
                    "search_read",
                    [("id", "=", new_produccion)],
                    fields=["name"],
                )
                for componente in vals_componentes:
                    # componente.append({'raw_material_production_id': new_produccion})
                    componente["raw_material_production_id"] = new_produccion
                    componente["name"] = thName[0]["name"]

                # raise UserError(str(vals_componentes))
                try:
                    new_production_line = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo, "stock.move", "create", vals_componentes
                    )
                except Exception as e:
                    # if not new_stock_move > 0:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - los componentes la orden de fabricacion no se crearon correctamente en Odoo 13 *¡Se realizó parcialmente la sincronización!*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "Los componentes de la orden de fabricacion no se crearon correctamente en Odoo 13 "
                        + str(e)
                    )
                # except de timeout

                # record.write({'id_odoo_13': int(new_produccion)})
                # 03 04 2024 12:27:00
                record.write({"id_odoo_13": int(new_produccion)})
                self.env.cr.commit()
                try:

                    Fabricacion = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "mrp.production",
                        "action_confirm",
                        [new_produccion],
                    )
                    Fabricacion = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "mrp.production",
                        "action_assign",
                        [new_produccion],
                    )
                    vals_mpp = {
                        "company_id": 1,
                        "production_id": new_produccion,
                        "product_id": thAuxProducto_p[0]["id"],
                        "qty_producing": record.product_qty,
                        "product_uom_id": int(idUnidadMedida_p),
                        "consumption": "strict",
                    }
                    ProductProduce = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo, "mrp.product.produce", "create", vals_mpp
                    )
                    DoFab = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "mrp.product.produce",
                        "do_produce",
                        [ProductProduce],
                    )
                    Fabricacion = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "mrp.production",
                        "button_mark_done",
                        [new_produccion],
                    )
                    fecha_hora = datetime.now() - timedelta(hours=6)
                    logging.warning(
                        "Antes de dar hecho la fecha es "
                        + str(fecha_hora.strftime("%Y-%m-%d %H:%M:%S"))
                    )
                    backdate_data = {
                        "date": fecha_hora.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),  # Establece la fecha que desees
                        "mrp_order_id": new_produccion,  # ID de la transferencia de stock que deseas validar
                    }
                    # Crear una instancia de StockPickingBackdate con los datos requeridos
                    backdate_instance_id = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "mrp.markdone.backdate.wizard",
                        "create",
                        [backdate_data],
                    )
                    logging.warning("Backdate instance " + str(backdate_instance_id))
                    logging.warning("Llamanado a process -------- ++++++++")
                    hace_fabricacion = self.env["datalayer"].odoo_execute_kw(
                        odoo_externo,
                        "mrp.markdone.backdate.wizard",
                        "process",
                        [backdate_instance_id[0]],
                    )
                    record.exportar = False
                    return hace_fabricacion
                except Exception as e:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - La orden de fabricacion no pudo marcarse como confirmada en Odoo 13 *¡No se realizó sincronización!*"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "La orden de fabricacion no se marco como confirmada en Odoo 13 "
                        + str(e)
                    )
                    # Llama a odoo_execute_kw con backdate_data
                    # confirma_transferencia = self.env['datalayer'].odoo_execute_kw(odoo_externo,"stock.picking.backdate", "process", [], **backdate_data)

            elif (
                len(thProduction) > 0
                and self.env["material.purchase.requisition"].search_count(
                    [("orden_produccion", "=", record.id)]
                )
                > 1
            ):
                thAuxProducto = None
                logging.warning(
                    "Ya se sincronizo la fabricacion y tiene mas de una requisicion"
                )
                Factura13 = self.env["datalayer"].odoo_execute_kw(
                    odoo_externo,
                    "sale.order",
                    "search_read",
                    [("x_ticket_ms", "=", record.ticket), ("invoice_ids", "!=", False)],
                    fields=["id", "invoice_ids"],
                )
                if len(Factura13) > 0:
                    mensaje = (
                        "Error - Ticket "
                        + str(record.ticket)
                        + " - La orden de fabricacion ya tiene factura en Odoo 13"
                    )
                    self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)
                    raise UserError(
                        "La fabricacion ya tiene factura en Odoo 13, hay "
                        + str(Factura13)
                    )
                if (
                    record.multi_requisicion_materiales
                ):  # Si hay requisicion de mas materiales
                    logging.warning("Hay mas de una requisicion de materiales")
                    for prod in thProduction:
                        try:
                            prod13 = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "mrp.production",
                                "action_cancel",
                                [prod["id"]],
                            )
                            logging.warning(
                                "Fabricacion puesta como cancelada preparando sincronizacion"
                            )
                        except Exception as e:
                            mensaje = (
                                "Error - Ticket "
                                + str(record.ticket)
                                + " - La orden de fabricacion no pudo cancelarse en Odoo 13 *¡No se realizó sincronización!*"
                            )
                            self.env["sale.order"].EnviarMensaje(
                                idchat, mensaje, urlimagen
                            )
                            raise UserError(
                                "La orden de fabricacion no se cancelo en Odoo 13 "
                                + str(e)
                            )
                        try:
                            prod13 = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "mrp.production",
                                "action_draft",
                                [prod["id"]],
                            )
                            logging.warning(
                                "Fabriacion puesta en borrador preparando sincronizacion"
                            )
                        except Exception as e:
                            mensaje = (
                                "Error - Ticket "
                                + str(record.ticket)
                                + " - La orden de fabricacion no pudo ponerse en borrador en Odoo 13 *¡No se realizó sincronización!*"
                            )
                            self.env["sale.order"].EnviarMensaje(
                                idchat, mensaje, urlimagen
                            )
                            raise UserError(
                                "La orden de fabricacion no se puso en borrador en Odoo 13 "
                                + str(e)
                            )
                        vals_componentes = []
                        x_bd_o = 0
                        x_bd_d = 0
                        bodega_origen = None
                        bodega_destino = None
                        aux_UnidadMedida = 0
                        thProducto = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "product.product",
                            "search_read",
                            [("product_tmpl_id.company_id", "=", 1)],
                            fields=["id", "name"],
                        )
                        for comp in record.move_raw_ids:
                            # Bodega de componentes
                            if x_bd_o != comp.location_id.id:
                                x_bd_o = comp.location_id.id
                                bodega_origen = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "stock.location",
                                    "search_read",
                                    [
                                        ("name", "=", comp.location_id.name),
                                        (
                                            "location_id.name",
                                            "=",
                                            comp.location_id.location_id.name,
                                        ),
                                    ],
                                    fields=["id", "name", "location_id"],
                                )
                            if not bodega_origen:
                                mensaje = (
                                    "Error - Ticket "
                                    + str(record.ticket)
                                    + " - La bodega "
                                    + str(comp.location_id.location_id.name)
                                    + "/"
                                    + str(comp.location_id.name)
                                    + " no existe en Odoo 13. *¡No se realizó sincronización!.*"
                                )
                                self.env["sale.order"].EnviarMensaje(
                                    idchat, mensaje, urlimagen
                                )
                                raise UserError(
                                    "La bodega "
                                    + str(comp.location_id.location_id.name)
                                    + "/"
                                    + str(comp.location_id.name)
                                    + " no existe en Odoo 13"
                                )
                            if x_bd_d != comp.location_dest_id.id:
                                x_bd_d = comp.location_dest_id.id
                                bodega_destino = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "stock.location",
                                    "search_read",
                                    [
                                        ("name", "=", comp.location_dest_id.name),
                                        (
                                            "location_id.name",
                                            "=",
                                            comp.location_dest_id.location_id.name,
                                        ),
                                    ],
                                    fields=["id", "name", "location_id"],
                                )
                            if not bodega_destino:
                                mensaje = (
                                    "Error - Ticket "
                                    + str(record.ticket)
                                    + " - La bodega "
                                    + str(comp.location_dest_id.location_id.name)
                                    + "/"
                                    + str(comp.location_dest_id.name)
                                    + " no existe en Odoo 13. *¡No se realizó sincronización!*"
                                )
                                self.env["sale.order"].EnviarMensaje(
                                    idchat, mensaje, urlimagen
                                )
                                raise UserError(
                                    "La bodega "
                                    + str(comp.location_dest_id.location_id.name)
                                    + "/"
                                    + str(comp.location_dest_id.name)
                                    + " no existe en Odoo 13"
                                )
                            if aux_UnidadMedida != comp.product_uom.id:
                                idUnidadMedida = 0
                                aux_UnidadMedida = comp.product_uom.id
                                UnidadMedida = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "uom.uom",
                                    "search_read",
                                    [("name", "=", comp.product_uom.name)],
                                    fields=["id"],
                                )
                                if not UnidadMedida:
                                    UnidadMedida = self.env[
                                        "datalayer"
                                    ].odoo_execute_kw(
                                        odoo_externo,
                                        "ir.translation",
                                        "search_read",
                                        [
                                            ("name", "=", "uom.uom,name"),
                                            ("lang", "=", "es_GT"),
                                            "|",
                                            ("value", "=", comp.product_uom.name),
                                            ("src", "=", comp.product_uom.name),
                                        ],
                                        fields=["res_id"],
                                    )
                                    if not UnidadMedida:
                                        mensaje = (
                                            "Error - Ticket "
                                            + str(record.ticket)
                                            + " - La unidad de medida "
                                            + str(comp.product_uom.name)
                                            + " no existe en Odoo 13 *¡No se realizó sincronización!*"
                                        )
                                        self.env["sale.order"].EnviarMensaje(
                                            idchat, mensaje, urlimagen
                                        )
                                        raise UserError(
                                            "La unidad de medida "
                                            + str(comp.product_uom.name)
                                            + " no existe en Odoo 13"
                                        )
                                    idUnidadMedida = UnidadMedida[0]["res_id"]
                                else:
                                    idUnidadMedida = UnidadMedida[0]["id"]
                            if not UnidadMedida:
                                mensaje = (
                                    "Error - Ticket "
                                    + str(record.ticket)
                                    + " - La unidad de medida "
                                    + str(comp.product_uom.name)
                                    + " no existe en Odoo 13 *¡No se realizó sincronización!*"
                                )
                                self.env["sale.order"].EnviarMensaje(
                                    idchat, mensaje, urlimagen
                                )
                                raise UserError(
                                    "La unidad de medida "
                                    + str(comp.product_uom.name)
                                    + " no existe en Odoo 13"
                                )
                            # producto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.template", "search_read",
                            #                            [('name', '=', comp.product_id.name), ('company_id', '=', 1)],
                            #                            fields=["id", "name"])
                            producto = None
                            producto = [
                                line
                                for line in thProducto
                                if line["name"] == comp.product_id.name
                            ]
                            if producto:
                                for linePro in producto:
                                    # thAuxProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.product", "search_read",
                                    #                                 [('product_tmpl_id', '=', linePro["id"])],
                                    #                                 fields=["id", "name"])
                                    thAuxProducto = None
                                    thAuxProducto = linePro["id"]
                                    if thAuxProducto:
                                        break
                                        # raise UserError('Desde product.product'+str(thAuxProducto))
                                        # continue
                            else:
                                producto = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "ir.translation",
                                    "search_read",
                                    [
                                        ("name", "=", "product.template,name"),
                                        ("lang", "=", "es_GT"),
                                        ("value", "=", comp.product_id.name),
                                    ],
                                    fields=["res_id", "name"],
                                )
                                if producto:
                                    for linePro in producto:
                                        logging.warning(
                                            "Desde traduccion " + str(producto)
                                        )
                                        # thPT = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.template", "search_read",
                                        #                        [('id', '=', linePro["res_id"]), ('company_id', '=', 1)],
                                        #                        fields=["id"])
                                        # thAuxProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.product", "search_read",
                                        #                                 [('product_tmpl_id', '=', thPT[0]["id"])],
                                        #                                 fields=["id", "name"])
                                        thAuxProducto_t = None
                                        thAuxProducto_t = self.env[
                                            "datalayer"
                                        ].odoo_execute_kw(
                                            odoo_externo,
                                            "product.product",
                                            "search_read",
                                            [
                                                (
                                                    "product_tmpl_id.id",
                                                    "=",
                                                    linePro["res_id"],
                                                ),
                                                ("product_tmpl_id.company_id", "=", 1),
                                            ],
                                            fields=["id", "name"],
                                            limit=1,
                                            order="id desc",
                                        )
                                        if thAuxProducto_t:
                                            thAuxProducto = thAuxProducto_t[0]["id"]
                                            # raise UserError('Desde traduccion'+str(thAuxProducto))
                                            break
                            if not thAuxProducto:
                                mensaje = (
                                    "Error - Ticket "
                                    + str(record.ticket)
                                    + " - El producto "
                                    + str(comp.product_id.name)
                                    + " no existe en Odoo 13 *¡No se realizó sincronización!*"
                                )
                                self.env["sale.order"].EnviarMensaje(
                                    idchat, mensaje, urlimagen
                                )
                                raise UserError(
                                    "El producto "
                                    + str(comp.product_id.name)
                                    + " no existe en Odoo 13"
                                )
                            # thReference = str(comp.reference) + " sincronizado de Odoo 16 -> Orden modificada"
                            # thName = str(comp.name) + " soncronizado de Odoo 16 -> Orden modificada"
                            # thDisplayName = str(comp.display_name) + " fabricacion de Odoo 16 -> Orden modificada"
                            vals_componentes.append(
                                {
                                    "product_id": thAuxProducto,
                                    "product_uom_qty": comp.product_uom_qty,
                                    "quantity_done": comp.quantity_done,
                                    "product_uom": int(
                                        idUnidadMedida
                                    ),  # UnidadMedida[0]["id"],
                                    "location_id": bodega_origen[0]["id"],
                                    "location_dest_id": bodega_destino[0]["id"],
                                    "name": thProduction[0]["name"],
                                    #'reference': thReference,
                                    #'name': thName,
                                    #'display_name': thDisplayName,
                                    "company_id": 1,
                                    "raw_material_production_id": prod["id"],
                                }
                            )

                        try:
                            new_production_line = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo, "stock.move", "create", vals_componentes
                            )
                            logging.warning("Componentes creados")
                        except Exception as e:
                            # if not new_stock_move > 0:
                            mensaje = (
                                "Error - Ticket "
                                + str(record.ticket)
                                + " - los componentes la orden de fabricacion no se crearon correctamente en Odoo 13 *¡Se realizó parcialmente la sincronización!*"
                            )
                            self.env["sale.order"].EnviarMensaje(
                                idchat, mensaje, urlimagen
                            )
                            raise UserError(
                                "Los componentes de la orden de fabricacion no se crearon correctamente en Odoo 13 "
                                + str(e)
                            )
                        # record.write({'id_odoo_13': int(new_produccion)})
                        self.env.cr.commit()
                        try:
                            Fabricacion = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "mrp.production",
                                "action_confirm",
                                [prod["id"]],
                            )
                            Fabricacion = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "mrp.production",
                                "action_assign",
                                [prod["id"]],
                            )
                            logging.warning("Fabricacion confirmada")
                            logging.warning("prod trae: " + str(prod))
                            vals_mpp = {
                                "company_id": 1,
                                "production_id": prod["id"],
                                "product_id": prod["product_id"][0],
                                "qty_producing": prod["product_qty"],
                                "product_uom_id": prod["product_uom_id"][0],
                                "consumption": "strict",
                            }
                            logging.warning("Vals_mpp trae: " + str(vals_mpp))
                            ProductProduce = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo, "mrp.product.produce", "create", vals_mpp
                            )
                            logging.warning(
                                "ProductProduce trae: " + str(ProductProduce)
                            )
                            DoFab = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "mrp.product.produce",
                                "do_produce",
                                [ProductProduce],
                            )
                            logging.warning("DoFab trae: " + str(DoFab))
                            # Fabricacion.do_produce()
                            Fabricacion = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "mrp.production",
                                "button_mark_done",
                                [prod["id"]],
                            )
                            logging.warning(
                                "Fabricacion marcada como hecha desde boton"
                            )
                            # Llama a odoo_execute_kw con backdate_data
                            # confirma_transferencia = self.env['datalayer'].odoo_execute_kw(odoo_externo,"stock.picking.backdate", "process", [], **backdate_data)
                            fecha_hora = datetime.now() - timedelta(hours=6)
                            logging.warning(
                                "Antes de dar hecho la fecha es "
                                + str(fecha_hora.strftime("%Y-%m-%d %H:%M:%S"))
                            )
                            backdate_data = {
                                "date": fecha_hora.strftime("%Y-%m-%d %H:%M:%S"),
                                # Establece la fecha que desees
                                "mrp_order_id": prod[
                                    "id"
                                ],  # ID de la transferencia de stock que deseas validar
                            }
                            # Crear una instancia de StockPickingBackdate con los datos requeridos
                            backdate_instance_id = self.env[
                                "datalayer"
                            ].odoo_execute_kw(
                                odoo_externo,
                                "mrp.markdone.backdate.wizard",
                                "create",
                                [backdate_data],
                            )
                            # Llamar al método process para validar la transferencia de stock
                            logging.warning(
                                "Backdate instance escenario 2"
                                + str(backdate_instance_id)
                            )
                            logging.warning("Llamanado a process -------- ++++++++")
                            record.exportar = False
                            self.env.cr.commit()
                            hace_fabricacion = self.env["datalayer"].odoo_execute_kw(
                                odoo_externo,
                                "mrp.markdone.backdate.wizard",
                                "process",
                                [backdate_instance_id[0]],
                            )
                            logging.warning("Fabricacion marcada como hecha")
                            return True
                        except Exception as e:
                            mensaje = (
                                "Error - Ticket "
                                + str(record.ticket)
                                + " - La orden de fabricacion no pudo confirmarse en Odoo 13 *¡No se realizó sincronización!*"
                            )
                            self.env["sale.order"].EnviarMensaje(
                                idchat, mensaje, urlimagen
                            )
                            raise UserError(
                                "La orden de fabricacion no se marco como hecho en Odoo 13 "
                                + str(e)
                            )
                        # Aqui va el for por cada orden de produccion o fabricacion
                        thPedidoVenta = None
                        thPedidoVenta = self.env["datalayer"].odoo_execute_kw(
                            odoo_externo,
                            "sale.order",
                            "search_read",
                            [
                                ("x_ticket_ms", "=", record.ticket),
                                ("invoice_count", "=", 0),
                            ],
                            fields=["id"],
                        )
                        if not thPedidoVenta:
                            mensaje = (
                                "Error - Ticket "
                                + str(record.ticket)
                                + " - no tiene pedido de venta en Odoo 13"
                            )
                            self.env["sale.order"].EnviarMensaje(
                                idchat, mensaje, urlimagen
                            )
                            raise UserError("No tiene pedido de venta en Odoo 13")
                        else:
                            for venta in thPedidoVenta:
                                vals_up_venta = {"state": "cancel"}
                                up_venta = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "sale.order",
                                    "write",
                                    [venta["id"]],
                                    vals_up_venta,
                                )
                                thSaleOrderLine = self.env["datalayer"].odoo_execute_kw(
                                    odoo_externo,
                                    "sale.order.line",
                                    "search_read",
                                    [
                                        ("order_id", "=", venta["id"]),
                                        ("product_id", "=", prod["product_id"]),
                                    ],
                                    fields=["id"],
                                )
                                for line in thSaleOrderLine:
                                    try:
                                        vals_up_venta_line = {
                                            "order_id": line["id"],
                                            "product_uom_qty": record.qty_producing,
                                            "qty_invoiced": record.qty_producing,
                                            "qty_delivered": record.qty_producing,
                                            "price_unit": record.ventas[0].amount_total
                                            / record.qty_producing,
                                        }
                                        up_venta_line = self.env[
                                            "datalayer"
                                        ].odoo_execute_kw(
                                            odoo_externo,
                                            "sale.order.line",
                                            "write",
                                            [line["id"]],
                                            vals_up_venta_line,
                                        )
                                    except Exception as e:
                                        mensaje = (
                                            "Error - Ticket "
                                            + str(record.ticket)
                                            + " - El pedido de venta "
                                            + str(record.ventas[0].name)
                                            + " no pudo sincronizarse en Odoo 13 *¡No se realizó sincronización de pedido de venta!*"
                                        )
                                        self.env["sale.order"].EnviarMensaje(
                                            idchat, mensaje, urlimagen
                                        )
                                        raise UserError(
                                            "El pedido de venta "
                                            + str(record.ventas[0].name)
                                            + " no existe en Odoo 13 "
                                            + str(e)
                                        )
                        mensaje = (
                            "Ticket "
                            + str(record.ticket)
                            + " - Orden fabricacion editada en Odoo 13"
                        )
                        self.env["sale.order"].EnviarMensaje(idchat, mensaje, urlimagen)

    @api.model
    @api.onchange("analytic_account_id")
    def onchange_analytic_account_id(self):
        if self.analytic_account_id:
            for req in self.requisiciones:
                req.analytic_account_id = self.analytic_account_id.id
