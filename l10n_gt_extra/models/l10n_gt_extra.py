# -*- encoding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


class L10nGtExtraImpuestos(models.Model):
    _name = "l10n_gt_extra.impuestos"
    _description = "Impuestos Por Factura - Guatemala"
    _rec_name = "nombre"

    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        default=lambda self: self.env.company,
        store=True,
        required=True,
    )
    nombre = fields.Char("Nombre", required=True)
    active = fields.Boolean("Activo", default=True)
    tipo = fields.Selection(
        [("compra", "Compra"), ("venta", "Venta")], string="Tipo", required=True
    )
    rangos_ids = fields.One2many(
        "l10n_gt_extra.impuestos.rangos", "impuesto_id", string="Rangos"
    )


class L10nGtExtraImpuestosRangos(models.Model):
    _name = "l10n_gt_extra.impuestos.rangos"
    _description = "Rangos de Impuestos Por Factura - Guatemala"

    # rango_inicial = fields.Float('Rango inicial')
    # rango_final = fields.Float('Rango final')
    # impuestos_ids = fields.Many2many('account.tax','impuestos_rangos_rel', string='Impuestos')
    impuesto_id = fields.Many2one(
        "l10n_gt_extra.impuestos", "Impuesto global", required=True
    )
    impuesto_calculo = fields.Many2one("account.tax", "Impuesto", required=True)
    python_compute = fields.Text(
        string="Calculo Python",
        help="Código Python para calcular el monto del impuesto. El resultado debe almacenarse en result. La variable amount_untaxed y partner_id están disponibles como parámetros para los cálculos.",
    )

    def evaluar_formula_python(self, amount_untaxed, position):
        result = 0.0  # Valor por defecto en caso de error
        context = {
            "amount_untaxed": amount_untaxed,
            "position": position,
            "result": result,
        }

        # Evalúa el código Python almacenado en python_compute
        try:
            exec(self.python_compute, {}, context)
            result = context["result"]
        except Exception as e:
            _logger.error(f"Error al evaluar el código Python: {e}")
        return result
