from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.http import request


class AccountAccountV(models.Model):
    _name = "account.account.v"
    _description = "Visor Cuentas Contables"

    fecha = fields.Date(string="Fecha", readonly=True)
    move_line_id = fields.Many2one(
        "account.move.line", string="Línea Asiento", readonly=True
    )
    move_id = fields.Many2one("account.move", string="Asiento", readonly=True)
    description = fields.Char(
        string="Descripción", store=True, related="move_line_id.name"
    )
    tipo_documento = fields.Selection(
        string="Tipo Documento", readonly=True, related="move_id.tipo_documento"
    )
    tipo_transaccion = fields.Selection(
        string="Tipo Transaccion", readonly=True, related="move_id.tipo_transaccion"
    )
    move_type = fields.Selection(
        string="Tipo", readonly=True, related="move_id.move_type"
    )
    ref = fields.Char(string="Referencia", readonly=True, related="move_id.ref")
    account_id = fields.Many2one("account.account", string="Cuenta", readonly=True)
    journal_id = fields.Many2one("account.journal", string="Diario", readonly=True)
    analytic_account_id = fields.Many2one(
        "account.analytic.account",
        string="Cuenta Analítica",
        readonly=True,
        store=True,
        related="move_line_id.analytic_account_id",
    )
    # analytic_account_id = fields.One2many('account.analytic.line', 'move_line_id', string="Cuenta Analítica", readonly=True)
    analytic_distribution = fields.Json(
        string="Distribución Analítica",
        readonly=True,
        related="move_line_id.analytic_distribution",
    )
    # analytic_tags = fields.Char(string="Proporcion Analítica", compute="_compute_analytic_tags", readonly=True)
    analytic_tags = fields.Char(
        string="Proporcion Analítica", readonly=True, store=True
    )
    balance = fields.Float(string="Balance", readonly=True)
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        # compute='_compute_currency_id',
        # store=True,
        readonly=True,
        related="move_line_id.currency_id",
        # precompute=True,
        # required=True,
    )
    price_unit = fields.Float(
        string="Precio", readonly=True, compute="_compute_price_unit"
    )  # related='move_line_id.price_unit')
    price_subtotal = fields.Monetary(
        string="Subtotal",
        readonly=True,
        currency_field="currency_id",
        compute="_compute_price_unit",
    )  # related='move_line_id.price_subtotal',)
    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)
    partner_id = fields.Many2one("res.partner", string="Contacto", readonly=True)
    tax_base_amount = fields.Float(string="Impuesto", readonly=True)

    session_identifier = fields.Char(
        string="Session Token", required=True
    )  # Campo para el token de sesión
    product_id = fields.Many2one(
        "product.product",
        string="Producto",
        store=True,
        related="move_line_id.product_id",
    )
    default_code = fields.Char(
        string="Código", store=True, related="product_id.default_code"
    )
    standard_price = fields.Float(
        string="Costo", compute="related_valuation"
    )  # related='product_id.standard_price')
    product_uom_id = fields.Many2one(
        "uom.uom",
        string="Unidad de Medida",
        store=True,
        related="move_line_id.product_uom_id",
    )
    tipo_gasto = fields.Selection(
        string="Tipo Gasto", store=True, related="move_line_id.tipo_gasto"
    )
    quantity = fields.Float(
        string="Cantidad", store=True, related="move_line_id.quantity"
    )
    tax_ids = fields.Many2many(
        "account.tax", string="Impuesto", store=False, related="move_line_id.tax_ids"
    )
    numero_fel = fields.Char(
        string="Número FEL", store=True, related="move_id.numero_fel"
    )
    serie_fel = fields.Char(string="Serie FEL", store=True, related="move_id.serie_fel")
    tipo_documento_fel = fields.Selection(
        string="Tipo Documento FEL",
        store=True,
        related="move_id.journal_id.tipo_documento_fel",
    )
    journal_type = fields.Selection(
        string="Tipo Diario", store=True, related="move_id.journal_id.type"
    )
    total_cost = fields.Float(
        string="Costo Total", readonly=True, compute="_compute_total_cost"
    )
    tax_names = fields.Char(
        string="Impuestos", compute="_compute_tax_names", store=False
    )
    payment_state = fields.Selection(
        string="Estado Pago", store=True, related="move_id.payment_state"
    )
    thwrite_date = fields.Datetime(
        string="Fecha Modificación", store=True, related="move_line_id.write_date"
    )
    amount_residual = fields.Monetary(
        string="Saldo", store=True, currency_field="currency_id"
    )

    def related_valuation(self):
        for record in self:
            if record.move_line_id:
                if record.move_line_id.stock_valuation_layer_ids:
                    record.standard_price = (
                        record.move_line_id.stock_valuation_layer_ids[0].unit_cost
                    )
                    # record.quantity = record.move_line_id.stock_valuation_layer_ids[0].quantity
                else:
                    record.standard_price = (
                        record.move_line_id.product_id.standard_price
                    )

    @api.depends("move_line_id.price_unit", "move_line_id.move_id.tipo_documento")
    def _compute_price_unit(self):
        for record in self:
            if record.move_line_id.move_id.tipo_documento == "NC":
                record.price_unit = -record.move_line_id.price_unit
                record.price_subtotal = -record.move_line_id.price_subtotal
            else:
                record.price_unit = record.move_line_id.price_unit
                record.price_subtotal = record.move_line_id.price_subtotal

    def _compute_tax_names(self):
        for record in self:
            if record.tax_ids:
                # Obtener los nombres de los impuestos y unirlos por comas
                record.tax_names = ", ".join(record.tax_ids.mapped("name"))
            else:
                record.tax_names = "N/A"

    @api.depends("standard_price", "quantity")
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.standard_price * record.quantity

    @api.model
    def get_session_identifier(self, fields_list):
        res = super(AccountAccountV, self).get_session_identifier(fields_list)
        session_identifier = request.session.sid
        if session_identifier:
            res["domain"] = [("session_identifier", "=", session_identifier)]
        return res

    @api.model
    def action_open_account_account_v(self):
        session_identifier = request.session.sid
        if any(
            f.company_id.id != self.env.company.id
            for f in self.env["account.account.v"].search(
                [("session_identifier", "=", session_identifier)]
            )
        ):
            self.env["account.account.v"].search(
                [("session_identifier", "=", session_identifier)]
            ).unlink()
        return {
            "name": "Visor Cuentas Contables",
            "type": "ir.actions.act_window",
            "res_model": "account.account.v",
            "view_mode": "list",
            "view_id": self.env.ref("fin.account_account_v_view_tree").id,
            "domain": [("session_identifier", "=", session_identifier)],
            "target": "current",
        }

    @api.model
    def create_or_update_records(self, results):
        session_identifier = self.get_session_identifier()
        self.search([("session_identifier", "=", session_identifier)]).unlink()
        for result in results:
            analytic_tags = self._compute_analytic_tags(result.analytic_distribution)
            self.create(
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
                    "session_identifier": session_identifier,
                }
            )

    @api.model
    def delete_old_records(self):
        # Define el umbral de 24 horas
        time_threshold = datetime.now() - timedelta(hours=24)
        # Busca los registros que son más antiguos de 24 horas
        old_records = self.search([("create_date", "<", time_threshold)])
        if old_records:
            old_records.unlink()

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        if "cost" in fields:
            fields.remove("cost")

        if "product_id" in groupby and "cost" not in fields:
            fields.append("product_id")
        # Agrega los campos necesarios a la lista de fields
        if "default_code" not in groupby:
            groupby.append("default_code")
        if "description" not in fields:
            fields.append("description")
        if "product_uom_id" not in groupby:
            groupby.append("product_uom_id")
        # Llamar al método original read_group
        result = super(AccountAccountV, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy
        )

        if "product_id" in groupby:
            for group in result:
                product_ids = group.get("product_id")
                if product_ids:
                    product_id = product_ids[0]
                    product = self.env["product.product"].browse(product_id)

                    # Obtener todas las líneas del producto
                    layers = self.search([("product_id", "=", product.id)] + domain)

                    if layers:
                        # Ordenar las líneas por fecha de modificación (campo `write_date`)
                        last_layer = layers.sorted(
                            key=lambda r: r.thwrite_date, reverse=True
                        )[0]

                        # Inicializar acumuladores
                        total_qty = 0.00
                        total_cost = 0.00

                        # Sumar cantidad y calcular el costo total
                        for layer in layers:
                            total_qty += layer.quantity
                            total_cost += layer.standard_price * layer.quantity

                        # Calcular el costo promedio ponderado
                        average_cost = (
                            total_cost / total_qty
                            if total_qty != 0 and total_cost != 0
                            else 0.00
                        )

                        # Tomar los valores del último registro modificado

                        group["quantity"] = total_qty
                        group["standard_price"] = average_cost
                        group["total_cost"] = total_cost
                        group["default_code"] = product.default_code
                        group["description"] = last_layer.description
                        group["product_uom_id"] = (
                            last_layer.product_uom_id.name
                            if last_layer.product_uom_id
                            else ""
                        )
                    else:
                        # Manejar el caso cuando no hay líneas
                        group["default_code"] = product.default_code
                        group["description"] = ""
                        group["product_uom_id"] = ""
                        group["quantity"] = 0
                        group["standard_price"] = 0
                        group["total_cost"] = 0

        return result

    # En account.account.v
    def open_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Consultar por Cuenta Contable",
            "res_model": "account.account.v.wizard",
            "view_mode": "form",
            "view_id": self.env.ref("fin.view_account_account_v_wizard_form").id,
            "target": "new",
            "context": {
                "default_account_ids": [(6, 0, self.ids)],
                "default_company_id": (
                    self.company_id.id if self.company_id else self.env.company.id
                ),
            },
        }
