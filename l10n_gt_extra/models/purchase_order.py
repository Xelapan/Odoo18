from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def impuesto_global(self):
        impuestos = self.env["l10n_gt_extra.impuestos"].search(
            [
                ("active", "=", True),
                ("tipo", "=", "compra"),
                ("company_id", "=", self.company_id.id),
            ]
        )
        if impuestos:
            quitar_impuestos = []
            impuestos_valores = []
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
                    for rango in impuestos.rangos_ids:
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
                    quitar_impuestos.append(
                        {
                            "nombre": impuesto.nombre,
                        }
                    )
            # valor absoluto suma_impuesto
            # Actualiza el total de impuestos en `account.move`
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
                    line = self.order_line.filtered(
                        lambda l: l.name == impuesto["nombre"]
                    )
                    if line:
                        # Si la línea ya existe, reemplaza el valor
                        line.update(
                            {
                                "price_unit": impuesto["total"],
                                "taxes_id": [(6, 0, [impuesto["impuesto_id"]])],
                                "price_subtotal": impuesto["total"],
                            }
                        )
                    else:
                        # Si no existe, crea una nueva línea
                        self.order_line.create(
                            {
                                "product_qty": 1,
                                "product_id": self.env["product.product"]
                                .search(
                                    [("name", "=", "Retención")],
                                    order="id asc",
                                    limit=1,
                                )
                                .id,
                                "name": impuesto["nombre"],
                                "price_unit": impuesto["total"],
                                "order_id": self.id,
                                "taxes_id": [(6, 0, [impuesto["impuesto_id"]])],
                                "price_subtotal": impuesto["total"],
                            }
                        )
                else:
                    # Elimina las líneas de impuestos si el valor es 0
                    self.order_line.filtered(
                        lambda l: l.name == impuesto["nombre"]
                    ).unlink()
            if not impuestos_valores:
                # Si no hay impuestos, muestra un mensaje
                # quitar los impuestos que esten en quitar_impuestos
                for impuesto in quitar_impuestos:
                    self.order_line.filtered(
                        lambda l: l.name == impuesto["nombre"]
                    ).unlink()
        return True

    def suma_impuesto(self, impuestos):
        # Función para sumar los valores de los impuestos
        return sum(impuesto.amount for impuesto in impuestos)

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        res.impuesto_global()
        return res
