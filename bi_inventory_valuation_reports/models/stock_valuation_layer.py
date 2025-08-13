from odoo import models, api, fields
from datetime import date
from odoo.exceptions import UserError


class ProductProductInherit(models.AbstractModel):
    _inherit = "stock.valuation.layer"

    location_id = fields.Many2one(
        "stock.location",
        "Ubicación Origen",
        index=True,
        related="stock_move_id.location_id",
        store=True,
        readonly=True,
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        "Ubicación Destino",
        index=True,
        related="stock_move_id.location_dest_id",
        store=True,
        readonly=True,
    )
    category_id = fields.Many2one(
        "product.category",
        "Categoría",
        related="product_id.categ_id",
        store=True,
        readonly=True,
    )

    @api.model
    def read_group(
        self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True
    ):
        if "unit_cost" in fields:
            fields.remove("unit_cost")

        if "product_id" in groupby and "unit_cost" not in fields:
            fields.append("product_id")

        result = super().read_group(
            domain, fields, groupby, offset, limit, orderby, lazy
        )

        if "product_id" in groupby:
            product_obj = self.env["product.product"]
            for group in result:
                product_ids = group.get("product_id")
                if product_ids:
                    # Asegúrate de que `product_ids` es un solo ID
                    # if isinstance(product_ids, list):
                    product_id = product_ids[0]
                    # else:
                    #    product_id = product_ids

                    product = product_obj.browse(product_id)

                    if len(product) == 1:
                        if product.categ_id.property_cost_method == "average":
                            total_cost = 0.0
                            total_qty = 0.0
                            layers = self.search(
                                # ('product_id', '=', product.id),
                                # ('create_date', '<=', date.today()),
                                group.get("__domain")
                            )
                            thtotal_costo = 0
                            thtotal_cantidad = 0
                            data_layer = [
                                {
                                    "unit_cost": layer.unit_cost,
                                    "quantity": layer.quantity,
                                }
                                for layer in layers
                            ]
                            for layer in layers:
                                total_cost += (
                                    layer.value
                                )  # layer.unit_cost * layer.quantity
                                total_qty += layer.quantity
                            if total_qty:
                                group["unit_cost"] = total_cost / total_qty
                                group["value"] = group["unit_cost"] * total_qty
                            else:
                                group["unit_cost"] = 0
                    else:
                        # Maneja el caso en que hay múltiples productos o ninguno
                        raise UserError(
                            "Expected singleton product, got %d records" % len(product)
                        )

        return result
