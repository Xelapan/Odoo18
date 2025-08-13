from collections import defaultdict

from odoo import models, fields, api
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
#             'view_mode': 'list',
#             'target': 'current',
#         }


class HrPayslipPrestacionesWizard(models.TransientModel):
    _name = "account.account.v.wizard"
    _description = "Visor Cuentas Contables Wizard"

    date_from = fields.Date(string="Fecha del")
    date_to = fields.Date(string="Fecha al", required=True)
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    account_ids = fields.Many2many("account.account", string="Cuenta")
    journal_ids = fields.Many2many("account.journal", string="Diario")
    journal_type = fields.Selection(
        [
            ("sale", "Venta"),
            ("purchase", "Compra"),
            ("general", "General"),
            ("cash", "Efectivo"),
            ("bank", "Banco"),
        ],
        string="Tipo de Diario",
    )
    # analytic_account_ids = fields.Many2many('account.analytic.account', string="Cuenta Analítica")

    analytic_tags = fields.Char(string="Proporción Analítica", readonly=True)

    # def open_prestaciones_at_date(self):
    #     self.ensure_one()
    #     date_to = self.date_to
    #
    #     # Eliminar datos anteriores para no duplicar
    #     self.env['account.account.v'].search([]).unlink()
    #     domain = [('date', '<=', date_to), ('company_id', '=', self.company_id.id), ('move_id.state', '=', 'posted')]
    #     if self.date_from:
    #         domain.append(('date', '>=', self.date_from))
    #     if self.account_ids:
    #         domain.append(('account_id', 'in', self.account_ids.ids))
    #     if self.journal_ids:
    #         domain.append(('journal_id', 'in', self.journal_ids.ids))
    #     # if self.analytic_account_ids:
    #     #     domain.append(('analytic_account_id', 'in', self.analytic_account_ids.ids))
    #
    #     results = self.env['account.move.line'].search(domain)
    #     visor_cuentas_contables = self.env['account.account.v']
    #     for result in results:
    #         analytic_tags = self._compute_analytic_tags(result.analytic_distribution)
    #         visor_cuentas_contables.create({
    #             'move_line_id': result.id,
    #             'fecha': result.date,
    #             'move_id': result.move_id.id,
    #             'account_id': result.account_id.id,
    #             'journal_id': result.journal_id.id,
    #             'balance': result.balance,
    #             'analytic_distribution': result.analytic_distribution,
    #             'analytic_tags': analytic_tags,  # Almacenar la proporción analítica calculada
    #             'partner_id': result.partner_id.id,
    #             'tax_base_amount': result.tax_base_amount,
    #         })
    #
    #     return {
    #         'name': 'Visor Cuentas Contables',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'account.account.v',
    #         'view_mode': 'list',
    #         'target': 'current',
    #     }

    def open_prestaciones_at_date(self):
        self.ensure_one()
        date_to = self.date_to

        # Obtener el session_id de la sesión HTTP actual
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual

        # Eliminar datos anteriores para esta sesión
        self.env["account.account.v"].search(
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
            "name": "Visor Cuentas Contables",
            "type": "ir.actions.act_window",
            "res_model": "account.account.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_account_v_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_account_v_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
            # Agrupar por mes
            "context": {"search_default_thfecha": 1},
        }

    # def _compute_analytic_tags(self, analytic_distribution):
    #     if analytic_distribution:
    #         tags = []
    #         for analytic_id, percentage in analytic_distribution.items():
    #             analytic_account = self.env['account.analytic.account'].browse(int(analytic_id))
    #             tags.append(f"{analytic_account.name} ({percentage}%)")
    #         return ", ".join(tags)
    #     return "N/A"
    def _compute_analytic_tags(self, analytic_distribution):
        if analytic_distribution:
            tags = []
            for analytic_id, percentage in analytic_distribution.items():
                analytic_account = self.env["account.analytic.account"].browse(
                    int(analytic_id)
                )
                # Reemplazo de cualquier salto de línea por espacios y formato correcto
                tags.append(
                    f"{analytic_account.name.strip()} ({str(percentage).strip()}%)"
                )
            # Unión de las cuentas en una sola línea con comas
            return ", ".join(tags).replace("\n", "").replace("\r", "")
        return "N/A"

    def get_move_lines(self):
        self.ensure_one()
        if not self.date_from or not self.date_to:
            raise UserError("Debe ingresar fecha de inicio y fin.")
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

        thImpuestoIVACredito = self.env["account.tax"].search(
            [
                ("name", "in", ["IVA Crédito Local", ""]),
                ("type_tax_use", "=", "purchase"),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )

        domain = [
            ("date", ">=", self.date_from),
            ("date", "<=", date_to),
            # ('move_id.journal_id.type','=', self.journal_type),
            ("company_id", "=", self.company_id.id),
            ("move_id.state", "=", "posted"),
            # ('display_type', 'in', ('product', 'line_section', 'line_note')),
            ("tax_ids", "in", thImpuestoIVACredito.ids),
            # ('tax_ids', '!=', False),
            (
                "move_id.journal_id.name",
                "not in",
                ["Partida de Apertura", "Partida de Cierre"],
            ),
        ]

        if self.journal_type:
            domain.append(("move_id.journal_id.type", "=", self.journal_type))
        # if self.account_ids:
        #     domain.append(('account_id', 'in', self.account_ids.ids))
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))

        results = self.env["account.move.line"].search(domain)
        auxresults = self.env["account.move.line"].search(
            [
                ("date", ">=", self.date_from),
                ("date", "<=", date_to),
                ("company_id", "=", self.company_id.id),
                ("move_id.state", "=", "posted"),
                ("journal_id.name", "in", ["Factura Pequeño Contribuyente"]),
                ("account_id.account_type", "=", "expense"),
                ("id", "not in", results.ids),
            ]
        )
        if results:
            results += auxresults
        else:
            results = auxresults
        visor_cuentas_contables = self.env["account.account.v"]
        for result in results:
            analytic_tags = self._compute_analytic_tags(result.analytic_distribution)
            if not result.date:
                aux = result.move_id.date
            thBalance = 0
            if result.move_id.tipo_documento == "NC":
                thBalance = result.balance * -1
            else:
                thBalance = result.balance
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
            "name": "Visor Cuentas Contables",
            "type": "ir.actions.act_window",
            "res_model": "account.account.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_account_v_purchase_view_tree").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    # def get_move_lines_inventario(self):
    #     self.ensure_one()
    #     if not self.date_to:
    #         raise UserError("Debe ingresar fecha fin")
    #     # if not self.journal_type:
    #     #     raise UserError("Debe seleccionar un tipo de diario.")
    #     date_to = self.date_to
    #
    #
    #     # Identificar la sesión basada en IP y User-Agent
    #     user_ip = request.httprequest.remote_addr
    #     user_agent = request.httprequest.headers.get('User-Agent')
    #     session_identifier = f"{user_ip}_{user_agent}"
    #
    #     # Eliminar datos anteriores para esta sesión
    #     self.env['account.account.v'].search([('session_identifier', '=', session_identifier)]).unlink()
    #
    #     domain = [
    #         #('date', '>=', self.date_from),
    #         #('product_id', '!=', False),
    #         ('date', '<=', date_to),
    #         #('move_id.journal_id.type','=', self.journal_type),
    #         ('company_id', '=', self.company_id.id),
    #         ('move_id.state', '=', 'posted'),
    #         ('display_type', 'in', ('product', 'line_section', 'line_note'))]
    #     if self.date_from:
    #         domain.append(('date', '>=', self.date_from))
    #     if self.journal_type:
    #         domain.append(('move_id.journal_id.type', '=', self.journal_type))
    #     if self.account_ids:
    #         domain.append(('account_id', 'in', self.account_ids.ids))
    #     if self.journal_ids:
    #         domain.append(('journal_id', 'in', self.journal_ids.ids))
    #
    #     results = self.env['account.move.line'].search(domain)
    #     visor_cuentas_contables = self.env['account.account.v']
    #     for result in results:
    #         analytic_tags = self._compute_analytic_tags(result.analytic_distribution)
    #         visor_cuentas_contables.create({
    #             'move_line_id': result.id,
    #             'fecha': result.date,
    #             'move_id': result.move_id.id,
    #             'account_id': result.account_id.id,
    #             'journal_id': result.journal_id.id,
    #             'balance': result.balance,
    #             'analytic_distribution': result.analytic_distribution,
    #             'analytic_tags': analytic_tags,
    #             'partner_id': result.partner_id.id,
    #             'tax_base_amount': result.tax_base_amount,
    #             'session_identifier': session_identifier,  # Asociar los datos a la cookie de sesión
    #         })
    #
    #     return {
    #         'name': 'Informe Inventario',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'account.account.v',
    #         'view_mode': 'tree',
    #         'view_id': self.env.ref('fin.account_account_v_inventario_view_tree').id,
    #         'search_view_id': self.env.ref('fin.view_account_account_v_search').id,
    #         'domain': [('session_identifier', '=', session_identifier)],
    #         'context': {'search_default_product_id': 1},
    #         'target': 'current'
    #     }

    def get_invoices_payments_at_date(self):
        self.ensure_one()
        date_to = self.date_to

        # Obtener el session_id de la sesión HTTP actual
        session_identifier = (
            request.session.sid
        )  # Este es el identificador de sesión actual

        # Eliminar datos anteriores para esta sesión
        self.env["account.account.v"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()

        domain = [
            ("date", "<=", date_to),
            ("company_id", "=", self.company_id.id),
            ("move_id.state", "=", "posted"),
            ("move_id.payment_id", "=", False),
            ("move_id.amount_total", "!=", 0),
        ]
        if self.date_from:
            domain.append(("date", ">=", self.date_from))
        if self.account_ids:
            domain.append(("account_id", "in", self.account_ids.ids))
        if self.journal_ids:
            domain.append(("journal_id", "in", self.journal_ids.ids))

        xresults = self.env["account.move.line"].search(
            domain
        )  # [('move_id.id','=',30818)])#domain)
        results = self.env["account.move.line"]
        visor_cuentas_contables = self.env["account.account.v"]
        # ThFacturasConPagos = self.env['advance.payment.line'].search([('invoice_id', 'in', xresults.mapped('move_id.id'))])
        FacturasCompletas = []
        AsientosPago = []
        AsientosPagoExcedidos = []
        # if ThFacturasConPagos:
        #     for thConcilia in ThFacturasConPagos:
        #         if thConcilia.invoice_id:
        #             PagosFactura = self.env['advance.payment.line'].search([('invoice_id', '=', thConcilia.invoice_id.id)])
        #             TotalPagado = sum([x.account_payment_id.amount for x in PagosFactura])
        #             if TotalPagado >= thConcilia.invoice_id.amount_total:
        #                 FacturasCompletas.append(thConcilia.invoice_id.id) #+= thConcilia.invoice_id

        # Definir el orden personalizado
        order_mapping = {
            "out_invoice": 1,
            "in_invoice": 2,
            "out_refund": 3,
            "in_refund": 4,
            "out_receipt": 5,
            "in_receipt": 6,
            "entry": 7,
        }
        thFacturas = self.env["account.move"].search(
            [("id", "in", xresults.mapped("move_id.id"))]
        )  # search([('id', '=', 30818)])#search([('id', 'in', xresults.mapped('move_id.id'))])
        # Ordenar en función del diccionario
        thFacturas = thFacturas.sorted(lambda m: order_mapping.get(m.move_type, 999))
        thAsientoEncontrado = []
        NoInlcuirApuntesParciales = []
        for thFactura in thFacturas:
            if thFactura.id in thAsientoEncontrado or thFactura.id in FacturasCompletas:
                continue
            pagos = thFactura.get_related_payments()
            xxthPagos = thFactura._compute_related_payment_journal_entries()
            thPagos = [payment for payment in xxthPagos if payment.date <= self.date_to]

            AsientosPago.append(thPagos)
            for thPaguito in thPagos:
                ElPago = thPaguito
                LaFactua = thFactura
                auxa = 1
                # thAsientoEncontrado.append(thPaguito.id)
                thAsientoEncontrado.append(thFactura.id)
                if (
                    thFactura.move_type not in ["out_refund", "in_refund", "entry"]
                    and thPaguito not in thAsientoEncontrado
                ):
                    FacturasCompletas.append(thPaguito.id)
            # TotalPagado = sum([x.amount for x in pagos])
            thPagFact = 0
            thPagFactConci = 0
            FacPagIds = self.env["account.payment"]
            FacFacIds = self.env["account.move"]
            for thP in thPagos:
                if thP.payment_id:
                    # for FacPag in thP.payment_id.dev_invoice_line_ids:
                    #     if FacPag.invoice_id.id == thFactura.id:
                    #         FacPagIds += thP.payment_id
                    #         thPagFact += FacPag.allocation
                    #         SaldoAux = []
                    #         AuxSaldo = 0.0
                    for LiqPag in thP.payment_id.bolson_id.cheques:
                        if LiqPag.state == "posted":
                            FacPagIds += thP.payment_id
                            thPagFact += LiqPag.amount
                            SaldoAux = []
                            AuxSaldo = 0.0
                    if (
                        thP.payment_id.state == "posted"
                        and thP.payment_id.date <= date_to
                        and thP.payment_id.id not in FacPagIds.ids
                    ):
                        for lline in thP.payment_id.line_ids:
                            auxa = lline
                            for mcline in lline.matched_credit_ids:
                                if mcline.credit_move_id.move_id.id == thFactura.id:
                                    auxa = mcline
                                    if (
                                        mcline.credit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):
                                        if (
                                            mcline.credit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                > mcline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mcline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.credit_move_id.balance
                                                                + mcline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mcline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.credit_move_id.id,
                                                            "fecha": mcline.credit_move_id.date,
                                                            "move_id": mcline.credit_move_id.move_id.id,
                                                            "amount_residual": mcline.credit_move_id.balance
                                                            + mcline.debit_amount_currency,
                                                            "account_id": mcline.credit_move_id.account_id.id,
                                                            "journal_id": mcline.credit_move_id.journal_id.id,
                                                            "balance": mcline.credit_move_id.balance
                                                            + mcline.debit_amount_currency,
                                                            "analytic_distribution": mcline.credit_move_id.analytic_distribution,
                                                            "partner_id": mcline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.credit_move_id.id
                                                    )
                                            elif (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                <= mcline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.credit_move_id.id
                                                )
                                        else:
                                            if (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                < mcline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mcline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.credit_move_id.balance
                                                                - mcline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mcline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.credit_move_id.id,
                                                            "fecha": mcline.credit_move_id.date,
                                                            "move_id": mcline.credit_move_id.move_id.id,
                                                            "amount_residual": mcline.credit_move_id.balance
                                                            - mcline.debit_amount_currency,
                                                            "account_id": mcline.credit_move_id.account_id.id,
                                                            "journal_id": mcline.credit_move_id.journal_id.id,
                                                            "balance": mcline.credit_move_id.balance
                                                            - mcline.debit_amount_currency,
                                                            "analytic_distribution": mcline.credit_move_id.analytic_distribution,
                                                            "partner_id": mcline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.credit_move_id.id
                                                    )
                                            elif (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                >= mcline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.credit_move_id.id
                                                )
                                if mcline.debit_move_id.move_id.id == thFactura.id:
                                    auxa = mcline
                                    if (
                                        mcline.debit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):
                                        if (
                                            mcline.debit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                > mcline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mcline.credit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.debit_move_id.balance
                                                                + mcline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mcline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.debit_move_id.id,
                                                            "fecha": mcline.debit_move_id.date,
                                                            "move_id": mcline.debit_move_id.move_id.id,
                                                            "amount_residual": mcline.debit_move_id.balance
                                                            + mcline.credit_amount_currency,
                                                            "account_id": mcline.debit_move_id.account_id.id,
                                                            "journal_id": mcline.debit_move_id.journal_id.id,
                                                            #'balance': mcline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mcline.debit_move_id.balance
                                                            + mcline.credit_amount_currency,
                                                            "analytic_distribution": mcline.debit_move_id.analytic_distribution,
                                                            "partner_id": mcline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.debit_move_id.id
                                                    )
                                            elif (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                <= mcline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.debit_move_id.id
                                                )
                                        else:
                                            if (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                < mcline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mcline.credit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.debit_move_id.balance
                                                                - mcline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mcline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.debit_move_id.id,
                                                            "fecha": mcline.debit_move_id.date,
                                                            "move_id": mcline.debit_move_id.move_id.id,
                                                            "amount_residual": mcline.debit_move_id.balance
                                                            - mcline.credit_amount_currency,
                                                            "account_id": mcline.debit_move_id.account_id.id,
                                                            "journal_id": mcline.debit_move_id.journal_id.id,
                                                            #'balance': mcline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mcline.debit_move_id.balance
                                                            - mcline.credit_amount_currency,
                                                            "analytic_distribution": mcline.debit_move_id.analytic_distribution,
                                                            "partner_id": mcline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.debit_move_id.id
                                                    )
                                            elif (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                >= mcline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.debit_move_id.id
                                                )

                            for mdline in lline.matched_debit_ids:
                                if mdline.debit_move_id.move_id.id == thFactura.id:
                                    auxa = mdline
                                    if (
                                        mdline.debit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):
                                        if (
                                            mdline.debit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mdline.credit_move_id != 0
                                                and mdline.credit_amount_currency
                                                > mdline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mdline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.debit_move_id.balance
                                                                + mdline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mdline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.debit_move_id.id,
                                                            "fecha": mdline.debit_move_id.date,
                                                            "move_id": mdline.debit_move_id.move_id.id,
                                                            "amount_residual": mdline.debit_move_id.balance
                                                            + mdline.credit_amount_currency,
                                                            "account_id": mdline.debit_move_id.account_id.id,
                                                            "journal_id": mdline.debit_move_id.journal_id.id,
                                                            #'balance': mdline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.debit_move_id.balance
                                                            + mdline.credit_amount_currency,
                                                            "analytic_distribution": mdline.debit_move_id.analytic_distribution,
                                                            "partner_id": mdline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.debit_move_id.id
                                                    )
                                            elif (
                                                mdline.credit_amount_currency != 0
                                                and mdline.credit_amount_currency
                                                <= mdline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.debit_move_id.id
                                                )
                                        else:
                                            if (
                                                mdline.credit_move_id != 0
                                                and mdline.credit_amount_currency
                                                < mdline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mdline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.debit_move_id.balance
                                                                - mdline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mdline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.debit_move_id.id,
                                                            "fecha": mdline.debit_move_id.date,
                                                            "move_id": mdline.debit_move_id.move_id.id,
                                                            "amount_residual": mdline.debit_move_id.balance
                                                            - mdline.credit_amount_currency,
                                                            "account_id": mdline.debit_move_id.account_id.id,
                                                            "journal_id": mdline.debit_move_id.journal_id.id,
                                                            #'balance': mdline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.debit_move_id.balance
                                                            - mdline.credit_amount_currency,
                                                            "analytic_distribution": mdline.debit_move_id.analytic_distribution,
                                                            "partner_id": mdline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.debit_move_id.id
                                                    )
                                            elif (
                                                mdline.credit_amount_currency != 0
                                                and mdline.credit_amount_currency
                                                >= mdline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.debit_move_id.id
                                                )

                                if mdline.credit_move_id.move_id.id == thFactura.id:
                                    auxa = mdline
                                    if (
                                        mdline.credit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):
                                        if (
                                            mdline.credit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                > mdline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mdline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.credit_move_id.balance
                                                                + mdline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mdline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.credit_move_id.id,
                                                            "fecha": mdline.credit_move_id.date,
                                                            "move_id": mdline.credit_move_id.move_id.id,
                                                            "amount_residual": mdline.credit_move_id.balance
                                                            + mdline.debit_amount_currency,
                                                            "account_id": mdline.credit_move_id.account_id.id,
                                                            "journal_id": mdline.credit_move_id.journal_id.id,
                                                            #'balance': mdline.credit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.credit_move_id.balance
                                                            + mdline.debit_amount_currency,
                                                            "analytic_distribution": mdline.credit_move_id.analytic_distribution,
                                                            "partner_id": mdline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.credit_move_id.id
                                                    )
                                            elif (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                >= mdline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.credit_move_id.id
                                                )
                                        else:
                                            if (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                < mdline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mdline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.credit_move_id.balance
                                                                - mdline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mdline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.credit_move_id.id,
                                                            "fecha": mdline.credit_move_id.date,
                                                            "move_id": mdline.credit_move_id.move_id.id,
                                                            "amount_residual": mdline.credit_move_id.balance
                                                            - mdline.debit_amount_currency,
                                                            "account_id": mdline.credit_move_id.account_id.id,
                                                            "journal_id": mdline.credit_move_id.journal_id.id,
                                                            #'balance': mdline.credit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.credit_move_id.balance
                                                            - mdline.debit_amount_currency,
                                                            "analytic_distribution": mdline.credit_move_id.analytic_distribution,
                                                            "partner_id": mdline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.credit_move_id.id
                                                    )
                                            elif (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                >= mdline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.credit_move_id.id
                                                )
                        if thP.payment_id:
                            FacPagIds += thP.payment_id

                        # thPagFactConci += thP.amount_total
                # ------------------------------------ Se buscan regularizaciones ------------------------
                else:
                    # if thP.state == 'posted':
                    #    thPagFact += thP.amount_total
                    if (
                        thP.state == "posted"
                        and thP.date <= date_to
                        and thP.id not in FacFacIds.ids
                    ):
                        for lline in thP.line_ids:
                            auxa = lline
                            for mcline in lline.matched_credit_ids:
                                if mcline.credit_move_id.move_id.id == thFactura.id:
                                    auxa = mcline
                                    if (
                                        mcline.credit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):
                                        if (
                                            mcline.credit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                > mcline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mcline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.credit_move_id.balance
                                                                + mcline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mcline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.credit_move_id.id,
                                                            "fecha": mcline.credit_move_id.date,
                                                            "move_id": mcline.credit_move_id.move_id.id,
                                                            "amount_residual": mcline.credit_move_id.balance
                                                            + mcline.debit_amount_currency,
                                                            "account_id": mcline.credit_move_id.account_id.id,
                                                            "journal_id": mcline.credit_move_id.journal_id.id,
                                                            "balance": mcline.credit_move_id.balance
                                                            + mcline.debit_amount_currency,
                                                            "analytic_distribution": mcline.credit_move_id.analytic_distribution,
                                                            "partner_id": mcline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.credit_move_id.id
                                                    )
                                            elif (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                <= mcline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.credit_move_id.id
                                                )
                                        else:
                                            if (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                < mcline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mcline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.credit_move_id.balance
                                                                - mcline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mcline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.credit_move_id.id,
                                                            "fecha": mcline.credit_move_id.date,
                                                            "move_id": mcline.credit_move_id.move_id.id,
                                                            "amount_residual": mcline.credit_move_id.balance
                                                            - mcline.debit_amount_currency,
                                                            "account_id": mcline.credit_move_id.account_id.id,
                                                            "journal_id": mcline.credit_move_id.journal_id.id,
                                                            "balance": mcline.credit_move_id.balance
                                                            - mcline.debit_amount_currency,
                                                            "analytic_distribution": mcline.credit_move_id.analytic_distribution,
                                                            "partner_id": mcline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.credit_move_id.id
                                                    )
                                            elif (
                                                mcline.debit_amount_currency != 0
                                                and mcline.debit_amount_currency
                                                >= mcline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.credit_move_id.id
                                                )
                                if mcline.debit_move_id.move_id.id == thFactura.id:
                                    auxa = mcline
                                    if (
                                        mcline.debit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):
                                        thCurrencyC = 0
                                        thCurrencyC = mcline.credit_amount_currency
                                        if (
                                            mcline.debit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                > mcline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mcline.credit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.debit_move_id.balance
                                                                + mcline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mcline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.debit_move_id.id,
                                                            "fecha": mcline.debit_move_id.date,
                                                            "move_id": mcline.debit_move_id.move_id.id,
                                                            "amount_residual": mcline.debit_move_id.balance
                                                            + mcline.credit_amount_currency,
                                                            "account_id": mcline.debit_move_id.account_id.id,
                                                            "journal_id": mcline.debit_move_id.journal_id.id,
                                                            #'balance': mcline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mcline.debit_move_id.balance
                                                            + mcline.credit_amount_currency,
                                                            "analytic_distribution": mcline.debit_move_id.analytic_distribution,
                                                            "partner_id": mcline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.debit_move_id.id
                                                    )
                                            elif (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                <= mcline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.debit_move_id.id
                                                )
                                        else:
                                            if (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                < mcline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mcline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mcline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mcline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mcline.credit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mcline.debit_move_id.balance
                                                                - mcline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mcline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mcline.debit_move_id.id,
                                                            "fecha": mcline.debit_move_id.date,
                                                            "move_id": mcline.debit_move_id.move_id.id,
                                                            "amount_residual": mcline.debit_move_id.balance
                                                            - mcline.credit_amount_currency,
                                                            "account_id": mcline.debit_move_id.account_id.id,
                                                            "journal_id": mcline.debit_move_id.journal_id.id,
                                                            #'balance': mcline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mcline.debit_move_id.balance
                                                            - mcline.credit_amount_currency,
                                                            "analytic_distribution": mcline.debit_move_id.analytic_distribution,
                                                            "partner_id": mcline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mcline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mcline.debit_move_id.id
                                                    )
                                            elif (
                                                mcline.credit_amount_currency != 0
                                                and mcline.credit_amount_currency
                                                >= mcline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mcline.debit_move_id.id
                                                )

                            for mdline in lline.matched_debit_ids:
                                if mdline.debit_move_id.move_id.id == thFactura.id:
                                    auxa = mdline
                                    if (
                                        mdline.debit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):
                                        if (
                                            mdline.debit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mdline.debit_amount_currency != 0
                                                and mdline.credit_amount_currency
                                                > mdline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mdline.credit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.debit_move_id.balance
                                                                + mdline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mdline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.debit_move_id.id,
                                                            "fecha": mdline.debit_move_id.date,
                                                            "move_id": mdline.debit_move_id.move_id.id,
                                                            "amount_residual": mdline.debit_move_id.balance
                                                            + mdline.credit_amount_currency,
                                                            "account_id": mdline.debit_move_id.account_id.id,
                                                            "journal_id": mdline.debit_move_id.journal_id.id,
                                                            #'balance': mdline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.debit_move_id.balance
                                                            + mdline.credit_amount_currency,
                                                            "analytic_distribution": mdline.debit_move_id.analytic_distribution,
                                                            "partner_id": mdline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.debit_move_id.id
                                                    )
                                            elif (
                                                mdline.credit_amount_currency != 0
                                                and mdline.credit_amount_currency
                                                <= mdline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.debit_move_id.id
                                                )
                                        else:
                                            if (
                                                mdline.debit_amount_currency != 0
                                                and mdline.credit_amount_currency
                                                < mdline.debit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.debit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.debit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.debit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mdline.credit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.debit_move_id.balance
                                                                - mdline.credit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mdline.credit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.debit_move_id.id,
                                                            "fecha": mdline.debit_move_id.date,
                                                            "move_id": mdline.debit_move_id.move_id.id,
                                                            "amount_residual": mdline.debit_move_id.balance
                                                            - mdline.credit_amount_currency,
                                                            "account_id": mdline.debit_move_id.account_id.id,
                                                            "journal_id": mdline.debit_move_id.journal_id.id,
                                                            #'balance': mdline.debit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.debit_move_id.balance
                                                            - mdline.credit_amount_currency,
                                                            "analytic_distribution": mdline.debit_move_id.analytic_distribution,
                                                            "partner_id": mdline.debit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.debit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.debit_move_id.id
                                                    )
                                            elif (
                                                mdline.credit_amount_currency != 0
                                                and mdline.credit_amount_currency
                                                >= mdline.debit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.debit_move_id.id
                                                )

                                if mdline.credit_move_id.move_id.id == thFactura.id:
                                    auxa = mdline
                                    if (
                                        mdline.credit_move_id.account_id.id
                                        in self.account_ids.ids
                                    ):

                                        if (
                                            mdline.credit_move_id.account_id.account_type
                                            == "liability_payable"
                                        ):
                                            if (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                > mdline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            + mdline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.credit_move_id.balance
                                                                + mdline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                + mdline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.credit_move_id.id,
                                                            "fecha": mdline.credit_move_id.date,
                                                            "move_id": mdline.credit_move_id.move_id.id,
                                                            "amount_residual": mdline.credit_move_id.balance
                                                            + mdline.debit_amount_currency,
                                                            "account_id": mdline.credit_move_id.account_id.id,
                                                            "journal_id": mdline.credit_move_id.journal_id.id,
                                                            # 'balance': mdline.credit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.credit_move_id.balance
                                                            + mdline.debit_amount_currency,
                                                            "analytic_distribution": mdline.credit_move_id.analytic_distribution,
                                                            "partner_id": mdline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.credit_move_id.id
                                                    )
                                            elif (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                <= mdline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.credit_move_id.id
                                                )
                                        else:
                                            if (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                < mdline.credit_move_id.balance
                                            ):
                                                thVisorCuentasContablesExiste = self.env[
                                                    "account.account.v"
                                                ].search(
                                                    [
                                                        (
                                                            "move_line_id.id",
                                                            "=",
                                                            mdline.credit_move_id.id,
                                                        ),
                                                        (
                                                            "move_id",
                                                            "=",
                                                            mdline.credit_move_id.move_id.id,
                                                        ),
                                                        (
                                                            "account_id",
                                                            "=",
                                                            mdline.credit_move_id.account_id.id,
                                                        ),
                                                        (
                                                            "session_identifier",
                                                            "=",
                                                            session_identifier,
                                                        ),
                                                    ]
                                                )
                                                if thVisorCuentasContablesExiste:
                                                    if (
                                                        round(
                                                            thVisorCuentasContablesExiste.balance
                                                            - mdline.debit_amount_currency,
                                                            2,
                                                        )
                                                        == 0
                                                    ):
                                                        thVisorCuentasContablesExiste.unlink()
                                                    else:
                                                        thVisorCuentasContablesExiste.write(
                                                            {
                                                                "amount_residual": mdline.credit_move_id.balance
                                                                - mdline.debit_amount_currency,
                                                                "balance": thVisorCuentasContablesExiste.balance
                                                                - mdline.debit_amount_currency,
                                                            }
                                                        )
                                                else:
                                                    visor_cuentas_contables.create(
                                                        {
                                                            "move_line_id": mdline.credit_move_id.id,
                                                            "fecha": mdline.credit_move_id.date,
                                                            "move_id": mdline.credit_move_id.move_id.id,
                                                            "amount_residual": mdline.credit_move_id.balance
                                                            - mdline.debit_amount_currency,
                                                            "account_id": mdline.credit_move_id.account_id.id,
                                                            "journal_id": mdline.credit_move_id.journal_id.id,
                                                            #'balance': mdline.credit_move_id.balance - thP.amount_total,
                                                            "balance": mdline.credit_move_id.balance
                                                            - mdline.debit_amount_currency,
                                                            "analytic_distribution": mdline.credit_move_id.analytic_distribution,
                                                            "partner_id": mdline.credit_move_id.partner_id.id,
                                                            "tax_base_amount": mdline.credit_move_id.tax_base_amount,
                                                            "session_identifier": session_identifier,
                                                            # Asociar los datos a la cookie de sesión
                                                        }
                                                    )
                                                    NoInlcuirApuntesParciales.append(
                                                        mdline.credit_move_id.id
                                                    )
                                            elif (
                                                mdline.debit_amount_currency != 0
                                                and mdline.debit_amount_currency
                                                >= mdline.credit_move_id.balance
                                            ):
                                                NoInlcuirApuntesParciales.append(
                                                    mdline.credit_move_id.id
                                                )
                        if thP:
                            FacFacIds += thP
                        # thPagFactConci += thP.amount_total
                # ------------------------------------ Se buscan regularizaciones ------------------------
            # -------------------------------------consolidar pagos -----------------------------------

            # -------------------------------------Se buscan facturas rectificativas -----------------
            thTotalReversion = 0
            # for AsientoReversion in thFactura.reversal_move_id:
            #     if AsientoReversion.state == 'posted' and AsientoReversion.date <= date_to:
            #         AsientosPago.append(AsientoReversion)
            #         thTotalReversion += AsientoReversion.amount_total
            # -------------------------------------Se buscan facturas rectificativas -----------------

            if round((thPagFact + thTotalReversion + thPagFactConci), 2) >= round(
                thFactura.amount_total, 2
            ):
                FacturasCompletas.append(thFactura.id)
            else:
                if thPagFact != 0:
                    for thLine in thFactura.line_ids:
                        if thLine.account_id.id in self.account_ids.ids:
                            thMonto = thFactura.amount_total - thPagFact
                            if thLine.account_id.account_type == "liability_payable":
                                thMonto = thMonto * -1
                            visor_cuentas_contables.create(
                                {
                                    "move_line_id": thLine.id,
                                    "fecha": thLine.date,
                                    "move_id": thLine.move_id.id,
                                    "amount_residual": thMonto,
                                    "account_id": thLine.account_id.id,
                                    "journal_id": thLine.journal_id.id,
                                    "balance": thMonto,
                                    "analytic_distribution": thLine.analytic_distribution,
                                    "partner_id": thLine.partner_id.id,
                                    "tax_base_amount": thLine.tax_base_amount,
                                    "session_identifier": session_identifier,  # Asociar los datos a la cookie de sesión
                                }
                            )
                            FacturasCompletas.append(thFactura.id)

            # -------------------------------------consolidar pagos -----------------------------------
            #                 if FacPag.allocation >= thFactura.amount_total:
            #                     FacturasCompletas.append(thFactura.id)
            #                 else:
            #                     for thLine in thFactura.line_ids:
            #                         if thLine.account_id.id in self.account_ids.ids:
            #                             analytic_tags = self._compute_analytic_tags(thLine.analytic_distribution)
            #                             visor_cuentas_contables.create({
            #                                 'move_line_id': thLine.id,
            #                                 'fecha': thLine.date,
            #                                 'move_id': thLine.move_id.id,
            #                                 'amount_residual': thFactura.amount_total-FacPag.allocation,
            #                                 'account_id': thLine.account_id.id,
            #                                 'journal_id': thLine.journal_id.id,
            #                                 'balance': thFactura.amount_total-FacPag.allocation,
            #                                 'analytic_distribution': thLine.analytic_distribution,
            #                                 'analytic_tags': analytic_tags,
            #                                 'partner_id': thLine.partner_id.id,
            #                                 'tax_base_amount': thLine.tax_base_amount,
            #                                 'session_identifier': session_identifier,
            #                             # Asociar los datos a la cookie de sesión
            #                             })
            #                             FacturasCompletas.append(thFactura.id)
            thAuxPagos = self.env["account.move"]
            for thPP in thPagos:
                if thPP.payment_id:
                    if thPP.payment_id.id not in FacPagIds.ids:
                        thAuxPagos += thPP
            TotalPagado = sum([x.amount_total for x in thAuxPagos])
            if thPagFact != 0:
                TotalPagado = thPagFact
            if TotalPagado > thFactura.amount_total and thFactura.amount_residual <= 0:
                FacturasCompletas.append(thFactura.id)
                for thPaguito in thPagos:
                    thPayment = self.env["account.payment"].search(
                        [("id", "=", thPaguito.payment_id.id)]
                    )
                    thinvoice = sum(
                        [x.amount_total for x in thPayment.reconciled_invoice_ids]
                    )
                    thinvocies = []
                    thbills = []
                    for inv in thPayment.reconciled_invoice_ids:
                        thinvocies.append(inv.id)
                    for bill in thPayment.reconciled_bill_ids:
                        thbills.append(bill.id)
                    thbill = sum(
                        [x.amount_total for x in thPayment.reconciled_bill_ids]
                    )
                    thPagado = abs(
                        sum([x.amount_total for x in thPayment.reconciled_invoice_ids])
                    ) + abs(
                        sum([x.amount_total for x in thPayment.reconciled_bill_ids])
                    )
                    if abs(thPayment.amount) != abs(thPagado):
                        if thPayment.bolson_id and (
                            thPayment.reconciled_invoice_ids
                            or thPayment.reconciled_bill_ids
                        ):
                            if thPayment.id not in AsientosPagoExcedidos:
                                AsientosPagoExcedidos.append(thPayment.id)
                        elif thPayment.bolson_id:
                            xthfact = sum(
                                [x.amount_total for x in thPayment.bolson_id.facturas]
                            )
                            if abs(thPayment.amount) != abs(
                                sum(
                                    [
                                        x.amount_total
                                        for x in thPayment.bolson_id.facturas
                                    ]
                                )
                            ):
                                if thPayment.id not in AsientosPagoExcedidos:
                                    AsientosPagoExcedidos.append(thPayment.id)
                        else:
                            if thPayment.id not in AsientosPagoExcedidos:
                                AsientosPagoExcedidos.append(thPayment.id)
                    thAsientoEncontrado.append(thPaguito.id)
            elif TotalPagado == thFactura.amount_total:
                FacturasCompletas.append(thFactura.id)
                for thPaguito in thPagos:
                    thAsientoEncontrado.append(thPaguito.id)

        thFacturasPendientePago = xresults.filtered(
            lambda x: x.move_id.id not in FacturasCompletas
        )
        thFacturasRevisarReversion = self.env["account.move"].search(
            [
                ("id", "in", thFacturasPendientePago.mapped("move_id.id")),
                ("reversal_move_id", "!=", False),
            ]
        )

        FacturasConReversion = []
        for thFacturaRR in thFacturasRevisarReversion:
            thTotalReversion = 0
            for AsientoReversion in thFacturaRR.reversal_move_id:
                if (
                    AsientoReversion.state == "posted"
                    and AsientoReversion.date <= date_to
                ):
                    AsientosPago.append(AsientoReversion)
                    thTotalReversion += AsientoReversion.amount_total
            if thTotalReversion >= thFacturaRR.amount_total:
                FacturasConReversion.append(thFacturaRR.id)
            else:
                if thTotalReversion != 0:
                    for thLine in thFacturaRR.line_ids:
                        # if thLine.account_id.id in self.account_ids.ids:
                        #     visor_cuentas_contables.create({
                        #         'move_line_id': thLine.id,
                        #         'fecha': thLine.date,
                        #         'move_id': thLine.move_id.id,
                        #         'amount_residual': thFacturaRR.amount_total - thTotalReversion,
                        #         'account_id': thLine.account_id.id,
                        #         'journal_id': thLine.journal_id.id,
                        #         'balance': thFacturaRR.amount_total - thTotalReversion,
                        #         'analytic_distribution': thLine.analytic_distribution,
                        #         'partner_id': thLine.partner_id.id,
                        #         'tax_base_amount': thLine.tax_base_amount,
                        #         'session_identifier': session_identifier,  # Asociar los datos a la cookie de sesión
                        #     })
                        FacturasConReversion.append(thFacturaRR.id)

        FacturasConNotasdeCredito = thFacturasPendientePago.filtered(
            lambda x: x.move_id.id not in FacturasConReversion
        )
        thFacturasRevisarNotasCredito = self.env["account.move"].search(
            [
                ("id", "in", FacturasConNotasdeCredito.mapped("move_id.id")),
                ("reversed_entry_id", "!=", False),
            ]
        )

        FacturasNotaCredito = []
        for thFactura in thFacturasRevisarNotasCredito:
            if (
                thFactura.reversed_entry_id
                and thFactura.reversed_entry_id.state == "posted"
                and thFactura.reversed_entry_id.amount_total >= thFactura.amount_total
                and thFactura.reversed_entry_id.date <= date_to
            ):
                AsientosPago.append(thFactura.reversed_entry_id)
                FacturasNotaCredito.append(thFactura.id)

        preresults = FacturasConNotasdeCredito.filtered(
            lambda x: x.move_id.id not in FacturasConReversion
            and x.move_id.id not in FacturasNotaCredito
        )
        domain = [cond for cond in domain if cond != ("move_id.payment_id", "=", False)]
        domain.append(("move_id.id", "not in", FacturasNotaCredito))
        domain.append(("move_id.id", "not in", FacturasConReversion))
        domain.append(("move_id.id", "not in", FacturasCompletas))
        domain.append(("move_id.id", "not in", preresults.mapped("move_id.id")))
        PrePreResultsConPagos = self.env["account.move.line"].search(domain)
        PreResultsConPagos = self.env["account.move.line"]
        for prep in PrePreResultsConPagos:
            if (
                not prep.move_id.payment_id
            ):  # and prep.move_id.bolson_id.asiento.date <= date_to:
                PreResultsConPagos += prep
        if sum(PreResultsConPagos.mapped("balance")) == 0:
            results = None
        else:
            results = PreResultsConPagos
        if preresults and results:
            results += preresults
        if preresults and not results:
            results = preresults
        # if AsientosPagoExcedidos:
        #     auxa = 1
        #     thMoveLines = self.env['account.move.line'].search([('move_id.payment_id', 'in', AsientosPagoExcedidos),('move_id.state', '=', 'posted'),('account_id.id','in',self.account_ids.ids)])
        #     if thMoveLines and results:
        #         results += thMoveLines
        #     else:
        #         results = thMoveLines
        # visor_cuentas_contables = self.env['account.account.v']
        if results:
            SaldoAux = []
            AuxSaldo = 0.0
            for result in results:
                if result.move_id.id not in SaldoAux:
                    SaldoAux.append(result.move_id.id)
                    AuxSaldo = result.move_id.amount_residual
                analytic_tags = self._compute_analytic_tags(
                    result.analytic_distribution
                )
                if result.id not in NoInlcuirApuntesParciales:
                    visor_cuentas_contables.create(
                        {
                            "move_line_id": result.id,
                            "fecha": result.date,
                            "move_id": result.move_id.id,
                            "amount_residual": AuxSaldo,
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
        # buscar en account_account_v los resgistros de session_identifier agrupados por partner_id
        # y sumar los valores de balance
        # si el valor de balance es 0, eliminar el registro
        # si el valor de balance es diferente de 0, actualizar el valor de amount_residual
        records = self.env["account.account.v"].search(
            [("session_identifier", "=", session_identifier)]
        )

        # Crear un diccionario para agrupar los datos manualmente
        grouped_data = defaultdict(lambda: {"balance": 0, "records": []})

        for rec in records:
            key = (
                rec.move_id.id,
                rec.partner_id.id,
                rec.account_id.id,
            )  # Clave de agrupación
            grouped_data[key]["balance"] += rec.balance
            grouped_data[key]["records"].append(rec)

        # Procesar los datos agrupados
        for key, data in grouped_data.items():
            move_id, partner_id, account_id = key
            if data["balance"] == 0:
                for rec in data["records"]:
                    rec.unlink()  # Eliminar registros si el balance es 0

        return {
            "name": "Visor Cuentas Contables",
            "type": "ir.actions.act_window",
            "res_model": "account.account.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_account_v_view_tree").id,
            "search_view_id": self.env.ref("fin.view_account_account_v_search").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
            # Agrupar por mes
            # 'context': {'search_default_partner_id': 1}
        }


class AccountMove(models.Model):
    _inherit = "account.move"

    def get_related_payments(self):
        """Obtener los pagos relacionados con las facturas actuales (self)"""
        self.ensure_one()  # Asegúrate de que solo estás operando sobre una factura
        self.env["account.move.line"].flush(
            ["move_id", "debit", "credit", "payment_id"]
        )
        self.env["account.payment"].flush(["move_id", "payment_type"])

        query = """
            SELECT DISTINCT payment.id
            FROM account_payment payment
            JOIN account_move move ON move.id = payment.move_id
            JOIN account_move_line line ON line.payment_id = payment.id
            JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
            JOIN account_move_line counterpart_line ON part.debit_move_id = counterpart_line.id OR part.credit_move_id = counterpart_line.id
            WHERE counterpart_line.move_id = %s
              AND move.state = 'posted'
        """
        self._cr.execute(query, (self.id,))
        payment_ids = [row[0] for row in self._cr.fetchall()]

        payments = self.env["account.payment"].browse(payment_ids)
        return payments

    @api.depends("move_type", "line_ids.amount_residual")
    def _compute_related_payment_journal_entries(self):
        for move in self:
            if move.id == 5109:
                auxa = 1
            journal_entries = []

            # Solo aplicable a facturas publicadas
            if move.state == "posted":
                # Obtener todas las reconciliaciones parciales de la factura
                reconciled_partials = move._get_all_reconciled_invoice_partials()

                # Recorrer las líneas contables reconciliadas
                for reconciled_partial in reconciled_partials:
                    counterpart_line = reconciled_partial[
                        "aml"
                    ]  # Línea contable reconciliada

                    # Agregar el asiento contable, independientemente de si tiene un pago relacionado o no
                    if counterpart_line.move_id not in journal_entries:
                        journal_entries.append(counterpart_line.move_id)

            # Asignar los asientos contables de pagos relacionados a la factura
            # move.payment_journal_entries = journal_entries
        return journal_entries
