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


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    product_account_id = fields.Many2one(
        "account.account",
        string="Cuenta de Producto",
        related="product_id.categ_id.property_stock_valuation_account_id",
    )


class AccountInventoryWizard(models.TransientModel):
    _name = "account.inventory.v.wizard"
    _description = "Visor Inventario Contable Wizard"

    date_from = fields.Date(string="Fecha del")
    date_to = fields.Date(string="Fecha al", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    account_ids = fields.Many2many(
        "account.account",
        string="Cuenta",
        domain="['|', ('name', 'ilike', 'Inventario%'),('name', 'ilike', 'Materia%')]",
    )
    journal_ids = fields.Many2many("account.journal", string="Diario")

    def open_inventory_at_date(self):
        self.ensure_one()
        date_to = self.date_to

        # Obtener el session_id de la sesión HTTP actual
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual

        # Eliminar datos anteriores para esta sesión
        self.env["account.inventory.v"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        domain = [
            ("date", "<=", date_to),
            ("company_id", "=", self.company_id.id),
            ("move_id.state", "=", "posted"),
        ]
        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))

        results = self.env["account.move.line"].search(domain)

        visor_cuentas_contables = self.env["account.inventory.v"]

        for result in results:
            # if result.product_account_id == result.product_id.category_id.property_stock_valuation_account_id:
            visor_cuentas_contables.create(
                {
                    "move_line_id": result.id,
                    "session_identifier": session_identifier,  # Asociar los datos a la cookie de sesión
                }
            )
            # visor_cuentas_contables.create({
            #     'move_line_id': result.id,
            #     'session_identifier': session_identifier,  # Asociar los datos a la cookie de sesión
            # })

        return {
            "name": "Visor Inventario Contable",
            "type": "ir.actions.act_window",
            "res_model": "account.inventory.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_inventory_v_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_inventory_v_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    def get_inventory_at_date(self):
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual
        self.ensure_one()
        date_to = self.date_to
        # Eliminar datos anteriores para esta sesión
        self.env["account.inventory.v"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        # Configurar el dominio para filtrar los movimientos de stock en el rango de fechas
        domain = [
            # ('date', '>=', date_from),
            ("move_id.date", "<=", date_to),
            ("move_id.state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
        ]
        if self.date_from:
            domain.append(("move_id.date", ">=", self.date_from))
        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))

        # Buscar los movimientos de stock
        # stock_moves = self.env['stock.move.line'].search(domain)
        move_lines = self.env["account.move.line"].search(domain)
        # move_lines ordenado por fecha descendente y obtener el ultimo valor osea la fecha mas actual
        move_lines_sorted = move_lines.sorted(
            key=lambda x: x.move_id.date, reverse=True
        )

        # Crear un diccionario para consolidar la información por producto
        product_data = {}
        thProductData = []
        # line_filtered = move_lines.filtered(lambda x: x.product_id.id == 717)
        # filtered_data = [{'id': line.id, 'product_id': line.product_id.id,
        #                   'quantity': line.quantity,'balance': line.balance}
        #                  for line in line_filtered]
        # svl = self.env['stock.valuation.layer'].search([('account_move_id.id', 'in', move_lines.mapped('move_id').ids)])
        # svl_data = [{'id': line.id, 'account_move': line.account_move_id, 'account_move_line': line.account_move_line_id, 'unit_cost': line.unit_cost, 'quantity': line.quantity}
        #             for line in svl]
        # movees = []
        for line in move_lines:
            # movees.append({
            #     'date': line.move_id.date,
            #     'move_id': line.move_id.name,
            #     'etiqueta': line.name,
            #     'cantidad': line.quantity,
            #     'costo': line.balance,
            #     'unit_cost': line.balance / line.quantity if line.quantity != 0 and line.balance != 0 else 0,
            # })
            # if line.product_id.id not in [x['product_id'] for x in thProductData] and line.account_id.id not in [x['account_id'] for x in thProductData]:
            #     thProductData.append({
            #         'product_id': line.product_id.id,
            #         'account_id': line.account_id.id,
            #         'total_quantity': 0,
            #         'total_cost': 0,
            #         'quantity': 0,
            #     })

            product_id = line.product_id.id
            if product_id not in product_data:
                product_data[product_id] = {
                    "total_quantity": 0,
                    "total_cost": 0,
                    "quantity": 0,
                }

            # Obtener el costo unitario del movimiento desde stock.valuation.layer
            cost = 0
            quantity = 0
            valuation = None
            # if line.stock_valuation_layer_ids:
            #     for uuu in line.stock_valuation_layer_ids:
            #         if uuu.unit_cost != 0:
            #             valuation = uuu.unit_cost
            # valuation = line.stock_valuation_layer_ids[0].unit_cost
            # valuation = self.env['stock.valuation.layer'].search([('account_move_id.id', '=', line.move_id.id), ('unit_cost', '!=', 0)])
            # if len(valuation)>1:
            #     auxa = 1
            # if valuation:
            #     cost = valuation[0].unit_cost
            #     quantity = valuation[0].quantity
            # else:
            #     cost = line.balance
            #     quantity = line.quantity
            cost = line.balance
            quantity = line.quantity
            # if line.product_id.id in [x['product_id'] for x in thProductData] and line.account_id.id in [x['account_id'] for x in thProductData]:
            if thProductData:
                thEncontrar = False
                for x in thProductData:
                    if (
                        int(x["product_id"]) == line.product_id.id
                        and int(x["account_id"]) == line.account_id.id
                    ):
                        thEncontrar = True
                        x["quantity"] += quantity
                        x["total_cost"] += cost
                if not thEncontrar:
                    thProductData.append(
                        {
                            "product_id": line.product_id.id,
                            "account_id": line.account_id.id,
                            "total_quantity": 0,
                            "total_cost": cost,
                            "quantity": quantity,
                        }
                    )
            else:
                thProductData.append(
                    {
                        "product_id": line.product_id.id,
                        "account_id": line.account_id.id,
                        "total_quantity": 0,
                        "total_cost": cost,
                        "quantity": quantity,
                    }
                )
            # Sumar o restar según la ubicación
            # if location_id:
            #     if move.location_dest_id.id == location_id.id:
            #         # Si la ubicación de destino es la seleccionada, es una entrada
            #         product_data[product_id]['total_quantity'] += move.qty_done
            #         product_data[product_id]['total_cost'] += move.qty_done * cost
            #     elif move.location_id.id == location_id.id:
            #         # Si la ubicación de origen es la seleccionada, es una salida
            #         product_data[product_id]['total_quantity'] -= move.qty_done
            #         product_data[product_id]['total_cost'] -= move.qty_done * cost
            # else:
            # Si no se especifica una ubicación, se hace el cálculo general
            product_data[product_id]["total_quantity"] += quantity
            # product_data[product_id]['total_cost'] += quantity * cost
            product_data[product_id]["total_cost"] += cost

        # Crear los registros consolidados en stock.inventory.at.date
        # for product_id, data in product_data.items():
        #     thunit_cost = 0
        #     self.env['account.inventory.v'].create({
        #         'product_id': product_id,
        #         'quantity': data['total_quantity'],
        #         'standard_price': data['total_cost'] / data['total_quantity'] if data['total_quantity'] and data['total_cost'] else 0.0,
        #         'total_cost': data['total_cost'], #data['total_quantity'] * thunit_cost,#data['total_cost'],
        #         'session_identifier': session_identifier,  # Asociar los datos a la cookie de sesión
        #         #'date': date_to,  # Fecha del reporte
        #     })
        for x in thProductData:
            if x["total_cost"] != 0:
                self.env["account.inventory.v"].create(
                    {
                        "product_id": x["product_id"],
                        "account_id": x["account_id"],
                        "quantity": x["quantity"],
                        "standard_price": (
                            x["total_cost"] / x["quantity"]
                            if x["quantity"] and x["total_cost"]
                            else 0.0
                        ),
                        "total_cost": x["total_cost"],
                        "session_identifier": session_identifier,  # Asociar los datos a la cookie de sesión
                    }
                )
        # # Retornar la acción para mostrar la vista del reporte
        # tree_view_id = self.env.ref('fin.view_account_inventory_v_tree').id
        # action = {
        #     'type': 'ir.actions.act_window',
        #     'views': [(tree_view_id, 'tree')],
        #     'view_id': tree_view_id,
        #     'view_mode': 'tree',
        #     'search_view_id': self.env.ref('fin.view_account_inventory_v_search').id,
        #     'domain': [('session_identifier', '=', session_identifier)],
        #
        #     'name': _('Reporte de Inventario'),
        #     'res_model': 'account.inventory.v',
        # }
        # return action
        return {
            "name": "Visor Inventario Contable",
            "type": "ir.actions.act_window",
            "res_model": "account.inventory.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_inventory_v_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_inventory_v_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    def get_move_lines_inventario(self):
        self.ensure_one()
        if not self.date_to:
            raise UserError("Debe ingresar fecha fin")
        # if not self.journal_type:
        #     raise UserError("Debe seleccionar un tipo de diario.")
        date_to = self.date_to

        # Identificar la sesión basada en IP y User-Agent
        user_ip = request.httprequest.remote_addr
        user_agent = request.httprequest.headers.get("User-Agent")
        session_identifier = f"{user_ip}_{user_agent}"

        # Eliminar datos anteriores para esta sesión
        self.env["account.account.v"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        domain = [
            # ('date', '>=', self.date_from),
            # ('product_id', '!=', False),
            ("date", "<=", date_to),
            # ('move_id.journal_id.type','=', self.journal_type),
            ("company_id", "=", self.company_id.id),
            ("move_id.state", "=", "posted"),
            ("display_type", "in", ("product", "line_section", "line_note")),
        ]
        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.journal_type:
            domain.append(("move_id.journal_id.type", "=", self.journal_type))
        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))

        results = self.env["account.move.line"].search(domain)
        visor_cuentas_contables = self.env["account.account.v"]
        for result in results:
            analytic_tags = self._compute_analytic_tags(result.analytic_distribution)
            visor_cuentas_contables.create(
                {
                    "move_line_id": result.id,
                    "fecha": result.date,
                    "move_id": result.move_id.id,
                    "account_id": result.account_id.id,
                    "journal_id": result.journal_id.id,
                    "balance": result.balance,
                    "analytic_distribution": result.analytic_distribution,
                    "analytic_tags": analytic_tags,
                    "partner_id": result.partner_id.id,
                    "tax_base_amount": result.tax_base_amount,
                    "session_identifier": session_identifier,  # Asociar los datos a la cookie de sesión
                }
            )

        return {
            "name": "Informe Inventario",
            "type": "ir.actions.act_window",
            "res_model": "account.account.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_account_v_inventario_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_account_v_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "context": {"search_default_product_id": 1},
            "target": "current",
        }
