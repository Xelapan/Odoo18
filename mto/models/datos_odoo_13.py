from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.http import request
import json


class SaleOrder13Report(models.Model):
    _name = "sale.order.13.report"
    _description = "Consolidado Tickets"
    _auto = True
    # _auto = False  # Indica que este modelo no tiene una tabla correspondiente en la base de datos de Odoo

    ticket = fields.Integer(string="Ticket")
    mesa_servicio = fields.Many2one("x_mesa_servicio", string="Mesa de Servicio")
    solicitud = fields.Many2one("helpdesk.ticket", string="Solicitud")
    area = fields.Char(string="Area")
    asignado = fields.Char(string="Asignado")
    etapa = fields.Char(string="Etapa")
    tipo = fields.Char(string="Tipo")
    fecha_creado = fields.Datetime(string="Fecha Creado")
    fecha_concluido = fields.Datetime(string="Fecha Concluido")
    fecha_rechazo = fields.Datetime(string="Fecha Rechazo")
    requisicion = fields.Many2one(
        "material.purchase.requisition", string="Requisicion 16"
    )
    fecha_requisicion = fields.Datetime(string="Fecha Requisicion 16")
    estado_requisicion = fields.Char(string="Estado Requisicion 16")
    req_total = fields.Float(string="Total Requisicion 16")
    venta16 = fields.Many2one("sale.order", string="Venta 16")
    fecha_venta16 = fields.Datetime(string="Fecha Venta 16")
    estado_venta16 = fields.Char(string="Estado Venta 16")
    venta_total16 = fields.Float(string="Total Venta 16")
    venta_firma16 = fields.Datetime(string="Fecha Confirma Venta")
    requisicion_13 = fields.Char(string="Requisicion 13")
    fecha_requisicion13 = fields.Datetime(string="Fecha Requisicion 13")
    estado_requisicion13 = fields.Char(string="Estado Requisicion 13")
    venta13 = fields.Char(string="Venta 13")
    fecha_venta13 = fields.Datetime(string="Fecha Venta 13")
    estado_venta13 = fields.Char(string="Estado Venta 13")
    venta_total13 = fields.Float(string="Total Venta 13")
    estado_factura13 = fields.Char(string="Factura 13")
    x_fecha_creacion = fields.Date(
        string="Fecha Creación",
        default=lambda self: fields.Date.today() - timedelta(days=365),
    )
    session_identifier = fields.Char(
        string="Session Token", required=True
    )  # Campo para el token de sesión

    @api.model
    def action_open_consolidado_ticket(self):
        session_identifier = request.session.sid
        return {
            "name": "Consolidado Tickets",
            "type": "ir.actions.act_window",
            "res_model": "sale.order.13.report",
            "view_mode": "list",
            "view_id": self.env.ref("mto.view_sale_order_13_report_tree").id,
            "search_view_id": self.env.ref("mto.view_sale_order_13_report_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    @api.model
    def delete_old_ticket_records(self):
        # Define el umbral de 24 horas
        time_threshold = datetime.now() - timedelta(hours=24)
        # Busca los registros que son más antiguos de 24 horas
        old_records = self.search([("create_date", "<", time_threshold)])
        if old_records:
            old_records.unlink()

    # def create_view(self):
    #     # Ejecutar la consulta y crear la vista materializada
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE VIEW sale_order_13_report AS(
    #         select
    #             ROW_NUMBER() OVER (ORDER BY xms.x_solicitud ASC) AS id,
    #             xms.x_solicitud ticket,
    #             xms.id mesa_servicio,


# 			ht.id solicitud,
# 			htm.name->>'es_GT' as area,
# 			hpy.name asignado,
# 			js.name->>'es_GT' as etapa,
#             htt.name->>'es_GT' as tipo,
#             xms.x_fecha_creacion fecha_creado,
#             xms.x_fecha_concluido fecha_concluido,
# 			xms.x_fecha_rechazo fecha_rechazo,
#             mpr.id requisicion,
#             mpr.request_date  fecha_requisicion,
#             case
#                 when mpr.state = 'draft' then
#                     'NUEVO'
#                 when mpr.state = 'dept_confirm' then
#                     'ESPERA APROBACION MTO'
#                 when mpr.state = 'ir_approve' then
#                     'APROBACION MTO'
#                 when mpr.state = 'approve' then
#                     'APROBACION CLIENTE'
#                 when mpr.state = 'stock' then
#                     'MATERIALES SOLICITADOS'
#                 when mpr.state = 'receive' then
#                     'MATERIALES ENTREGADOS'
#                 when mpr.state = 'cancel' then
#                     'CANCELADO'
#                 when mpr.state = 'reject' then
#                     'RECHAZADO'
#                 else
#                     null
#             end estado_requisicion,
#             mpr.x_costo_total req_total,
#             so16.id venta16,
#             so16.create_date fecha_venta16,
#             so16.state estado_venta16,
#             so16.amount_total venta_total16,
# 			case
# 				when req13.id is not null then
# 				concat('https://corporativo.siesa.biz/web#id=',req13.id,'&action=688&model=material.purchase.requisition&view_type=form&cids=1&menu_id=494')
# 				else null
# 			end requisicion_13,
# 			req13.request_date fecha_requisicion13,
# 			case
#                 when req13.state = 'draft' then
#                     'NUEVO'
#                 when req13.state = 'dept_confirm' then
#                     'EN ESPERA DE APROBACION DEL DEPARTAMENTO'
#                 when req13.state = 'ir_approve' then
#                     'ESPERANDO APROBACION DE IR.'
#                 when req13.state = 'approve' then
#                     'APROBADO'
#                 when req13.state = 'stock' then
#                     'PEDIDO DE COMPRA CREADO'
#                 when req13.state = 'receive' then
#                     'RECIBIDO'
#                 when req13.state = 'cancel' then
#                     'CANCELADO'
#                 when req13.state = 'reject' then
#                     'RECHAZADO'
#                 else
#                     null
#             end estado_requisicion13,
#             case
#                 when so13.id is not null then
#                     concat('https://corporativo.siesa.biz/web#id=',so13.id,'&action=581&model=sale.order&view_type=form&cids=1&menu_id=394')
#                 else
#                     null
#             end venta13,
#             so13.create_date fecha_venta13,
#             so13.state estado_venta13,
#             so13.amount_total venta_total13,
#             case
#                 when so13.invoice_status = 'invoiced' then
#                     'Facturado'
#                 when so13.invoice_status = 'to invoice' then
#                     'Por Facturar'
#                 when so13.invoice_status = 'no' then
#                     'Nada que Facturar'
#                 when so13.invoice_status = 'upselling' then
#                     'Oportunidad de Upselling'
#                 else
#                     null
#             end estado_factura13
#             from x_mesa_servicio xms
# 			left join helpdesk_ticket ht on ht.x_ticket = xms.x_solicitud
# 			left join helpdesk_team htm on htm.id = ht.team_id
# 			left join helpdesk_stage js on js.id = ht.stage_id
# 			left join hr_employee hpy on hpy.id = ht.x_asignado
#             left join helpdesk_ticket_type htt on htt.id = ht.ticket_type_id
#             left join sale_order so16 on so16.x_no_ticket = xms.x_solicitud
#             left join material_purchase_requisition mpr on mpr.x_no_ticket = xms.x_solicitud
# 			left join material_purchase_requisition_13 req13 on req13.x_ticket_ms = xms.x_solicitud and req13.x_ticket_ms is not null
#             left join sale_order_13 so13 on so13.x_ticket_ms = xms.x_solicitud and so13.x_ticket_ms is not null
#             where xms.x_tipo_solicitud_id != 5
#             order by xms.x_solicitud asc
#         )
#     """)
