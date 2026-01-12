from odoo import models, fields, api
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # orden_produccion = fields.Many2one('mrp.production', string='Orden de Producción', store=True)
    x_ticket = fields.Many2one(
        "helpdesk.ticket", string="Ticket Correctivo", store=True
    )
    x_no_ticket = fields.Integer(
        string="Ticket", store=True, readonly=True, compute="_compute_ticket"
    )
    x_fecha_concluido = fields.Datetime(
        string="Fecha Concluido", store=True, readonly=True, compute="_compute_ticket"
    )
    # url_venta_13 = fields.Char(string="Venta Odoo 13", store=True)
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Cuenta Analítica",
        store=True
    )
    @api.depends("x_ticket")
    def _compute_ticket(self):
        for record in self:
            if record.x_ticket:
                record.write(
                    {
                        "x_no_ticket": record.x_ticket.x_ticket,
                        "x_fecha_concluido": record.x_ticket.x_fecha_concluido,
                    }
                )
            else:
                record.write({"x_no_ticket": 0, "x_fecha_concluido": False})

    # @api.model
    # @api.depends('orden_produccion', 'state')
    # @api.onchange('state')
    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     for record in self:
    #         if record.orden_produccion.state == 'confirmed':
    #             record.orden_produccion.requisiciones.user_approve()
    #             record.orden_produccion.requisiciones.request_stock()
