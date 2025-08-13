# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models, fields, api
import logging


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    x_asignado = fields.Many2one(
        "hr.employee.ticket",
        string="Asignado a (colaborador)",
        store=True,
        domain="[('team_id', '!=', False)]",
    )
    autorizador = fields.Many2one(
        "res.partner",
        string="Autorizador",
        readonly=True,
        compute="_compute_autorizador",
    )
    x_ticket = fields.Integer(string="Ticket", store=True, compute="_compute_ticket")
    x_ticket_ms_origen = fields.Integer(
        string="Ticket Origen",
        store=True,
        readonly=True,
        compute="_compute_ticket_ms_origen",
    )
    x_ticket_odoo_origen = fields.Many2one(
        "helpdesk.ticket", string="Ticket Origen", store=True
    )
    x_mesa_servicio = fields.Many2one(
        "x_mesa_servicio", string="Mesa de Servicio", store=True
    )
    x_cant_rechazos = fields.Integer(string="Cant. de Rechazos", store=True)
    x_fecha_concluido = fields.Datetime(
        string="Fecha de Conclusión",
        store=True,
        related="x_mesa_servicio.x_fecha_concluido",
    )
    x_fecha_programada = fields.Datetime(string="Fecha Programada", store=True)
    x_fecha_rechazo = fields.Datetime(string="Fecha Rechazo", store=True)
    x_requisiciones = fields.One2many(
        "material.purchase.requisition", "x_ticket", string="Requisiciones", store=True
    )
    analytic_account_id = fields.Many2one(
        "account.analytic.account", string="Cuenta Analitíca", store=True
    )
    x_ventas = fields.One2many("sale.order", "x_ticket", string="Ventas", store=True)
    priority = fields.Selection(
        [("0", "Baja"), ("1", "Media"), ("2", "Alta"), ("3", "Emergencia")],
        "Prioridad",
        store=True,
        copy=True,
    )
    # @api.onchange('team_id')
    # def _onchange_team_id(self):
    #     if self.team_id:
    #         self.x_asignado = False
    #         # agregar dominio para empleados del equipo seleccionado
    #         return {'domain': {'x_asignado': [('team_id', '!=', False)]}}

    def _compute_ticket(self):
        for record in self:
            record.x_ticket = record.x_mesa_servicio.x_solicitud

    def _compute_ticket_ms_origen(self):
        for record in self:
            record.x_ticket_ms_origen = record.x_ticket_odoo_origen.x_ticket

    def _compute_autorizador(self):
        for ticket in self:
            if ticket.analytic_account_id:
                if len(ticket.analytic_account_id.project_ids) > 0:
                    if ticket.analytic_account_id.project_ids[0].x_autorizador:
                        ticket.write(
                            {
                                "autorizador": ticket.analytic_account_id.project_ids[
                                    0
                                ].x_autorizador.id,
                            }
                        )
                    else:
                        ticket.write(
                            {
                                "autorizador": False,
                            }
                        )
                else:
                    ticket.write(
                        {
                            "autorizador": False,
                        }
                    )
            else:
                ticket.write(
                    {
                        "autorizador": False,
                    }
                )

    def name_get(self):
        result = []
        for ticket in self:
            result.append((ticket.id, "%s (#%s)" % (ticket.name, ticket.x_ticket)))
        return result

    @api.model
    @api.onchange("analytic_account_id")
    def _onchange_analytic_account_id(self):
        if self.analytic_account_id:
            for req in self.x_requisiciones:
                req.analytic_account_id = self.analytic_account_id.id

    # @api.depends('x_mesa_servicio', 'x_mesa_servicio.x_fecha_programada')
    # def _compute_fecha_programada(self):
    #     for record in self:
    #         if record.ticket_type_id.id == 3:
    #             if record.x_mesa_servicio and record.x_mesa_servicio.x_fecha_programada:
    #                 record.x_fecha_programada = record.x_mesa_servicio.x_fecha_programada + timedelta(hours=6)

    @api.onchange("x_fecha_programada")
    def _onchange_fecha_programada(self):
        """Si cambia la fecha en ticket, actualizar en mesa_servicio"""
        if (
            self.x_mesa_servicio
            and self.x_fecha_programada
            and not self.x_mesa_servicio.x_fecha_programada
        ):
            self.x_mesa_servicio.x_fecha_programada = (
                self.x_fecha_programada + timedelta(hours=6)
            )


class UoM(models.Model):
    _inherit = "uom.uom"

    def get_uom_id(self, name):
        # Construir la consulta en función del idioma proporcionado
        query = """
            SELECT id FROM uom_uom
            WHERE name->>'es_GT' = %s
            ORDER BY id DESC
            LIMIT 1
        """
        thName = str(name["name"])
        self.env.cr.execute(query, (thName,))
        result = self.env.cr.fetchone()
        # Obtener el query resultante
        query_result = self.env.cr.mogrify(query, (thName,))

        if result:
            uom_id = result[0]
            return uom_id
        else:
            return False
            # Generar una advertencia con el query resultante en el mensaje
            # warning_msg = "No se encontró ningún registro. Query: %s" % query_result.decode('utf-8')
            # raise Warning(warning_msg)
