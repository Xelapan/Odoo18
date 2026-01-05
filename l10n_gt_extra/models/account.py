# -*- encoding: utf-8 -*-
import math

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime
import logging


class AccountMove(models.Model):
    _inherit = "account.move"

    tipo_gasto = fields.Selection(
        [
            ("mixto", "Mixto"),
            ("compra", "Compra/Bien"),
            ("servicio", "Servicio"),
            ("importacion", "Importación/Exportación"),
            ("combustible", "Combustible"),
        ],
        string="Tipo de Gasto",
        default="mixto",
    )
    serie_rango = fields.Char(string="Serie Rango")
    inicial_rango = fields.Integer(string="Inicial Rango")
    final_rango = fields.Integer(string="Final Rango")
    diario_facturas_por_rangos = fields.Boolean(
        string="Las facturas se ingresan por rango",
        help="Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción",
        related="journal_id.facturas_por_rangos",
    )
    nota_debito = fields.Boolean(string="Nota de debito")

    # Xelapan 06 07 2023 Alex Martínez
    # Asiste Libros
    tipo_transaccion = fields.Selection(
        [("L", "Local"), ("I", "Importación"), ("E", "Exportación")],
        string="Tipo Transacción",
        store=True,
        default="L",
    )
    tipo_documento = fields.Selection(
        [
            ("FC", "FC - Factura Cambiaria"),
            ("FE", "FE - Factura Especial"),
            ("FCE", "FCE - Factura Cambiaria Electrónica"),
            ("NC", "NC - Nota de Crédito"),
            ("ND", "ND - Nota de Débito"),
            ("FPC", "FPC - Factura Pequeño Contribuyente"),
            ("DA", "DA - Declaración Aduanera"),
            ("FPE", "FPE - "),
            ("FAPE", "FAPE - "),
            ("FACA", "FACA - "),
            ("FAAE", "FAAE - "),
            ("FA", "FA - "),
            ("FO", "FO - Formulario"),
            ("EP", "EP - Escritura Pública"),
            ("FDU", "FDU - "),
        ],
        string="Tipo Documento",
        store=True,
        default="FC",
        help="Se muestran todos los tipos de documentos, para ser tomados en cuenta en calculos detallados como por ejemplo el IDP",
    )
    estado_factura = fields.Char(
        string="Estado Factura", compute="_estado_factura", readonly=True
    )

    txt_total_bien_cpa = fields.Float(
        string="Total Bien Local CPA", readonly=True, compute="_txt_total_bien_cpa"
    )
    txt_total_servicio_cpa = fields.Float(
        string="Total Servicio Local CPA",
        readonly=True,
        compute="_txt_total_servicio_cpa",
    )

    txt_total_ie_bien_cpa = fields.Float(
        string="Total I/E Bien CPA", readonly=True, compute="_txt_total_ie_bien_cpa"
    )
    txt_total_ie_servicio_cpa = fields.Float(
        string="Total I/E Servicio CPA",
        readonly=True,
        compute="_txt_total_ie_servicio_cpa",
    )
    # Alex
    # txt_local_bienpq = fields.Char(string="Local Bien PQ", readonly=True)
    # txt_local_servpq = fields.Char(string="Local Servicio PQ", readonly=True)
    # sum_iva_asiste = fields.Char(string="Suma IVA Asistelibros", readonly=True)

    txt_exter_ie_exen_bien = fields.Float(
        string="I/E Exento Bien", readonly=True, compute="_txt_exter_exen_bien"
    )
    txt_exter_ie_exen_serv = fields.Float(
        string="I/E Exento Servicio", readonly=True, compute="_txt_exter_exen_serv"
    )

    txt_local_bien_pq = fields.Float(
        string="Local Bien PQ", readonly=True, compute="_txt_local_bien_pq"
    )
    txt_local_serv_pq = fields.Float(
        string="Local Servicio PQ", readonly=True, compute="_txt_local_serv_pq"
    )

    txt_total_idp_arb = fields.Float(
        string="Total IDP u Otros Arbitrios",
        readonly=True,
        compute="_txt_total_idp_arb",
    )
    txt_sum_iva_asiste = fields.Float(
        string="Suma IVA Asistelibros", readonly=True, compute="_txt_sum_iva_asiste"
    )
    txt_total_libro_compras = fields.Float(
        string="Total Libro de Compras",
        readonly=True,
        compute="_txt_total_libro_compras",
    )
    txt_total_solo_bienes = fields.Float(
        string="Total Bienes sin Combustibles",
        readonly=True,
        compute="_txt_total_solo_bienes",
    )
    total_facturas_combustibles = fields.Float(
        string="Total de Facturas de Combustible",
        readonly=True,
        compute="_total_facturas_combustibles",
    )
    total_final_idp = fields.Float(
        string="Total Final IDP", readonly=True, compute="_total_final_idp"
    )

    total_bien_s_iva = fields.Float(
        string="Total Bien sin IVA", readonly=True, compute="_total_bien_s_iva"
    )
    total_serv_s_iva = fields.Float(
        string="Total Servicio sin IVA", readonly=True, compute="_total_serv_s_iva"
    )
    total_ie_bien_s_iva = fields.Float(
        string="Total I/E Bien sin IVA", readonly=True, compute="_total_ie_bien_s_iva"
    )
    total_ie_serv_s_iva = fields.Float(
        string="Total I/E Servicio sin IVA",
        readonly=True,
        compute="_total_ie_serv_s_iva",
    )

    total_local_exento_bien = fields.Float(
        string="Total Local Exento Bien", readonly=True, compute="_local_exento_bien"
    )
    total_local_exento_serv = fields.Float(
        string="Total Local Exento Servicio",
        readonly=True,
        compute="_local_exento_serv",
    )

    total_retencion_iva = fields.Float(
        string="Total Retención IVA", readonly=True, compute="_total_retencion_iva"
    )
    total_iva_retenido = fields.Float(
        string="Total IVA Retenido", readonly=True, compute="_total_iva_retenido"
    )

    referencia_interna = fields.Char(string="Referencia Interna", store=True)

    # Libro de Compras

    # def suma_impuesto(self,impuestos_ids):
    #     suma_monto = 0
    #     for impuesto in impuestos_ids:
    #         suma_monto += impuesto.amount
    #     return suma_monto
    #
    # def impuesto_global(self):
    #     impuestos = self.env['l10n_gt_extra.impuestos'].search([['active','=',True],['tipo','=','compra']])
    #     impuestos_valores = []
    #     diferencia  = 0
    #     suma_impuesto = 0
    #     impuesto_total = 0
    #     rango_final_anterior = 0
    #     for rango in impuestos.rangos_ids:
    #         if self.amount_untaxed > rango.rango_final and diferencia == 0:
    #             diferencia = self.amount_untaxed - rango.rango_final
    #             impuesto_individual = rango.rango_final * (self.suma_impuesto(rango.impuestos_ids) / 100)
    #             suma_impuesto += impuesto_individual
    #             # impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
    #         elif self.amount_untaxed <= rango.rango_final and diferencia == 0 and rango_final_anterior == 0:
    #             impuesto_individual = self.amount_untaxed * (self.suma_impuesto(rango.impuestos_ids) / 100)
    #             suma_impuesto += impuesto_individual
    #             rango_final_anterior = rango.rango_final
    #             # impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
    #         elif diferencia > 0:
    #             impuesto_individual = diferencia * (self.suma_impuesto(rango.impuestos_ids) / 100)
    #             suma_impuesto += impuesto_individual
    #             # impuestos_valores.append({'nombre': rango.impuestos_ids[0].name,'impuesto_id': rango.impuestos_ids[0].id,'account_id': rango.impuestos_ids[0].account_id.id,'total': impuesto_individual})
    #     impuesto_total = 0
    #     self.update({'amount_tax': suma_impuesto, 'amount_total': impuesto_total + self.amount_untaxed})
    #     # account_invoice_tax = self.env['account.invoice.tax']
    #     #
    #     # for impuesto in impuestos_valores:
    #     #     account_invoice_tax.create({'invoice_id': self.id,'tax_id':impuesto['impuesto_id'],'name': impuesto['nombre'],'account_id': impuesto['account_id'],'amount':impuesto['total'] })
    #     return True

    def impuesto_global(self):
        impuestos = None
        if self.move_type == "in_invoice":
            impuestos = self.env["l10n_gt_extra.impuestos"].search(
                [
                    ("active", "=", True),
                    ("tipo", "=", "compra"),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        elif self.move_type == "out_invoice":
            impuestos = self.env["l10n_gt_extra.impuestos"].search(
                [
                    ("active", "=", True),
                    ("tipo", "=", "venta"),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        elif self.tipo_documento == "FE":
            impuestos = self.env["l10n_gt_extra.impuestos"].search(
                [
                    ("active", "=", True),
                    ("tipo", "=", "compra"),
                    ("company_id", "=", self.company_id.id),
                ]
            )
            if not impuestos:
                impuestos = self.env["l10n_gt_extra.impuestos"].search(
                    [
                        ("active", "=", True),
                        ("tipo", "=", "venta"),
                        ("company_id", "=", self.company_id.id),
                    ]
                )
        if impuestos:
            impuestos_valores = []
            quitar_impuestos = []
            suma_impuesto = 0

            for impuesto in impuestos:
                # Llama a la función para evaluar el `python_compute` con el `amount_untaxed`
                for rango in impuesto.rangos_ids:
                    impuesto_calculado = rango.evaluar_formula_python(
                        self.amount_untaxed,
                        self.partner_id.property_account_position_id.name,
                    )
                    # impuesto_calculado = impuesto.evaluar_formula_python(self.amount_untaxed)

                    # Registra el valor del impuesto en la lista para líneas
                    if impuesto_calculado != 0:
                        # for rango in impuestos.rangos_ids:
                        impuestos_valores.append(
                            {
                                "nombre": rango.impuesto_calculo.name,
                                "impuesto_id": rango.impuesto_calculo.id,
                                "tax_group_id": rango.impuesto_calculo.tax_group_id.id,
                                "account_id": rango.impuesto_calculo.invoice_repartition_line_ids.filtered(
                                    lambda r: r.repartition_type == "tax"
                                ).account_id.id,
                                "total": impuesto_calculado,
                            }
                        )
                        suma_impuesto += impuesto_calculado
                    else:
                        quitar_impuestos.append({"nombre": rango.impuesto_calculo.name})
            # valor absoluto suma_impuesto
            # Actualiza el total de impuestos en `account.move`
            if suma_impuesto != 0:
                thAmount_tax = self.amount_tax + abs(suma_impuesto)
                self.update(
                    {
                        "amount_tax": thAmount_tax,
                        "amount_total": thAmount_tax + self.amount_untaxed,
                    }
                )

            # Crear o reemplazar líneas de impuestos en `account.move.line`
            for impuesto in impuestos_valores:
                if suma_impuesto != 0:
                    thGroup = self.env["account.tax.group"].search(
                        [("id", "=", int(impuesto["tax_group_id"]))]
                    )
                    line = self.line_ids.filtered(
                        lambda l: l.name == impuesto["nombre"]
                        and l.display_type in ["product", "line_section", "line_note"]
                    )
                    if line:
                        # Si la línea ya existe, reemplaza el valor
                        line.update(
                            {
                                "price_unit": impuesto["total"],
                                "account_id": impuesto["account_id"],
                                # 'tax_line_id': impuesto['impuesto_id'],
                                # colocar en tax_ids el id del impuesto
                                # 'tax_ids': [(6, 0, [impuesto['impuesto_id']])],
                                # 'credit': 0.0,
                                "tax_ids": False,
                                "debit": (
                                    abs(impuesto["total"])
                                    if impuesto["total"] != 0
                                    else 0.0
                                ),
                                "price_subtotal": impuesto["total"],
                                "tax_group_id": thGroup.id,
                            }
                        )
                    else:
                        # Si no existe, crea una nueva línea
                        self.line_ids.create(
                            {
                                "price_unit": impuesto["total"],
                                "move_id": self.id,
                                "name": impuesto["nombre"],
                                "account_id": impuesto["account_id"],
                                "tax_ids": False,
                                # 'tax_ids': impuesto['impuesto_id'],
                                # 'tax_ids': [(6, 0, [impuesto['impuesto_id']])],
                                # 'credit': 0.0,
                                "debit": (
                                    abs(impuesto["total"])
                                    if impuesto["total"] != 0
                                    else 0.0
                                ),
                                "price_subtotal": impuesto["total"],
                                "tax_group_id": thGroup.id,
                            }
                        )
                else:
                    self_with_context = self.with_context({"dynamic_unlink": True})
                    line = self_with_context.line_ids.filtered(
                        lambda l: l.name == impuesto["nombre"]
                    )
                    if line:
                        line.unlink()
            if not impuestos_valores:
                self_with_context = self.with_context({"dynamic_unlink": True})
                line = self_with_context.line_ids.filtered(
                    lambda l: l.name
                    in [impuesto["nombre"] for impuesto in quitar_impuestos]
                )
                if line:
                    line.unlink()
        return True

    def suma_impuesto(self, impuestos):
        # Función para sumar los valores de los impuestos
        return sum(impuesto.amount for impuesto in impuestos)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record.impuesto_global()  # Aplicar impuestos al crear
        return record

    @api.constrains("reference")
    def _validar_factura_proveedor(self):
        if self.reference:
            facturas = self.search(
                [
                    ("reference", "=", self.reference),
                    ("partner_id", "=", self.partner_id.id),
                    ("type", "=", "in_invoice"),
                ]
            )
            if len(facturas) > 1:
                raise ValidationError("Ya existe una factura con ese mismo numero.")

    @api.constrains("inicial_rango", "final_rango")
    def _validar_rango(self):
        if self.diario_facturas_por_rangos:
            if int(self.final_rango) < int(self.inicial_rango):
                raise ValidationError(
                    "El número inicial del rango es mayor que el final."
                )
            cruzados = self.search(
                [
                    ("serie_rango", "=", self.serie_rango),
                    ("inicial_rango", "<=", self.inicial_rango),
                    ("final_rango", ">=", self.inicial_rango),
                ]
            )
            if len(cruzados) > 1:
                raise ValidationError(
                    "Ya existe otra factura con esta serie y en el mismo rango"
                )
            cruzados = self.search(
                [
                    ("serie_rango", "=", self.serie_rango),
                    ("inicial_rango", "<=", self.final_rango),
                    ("final_rango", ">=", self.final_rango),
                ]
            )
            if len(cruzados) > 1:
                raise ValidationError(
                    "Ya existe otra factura con esta serie y en el mismo rango"
                )
            cruzados = self.search(
                [
                    ("serie_rango", "=", self.serie_rango),
                    ("inicial_rango", ">=", self.inicial_rango),
                    ("inicial_rango", "<=", self.final_rango),
                ]
            )
            if len(cruzados) > 1:
                raise ValidationError(
                    "Ya existe otra factura con esta serie y en el mismo rango"
                )

            self.name = "{}-{} al {}-{}".format(
                self.serie_rango, self.inicial_rango, self.serie_rango, self.final_rango
            )

    # Libro compras Alex Martínez 11 07 2023
    @api.depends("state")
    def _estado_factura(self):
        for record in self:
            if record.state == "cancel":
                record.estado_factura = "A"
            elif record.state == "posted":
                record.estado_factura = "E"
            else:
                record.estado_factura = "0"

    @api.depends("invoice_line_ids")
    def _txt_total_bien_cpa(self):
        for record in self:
            record.txt_total_bien_cpa = format(
                sum([(p.local_bien_cpa) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_total_servicio_cpa(self):
        for record in self:
            record.txt_total_servicio_cpa = format(
                sum([(p.local_servicio_cpa) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_total_ie_bien_cpa(self):
        for record in self:
            record.txt_total_ie_bien_cpa = format(
                sum([(p.ie_bien_cpa) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_total_ie_servicio_cpa(self):
        for record in self:
            record.txt_total_ie_servicio_cpa = format(
                sum([(p.ie_servicio_cpa) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_local_bien_pq(self):
        for record in self:
            record.txt_local_bien_pq = format(
                sum([(p.local_peq_bien) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_local_serv_pq(self):
        for record in self:
            record.txt_local_serv_pq = format(
                sum([(p.local_peq_serv) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_total_idp_arb(self):
        for record in self:
            record.txt_total_idp_arb = format(
                sum([(p.idp_arbitrios) for p in record.line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_sum_iva_asiste(self):
        for record in self:
            record.txt_sum_iva_asiste = format(
                sum([(p.iva_asiste) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_total_libro_compras(self):
        for record in self:
            record.txt_total_libro_compras = format(
                sum([(p.total_asiste) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_exter_exen_bien(self):
        for record in self:
            record.txt_exter_ie_exen_bien = format(
                sum([(p.exter_ie_exen_bien) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_exter_exen_serv(self):
        for record in self:
            record.txt_exter_ie_exen_serv = format(
                sum([(p.exter_ie_exen_serv) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _txt_total_solo_bienes(self):
        for record in self:
            record.txt_total_solo_bienes = format(
                sum([(p.monto_base_solo_bienes) for p in record.invoice_line_ids]),
                ".2f",
            )

    @api.depends("invoice_line_ids")
    def _total_facturas_combustibles(self):
        for record in self:
            record.total_facturas_combustibles = format(
                sum([(p.facturas_combustible) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _total_final_idp(self):
        for record in self:
            record.total_final_idp = format(
                sum([(p.idp_total) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _total_bien_s_iva(self):
        for record in self:
            # total = sum(p.local_grav_bien for p in record.invoice_line_ids) / 1.12
            # record.total_bien_s_iva = math.ceil(total * 100) / 100
            record.total_bien_s_iva = format(
                (sum([(p.local_grav_bien) for p in record.invoice_line_ids])) / 1.12,
                ".2f",
            )

    @api.depends("invoice_line_ids")
    def _total_serv_s_iva(self):
        for record in self:
            record.total_serv_s_iva = format(
                (sum([(p.local_grav_serv) for p in record.invoice_line_ids])) / 1.12,
                ".2f",
            )

    @api.depends("invoice_line_ids")
    def _total_ie_bien_s_iva(self):
        for record in self:
            record.total_ie_bien_s_iva = format(
                (sum([(p.ie_grav_bien) for p in record.invoice_line_ids])) / 1.12, ".2f"
            )

    @api.depends("invoice_line_ids")
    def _total_ie_serv_s_iva(self):
        for record in self:
            record.total_ie_serv_s_iva = format(
                (sum([(p.ie_grav_serv) for p in record.invoice_line_ids])) / 1.12, ".2f"
            )

    @api.depends("invoice_line_ids")
    def _local_exento_bien(self):
        for record in self:
            record.total_local_exento_bien = format(
                sum([(p.local_exento_bien) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _local_exento_serv(self):
        for record in self:
            record.total_local_exento_serv = format(
                sum([(p.local_exento_serv) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids")
    def _total_retencion_iva(self):
        for record in self:
            record.total_retencion_iva = format(
                sum([(p.retencion_iva) for p in record.invoice_line_ids]), ".2f"
            )

    @api.depends("invoice_line_ids", "amount_total")
    def _total_iva_retenido(self):
        for record in self:
            if record.amount_total > 2500:
                # record.total_iva_retenido = format((sum([(p.retencion_iva) for p in record.invoice_line_ids]))*0.15, ".2f")
                record.total_iva_retenido = format(
                    (record.txt_sum_iva_asiste) * 0.15, ".2f"
                )
                auxa = record.total_iva_retenido
            else:
                record.total_iva_retenido = 0


# Xelapan 06 07 2023 Alex Martínez
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    # Todos los cambios de PROMMIT en este modulo para eficientar el procesamiento y aplicar buenas practicas de desarrollo - Alex Martínez
    total_asiste = fields.Float(
        string="Total Sin Impuesto Asiste", compute="_total_asiste", readonly=True
    )
    idp_arbitrios = fields.Float(
        string="IDP u Otros Arbitrios", readonly=True, compute="_idp_arbitrios"
    )
    iva_asiste = fields.Float(string="IVA Asiste", readonly=True, compute="_iva_asiste")
    retencion_iva = fields.Float(
        string="Retención IVA", readonly=True, compute="_retencion_iva"
    )
    idp_total = fields.Float(string="Total IDP", readonly=True, compute="_idp_total")

    local_peq_bien = fields.Float(
        string="Local Bien Pequeño Contribuyente",
        readonly=True,
        compute="_local_peq_bien",
    )
    local_peq_serv = fields.Float(
        string="Local Servicio Pequeño Contribuyente",
        readonly=True,
        compute="_local_peq_serv",
    )

    ie_bien_cpa = fields.Float(
        string="I/E Bien CPA", readonly=True, compute="_ie_bien_cpa"
    )
    ie_servicio_cpa = fields.Float(
        string="I/E Servicio CPA", readonly=True, compute="_ie_servicio_cpa"
    )

    local_bien_cpa = fields.Float(
        string="Local Bien CPA", readonly=True, compute="_local_bien_cpa"
    )
    local_servicio_cpa = fields.Float(
        string="Local Servicio CPA", readonly=True, compute="_local_servicio_cpa"
    )

    exter_ie_exen_bien = fields.Float(
        string="I/E Exento Bien", readonly=True, compute="_exter_ie_exen_bien"
    )
    exter_ie_exen_serv = fields.Float(
        string="I/E Exento Servicio", readonly=True, compute="_exter_ie_exen_serv"
    )
    facturas_combustible = fields.Float(
        string="Facturas de Combustible", readonly=True, compute="_facturas_combustible"
    )
    monto_base_solo_bienes = fields.Float(
        string="Total de Bienes sin Combustible",
        readonly=True,
        compute="_monto_base_solo_bienes",
    )

    local_grav_bien = fields.Float(
        string="Local Gravado Bien", readonly=True, compute="_local_grav_bien"
    )
    local_grav_serv = fields.Float(
        string="Local Gravado Servicio", readonly=True, compute="_local_grav_serv"
    )

    ie_grav_bien = fields.Float(
        string="I/E Gravado Bien", readonly=True, compute="_ie_grav_bien"
    )
    ie_grav_serv = fields.Float(
        string="I/E Gravado Servicio", readonly=True, compute="_ie_grav_serv"
    )

    local_exento_bien = fields.Float(
        string="Local Exento Bien", readonly=True, compute="_local_exento_bien"
    )
    local_exento_serv = fields.Float(
        string="Local Exento Servicio", readonly=True, compute="_local_exento_serv"
    )

    # exter_peq_bien = fields.Float(string="I/E Bien Pequeño Contribuyente", readonly=True, compute='_exter_peq_bien')
    # exter_peq_serv = fields.Float(string="I/E Servicio Pequeño Contribuyente", readonly=True, compute='_exter_peq_serv')

    tipo_gasto = fields.Selection(
        [
            ("servicio", "Servicio"),
            ("bien", "Bien"),
            ("combustible", "Combustible"),
            ("importacion", "Importación"),
            ("exportacion", "Exportación"),
        ],
        string="Tipo de Gasto",
        default=False,
    )

    @api.depends("quantity", "price_unit")
    def _total_asiste(self):
        for record in self:
            if record.discount > 0:
                record.total_asiste = (
                    record.quantity * record.price_unit * (1 - record.discount / 100)
                )
            else:
                record.total_asiste = (
                    record.quantity * record.price_unit
                )  # record.price_total #record.price_subtotal

    @api.depends("total_asiste", "product_id")
    def _idp_arbitrios(self):
        xItera = 0
        for record in self:
            # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                # if len(record.tax_ids) > 0:
                #     record.idp_arbitrios = (
                #             (record.total_asiste) - (record.price_subtotal + (record.price_subtotal * 0.12)))
                # if xItera == 0:
                if record.idp_arbitrios == 0:
                    # for line2 in record.move_id.line_ids:
                    # xItera = 1
                    if record.account_id.name in [
                        "Impuestos Tasas y Contribuciones",
                        "Construcciones en Proceso Propiedad Ajena",
                        "Construcciones en proceso",
                    ] and (
                        record.display_type
                        not in ["product", "line_section", "line_note"]
                        or len(record.tax_ids) == 0
                    ):
                        record.idp_arbitrios = record.balance
                # if record.display_type not in ['product','line_sectio n','line_note'] and record.account_id.name == 'Impuestos Tasas y Contribuciones':
                # if record.display_type == 'tax' and record.account_id.name == 'Impuestos Tasas y Contribuciones':
                #     record.idp_arbitrios = (record.total_asiste)
                else:
                    record.idp_arbitrios = 0
            else:
                record.idp_arbitrios = 0

    @api.depends("total_asiste", "product_id")
    def _iva_asiste(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if len(record.tax_ids) > 0:
                    if (
                        record.move_id.tipo_documento == "NC"
                        or record.move_id.tipo_documento == "ND"
                    ):
                        record.iva_asiste = (
                            ((record.total_asiste - record.idp_total) / 1.12) * 0.12
                        ) * -1
                    else:
                        record.iva_asiste = (
                            (record.total_asiste - record.idp_total) / 1.12
                        ) * 0.12
                else:
                    record.iva_asiste = 0
            else:
                record.iva_asiste = 0

    @api.depends("total_asiste", "product_id")
    def _local_peq_bien(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento == "FPC"
                or record.move_id.tipo_documento == "FPE"
                or record.move_id.tipo_documento == "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if record.tipo_gasto == "bien":
                        record.local_peq_bien = record.total_asiste
                    else:
                        record.local_peq_bien = 0
                else:
                    record.local_peq_bien = 0
            else:
                record.local_peq_bien = 0

    @api.depends("total_asiste", "product_id")
    def _local_peq_serv(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento == "FPC"
                or record.move_id.tipo_documento == "FPE"
                or record.move_id.tipo_documento == "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if record.tipo_gasto == "servicio":
                        record.local_peq_serv = record.total_asiste
                    else:
                        record.local_peq_serv = 0
                else:
                    record.local_peq_serv = 0
            else:
                record.local_peq_serv = 0

    @api.depends("total_asiste", "product_id")
    def _ie_bien_cpa(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if (
                    record.move_id.tipo_transaccion == "I"
                    or record.move_id.tipo_transaccion == "E"
                ):
                    if len(record.tax_ids) > 0:
                        if record.tipo_gasto == "bien":
                            # if record.product_id.tipo_gasto == 'Bien':
                            record.ie_bien_cpa = (
                                record.total_asiste / 1.12
                            ) - record.idp_arbitrios
                        else:
                            record.ie_bien_cpa = 0
                    else:
                        record.ie_bien_cpa = 0
                else:
                    record.ie_bien_cpa = 0
            else:
                record.ie_bien_cpa = 0

    @api.depends("total_asiste", "product_id")
    def _ie_servicio_cpa(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento == "FPC"
                or record.move_id.tipo_documento == "FPE"
                or record.move_id.tipo_documento == "FAPE"
            ):
                if (
                    record.move_id.tipo_transaccion == "I"
                    or record.move_id.tipo_transaccion == "E"
                ):
                    if len(record.tax_ids) > 0:
                        if record.tipo_gasto == "servicio":
                            record.ie_servicio_cpa = (
                                record.total_asiste / 1.12
                            ) - record.idp_arbitrios
                        else:
                            record.ie_servicio_cpa = 0
                    else:
                        record.ie_servicio_cpa = 0
                else:
                    record.ie_servicio_cpa = 0
            else:
                record.ie_servicio_cpa = 0

    @api.depends("total_asiste", "product_id")
    def _local_servicio_cpa(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if len(record.tax_ids) > 0:
                        # if record.product_id.tipo_gasto == 'Servicio':
                        if (record.tipo_gasto and record.tipo_gasto == "servicio") or (
                            not record.tipo_gasto
                            and record.product_id.tipo_gasto == "Servicio"
                        ):
                            if (
                                record.move_id.tipo_documento == "NC"
                                or record.move_id.tipo_documento == "ND"
                            ):
                                record.local_servicio_cpa = (
                                    (
                                        (record.total_asiste - record.idp_arbitrios)
                                        / 1.12
                                    )
                                ) * -1
                            else:
                                record.local_servicio_cpa = (
                                    record.total_asiste - record.idp_arbitrios
                                ) / 1.12
                        else:
                            record.local_servicio_cpa = 0
                    else:
                        record.local_servicio_cpa = 0
                else:
                    record.local_servicio_cpa = 0
            else:
                record.local_servicio_cpa = 0

    @api.depends("total_asiste", "product_id")
    def _local_bien_cpa(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if len(record.tax_ids) > 0:
                        # if record.product_id.tipo_gasto == 'Bien' or record.product_id.tipo_gasto == 'Combustible':
                        if (
                            record.tipo_gasto
                            and record.tipo_gasto == "bien"
                            or record.tipo_gasto == "combustible"
                        ) or (
                            not record.tipo_gasto
                            and record.product_id.tipo_gasto == "Bien"
                        ):
                            if record.move_id.tipo_documento == "NC":
                                # 27/11/2024 Edvin se solicito quitar la retención iva de la formula
                                record.local_bien_cpa = (
                                    ((record.total_asiste) - record.idp_arbitrios)
                                    / 1.12
                                ) * -1
                                # record.local_bien_cpa = (((record.total_asiste) - record.idp_arbitrios + record.retencion_iva) / 1.12) * -1
                            else:
                                if any("IDP" in p.name for p in record.tax_ids):
                                    thArbitrios = sum(
                                        [
                                            (p.idp_arbitrios)
                                            for p in record.move_id.line_ids
                                        ]
                                    )
                                    record.local_bien_cpa = (
                                        (record.total_asiste) - thArbitrios
                                    ) / 1.12
                                else:
                                    record.local_bien_cpa = (
                                        (record.total_asiste)
                                    ) / 1.12
                                # record.local_bien_cpa = ((record.total_asiste) - record.idp_arbitrios + record.retencion_iva) / 1.12
                        else:
                            record.local_bien_cpa = 0
                    else:
                        record.local_bien_cpa = 0
                else:
                    record.local_bien_cpa = 0
            else:
                record.local_bien_cpa = 0

    @api.depends("tax_ids")
    def _retencion_iva(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            # Alex 21 09 2024 Retencion IVA 5
            if (
                sum(
                    [
                        (("Retenci" in p.name or "RETENCI" in p.name) and "5" in p.name)
                        for p in record.tax_ids
                    ]
                )
                == 1
            ):
                record.retencion_iva = record.total_asiste * 0.05
            else:
                record.retencion_iva = 0

    @api.depends("total_asiste", "price_subtotal", "tax_ids")
    def _idp_total(self):
        for record in self:
            # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if len(record.tax_ids) > 0:
                    # x_id_idp - Esta es la traduccion de x_id_idp de prommit
                    if (
                        sum(
                            [
                                ("idp" in p.name or "IDP" in p.name)
                                for p in record.tax_ids
                            ]
                        )
                        == 1
                    ):
                        record.idp_total = (record.total_asiste) - (
                            record.price_subtotal + (record.price_subtotal * 0.12)
                        )
                    else:
                        record.idp_total = 0
                else:
                    record.idp_total = 0
            else:
                record.idp_total = 0

    @api.depends("total_asiste", "product_id")
    def _exter_ie_exen_bien(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if (
                    record.move_id.tipo_transaccion == "I"
                    or record.move_id.tipo_transaccion == "E"
                ):
                    if len(record.tax_ids) < 1:
                        if record.product_id.tipo_gasto == "Bien":
                            record.exter_ie_exen_bien = record.total_asiste
                        else:
                            record.exter_ie_exen_bien = 0
                    else:
                        record.exter_ie_exen_bien = 0
                else:
                    record.exter_ie_exen_bien = 0
            else:
                record.exter_ie_exen_bien = 0

    @api.depends("total_asiste", "product_id")
    def _exter_ie_exen_serv(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if (
                    record.move_id.tipo_transaccion == "I"
                    or record.move_id.tipo_transaccion == "E"
                ):
                    if len(record.tax_ids) < 1:
                        if record.product_id.tipo_gasto == "Servicio":
                            record.exter_ie_exen_serv = record.total_asiste
                        else:
                            record.exter_ie_exen_serv = 0
                    else:
                        record.exter_ie_exen_serv = 0
                else:
                    record.exter_ie_exen_serv = 0
            else:
                record.exter_ie_exen_serv = 0

    @api.depends("total_asiste", "product_id")
    def _monto_base_solo_bienes(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if len(record.tax_ids) > 0:
                        if record.product_id.tipo_gasto == "Combustible":
                            # x_id_idp - Esta es la traduccion de x_id_idp de prommit
                            if sum([("idp" in p.name) for p in record.tax_ids]) == 0:
                                record.monto_base_solo_bienes = record.total_asiste
                            else:
                                record.monto_base_solo_bienes = 0
                        else:
                            record.monto_base_solo_bienes = 0
                    else:
                        record.monto_base_solo_bienes = 0
                else:
                    record.monto_base_solo_bienes = 0
            else:
                record.monto_base_solo_bienes = 0

    @api.depends("total_asiste", "product_id")
    def _facturas_combustible(self):
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if len(record.tax_ids) > 0:
                    # x_id_idp - Esta es la traduccion de x_id_idp de prommit
                    if sum([("idp" in p.name) for p in record.tax_ids]) == 1:
                        record.facturas_combustible = (
                            record.total_asiste - record.idp_total
                        ) / 1.12
                    else:
                        record.facturas_combustible = 0
                else:
                    record.facturas_combustible = 0
            else:
                record.facturas_combustible = 0

    @api.depends("total_asiste", "product_id")
    def _local_grav_bien(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if len(record.tax_ids) > 0:
                        if record.product_id.tipo_gasto == "Bien":
                            record.local_grav_bien = record.total_asiste
                        elif record.product_id.tipo_gasto == "Combustible":
                            record.local_grav_bien = (
                                record.total_asiste - record.idp_total
                            )
                        else:
                            record.local_grav_bien = 0
                    else:
                        record.local_grav_bien = 0
                else:
                    record.local_grav_bien = 0
            else:
                record.local_grav_bien = 0

    @api.depends("total_asiste", "product_id")
    def _local_grav_serv(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if len(record.tax_ids) > 0:
                        if record.product_id.tipo_gasto == "Servicio":
                            record.local_grav_serv = record.total_asiste
                        else:
                            record.local_grav_serv = 0
                    else:
                        record.local_grav_serv = 0
                else:
                    record.local_grav_serv = 0
            else:
                record.local_grav_serv = 0

    @api.depends("total_asiste", "product_id")
    def _ie_grav_bien(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if (
                    record.move_id.tipo_transaccion == "I"
                    or record.move_id.tipo_transaccion == "E"
                ):
                    if len(record.tax_ids) > 0:
                        if record.product_id.tipo_gasto == "Bien":
                            record.ie_grav_bien = record.total_asiste
                        else:
                            record.ie_grav_bien = 0
                    else:
                        record.ie_grav_bien = 0
                else:
                    record.ie_grav_bien = 0
            else:
                record.ie_grav_bien = 0

    @api.depends("total_asiste", "product_id")
    def _ie_grav_serv(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if (
                    record.move_id.tipo_transaccion == "I"
                    or record.move_id.tipo_transaccion == "E"
                ):
                    if len(record.tax_ids) > 0:
                        if record.product_id.tipo_gasto == "Servicio":
                            record.ie_grav_serv = record.total_asiste
                        else:
                            record.ie_grav_serv = 0
                    else:
                        record.ie_grav_serv = 0
                else:
                    record.ie_grav_serv = 0
            else:
                record.ie_grav_serv = 0

    @api.depends("total_asiste", "product_id")
    def _local_exento_bien(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    # x_id_idp - Esta es la traduccion de x_id_idp de prommit
                    if (
                        len(record.tax_ids) < 1
                        or sum([("idp" in p.name) for p in record.tax_ids]) == 1
                    ):
                        if (
                            record.tipo_gasto == "Bien" or record.tipo_gasto == "bien"
                        ) and record.product_id.name not in [
                            "Impuestos Tasas y Contribuciones",
                            "Construcciones en Proceso Propiedad Ajena",
                            "Construcciones en proceso",
                        ]:
                            record.local_exento_bien = record.total_asiste
                        elif record.product_id.tipo_gasto == "Combustible":
                            record.local_exento_bien = record.idp_arbitrios
                        else:
                            record.local_exento_bien = 0
                    else:
                        record.local_exento_bien = 0
                else:
                    record.local_exento_bien = 0
            else:
                record.local_exento_bien = 0

    @api.depends("total_asiste", "product_id")
    def _local_exento_serv(self):
        # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
        for record in self:
            if (
                record.move_id.tipo_documento != "FPC"
                and record.move_id.tipo_documento != "FPE"
                and record.move_id.tipo_documento != "FAPE"
            ):
                if record.move_id.tipo_transaccion == "L":
                    if len(record.tax_ids) < 1:
                        if (
                            record.tipo_gasto == "servicio"
                            or record.tipo_gasto == "Servicio"
                        ) and record.product_id.name not in [
                            "Impuestos Tasas y Contribuciones",
                            "Construcciones en Proceso Propiedad Ajena",
                            "Construcciones en proceso",
                        ]:
                            record.local_exento_serv = record.total_asiste
                        else:
                            record.local_exento_serv = 0
                    else:
                        record.local_exento_serv = 0
                else:
                    record.local_exento_serv = 0
            else:
                record.local_exento_serv = 0

    # @api.depends('total_asiste', 'product_id')
    # def _exter_peq_bien(self):
    # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
    # for record in self:
    # if record.move_id.tipo_documento == 'FPC' or record.move_id.tipo_documento == 'FPE' or record.move_id.tipo_documento == 'FAPE':
    # if record.move_id.tipo_transaccion == 'E':
    # if len(record.tax_ids) < 1:
    # if record.product_id.tipo_gasto == 'Bien':
    # record.exter_peq_bien = record.total_asiste
    # else:
    # record.exter_peq_bien = 0
    # else:
    # record.exter_peq_bien = 0
    # else:
    # record.exter_peq_bien = 0
    # else:
    # record.exter_peq_bien = 0

    # @api.depends('total_asiste', 'product_id')
    # def _exter_peq_serv(self):
    # x_compapq - esta condicion if es la traduccion de el campo x_compapq == 0 de prommit
    # for record in self:
    # if record.move_id.tipo_documento == 'FPC' or record.move_id.tipo_documento == 'FPE' or record.move_id.tipo_documento == 'FAPE':
    # if record.move_id.tipo_transaccion == 'E':
    # if len(record.tax_ids) < 1:
    # if record.product_id.tipo_gasto == 'Servicio':
    # record.exter_peq_serv = record.total_asiste
    # else:
    # record.exter_peq_serv = 0
    # else:
    # record.exter_peq_serv = 0
    # else:
    # record.exter_peq_serv = 0
    # else:
    # record.exter_peq_serv = 0


# Xelapan - Alex Martínez Libro de Compras 11 07 2023
class ProductTemplate(models.Model):
    _inherit = "product.template"
    tipo_gasto = fields.Selection(
        [
            ("Servicio", "Servicio"),
            ("Bien", "Bien"),
            ("Combustible", "Combustible"),
            ("Importación", "Importación"),
            ("Exportación", "Exportación"),
        ],
        string="Tipo Gasto",
        store=True,
        help="Este campo se utiliza para calcular impuestos para libro de compras y venta en Asistelibros",
    )


class DocumentoRetencionExencion(models.Model):
    _name = "x_doc_ret_exe"
    _description = "Documento de Retención o Exención"

    name = fields.Char(string="Número de Documento", store=True)
    tipo_constancia = fields.Selection(
        [("CADI", "CADI"), ("CEXE", "CEXE"), ("CRIVA", "CRIVA")],
        string="Tipo de Constancia",
        store=True,
    )
    valor = fields.Float(string="Valor", store=True)


# Fin Xelapan 06 07 2023 Alex Martínez
class AccountPayment(models.Model):
    _inherit = "account.payment"

    descripcion = fields.Char(string="Descripción")
    numero_viejo = fields.Char(string="Numero Viejo")
    nombre_impreso = fields.Char(string="Nombre Impreso")
    no_negociable = fields.Boolean(string="No Negociable", default=True)
    anulado = fields.Boolean("Anulado")
    fecha_anulacion = fields.Date("Fecha anulación")

    def cancel(self):
        for rec in self:
            rec.write({"numero_viejo": rec.name})
        return super(AccountPayment, self).cancel()

    def anular(self):
        for rec in self:
            # for move in rec.move_line_ids.mapped("move_id"):
            #     move.button_cancel()
            for move in rec.move_id:
                move.button_cancel()

            # rec.move_line_ids.remove_move_reconcile()
            # rec.move_line_ids.write({"debit": 0, "credit": 0, "amount_currency": 0})
            rec.move_id.line_ids.remove_move_reconcile()
            rec.move_id.line_ids.write({"debit": 0, "credit": 0, "amount_currency": 0})

            # for move in rec.move_line_ids.mapped("move_id"):
            #     move.post()
            for move in rec.move_id:
                move.post()
            rec.anulado = True
            rec.fecha_anulacion = datetime.datetime.strftime(
                datetime.datetime.now(), "%Y-%m-%d"
            )


class AccountJournal(models.Model):
    _inherit = "account.journal"

    direccion = fields.Many2one("res.partner", string="Dirección")
    codigo_establecimiento = fields.Integer(string="Código de establecimiento")
    facturas_por_rangos = fields.Boolean(
        string="Las facturas se ingresan por rango",
        help="Cada factura realmente es un rango de factura y el rango se ingresa en Referencia/Descripción",
    )
    usar_referencia = fields.Boolean(
        string="Usar referencia para libro de ventas",
        help="El número de la factua se ingresa en Referencia/Descripción",
    )
