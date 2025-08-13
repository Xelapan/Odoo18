# necesito un nuevo modelo llamado x_mesa_servicio con los siquientes campos:
# x_active	Activo	Mesa de Servicio	booleano	Campo personalizado	FALSO	VERDADERO	FALSO
# x_cant_rechazos	Cant. Rechazos	Mesa de Servicio	entero	Campo personalizado	FALSO	VERDADERO	VERDADERO
# x_colaborador_id	Asignar a (Colaborador)	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	FALSO	hr.employee
# x_colaborador_que_acepta_id	Colaborador que acepta	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	FALSO	hr.employee
# x_company_id	Compañia	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	FALSO	res.company
# x_descripcion	Descripción	Mesa de Servicio	html	Campo personalizado	FALSO	VERDADERO	FALSO
# x_estado	Estado	Mesa de Servicio	selection	Campo personalizado	FALSO	VERDADERO	FALSO
# x_estado_operativo	Estado Operativo	Mesa de Servicio	selection	Campo personalizado	FALSO	VERDADERO	VERDADERO
# x_fabricacion	Fabricacion	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	VERDADERO	mrp.production
# x_fecha_cierre	Fecha Cierre	Mesa de Servicio	Fecha y hora	Campo personalizado	FALSO	VERDADERO	FALSO
# x_fecha_concluido	Fecha Concluido	Mesa de Servicio	Fecha y hora	Campo personalizado	FALSO	VERDADERO	FALSO
# x_fecha_creacion	Fecha de Creación	Mesa de Servicio	Fecha y hora	Campo personalizado	FALSO	VERDADERO	FALSO
# x_fecha_programada	Fecha Programada	Mesa de Servicio	Fecha y hora	Campo personalizado	FALSO	VERDADERO	FALSO
# x_fecha_rechazo	Fecha Rechazo	Mesa de Servicio	Fecha y hora	Campo personalizado	FALSO	VERDADERO	FALSO
# x_lugar_ubicacion	Solicitado de (Ubicación)	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	FALSO	account.analytic.account
# x_motivo_rechazo	Motivo Rechazo	Mesa de Servicio	Carácter	Campo personalizado	FALSO	VERDADERO	FALSO
# x_name	Name	Mesa de Servicio	Carácter	Campo personalizado	FALSO	VERDADERO	VERDADERO
# x_prioridad	Prioridad	Mesa de Servicio	selection	Campo personalizado	FALSO	VERDADERO	FALSO
# x_proyecto	Proyecto	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	FALSO	project.project
# x_solicitante	Colaborador que Solicita	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	FALSO	hr.employee
# x_solicitar_a_id	Departamento / Area Solicitud	Mesa de Servicio	selection	Campo personalizado	FALSO	VERDADERO	FALSO
# x_solicitud	Solicitud No.	Mesa de Servicio	entero	Campo personalizado	VERDADERO	VERDADERO	FALSO
# x_solicitud_rechazada	Id Solicitud Rechazada	Mesa de Servicio	entero	Campo personalizado	FALSO	VERDADERO	FALSO
# x_ticket_listo	Ticket Listo	Mesa de Servicio	selection	Campo personalizado	FALSO	VERDADERO	FALSO
# x_ticket_odoo	Ticket Odoo	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	VERDADERO	helpdesk.ticket
# x_tipo_solicitud_id	Tipo Solicitud	Mesa de Servicio	many2one	Campo personalizado	FALSO	VERDADERO	FALSO	helpdesk.ticket.type
# x_titulo	Titulo	Mesa de Servicio	Carácter	Campo personalizado	VERDADERO	VERDADERO	FALSO
from datetime import timedelta

# necesito un nuevo modelo llamado x_mesa_servicio con los campos anteriores
from odoo import models, fields, api, _


class x_mesa_servicio(models.Model):
    _name = "x_mesa_servicio"
    _description = "Mesa de Servicio"

    x_active = fields.Boolean("Activo", default=True, store=True)
    x_cant_rechazos = fields.Integer(
        "Cant. Rechazos", store=True, readonly=True, copy=True
    )
    x_colaborador_id = fields.Many2one(
        "hr.employee.ticket", "Asignar a (Colaborador)", store=True, copy=True
    )
    x_colaborador_que_acepta_id = fields.Many2one(
        "hr.employee.ticket", "Colaborador que acepta", store=True, copy=True
    )
    x_company_id = fields.Many2one(
        "res.company", "Compañia", store=True, copy=True, required=True
    )
    x_descripcion = fields.Html("Descripción", store=True, copy=True)
    x_estado = fields.Selection(
        [
            ("1", "No Asignado"),
            ("19", "Asignado"),
            ("20", "Planificado"),
            ("21", "Autorizado"),
            ("22", "Concluido"),
            ("31", "Rechazado"),
            ("30", "Cancelado"),
        ],
        "Estado",
        store=True,
        copy=True,
    )
    x_estado_operativo = fields.Selection(
        [
            ("concluido", "Concluido"),
            ("rechazado", "Rechazado"),
            ("cancelado", "Cancelado"),
        ],
        "Estado Operativo",
        store=True,
        readonly=True,
        copy=True,
    )
    x_fecha_cierre = fields.Datetime(
        "Fecha Cierre", store=True, readonly=True, copy=True
    )
    x_fecha_concluido = fields.Datetime(
        "Fecha Concluido",
        store=True,
        readonly=True,
        copy=True,
        compute="_compute_fecha_concluido",
    )
    x_fecha_creacion = fields.Datetime("Fecha de Creación", store=True, copy=True)
    x_fecha_programada = fields.Datetime("Fecha Programada", store=True, copy=True)
    x_fecha_rechazo = fields.Datetime("Fecha Rechazo", store=True, copy=True)
    x_lugar_ubicacion = fields.Many2one(
        "account.analytic.account", "Solicitado de (Ubicación)", store=True, copy=True
    )
    x_motivo_rechazo = fields.Char("Motivo Rechazo", store=True, copy=True)
    x_name = fields.Char("Name", store=True, copy=True, compute="_compute_name")
    name = fields.Char("Name", store=True, copy=True, compute="_compute_name")
    display_name = fields.Char("Name", store=True, copy=True, compute="_compute_name")
    x_prioridad = fields.Selection(
        [("0", "Baja"), ("1", "Media"), ("2", "Alta"), ("3", "Emergencia")],
        "Prioridad",
        store=True,
        copy=True,
    )
    x_solicitante = fields.Many2one(
        "hr.employee.ticket", "Colaborador que Solicita", store=True, copy=True
    )
    x_solicitar_a_id = fields.Selection(
        [("1", "MANTENIMIENTO"), ("2", "INFORMATICA")],
        "Departamento / Area Solicitud",
        store=True,
        copy=True,
    )
    x_solicitud = fields.Integer("Solicitud No.", store=True, copy=True, index=True)
    x_solcitud_rechazada = fields.Integer(
        "Id Solicitud Rechazada", store=True, copy=True
    )
    x_ticket_listo = fields.Selection(
        [("proceso", "En Proceso"), ("listo", "Listo"), ("cancelado", "Cancelado")],
        "Ticket Listo",
        store=True,
        copy=True,
    )
    x_ticket_odoo = fields.Many2one(
        "helpdesk.ticket", "Ticket Odoo", store=True, copy=True
    )
    x_tipo_solicitud_id = fields.Many2one(
        "helpdesk.ticket.type", "Tipo Solicitud", store=True, copy=True
    )
    x_titulo = fields.Char("Titulo", store=True, copy=True)
    x_proyecto = fields.Many2one("project.project", "Proyecto", store=True, copy=True)

    @api.model
    @api.depends("x_solicitud", "x_titulo")
    def _compute_name(self):
        for record in self:
            record.x_name = str(record.x_solicitud) + " - " + str(record.x_titulo)
            record.name = str(record.x_solicitud) + " - " + str(record.x_titulo)
            record.display_name = str(record.x_solicitud) + " - " + str(record.x_titulo)

    def _compute_fecha_concluido(self):
        for record in self:
            if record.x_fecha_cierre:
                record.x_fecha_concluido = record.x_fecha_cierre
            if record.x_fecha_rechazo:
                record.x_fecha_concluido = record.x_fecha_rechazo

    @api.onchange("x_fecha_programada")
    def _onchange_fecha_mesa(self):
        """Si cambia la fecha en mesa_servicio, actualizar en ticket"""
        if self.x_ticket_odoo and self.x_fecha_programada:
            self.x_ticket_odoo.x_fecha_programada = self.x_fecha_programada + timedelta(
                hours=6
            )  # 6 horas de diferencia
