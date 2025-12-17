from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.http import request


class AccountInventoryV(models.Model):
    _name = "account.inventory.v"
    _description = "Visor Inventario Contable"

    session_identifier = fields.Char(
        string="Session Token", required=True
    )  # Campo para el token de sesión
    # move_line_id = fields.Many2one('account.move.line', string='Línea de Movimiento')
    # move_id = fields.Many2one('account.move', string='Movimiento', related='move_line_id.move_id')
    # move_type = fields.Selection(string='Tipo de Movimiento', related='move_line_id.move_id.move_type')
    # date = fields.Date(string='Fecha', related='move_line_id.date')
    account_id = fields.Many2one("account.account", string="Cuenta")
    # journal_id = fields.Many2one('account.journal', string='Diario', related='move_line_id.journal_id')
    product_id = fields.Many2one("product.product", string="Producto", store=True)
    tipo_gasto = fields.Selection(
        string="Tipo de Gasto", related="product_id.tipo_gasto"
    )
    default_code = fields.Char(string="Código", related="product_id.default_code")
    description = fields.Char(string="Descripcion", related="product_id.name")
    product_uom_id = fields.Many2one(
        "uom.uom", string="UM", related="product_id.uom_id"
    )
    avg_unit_cost = fields.Float(string="Costo Promedio Ponderado", store=True)
    quantity = fields.Float(string="Cantidad")
    standard_price = fields.Float(string="Costo Unitario")
    total_cost = fields.Float(string="Costo Total")

    # def related_valuation(self):
    #     for record in self:
    #         if record.move_line_id:
    #             svl = self.env['stock.valuation.layer'].search([('product_id', '=', record.move_line_id.produt_id.id), ('create_date', '<=', record.date_to)], order='create_date desc', limit=1)
    #             if svl:
    #                 total_cost = 0.0
    #                 total_qty = 0.0
    #                 for layer in svl:
    #                     total_cost += layer.value
    #                     total_qty += layer.quantity
    #
    #                 record.standard_price = total_cost / total_qty if total_cost != 0 and total_qty != 0 else 0 # record.move_line_id.stock_valuation_layer_ids[0].unit_cost
    #                 record.total_cost = record.standard_price * record.quantity #record.move_line_id.stock_valuation_layer_ids[0].unit_cost * record.move_line_id.stock_valuation_layer_ids[0].quantity
    #             else:
    #                 record.standard_price = record.move_line_id.product_id.standard_price
    #                 record.total_cost = record.move_line_id.product_id.standard_price * record.move_line_id.quantity

    @api.model
    def get_session_identifier(self, fields_list):
        res = super(AccountInventoryV, self).get_session_identifier(fields_list)
        session_identifier = request.session.sid
        if session_identifier:
            res["domain"] = [("session_identifier", "=", session_identifier)]
        return res

    @api.model
    def action_open_account_inventory_v(self):
        session_identifier = request.session.sid
        return {
            "name": "Visor Inventario Contable",
            "type": "ir.actions.act_window",
            "res_model": "account.inventory.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_inventory_v_view_tree").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    @api.model
    def create_or_update_records(self, results):
        session_identifier = self.get_session_identifier()
        self.search([("session_identifier", "=", session_identifier)]).unlink()
        for result in results:
            self.create(
                {
                    "session_identifier": session_identifier,
                }
            )

    @api.model
    def delete_old_inventory_records(self):
        # Define el umbral de 24 horas
        time_threshold = datetime.now() - timedelta(hours=24)
        # Busca los registros que son más antiguos de 24 horas
        old_records = self.search([("create_date", "<", time_threshold)])
        if old_records:
            old_records.unlink()

    def open_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Consultar Inventario Contable',
            'res_model': 'account.inventory.v.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('fin.view_account_inventory_v_wizard_form').id,
            'target': 'new',
            'context': {
                'default_account_ids': [(6, 0, self.ids)],
                # 'default_company_id': (
                #     self.company_id.id if self.company_id else self.env.company.id
                # )
            }
        }
