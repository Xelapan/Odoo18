from odoo import models, fields, api, _
import uuid

from odoo.exceptions import UserError
from odoo.http import request

# class HrPayslipPrestacionesWizard(models.TransientModel):
#     _name = 'account.account.v.wizard'
#     _description = 'Visor Cuentas Contables Wizard'
#
#     date_to = fields.Date(string='Fecha al', required=True)
#     company_id = fields.Many2one('res.company', string='Compañía', required=True, default=lambda self: self.env.company)
#     account_ids = fields.Many2many('account.account', string="Cuenta")
#     journal_ids = fields.Many2many('account.journal', string="Diario")
#     #analytic_account_ids = fields.Many2many('account.analytic.account', string="Cuenta Analítica")
#
#
#     def open_prestaciones_at_date(self):
#         self.ensure_one()
#         date_to = self.date_to
#
#
#         # Eliminar datos anteriores para no duplicar
#         self.env['account.account.v'].search([]).unlink()
#         domain = [('date', '<=', date_to), ('company_id', '=', self.company_id.id),('move_id.state', '=', 'posted')]
#         if self.account_ids:
#             domain.append(('account_id', 'in', self.account_ids.ids))
#         if self.journal_ids:
#             domain.append(('journal_id', 'in', self.journal_ids.ids))
#         # if self.analytic_account_ids:
#         #     domain.append(('analytic_account_id', 'in', self.analytic_account_ids.ids))
#         results = self.env['account.move.line'].search(domain)
#         visor_cuentas_contables = self.env['account.account.v']
#         for result in results:
#             visor_cuentas_contables.create({
#                 'move_line_id': result.id,
#                 'fecha': result.date,
#                 'move_id': result.move_id.id,
#                 'account_id': result.account_id.id,
#                 'journal_id': result.journal_id.id,
#                 'balance': result.balance,
#                 'analytic_distribution': result.analytic_distribution,
#                 'partner_id': result.partner_id.id,
#                 'tax_base_amount': result.tax_base_amount,
#             })
#
#         return {
#             'name': 'Visor Cuentas Contables',
#             'type': 'ir.actions.act_window',
#             'res_model': 'account.account.v',
#             'view_mode': 'tree',
#             'target': 'current',
#         }


class SaleOrder13ReportWizard(models.TransientModel):
    _name = "sale.order.13.report.wizard"
    _description = "Consolidado Tickets 13 - 16 Wizard"

    date_from = fields.Date(string="Fecha del")
    date_to = fields.Date(string="Fecha al")
    area_ids = fields.Many2many("helpdesk.team", string="Area")
    employee_ids = fields.Many2many("hr.employee", string="Asignado")
    no_ticket = fields.Integer(string="No. Ticket")

    def open_consolidado_ticket(self):
        self.ensure_one()

        # Obtener el session_id de la sesión HTTP actual
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual

        # Eliminar datos anteriores para esta sesión
        self.env["sale.order.13.report"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        query = """
            select 
                ROW_NUMBER() OVER (ORDER BY xms.x_solicitud ASC) AS id,
                xms.x_solicitud ticket,
                xms.id mesa_servicio,
                ht.id solicitud,
                htm.name->>'es_GT' as area,
                hpy.name asignado,
                js.name->>'es_GT' as etapa,
                htt.name->>'es_GT' as tipo,
                xms.x_fecha_creacion fecha_creado,
                xms.x_fecha_concluido fecha_concluido,
                xms.x_fecha_rechazo fecha_rechazo,
                mpr.id requisicion,
                mpr.request_date fecha_requisicion,
                case 
                    when mpr.state = 'draft' then 'NUEVO' 
                    when mpr.state = 'dept_confirm' then 'ESPERA APROBACION MTO'
                    when mpr.state = 'ir_approve' then 'APROBACION MTO'
                    when mpr.state = 'approve' then 'APROBACION CLIENTE'
                    when mpr.state = 'stock' then 'MATERIALES SOLICITADOS'
                    when mpr.state = 'receive' then 'MATERIALES ENTREGADOS'
                    when mpr.state = 'cancel' then 'CANCELADO'
                    when mpr.state = 'reject' then 'RECHAZADO'
                    else null 
                end estado_requisicion,
                mpr.x_costo_total req_total,
                so16.id venta16,
                so16.create_date fecha_venta16,
                so16.state estado_venta16,
                so16.amount_total venta_total16,
                so16.signed_on venta_firma16,
                case 
                    when req13.id is not null then
                        concat('https://corporativo.siesa.biz/web#id=', req13.id, '&action=688&model=material.purchase.requisition&view_type=form&cids=1&menu_id=494')
                    else null
                end requisicion_13,
                req13.request_date fecha_requisicion13,
                case 
                    when req13.state = 'draft' then 'NUEVO' 
                    when req13.state = 'dept_confirm' then 'EN ESPERA DE APROBACION DEL DEPARTAMENTO'
                    when req13.state = 'ir_approve' then 'ESPERANDO APROBACION DE IR.'
                    when req13.state = 'approve' then 'APROBADO'
                    when req13.state = 'stock' then 'PEDIDO DE COMPRA CREADO'
                    when req13.state = 'receive' then 'RECIBIDO'
                    when req13.state = 'cancel' then 'CANCELADO'
                    when req13.state = 'reject' then 'RECHAZADO'
                    else null
                end estado_requisicion13,
                case 
                    when so13.id is not null then
                        concat('https://corporativo.siesa.biz/web#id=', so13.id, '&action=581&model=sale.order&view_type=form&cids=1&menu_id=394') 
                    else
                        null
                end venta13,
                so13.create_date fecha_venta13,
                so13.state estado_venta13,
                so13.amount_total venta_total13,
                case
                    when so13.invoice_status = 'invoiced' then 'Facturado'
                    when so13.invoice_status = 'to invoice' then 'Por Facturar'
                    when so13.invoice_status = 'no' then 'Nada que Facturar'
                    when so13.invoice_status = 'upselling' then 'Oportunidad de Upselling'
                    else null
                end estado_factura13
                from x_mesa_servicio xms
                left join helpdesk_ticket ht on ht.x_ticket = xms.x_solicitud
                left join helpdesk_team htm on htm.id = ht.team_id
                left join helpdesk_stage js on js.id = ht.stage_id
                left join hr_employee hpy on hpy.id = ht.x_asignado
                left join helpdesk_ticket_type htt on htt.id = ht.ticket_type_id
                left join sale_order so16 on so16.x_no_ticket = xms.x_solicitud
                left join material_purchase_requisition mpr on mpr.x_no_ticket = xms.x_solicitud
                left join material_purchase_requisition_13 req13 on req13.x_ticket_ms = xms.x_solicitud and req13.x_ticket_ms is not null
                left join sale_order_13 so13 on so13.x_ticket_ms = xms.x_solicitud and so13.x_ticket_ms is not null
                where 1=1
        """

        # Parámetros dinámicos
        params = []

        # Condiciones dinámicas para fecha
        if self.date_from:
            query += " and xms.x_fecha_creacion >= %s"
            params.append(self.date_from)

        if self.date_to:
            query += " and xms.x_fecha_creacion <= %s"
            params.append(self.date_to)

        # Condición dinámica para áreas
        if self.area_ids:
            query += " and htm.id in %s"
            params.append(tuple(self.area_ids.ids))

        # Condición dinámica para empleados
        if self.employee_ids:
            query += " and hpy.id in %s"
            params.append(tuple(self.employee_ids.ids))

        # Condición dinámica para el número de ticket
        if self.no_ticket:
            query += " and xms.x_solicitud = %s"
            params.append(self.no_ticket)

        query += " order by xms.x_solicitud asc"

        # Ejecutar la consulta con los parámetros
        self.env.cr.execute(query, tuple(params))

        thQuery = self.env.cr.dictfetchall()
        visor_consolidado = self.env["sale.order.13.report"]
        for result in thQuery:
            visor_consolidado.create(
                {
                    "session_identifier": session_identifier,  # Asociar los datos a la cookie de sesión
                    "ticket": result["ticket"],
                    "mesa_servicio": result["mesa_servicio"],
                    "solicitud": result["solicitud"],
                    "area": result["area"],
                    "asignado": result["asignado"],
                    "etapa": result["etapa"],
                    "tipo": result["tipo"],
                    "fecha_creado": result["fecha_creado"],
                    "fecha_concluido": result["fecha_concluido"],
                    "fecha_rechazo": result["fecha_rechazo"],
                    "requisicion": result["requisicion"],
                    "fecha_requisicion": result["fecha_requisicion"],
                    "estado_requisicion": result["estado_requisicion"],
                    "req_total": result["req_total"],
                    "venta16": result["venta16"],
                    "fecha_venta16": result["fecha_venta16"],
                    "estado_venta16": result["estado_venta16"],
                    "venta_total16": result["venta_total16"],
                    "venta_firma16": result["venta_firma16"],
                    "requisicion_13": result["requisicion_13"],
                    "fecha_requisicion13": result["fecha_requisicion13"],
                    "estado_requisicion13": result["estado_requisicion13"],
                    "venta13": result["venta13"],
                    "fecha_venta13": result["fecha_venta13"],
                    "estado_venta13": result["estado_venta13"],
                    "venta_total13": result["venta_total13"],
                    "estado_factura13": result["estado_factura13"],
                }
            )

        return {
            "name": "Visor Consolidado Tickets",
            "type": "ir.actions.act_window",
            "res_model": "sale.order.13.report",
            "view_mode": "list",
            "view_id": self.env.ref("mto.view_sale_order_13_report_tree").id,
            "search_view_id": self.env.ref("mto.view_sale_order_13_report_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }
