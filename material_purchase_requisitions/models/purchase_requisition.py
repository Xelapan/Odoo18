# -*- coding: utf-8 -*-

# WhatsApp
from zeep import Client
import json
import logging

logger = logging.getLogger()
_logger = logging.getLogger(__name__)
# Fin WhatsApp
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError
import html2text
from collections import defaultdict


class MaterialPurchaseRequisition(models.Model):
    _name = "material.purchase.requisition"
    _description = "Requisicion Materiales"
    # _inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ["mail.thread", "mail.activity.mixin", "portal.mixin"]  # odoo11
    _order = "id desc"

    orden_produccion = fields.Many2one(
        "mrp.production",
        string="Orden de Fabricación",
        store=True,
        readonly=True,
        on_delete="restrict",
    )
    x_no_ticket = fields.Integer(
        string="Ticket", #store=True,
        compute="_compute_ticket", readonly=True
    )
    # transaccion_proceso = fields.Boolean(string="Transaccion en Proceso", store=True, default=False)
    # exportado_13 = fields.Datetime(string="ExpoOdoo 13", store=True)
    x_ticket = fields.Many2one(
        "helpdesk.ticket", string="Ticket", store=True, on_delete="restrict"
    )

    name = fields.Char(
        string="Number",
        index=True,
        readonly=1,
    )
    state = fields.Selection(
        [
            ("draft", "Nuevo"),
            ("dept_confirm", "Espera Aprobación MTO"),
            ("ir_approve", "Aprobación MTO"),
            ("approve", "Aprobación Cliente"),
            ("stock", "Materiales Solicitados"),
            ("receive", "Materiales Entregados"),
            ("cancel", "Cancelado"),
            ("reject", "Rechazado"),
        ],
        default="draft",
        track_visibility="onchange",
    )
    request_date = fields.Date(
        string="Fecha de Requisición",
        default=fields.Date.today() + timedelta(hours=12),
        required=True,
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Departamento",
        # default=lambda self: self.employee_id.department_id,
        required=True,
        copy=True,
    )
    # employee_id = fields.Many2one(
    #     'hr.employee',
    #     string='Empleado',
    #     default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
    #     #compute='_compute_employee_id',
    #     store = True,
    #     required=True,
    #     copy=True,
    # )
    employee_id = fields.Many2one(
        "hr.employee.ticket",
        string="Empleado",
        default=lambda self: self.env["hr.employee.ticket"].search(
            [("user_id", "=", self.env.uid)], limit=1
        ),
        # compute='_compute_employee_id',
        store=True,
        required=True,
        copy=True,
    )
    # approve_manager_id = fields.Many2one(
    #     'hr.employee',
    #     string='Department Manager',
    #     readonly=True,
    #     copy=False,
    # )
    approve_manager_id = fields.Many2one(
        "hr.employee.ticket",
        string="Department Manager",
        readonly=True,
        copy=False,
    )
    reject_manager_id = fields.Many2one(
        "hr.employee.ticket",
        string="Department Manager Reject",
        readonly=True,
    )
    approve_employee_id = fields.Many2one(
        "hr.employee.ticket",
        string="Approved by",
        readonly=True,
        copy=False,
    )
    reject_employee_id = fields.Many2one(
        "hr.employee.ticket",
        string="Rejected by",
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Compañia",
        # default=lambda self: self.env.user.company_id,
        default=lambda self: self.env.company,
        required=True,
        copy=True,
    )
    location_id = fields.Many2one(
        "stock.location",
        string="Ubicación de Origen",
        copy=True,
    )
    requisition_line_ids = fields.One2many(
        "material.purchase.requisition.line",
        "requisition_id",
        string="Purchase Requisitions Line",
        copy=True,
    )
    date_end = fields.Date(
        string="Fecha Limite",
        readonly=True,
        help="Last date for the product to be needed",
        copy=True,
    )
    date_done = fields.Date(
        string="Date Done",
        readonly=True,
        help="Date of Completion of Purchase Requisition",
    )
    managerapp_date = fields.Date(
        string="Department Approval Date",
        readonly=True,
        copy=False,
    )
    manareject_date = fields.Date(
        string="Department Manager Reject Date",
        readonly=True,
    )
    userreject_date = fields.Date(
        string="Rejected Date",
        readonly=True,
        copy=False,
    )
    userrapp_date = fields.Date(
        string="Approved Date",
        readonly=True,
        copy=False,
    )
    receive_date = fields.Date(
        string="Fecha Recepción",
        readonly=True,
        copy=False,
    )
    reason = fields.Text(
        string="Motivo de Requisición",
        required=False,
        copy=True,
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Lugar y Ubicación",
        # default=lambda self: self.x_ticket.analytic_account_id if self.x_ticket else self.orden_produccion.analytic_account_id,
        # compute='_compute_analytic_account_id',
        store=True,
        copy=True,
    )
    dest_location_id = fields.Many2one(
        "stock.location",
        string="Ubicación de Destino",
        required=False,
        copy=True,
    )
    delivery_picking_id = fields.Many2one(
        "stock.picking",
        string="Transferencia",
        readonly=True,
        copy=False,
    )
    requisiton_responsible_id = fields.Many2one(
        "hr.employee.ticket",
        string="Autorizador",
        default=lambda self: self.employee_id.parent_id.id,
        copy=True,
    )
    employee_confirm_id = fields.Many2one(
        "hr.employee.ticket",
        string="Confirmed by",
        readonly=True,
        copy=False,
    )
    confirm_date = fields.Date(
        string="Confirmed Date",
        readonly=True,
        copy=False,
    )

    purchase_order_ids = fields.One2many(
        "purchase.order",
        "custom_requisition_id",
        string="Purchase Order",
    )
    custom_picking_type_id = fields.Many2one(
        "stock.picking.type",
        string="Tipo de Operación de Inventario",
        copy=False,
        store=True,
    )

    x_margen_p = fields.Float(
        string="Margen %",
        store=True,
    )

    x_margen = fields.Float(
        string="Margen",
        store=True,
    )

    x_costo_total = fields.Float(
        string="Costo Total",
        store=True,
    )

    x_costo_sin_margen = fields.Float(
        string="Costo sin Margen",
        store=True,
    )

    x_iva = fields.Float(
        string="IVA %",
        store=True,
    )

    x_id_odoo_13 = fields.Integer(string="ID Odoo 13", store=True)

    @api.depends("x_ticket")
    def _compute_ticket(self):
        for record in self:
            # if record.x_ticket and record.orden_produccion:
            #     raise UserError('No puede tener una orden de producción y un ticket al mismo tiempo')
            if record.x_ticket:
                record.write({"x_no_ticket": record.x_ticket.x_ticket})
            # elif record.orden_produccion:
            #     record.write({'x_no_ticket': record.orden_produccion.ticket})
            else:
                record.write({"x_no_ticket": 0})

    def EnviarMensaje(self, idchat, mensaje, urlimagen):
        try:
            json_str = (
                '{"numero": "' + idchat + '", '
                '"texto": "' + mensaje + '", '
                '"url": "' + str(urlimagen) + '"}'
            )
            data = json.loads(json_str)
            wsdl = "http://mix.xelapan.com:55/Alertas.asmx?WSDL"
            client = Client(wsdl=wsdl)
            client.service.EnviarMsj(str(data))

        except Exception as x:
            print("error al consultar datos")
            logger.exception(str(x))

    # @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ("draft", "cancel", "reject"):
                raise Warning(
                    _(
                        "You can not delete Purchase Requisition which is not in draft or cancelled or rejected state."
                    )
                )
        return super(MaterialPurchaseRequisition, self).unlink()

    @api.model
    def create(self, vals):
        name = self.env["ir.sequence"].next_by_code("purchase.requisition.seq")
        vals.update({"name": name})
        res = super(MaterialPurchaseRequisition, self).create(vals)
        return res

    # @api.multi
    def requisition_confirm(self):
        for rec in self:
            # manager_mail_template = self.env.ref('material_purchase_requisitions.email_confirm_material_purchase_requistion')
            rec.employee_confirm_id = rec.employee_id.id
            rec.confirm_date = fields.Date.today()
            rec.state = "dept_confirm"
            # if rec.orden_produccion and not rec.x_ticket:
            #     rec.orden_produccion.write({})
            #     #rec.x_costo_total = rec.orden_produccion.costo_total
            #     if rec.orden_produccion.mesa_servicio.x_proyecto:
            #         rec.custom_picking_type_id = rec.orden_produccion.mesa_servicio.x_proyecto.custom_picking_type_id.id
            # if len(rec.orden_produccion.requisiciones) > 0:
            #     thFirstReq = self.env['material.purchase.requisition'].search([('orden_produccion', '=', rec.orden_produccion.id)], order='id asc', limit=1)
            #     thReqs = self.env['material.purchase.requisition'].search([('orden_produccion', '=', rec.orden_produccion.id), ('id', '!=', thFirstReq.id)], order='id asc')
            #     thTotal = rec.orden_produccion.costo_total
            #     if rec.orden_produccion.id != thFirstReq.id:
            #         rec.x_costo_total = sum(line.x_monto for line in rec.requisition_line_ids)
            #     thFirstReq.write({'x_costo_total': float(thTotal)})
            #     for req in thReqs:
            #         thFirstReq.write({'x_costo_total': thFirstReq.x_costo_total - sum(line.x_monto for line in req.requisition_line_ids)})
            #         req.x_costo_total = sum(line.x_monto for line in req.requisition_line_ids)
            # else:
            #     rec.x_costo_total = rec.orden_produccion.costo_total
            # elif not rec.orden_produccion and rec.x_ticket:
            #     rec.x_ticket.write({})
            #     rec.custom_picking_type_id = 46  # Consumo de materiales de DIPROSA a DIMASA
            # else:
            #     rec.custom_picking_type_id = False
            # # if manager_mail_template:
            #   #  manager_mail_template.send_mail(self.id)

    # @api.multi
    def requisition_reject(self):
        for rec in self:
            rec.state = "reject"
            rec.reject_employee_id = self.env["hr.employee.ticket"].search(
                [("user_id", "=", self.env.uid)], limit=1
            )
            rec.userreject_date = fields.Date.today()

    # @api.multi
    def manager_approve(self):
        for rec in self:
            rec.managerapp_date = fields.Date.today()
            rec.approve_manager_id = self.env["hr.employee.ticket"].search(
                [("user_id", "=", self.env.uid)], limit=1
            )
            rec.state = "ir_approve"
            # if rec.orden_produccion.id and not rec.x_ticket.id:
            #     logging.warning('Aprobacion gerente desde fabricacion')
            #     if rec.orden_produccion.ventas.invoice_status == 'invoiced':
            #         raise UserError(
            #             'Ya no es permitido crear requisiciones, la orden de produccion ya tiene una factura asociada en Odoo 13')
            #     estado_original = ''
            #     if len(rec.orden_produccion.requisiciones) > 0 and len(rec.orden_produccion.ventas) > 0:
            #         if rec.orden_produccion.state == 'done':
            #             estado_original = rec.orden_produccion.state
            #     if len(rec.orden_produccion.requisiciones) > 1:
            #         if rec.id == self.env['material.purchase.requisition'].search([('orden_produccion', '=', rec.orden_produccion.id)], order="id desc", limit=1).id:
            #             logging.warning('Requisicion encontrada esta es la ultima por nombre ' + str(rec.name))
            #             logging.warning('Llamando a manager_approve_fabricacion')
            #             self.manager_approve_fabricacion(rec)
            #     else:
            #         # -------------------------------------------------------------
            #         for line in rec.requisition_line_ids:
            #             logging.warning('---- entrando a for de requisicion line')
            #             if line.product_id.type == 'product':
            #                 logging.warning('---- si es producto')
            #                 if not any(comp.product_id.id == line.product_id.id and comp.product_uom == line.uom and comp.product_uom_qty == line.qty for comp in rec.orden_produccion.move_raw_ids):  # Comprobamos si hay productos
            #                     logging.warning('---- si hay productos en la orden de fabricacion que estan en la requisicion nueva')
            #                     # thCostoOriginal = rec.orden_produccion.costo_total
            #                     if any(comp.product_id.id == line.product_id.id for comp in rec.orden_produccion.move_raw_ids):  # Comprobamos si hay productos
            #                         for comp in rec.orden_produccion.move_raw_ids:
            #                             if line.product_id.id == comp.product_id.id:
            #                                 logging.warning('---- si es el mismo producto')
            #                                 comp.write({
            #                                     'product_uom_qty': comp.product_uom_qty + line.qty,
            #                                     'quantity_done': comp.quantity_done + line.qty,
            #                                     'lst_price': line.x_price,
            #                                 })
            #                     else:
            #                         try:
            #                             logging.warning('---- no hay productos en la orden de fabricacion que estan en la requisicion nueva')
            #                             rec.orden_produccion.write({'move_raw_ids': [(0, 0, {
            #                                 'product_id': line.product_id.id,
            #                                 'product_uom_qty': line.qty,
            #                                 'quantity_done': line.qty,
            #                                 'lst_price': line.x_price,
            #                                 'product_uom': line.uom.id,
            #                                 'name': line.product_id.name,
            #                             })]})
            #                             logging.warning('---- se agrego el producto a la orden de fabricacion')
            #                         except Exception as e:
            #                             raise UserError('Error al agregar el producto a la orden de fabricación ' + str(e))
            #     self.env.cr.commit()
            #     rec.orden_produccion._compute_costo_total()
            #         # thLinesReq = self.env['material.purchase.requisition.line'].search([
            #         #     ('requisition_id.x_no_ticket', '=', rec.x_no_ticket),
            #         #     ('product_id.type', '=', 'service'),
            #         #     ('requisition_id.orden_produccion.id', '=', rec.orden_produccion.id)])
            #         # #if any(line.product_id.type == 'service' for line in rec.requisition_line_ids):
            #         # rec.orden_produccion.write({'costo_total': rec.orden_produccion.costo_total + (sum(line.x_monto for line in thLinesReq) * 1.12)})
            #         # -------------------------------------------------------------
            #     logging.warning('Llamando compute_ventas')
            #     rec.orden_produccion._compute_ventas()
            #     #Alex
            #     #13 05 2024 Con la confirmacion del pedido de venta se genera transferencia
            #     # if rec.orden_produccion.proyecto.presupuestado:
            #     #     rec.request_stock()
            #     # if estado_original == 'done':
            #     #     logging.warning('El estado de la fabriacion era Hecho')
            #     #     thFabricar = self.env["mrp.consumption.warning"].create({'mrp_production_ids': [(4, rec.orden_produccion.id)]})
            #     #     try:
            #     #         thFabricar.action_confirm()
            #     #         logging.warning('Fabricacion confirmada desde manager_approve')
            #     #     except Exception as e:
            #     #         raise UserError('Error al confirmar fabricacion '+str(e))
            #         #10 05 2024 Ya no fabricamos
            #         #rec.orden_produccion.sincroniza_fabricacion('Odoo 13', rec.orden_produccion)
            #         # try:
            #         #     Fab13 = self.env['datalayer'].odoo_execute_kw('Odoo 13', "mrp.production", "action_cancel", [rec.orden_produccion.id_odoo_13])
            #         # except Exception as e:
            #         #     raise UserError('Error al cancelar fabricacion en Odoo 13 '+str(e))
            #         # try:
            #         #     Fab13 = self.env['datalayer'].odoo_execute_kw('Odoo 13', "mrp.production", "action_draft", [rec.orden_produccion.id_odoo_13])
            #         # except Exception as e:
            #         #     raise UserError('Error al pasar a borrador la fabricacion en Odoo 13 ' + str(e))

    # Primero va al modulo produccion, si ya hay ventas o mas de una requisicion retorna aca
    # def manager_approve_fabricacion(self, rec):
    #     logging.warning('manager_approve_fabricacion ---- entrando')
    #     estado_original = ''
    #     #for rec in self:
    #     rec.managerapp_date = fields.Date.today()
    #     rec.approve_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #     if rec.orden_produccion.id and not rec.x_ticket.id:
    #         logging.warning('---- entrando a fabricacion y no ticket')
    #         if any(line.product_id.type == 'product' for line in rec.requisition_line_ids):  # Comprobamos si hay productos
    #             logging.warning('---- si hay productos')
    #             try:
    #                 if rec.orden_produccion.state == 'done':
    #                     # object has no attribute 'multi_requisicion_materiales'
    #                     rec.orden_produccion.set_return_confirmed()
    #                     rec.orden_produccion.set_to_draft()
    #                     rec.orden_produccion.write({
    #                         'exportar': True,
    #                     })
    #                     logging.warning('---- orden de fabricacion cambiado state done a draft')
    #                 else:
    #                     rec.orden_produccion.set_to_draft()
    #                     logging.warning('---- orden de fabricacion cambiado state a draft')
    #                 rec.orden_produccion.multi_requisicion_materiales = True
    #                 logging.warning('Cambio a multi_requisicion_materiales '+str(rec.orden_produccion.multi_requisicion_materiales))
    #             except Exception as e:
    #                 raise UserError('Error al cambiar el estado de la orden de fabricación ' + str(e))
    #             for line in rec.requisition_line_ids:
    #                 logging.warning('---- entrando a for de requisicion line')
    #                 if line.product_id.type == 'product':
    #                     logging.warning('---- si es producto')
    #                     if any(comp.product_id.id == line.product_id.id for comp in rec.orden_produccion.move_raw_ids):  # Comprobamos si hay productos
    #                         logging.warning('---- si hay productos en la orden de fabricacion que estan en la requisicion nueva')
    #                         #thCostoOriginal = rec.orden_produccion.costo_total
    #                         for comp in rec.orden_produccion.move_raw_ids:
    #                             if line.product_id.id == comp.product_id.id:
    #                                 logging.warning('---- si es el mismo producto')
    #                                 comp.write({
    #                                     'product_uom_qty': comp.product_uom_qty + line.qty,
    #                                     'quantity_done': comp.quantity_done + line.qty,
    #                                     'lst_price': line.x_price,
    #                                 })
    #                     else:
    #                         try:
    #                             logging.warning('---- no hay productos en la orden de fabricacion que estan en la requisicion nueva')
    #                             rec.orden_produccion.write({'move_raw_ids': [(0, 0, {
    #                                 'product_id': line.product_id.id,
    #                                 'product_uom_qty': line.qty,
    #                                 'quantity_done': line.qty,
    #                                 'lst_price': line.x_price,
    #                                 'product_uom': line.uom.id,
    #                                 'name': line.product_id.name,
    #                             })]})
    #                             logging.warning('---- se agrego el producto a la orden de fabricacion')
    #                         except Exception as e:
    #                             raise UserError('Error al agregar el producto a la orden de fabricación ' + str(e))
    #
    #             rec.orden_produccion._compute_costo_total()
    #
    #         # if any(line.product_id.type == 'service' for line in rec.requisition_line_ids):
    #         #     rec.orden_produccion.write({'costo_total': rec.orden_produccion.costo_total+sum(line.x_monto for line in rec.requisition_line_ids if line.product_id.type == 'service')})
    #         # thLinesReq = self.env['material.purchase.requisition.line'].search([
    #         #     ('requisition_id.x_no_ticket', '=', rec.x_no_ticket),
    #         #     ('product_id.type', '=', 'service'),
    #         #     ('requisition_id.orden_produccion.id', '=', rec.orden_produccion.id)])
    #         # # if any(line.product_id.type == 'service' for line in rec.requisition_line_ids):
    #         # rec.orden_produccion.write({'costo_total': rec.orden_produccion.costo_total + (sum(line.x_monto for line in thLinesReq) * 1.12)})
    #         try:
    #             rec.orden_produccion.action_confirm()
    #             logging.warning('---- orden de fabricacion confirmada')
    #         except Exception as e:
    #             raise UserError('Error al confirmar la orden de fabricación ' + str(e))
    #     rec.orden_produccion.unica_requisicion = False
    #     rec.state = 'ir_approve'
    #     self.env.cr.commit()
    #     logging.warning('Se hace commit')
    #     logging.warning('manager_approve_fabricacion ---- saliendo')

    # def sincroniza_requisicion(self, odoo_externo, rec):
    #     # idchat = '+120363179270802732@g.us'
    #     idchat = '+50250205026'
    #     urlimagen = False
    #     #odoo_execute_kw = self.env['datalayer']._eval_context_odoo2odoox(odoo_externo).get('odoo_execute_kw')
    #     #odoo_execute_kw4 = 1
    #     #if odoo_execute_kw4==1:
    #     if any(line.product_id.detailed_type in ['product','consu']  for line in rec.requisition_line_ids):
    #         existe = self.env['datalayer'].odoo_execute_kw(odoo_externo, "material.purchase.requisition", "search_read", [('x_id_odoo_16', '=', rec.id)], fields=["id"])
    #         if not existe:
    #             Factura13 = self.env['datalayer'].odoo_execute_kw(odoo_externo,"sale.order", "search_read",[('x_ticket_ms', '=', rec.x_no_ticket), ('invoice_ids', '!=', False)], fields=["id", "invoice_ids"])
    #             if len(Factura13) > 0:
    #                 mensaje = "Error - Ticket " + str(
    #                     rec.x_no_ticket) + " - La orden de fabricacion ya tiene factura en Odoo 13"
    #                 self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                 raise UserError('La fabricacion ya tiene factura en Odoo 13, hay ' + str(Factura13))
    #
    #             if not rec.employee_id:
    #                 mensaje = "Error - Ticket " + str(rec.x_no_ticket) + " - La Requisicion " + str(
    #                     rec.name) + " tiene vacio el campo empleado *¡No se realizó sincronización!*"
    #                 self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                 raise UserError(
    #                     'La Requisicion ' + str(rec.name) + ' tiene vacio el campo empleado')
    #
    #             employee = self.env['datalayer'].odoo_execute_kw(odoo_externo,"hr.employee", "search_read",
    #                                        [('name', '=', rec.employee_id.name)],
    #                                        fields=["id", "name"])
    #             if not employee:
    #                 mensaje = "Error - Ticket " + str(rec.x_no_ticket) + " - El empleado " + str(
    #                     rec.employee_id.name) + " no existe en Odoo 13 *¡No se realizó sincronización!*"
    #                 self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                 raise UserError(
    #                     'El empleado ' + str(rec.employee_id.name) + ' no existe en Odoo 13')
    #
    #             responsable = self.env['datalayer'].odoo_execute_kw(odoo_externo,"hr.employee", "search_read",
    #                                           [('name', '=', rec.employee_id.parent_id.name)],
    #                                           fields=["id", "name"])
    #             if not responsable:
    #                 mensaje = "Error - Ticket " + str(rec.x_no_ticket) + " - El empleado " + str(
    #                     rec.employee_id.name) + " no tiene definido un jefe directo en la ficha del empleado *¡No se realizó sincronización!*"
    #                 self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                 raise UserError('El empleado ' + str(
    #                     rec.employee_id.name) + ' no tiende definido un jefe directo en la ficha del empleado')
    #
    #             if rec.custom_picking_type_id.id == 47:
    #                 tipo_operacion = self.env['datalayer'].odoo_execute_kw(odoo_externo,"stock.picking.type", "search_read", [
    #                     ('id', '=', 5)],
    #                                                  fields=["id", "name", "warehouse_id",
    #                                                          "default_location_src_id",
    #                                                          "default_location_dest_id"])
    #             else:
    #                 # Tomar en cuenta las ubicaciones de orgien en este caso BDIP/Stock
    #                 tipo_operacion = self.env['datalayer'].odoo_execute_kw(odoo_externo,"stock.picking.type", "search_read", [
    #                     ('name', '=', rec.custom_picking_type_id.name),
    #                     ('code', '=', rec.custom_picking_type_id.code),
    #                     ('warehouse_id.name', '=', rec.custom_picking_type_id.warehouse_id.name),
    #                     ('default_location_src_id.name', '=',
    #                      rec.custom_picking_type_id.default_location_src_id.name),
    #                     ('default_location_src_id.location_id.name', '=',
    #                      rec.custom_picking_type_id.default_location_src_id.location_id.name),
    #                     ('default_location_dest_id.name', '=',
    #                      rec.custom_picking_type_id.default_location_dest_id.name),
    #                     ('default_location_dest_id.location_id.name', '=',
    #                      rec.custom_picking_type_id.default_location_dest_id.location_id.name)],
    #                                                  fields=["id", "name", "warehouse_id",
    #                                                          "default_location_src_id",
    #                                                          "default_location_dest_id"])
    #             if not tipo_operacion:
    #                 mensaje = "Error - Ticket " + str(
    #                     rec.x_no_ticket) + " - El tipo de operacion " + str(
    #                     rec.custom_picking_type_id.name) + " " + str(
    #                     rec.custom_picking_type_id.code) + " " + str(
    #                     rec.custom_picking_type_id.warehouse_id.name) + " no existe en Odoo 13 *¡No se realizó sincronización!*"
    #                 self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                 raise UserError('El tipo de operacion ' + str(
    #                     rec.custom_picking_type_id.default_location_src_id.name) + ' ' + str(
    #                     rec.custom_picking_type_id.name) + ' no existe en Odoo 13')
    #             x_CuentasAnaliticas = None
    #             #x_CuentasAnaliticas = self.env['datalayer'].odoo_execute_kw(odoo_externo,"account.analytic.account", "search_read",[('code', '=', rec.analytic_account_id.name),('company_id', '=', 1)], fields=["id", "name", "code"])
    #             thCuentasAnaliticas = self.env['datalayer'].odoo_execute_kw(odoo_externo,"account.analytic.account", "search_read",[('company_id.id', '=', 1)], fields=["id", "name", "code"])
    #             thUnidadesMedida = self.env['datalayer'].odoo_execute_kw(odoo_externo,"uom.uom", "search_read", [], fields=["id", "name"])
    #             x_CuentasAnaliticas = [x for x in thCuentasAnaliticas if x["code"] == rec.analytic_account_id.name]
    #             if not x_CuentasAnaliticas:
    #                 mensaje = "Error - Ticket " + str(
    #                     rec.x_no_ticket) + " - La cuenta analitica " + str(
    #                     rec.analytic_account_id.name) + " existe en Odoo 13 *¡No se realizó sincronización !*"
    #                 self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                 raise UserError('La cuenta analitica ' + str(
    #                     rec.analytic_account_id.name) + ' no existe en Odoo 13')
    #             # else:
    #             # raise UserError('El tipo de operacion es '+str(tipo_operacion))
    #             if rec.custom_picking_type_id.id == 47:
    #                 vals = {
    #                     "analytic_account_id": x_CuentasAnaliticas[0]["id"],
    #                     "employee_id": employee[0]["id"],
    #                     "requisiton_responsible_id": responsable[0]["id"],
    #                     "department_id": 5,
    #                     "company_id": 1,
    #                     "x_id_odoo_16": rec.id,
    #                     "state": 'draft',
    #                     "reason": rec.reason,
    #                     "custom_picking_type_id": tipo_operacion[0]["id"],
    #                     "location_id": 290,
    #                     "dest_location_id": int(tipo_operacion[0]["default_location_dest_id"][0]),
    #                     "x_ticket_ms": rec.x_no_ticket,
    #                 }
    #             else:
    #                 vals = {
    #                     "analytic_account_id": x_CuentasAnaliticas[0]["id"],
    #                     "employee_id": employee[0]["id"],
    #                     "requisiton_responsible_id": responsable[0]["id"],
    #                     "department_id": 5,
    #                     "company_id": 1,
    #                     "x_id_odoo_16": rec.id,
    #                     "state": 'draft',
    #                     "reason": rec.reason,
    #                     "custom_picking_type_id": tipo_operacion[0]["id"],
    #                     "location_id": int(tipo_operacion[0]["default_location_src_id"][0]),
    #                     "dest_location_id": int(tipo_operacion[0]["default_location_dest_id"][0]),
    #                     "x_ticket_ms": rec.x_no_ticket,
    #                 }
    #             vals_line = []
    #             altura = 0
    #             aux_UnidadMedida = 0
    #             productos = rec.requisition_line_ids
    #             if productos:
    #                 productos_ordenados = sorted(productos, key=lambda x: x.product_id.name)
    #                 primera_letra = productos_ordenados[0].product_id.name[0]
    #                 ultima_letra = productos_ordenados[-1].product_id.name[0]
    #             thProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo, "product.product", "search_read", [('product_tmpl_id.company_id', '=', 1), ('name', '>=', primera_letra), ('name', '<=', ultima_letra)], fields=["id", "name"])
    #             #thProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo, "product.product", "search_read", [('product_tmpl_id.company_id', '=', 1), ('name', '>=', primera_letra), ('name', '<=', ultima_letra)], fields=["id", "name", "categ_id", "valuation"])
    #             for line_rec in rec.requisition_line_ids:
    #                 if line_rec.product_id.detailed_type == 'product':
    #                     thAuxProducto = None
    #                     if line_rec.uom.id != aux_UnidadMedida:
    #                         idUnidadMedida = 0
    #                         aux_UnidadMedida = line_rec.uom.id
    #                         UnidadMedida = self.env['datalayer'].odoo_execute_kw(odoo_externo,"uom.uom", "search_read", [('name', '=', line_rec.uom.name)], fields=["id"])
    #
    #                         if not UnidadMedida:
    #                             UnidadMedida = self.env['datalayer'].odoo_execute_kw(odoo_externo, "ir.translation", "search_read", [
    #                                 ('name', '=', 'uom.uom,name'),
    #                                 ('lang', '=', 'es_GT'),
    #                                 '|',
    #                                 ('value', '=', line_rec.uom.name),
    #                                 ('src', '=', line_rec.uom.name)], fields=["res_id"])
    #                             if not UnidadMedida:
    #                                 mensaje = "Error - Ticket " + str(rec.x_no_ticket) + " - La unidad de medida " + str(
    #                                     line_rec.uom.name) + " no existe en Odoo 13 *¡No se realizó sincronización!*"
    #                                 self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                                 raise UserError('La unidad de medida ' + str(line_rec.uom.name) + ' no existe en Odoo 13')
    #                             idUnidadMedida = UnidadMedida[0]["res_id"]
    #                         else:
    #                             idUnidadMedida = UnidadMedida[0]["id"]
    #                     #UnidadMedida = [x for x in thUnidadesMedida if x["name"] == line_rec.uom.name]
    #
    #                     #producto = self.env['datalayer'].odoo_execute_kw(odoo_externo, "product.template", "search_read", [('name', '=', line_rec.product_id.name)], fields=["id", "name"])
    #                     # producto = self.env['datalayer'].odoo_execute_kw(odoo_externo, "product.product", "search_read", [
    #                     #     ('product_tmpl_id.name', '=', line_rec.product_id.name), ('product_tmpl_id.company_id.id', '=', 1)], fields=["id"], limit=1, order='id desc')
    #                     producto = None
    #                     producto = [x for x in thProducto if x["name"] == line_rec.product_id.name]
    #                     # ----------------------------------------- V 2.0 ------------------------------------------------------------
    #                     if producto:
    #                         for linePro in producto:
    #                             # thAuxProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.product", "search_read",
    #                             #                                 [('product_tmpl_id', '=', linePro["id"])],
    #                             #                                 fields=["id"])
    #                             thAuxProducto = None
    #                             thAuxProducto = linePro["id"]
    #                             if thAuxProducto:
    #                                 break
    #                     else:
    #                         producto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"ir.translation", "search_read",
    #                                                    [('name', '=', 'product.template,name'),
    #                                                     ('lang', '=', 'es_GT'),
    #                                                     ('value', '=', line_rec.product_id.name)],
    #                                                    fields=["res_id", "name"])
    #                         if producto:
    #                             for linePro in producto:
    #                                 # thAuxProducto = self.env['datalayer'].odoo_execute_kw(odoo_externo,"product.product", "search_read", [
    #                                 #     ('product_tmpl_id', '=', linePro["res_id"])], fields=["id"])
    #                                 thAuxProducto_t = None
    #                                 thAuxProducto_t = self.env['datalayer'].odoo_execute_kw(odoo_externo, "product.product",
    #                                                                                       "search_read", [('product_tmpl_id.id', '=', linePro["res_id"]),
    #                                                                                           ('product_tmpl_id.company_id','=', 1)], fields=["id", "name"], limit=1, order='id desc')
    #                                 if thAuxProducto_t:
    #                                     thAuxProducto = thAuxProducto_t[0]["id"]
    #                                     break
    #                     if not thAuxProducto:
    #                         mensaje = "Error - Ticket " + str(
    #                             rec.x_no_ticket) + " - El producto " + str(
    #                             line_rec.product_id.name) + " no existe en Odoo 13 *¡No se realizó sincronización!*"
    #                         self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                         raise UserError(
    #                             'El producto ' + str(line_rec.product_id.name) + ' no existe en Odoo 13')
    #                     if not UnidadMedida:
    #                         mensaje = "Error - Ticket " + str(
    #                             rec.x_no_ticket) + " - La unidad de medida " + str(
    #                             line_rec.uom.name) + " no existe en Odoo 13 *¡No se realizó sincronización!*"
    #                         self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                         raise UserError(
    #                             'La unidad de medida ' + str(line_rec.uom.name) + ' no existe en Odoo 13')
    #                     logging.warning('Producto: -------------------- ' + str(thAuxProducto))
    #                     vals_line.append([])
    #                     vals_line[altura] = {
    #                         #"requisition_id": new_req,
    #                         "requisition_type": 'internal',
    #                         "product_id": thAuxProducto,
    #                         "description": str(line_rec.description),
    #                         "x_monto_fac": line_rec.x_monto / 1.12,
    #                         "qty": line_rec.qty,
    #                         "x_id_odoo_16": line_rec.id,
    #                         "uom": int(idUnidadMedida),
    #                         "x_ticket_ms": rec.x_no_ticket,
    #                     }
    #                     altura += 1
    #             try:
    #                 new_req = self.env['datalayer'].odoo_execute_kw(odoo_externo,"material.purchase.requisition", "create", vals)
    #                 rec.write({
    #                     "x_id_odoo_13": new_req,
    #                 })
    #             except Exception as e:
    #                 raise UserError('La requisicion no se creo correctamente en Odoo 13 ' + str(e))
    #             for vals_line_rec in vals_line:
    #                 try:
    #                     vals_line_rec["requisition_id"] = new_req
    #                     external_requisicion = self.env['datalayer'].odoo_execute_kw(odoo_externo,"material.purchase.requisition.line", "create", vals_line_rec)
    #                 except Exception as e:
    #                     raise UserError('La linea de requisicion no se creo correctamente en Odoo 13 ' + str(e))
    #             try:
    #                 external_requisicion = self.env['datalayer'].odoo_execute_kw(odoo_externo,"material.purchase.requisition", "requisition_confirm", [new_req])
    #             except Exception as e:
    #                 # if not new_stock_move > 0:
    #                 raise UserError('La transferencia no se creo correctamente en Odoo 13 ' + str(e))
    #             try:
    #                 external_requisicion = self.env['datalayer'].odoo_execute_kw(odoo_externo,"material.purchase.requisition",
    #                                                        "manager_approve", [new_req])
    #             except Exception as e:
    #                 # if not new_stock_move > 0:
    #                 raise UserError('La transferencia no se creo correctamente en Odoo 13 ' + str(e))
    #             try:
    #                 external_requisicion = self.env['datalayer'].odoo_execute_kw(odoo_externo,"material.purchase.requisition", "user_approve",
    #                                                        [new_req])
    #             except Exception as e:
    #                 # if not new_stock_move > 0:
    #                 raise UserError('La transferencia no se creo correctamente en Odoo 13 ' + str(e))
    #             try:
    #                 external_requisicion = self.env['datalayer'].odoo_execute_kw(odoo_externo,"material.purchase.requisition", "request_stock",[new_req])
    #             # estas son las transferencias de Odoo 16 para pasar este idtransferencia a odoo 13
    #             except Exception as e:
    #                 # if not new_stock_move > 0:
    #                 raise UserError('La transferencia no se creo correctamente en Odoo 13 ' + str(e))
    #             thTransferencia16 = self.env["stock.picking"].search(
    #                 [('custom_requisition_id', '=', rec.id)])
    #             for trans in thTransferencia16:
    #                 thTransferencia13 = self.env['datalayer'].odoo_execute_kw(odoo_externo,"stock.picking", "search_read", [
    #                     ('custom_requisition_id', '=', new_req),
    #                     ('x_id_odoo_16', '=', False)],
    #                                                     fields=["id", "partner_id", "scheduled_date",
    #                                                             "custom_requisition_id", "user_id",
    #                                                             "move_ids_without_package", "x_id_odoo_16",
    #                                                             "x_ticket_ms"])
    #                 if not thTransferencia13:
    #                     mensaje = "Error - Ticket " + str(
    #                         rec.x_no_ticket) + " - La transferencia no existe en Odoo 13, la requisicion tiene mas de 1 transferencia en Odoo 16"
    #                     self.EnviarMensaje(idchat, mensaje, urlimagen)
    #                     raise UserError(
    #                         'La transferencia no existe en Odoo 13, hay que eliminar las requisicones de odoo 16 que estan de mas')
    #                 vals_trans = {
    #                     "x_id_odoo_16": trans.id,
    #                     "x_ticket_ms": rec.x_no_ticket,
    #                 }
    #                 thActualiza2 = self.env['datalayer'].odoo_execute_kw(odoo_externo,"stock.picking", "write", [thTransferencia13[0]["id"]],
    #                                                vals_trans)
    #                 trans.write({
    #                     "x_id_odoo_13": thTransferencia13[0]["id"],
    #                 })
    #             mensaje = "Ticket " + str(rec.x_no_ticket) + " - requisicion creada en Odoo 13"
    #             self.EnviarMensaje(idchat, mensaje, urlimagen)
    #         else:
    #             mensaje = "Error - Ticket " + str(rec.x_no_ticket) + " - La requisicion ya existe en Odoo 13 *¡No se realizó sincronización!*"
    #             rec.write({
    #                 'x_id_odoo_13': int(existe[0]["id"]),
    #             })
    #             self.EnviarMensaje(idchat, mensaje, urlimagen)
    #             # ----------------------------------------- FIN V 2.0 ------------------------------------------------------------
    #     else:
    #         rec.write({
    #             'x_id_odoo_13': 1,
    #         })
    # @api.multi
    def user_approve(self):
        for rec in self:
            rec.userrapp_date = fields.Date.today()
            rec.approve_employee_id = self.env["hr.employee.ticket"].search(
                [("user_id", "=", self.env.uid)], limit=1
            )
            rec.state = "approve"

    # @api.multi
    def reset_draft(self):
        for rec in self:
            rec.state = "draft"

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        pick_vals = {
            "product_id": line.product_id.id,
            "product_uom_qty": line.qty,
            "product_uom": line.uom.id,
            "location_id": self.location_id.id,
            "location_dest_id": self.dest_location_id.id,
            "name": line.product_id.name,
            "picking_type_id": self.custom_picking_type_id.id,
            "picking_id": stock_id.id,
            "custom_requisition_line_id": line.id,
            "company_id": line.requisition_id.company_id.id,
        }
        return pick_vals

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        po_line_vals = {
            "product_id": line.product_id.id,
            "name": line.product_id.name,
            "product_qty": line.qty,
            "product_uom": line.uom.id,
            "date_planned": fields.Date.today(),
            "price_unit": line.product_id.standard_price,
            "order_id": purchase_order.id,
            "account_analytic_id": self.analytic_account_id.id,
            "custom_requisition_line_id": line.id,
        }
        return po_line_vals

    # @api.multi
    def request_stock(self):
        stock_obj = self.env["stock.picking"]
        move_obj = self.env["stock.move"]
        # internal_obj = self.env['stock.picking.type'].search([('code','=', 'internal')], limit=1)
        # internal_obj = self.env['stock.location'].search([('usage','=', 'internal')], limit=1)
        purchase_obj = self.env["purchase.order"]
        purchase_line_obj = self.env["purchase.order.line"]
        #         if not internal_obj:
        #             raise UserError(_('Please Specified Internal Picking Type.'))
        for rec in self:
            if not rec.requisition_line_ids:
                raise Warning(_("Please create some requisition lines."))
            if any(
                line.requisition_type == "internal" for line in rec.requisition_line_ids
            ):
                if not rec.location_id.id:
                    raise Warning(
                        _("Select Source location under the picking details.")
                    )
                if not rec.custom_picking_type_id.id:
                    raise Warning(_("Select Picking Type under the picking details."))
                if not rec.dest_location_id:
                    raise Warning(
                        _("Select Destination location under the picking details.")
                    )
                #                 if not rec.employee_id.dest_location_id.id or not rec.employee_id.department_id.dest_location_id.id:
                #                     raise Warning(_('Select Destination location under the picking details.'))
                # Alex 09 03 2024 Una condicion para pasar la restriccion de contacto de la empresa de odoo 16
                if (
                    rec.employee_id.company_id == rec.company_id.id
                    or rec.employee_id.company_id == False
                ):
                    thPartner = rec.employee_id.work_contact_id
                else:
                    thPartner = rec.requisiton_responsible_id.work_contact_id
                picking_vals = {
                    #'partner_id' : rec.employee_id.sudo().address_home_id.id, Alex 09 03 2024
                    "partner_id": thPartner,
                    #'min_date' : fields.Date.today(),
                    "location_id": rec.location_id.id,
                    "location_dest_id": rec.dest_location_id.id,  # and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
                    "picking_type_id": rec.custom_picking_type_id.id,  # internal_obj.id,
                    "note": rec.reason,
                    "custom_requisition_id": rec.id,
                    "origin": rec.name,
                    "company_id": rec.company_id.id,
                }
                stock_id = stock_obj.create(picking_vals)
                delivery_vals = {
                    "delivery_picking_id": stock_id.id,
                }
                rec.write(delivery_vals)

            po_dict = {}
            for line in rec.requisition_line_ids:
                if (
                    line.requisition_type == "internal"
                    and line.product_id.detailed_type != "service"
                ):
                    pick_vals = rec._prepare_pick_vals(line, stock_id)
                    move_id = move_obj.sudo().create(pick_vals)
                # else:
                if line.requisition_type == "purchase":  # 10/12/2019
                    if not line.partner_id:
                        raise Warning(
                            _(
                                "Please enter atleast one vendor on Requisition Lines for Requisition Action Purchase"
                            )
                        )
                    for partner in line.partner_id:
                        if partner not in po_dict:
                            po_vals = {
                                "partner_id": partner.id,
                                "currency_id": rec.env.user.company_id.currency_id.id,
                                "date_order": fields.Date.today(),
                                #                                'company_id':rec.env.user.company_id.id,
                                "company_id": rec.company_id.id,
                                "custom_requisition_id": rec.id,
                                "origin": rec.name,
                            }
                            purchase_order = purchase_obj.create(po_vals)
                            po_dict.update({partner: purchase_order})
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
                            #                            {
                            #                                     'product_id': line.product_id.id,
                            #                                     'name':line.product_id.name,
                            #                                     'product_qty': line.qty,
                            #                                     'product_uom': line.uom.id,
                            #                                     'date_planned': fields.Date.today(),
                            #                                     'price_unit': line.product_id.lst_price,
                            #                                     'order_id': purchase_order.id,
                            #                                     'account_analytic_id': rec.analytic_account_id.id,
                            #                            }
                            purchase_line_obj.sudo().create(po_line_vals)
                        else:
                            purchase_order = po_dict.get(partner)
                            po_line_vals = rec._prepare_po_line(line, purchase_order)
                            #                            po_line_vals =  {
                            #                                 'product_id': line.product_id.id,
                            #                                 'name':line.product_id.name,
                            #                                 'product_qty': line.qty,
                            #                                 'product_uom': line.uom.id,
                            #                                 'date_planned': fields.Date.today(),
                            #                                 'price_unit': line.product_id.lst_price,
                            #                                 'order_id': purchase_order.id,
                            #                                 'account_analytic_id': rec.analytic_account_id.id,
                            #                            }
                            purchase_line_obj.sudo().create(po_line_vals)
            rec.state = "stock"
            # 02 05 2024 Alex
            # if not rec.x_id_odoo_13 and rec.orden_produccion and not rec.x_ticket:
            #     rec.sincroniza_requisicion('Odoo 13', rec)

    # @api.multi
    # def request_stock_interno(self):
    #     stock_obj = self.env['stock.picking']
    #     move_obj = self.env['stock.move']
    #     # internal_obj = self.env['stock.picking.type'].search([('code','=', 'internal')], limit=1)
    #     # internal_obj = self.env['stock.location'].search([('usage','=', 'internal')], limit=1)
    #     purchase_obj = self.env['purchase.order']
    #     purchase_line_obj = self.env['purchase.order.line']
    #     #         if not internal_obj:
    #     #             raise UserError(_('Please Specified Internal Picking Type.'))
    #     for rec in self:
    #         if not rec.requisition_line_ids:
    #             raise Warning(_('Please create some requisition lines.'))
    #         if any(line.requisition_type == 'internal' for line in rec.requisition_line_ids):
    #             if not rec.location_id.id:
    #                 raise Warning(_('Select Source location under the picking details.'))
    #             if not rec.custom_picking_type_id.id:
    #                 raise Warning(_('Select Picking Type under the picking details.'))
    #             if not rec.dest_location_id:
    #                 raise Warning(_('Select Destination location under the picking details.'))
    #             #                 if not rec.employee_id.dest_location_id.id or not rec.employee_id.department_id.dest_location_id.id:
    #             #                     raise Warning(_('Select Destination location under the picking details.'))
    #             picking_vals = {
    #                 'partner_id': rec.employee_id.sudo().address_home_id.id,
    #                 # 'min_date' : fields.Date.today(),
    #                 'location_id': 56, # 56 es el ID de BDIP/STOCK #rec.location_id.id,
    #                 'location_dest_id': 24, # 24 B01/BD Central Dimasa #rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
    #                 'picking_type_id': 47, # 47 es el ID de traslado de insumos #rec.custom_picking_type_id.id,  # internal_obj.id,
    #                 'note': rec.reason,
    #                 'custom_requisition_id': rec.id,
    #                 'origin': rec.name,
    #                 'company_id': rec.company_id.id,
    #
    #             }
    #             stock_id = stock_obj.sudo().create(picking_vals)
    #             delivery_vals = {
    #                 'delivery_picking_id': stock_id.id,
    #             }
    #             rec.write(delivery_vals)
    #
    #         po_dict = {}
    #         for line in rec.requisition_line_ids:
    #             if line.requisition_type == 'internal' and line.product_id.detailed_type != 'service':
    #                 pick_vals = rec._prepare_pick_vals(line, stock_id)
    #                 move_id = move_obj.sudo().create(pick_vals)
    #             # else:
    #             if line.requisition_type == 'purchase':  # 10/12/2019
    #                 if not line.partner_id:
    #                     raise Warning(
    #                         _('Please enter atleast one vendor on Requisition Lines for Requisition Action Purchase'))
    #                 for partner in line.partner_id:
    #                     if partner not in po_dict:
    #                         po_vals = {
    #                             'partner_id': partner.id,
    #                             'currency_id': rec.env.user.company_id.currency_id.id,
    #                             'date_order': fields.Date.today(),
    #                             #                                'company_id':rec.env.user.company_id.id,
    #                             'company_id': rec.company_id.id,
    #                             'custom_requisition_id': rec.id,
    #                             'origin': rec.name,
    #                         }
    #                         purchase_order = purchase_obj.create(po_vals)
    #                         po_dict.update({partner: purchase_order})
    #                         po_line_vals = rec._prepare_po_line(line, purchase_order)
    #                         #                            {
    #                         #                                     'product_id': line.product_id.id,
    #                         #                                     'name':line.product_id.name,
    #                         #                                     'product_qty': line.qty,
    #                         #                                     'product_uom': line.uom.id,
    #                         #                                     'date_planned': fields.Date.today(),
    #                         #                                     'price_unit': line.product_id.lst_price,
    #                         #                                     'order_id': purchase_order.id,
    #                         #                                     'account_analytic_id': rec.analytic_account_id.id,
    #                         #                            }
    #                         purchase_line_obj.sudo().create(po_line_vals)
    #                     else:
    #                         purchase_order = po_dict.get(partner)
    #                         po_line_vals = rec._prepare_po_line(line, purchase_order)
    #                         #                            po_line_vals =  {
    #                         #                                 'product_id': line.product_id.id,
    #                         #                                 'name':line.product_id.name,
    #                         #                                 'product_qty': line.qty,
    #                         #                                 'product_uom': line.uom.id,
    #                         #                                 'date_planned': fields.Date.today(),
    #                         #                                 'price_unit': line.product_id.lst_price,
    #                         #                                 'order_id': purchase_order.id,
    #                         #                                 'account_analytic_id': rec.analytic_account_id.id,
    #                         #                            }
    #                         purchase_line_obj.sudo().create(po_line_vals)
    #             rec.state = 'stock'

    # @api.multi
    def action_received(self):
        # if not self.employee_id.mobile_phone:
        #     raise UserError('El empleado '+self.employee_id.name+' no tiene registrado un telefono corporativo')
        for rec in self:
            rec.receive_date = fields.Date.today()
            rec.state = "receive"
            # if rec.orden_produccion:
            #     rec.orden_produccion.write({'qty_producing': rec.orden_produccion.product_qty})
            #     for line in rec.orden_produccion.move_raw_ids:
            #         line.write({
            #             'quantity_done': line.product_uom_qty})
            # idchat = '+502' + self.employee_id.mobile_phone
            # mensaje = "MATERIALES LISTOS Saludos "+self.employee_id.name+" materiales listos para el ticket #"+str(self.x_no_ticket)+" la tarea a realizar es "+self.x_ticket.name+" en "+self.analytic_account_id.name
            # urlimagen = False
            # self.EnviarMensaje(idchat, mensaje, urlimagen)  # Llama al método EnviarMensaje de la instancia whatsapp_obj

    # @api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"

    # @api.onchange('employee_id')
    # def set_department(self):
    #     for rec in self:
    #         rec.department_id = rec.employee_id.department_id.id
    #         # Me coloca en blanco el departamento 13 02 2024 Alex
    #         # rec.dest_location_id = rec.employee_id.sudo().dest_location_id.id or rec.employee_id.sudo().department_id.dest_location_id.id

    @api.onchange("department_id")
    def set_dest_location(self):
        for record in self:
            if (
                record.department_id.parent_id.name
                and "Mantenimiento" in record.department_id.parent_id.name
            ):
                record.location_id = 192
                record.dest_location_id = 5
                record.custom_picking_type_id = 137
                thAutorizador = self.env["ir.config_parameter"].search(
                    [("key", "=", "Gerente MTO")], order="id desc", limit=1
                )
                thAutorizador_id = self.env["hr.employee.ticket"].search(
                    [("name", "=", thAutorizador.value)], limit=1
                )
                record.requisiton_responsible_id = thAutorizador_id

            elif (
                record.department_id.parent_id.name
                and "Servicios Generales" in record.department_id.parent_id.name
            ):
                record.location_id = 240
                record.dest_location_id = 5
                record.custom_picking_type_id = 203
                thAutorizador = self.env["ir.config_parameter"].search(
                    [("key", "=", "Gerente ServG")], order="id desc", limit=1
                )
                thAutorizador_id = self.env["hr.employee.ticket"].search(
                    [("name", "=", thAutorizador.value)], limit=1
                )
                record.requisiton_responsible_id = thAutorizador_id

    # @api.multi
    def show_picking(self):
        for rec in self:
            res = self.env.ref("stock.action_picking_tree_all")
            res = res.read()[0]
            res["domain"] = str([("custom_requisition_id", "=", rec.id)])
        return res

    # @api.multi
    def action_show_po(self):
        for rec in self:
            purchase_action = self.env.ref("purchase.purchase_rfq")
            purchase_action = purchase_action.read()[0]
            purchase_action["domain"] = str([("custom_requisition_id", "=", rec.id)])
        return purchase_action

    @api.onchange("x_ticket")
    def onchange_x_ticket(self):
        for rec in self:
            if rec.x_ticket:
                rec.analytic_account_id = rec.x_ticket.analytic_account_id.id
                rec.employee_id = rec.x_ticket.x_asignado.id
                rec.x_ticket = rec.x_ticket.id
                if rec.x_ticket.description:
                    rec.reason = (
                        "Ticket No.: "
                        + str(rec.x_ticket.x_ticket)
                        + "\nDescripción: "
                        + str(html2text.html2text(rec.x_ticket.description))
                    )

    # @api.depends('x_ticket', 'orden_produccion')
    # def _compute_analytic_account_id(self):
    #     for rec in self:
    #         if rec.x_ticket:
    #             rec.analytic_account_id = rec.x_ticket.analytic_account_id.id
    #         else:
    #             if rec.orden_produccion:
    #                 rec.analytic_account_id = rec.orden_produccion.analytic_account_id.id
    #             else:
    #                 rec.analytic_account_id = False

    # @api.depends('employee_id', 'x_ticket', 'orden_produccion')
    # def _compute_employee_id(self):
    #     for rec in self:
    #         if rec.x_ticket:
    #             rec.employee_id = rec.x_ticket.x_asignado.id
    #         else:
    #             if rec.orden_produccion:
    #                 rec.employee_id = rec.orden_produccion.asignado.id
    #             else:
    #                 rec.employee_id = False

    # @api.onchange('orden_produccion')
    # def _onchange_orden_produccion(self):
    #     for rec in self:
    #         if rec.orden_produccion:
    #             rec.employee_id = rec.orden_produccion.asignado.id
    #             rec.analytic_account_id = rec.orden_produccion.analytic_account_id.id
    #             if rec.orden_produccion.mesa_servicio.x_descripcion:
    #                 rec.reason = "Ticket No.: " + str(rec.orden_produccion.ticket) + "\nDescripción: " + str(
    #                     html2text.html2text(rec.orden_produccion.mesa_servicio.x_descripcion))

    @api.onchange("employee_id")
    def onchange_employee_id(self):
        for rec in self:
            rec.requisiton_responsible_id = rec.employee_id.parent_id.id

    @api.onchange("x_margen_p")
    def onchange_x_margen_p(self):
        for rec in self:
            if (sum(line.x_monto for line in rec.requisition_line_ids)) != 0:
                rec.x_costo_total = sum(
                    line.x_monto for line in rec.requisition_line_ids
                )  # + rec.x_margen + rec.x_iva)

    @api.onchange("x_margen")
    def onchange_x_margen(self):
        for rec in self:
            if (sum(line.x_monto for line in rec.requisition_line_ids)) != 0:
                rec.x_costo_total = sum(
                    line.x_monto for line in rec.requisition_line_ids
                )  # + rec.x_margen + rec.x_iva)

    @api.model
    def _compute_costo_total(self):
        for rec in self:
            if rec.x_margen_p != 0:
                rec.x_costo_total = sum(
                    line.x_monto for line in rec.requisition_line_ids
                )  # + rec.x_margen + rec.x_iva

    @api.onchange("requisition_line_ids")
    def onchange_requisition_line_ids(self):
        for rec in self:
            if rec.x_ticket and not rec.orden_produccion:
                rec.x_costo_total = sum(
                    line.x_monto for line in rec.requisition_line_ids
                )
            if not rec.x_ticket and not rec.orden_produccion:
                rec.x_costo_total = sum(
                    line.x_monto for line in rec.requisition_line_ids
                )
            elif rec.orden_produccion and not rec.x_ticket:
                thMateriales = sum(
                    line.x_monto
                    for line in rec.requisition_line_ids
                    if line.product_id.detailed_type != "service"
                )
                thServicios = (
                    sum(
                        line.x_monto
                        for line in rec.requisition_line_ids
                        if line.product_id.detailed_type == "service"
                    )
                ) * 1.12
                thManoObra = self.env["ir.config_parameter"].search(
                    [("key", "=", "Porcentaje Mano de Obra")], order="id desc", limit=1
                )
                thMargenGanancia = self.env["ir.config_parameter"].search(
                    [("key", "=", "Margen Ganancia")], order="id desc", limit=1
                )
                thMargenManoObral = thMateriales * (float(thManoObra.value) / 100)
                thMargenGanancial = thMargenManoObral * (
                    float(thMargenGanancia.value) / 100
                )
                rec.x_costo_total = (
                    thMateriales + thServicios + thMargenManoObral + thMargenGanancial
                )

    # @api.depends('orden_produccion', 'x_ticket')
    # def _compute_custom_picking_type_id(self):
    #     for rec in self:
    #         if rec.orden_produccion and not rec.x_ticket:
    #             if rec.orden_produccion.mesa_servicio.x_proyecto:
    #                 rec.custom_picking_type_id = rec.orden_produccion.mesa_servicio.x_proyecto.custom_picking_type_id.id
    #             else:
    #                 rec.custom_picking_type_id = 47 # Traslado de insumos
    #         elif not rec.orden_produccion and rec.x_ticket:
    #             rec.custom_picking_type_id = 46 # Consumo de materiales de DIPROSA a DIMASA
    #         else:
    #             rec.custom_picking_type_id = False

    # @api.onchange('custom_picking_type_id')
    # def onchange_custom_picking_type_id(self):
    #     for rec in self:
    #         if rec.custom_picking_type_id:
    #             rec.location_id = rec.custom_picking_type_id.default_location_src_id.id
    #             rec.dest_location_id = rec.custom_picking_type_id.default_location_dest_id.id
    #         else:
    #             raise UserError('El tipo de operacion esta vacio, en la requisicion de matareiales')
