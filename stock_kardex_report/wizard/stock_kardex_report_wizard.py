# Copyright 2020, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from datetime import datetime, time, timedelta

from odoo import _, fields, models
import textwrap


class StockKardexReportWiz(models.TransientModel):
    _name = "stock.kardex.report.wiz"
    _description = "Wizard to create kardex report of stock moves"

    # date_from = fields.Datetime(string='Desde', required=True, default=lambda self: datetime.combine(fields.Datetime.now().date(), time.min))
    # date_to = fields.Datetime(string='Hasta', required=True, default=lambda self: datetime.combine(fields.Datetime.now().date(), time.max ))
    date_to = fields.Datetime(
        string="Hasta",
        required=True,
        default=lambda self: datetime.combine(
            fields.Date.context_today(self), time(23, 59, 59)
        ).replace(tzinfo=None),
    )
    product = fields.Many2one("product.product", required=True, string="Producto")
    location = fields.Many2one("stock.location", string="Ubicación")
    company_id = fields.Many2one(
        "res.company", string="Compañía", default=lambda self: self.env.company
    )

    def open_table(self):

        if (
            self.env.context.get("default_product")
            and self.env.context.get("default_location")
            and self.env.context.get("default_date_to")
            and self.env.context.get("default_company_id")
        ):
            # product_id = self.env.context.get('default_product')
            product_id = self.env["product.product"].browse(
                self.env.context.get("default_product")
            )
            location_id = self.env["stock.location"].browse(
                self.env.context.get("default_location")
            )
            # date_to = self.env.context.get('default_date_to')
            date_to = self.env.context.get("default_date_to")
            # date_to = (datetime.strptime(date_to, '%Y-%m-%d') + timedelta(hours=6)) if isinstance(date_to, str) else (date_to + timedelta(hours=6) if isinstance(date_to, datetime) else date_to)
            date_to = (
                (datetime.strptime(date_to, "%Y-%m-%d"))
                if isinstance(date_to, str)
                else (date_to if isinstance(date_to, datetime) else date_to)
            )
            company_id = self.env["res.company"].browse(
                self.env.context.get("default_company_id")
            )
            # self.env.context.get('default_company_id')
        else:
            product_id = self.product
            location_id = self.location
            date_to = self.date_to + timedelta(hours=6)
            company_id = self.company_id

        self.env["stock.kardex.report"].search([]).unlink()
        total = 0
        if location_id.id:
            # Obtener movimientos y costos
            self._cr.execute(
                """
            WITH one AS (
                SELECT
                    sml.product_id, 
                    sml.product_uom_id,
                    sml.owner_id, 
                    sml.package_id,
                    sml.qty_done, 
                    sml.move_id, 
                    sml.location_id,
                    sml.location_dest_id, 
                    sm.date, 
                    sm.origin,
                    sml.reference,
                    sm.state,
                    sm.write_uid,
                    sm.write_date,
                    sm.picking_type_id
                FROM stock_move_line sml
                INNER JOIN stock_move sm ON sml.move_id = sm.id
                WHERE 
                    sm.date <= %s
                    AND sm.company_id = %s
            ),
            two AS (
                SELECT *
                FROM one
                WHERE location_id = %s OR location_dest_id = %s
            )
            SELECT two.*, svl.unit_cost, svl.value AS total_cost -- (two.qty_done * svl.unit_cost) AS total_cost
            FROM two
            LEFT JOIN stock_valuation_layer svl ON svl.stock_move_id = two.move_id and svl.unit_cost != 0 and svl.quantity != 0
            WHERE two.product_id = %s AND two.state = 'done'
            ORDER BY two.date;
            """,
                [date_to, company_id.id, location_id.id, location_id.id, product_id.id],
            )
        else:
            # Obtener movimientos y costos
            self._cr.execute(
                """
            WITH one AS (
                SELECT
                    sml.product_id, 
                    sml.product_uom_id,
                    sml.owner_id, 
                    sml.package_id,
                    sml.qty_done, 
                    sml.move_id, 
                    sml.location_id,
                    sml.location_dest_id, 
                    sm.date, 
                    sm.origin,
                    sml.reference,
                    sm.state,
                    sm.write_uid,
                    sm.write_date,
                    sm.picking_type_id
                FROM stock_move_line sml
                INNER JOIN stock_move sm ON sml.move_id = sm.id
                WHERE sm.date <= %s AND sm.company_id = %s
            ),
            two AS (
                SELECT *
                FROM one
            )
            SELECT two.*, svl.unit_cost, svl.value AS total_cost -- (two.qty_done * svl.unit_cost) AS total_cost
            FROM two
            LEFT JOIN stock_valuation_layer svl ON svl.stock_move_id = two.move_id and svl.unit_cost != 0 and svl.quantity != 0
            WHERE two.product_id = %s AND two.state = 'done'
            ORDER BY two.date;
            """,
                [date_to, company_id.id, product_id.id],
            )
        moves = self._cr.dictfetchall()
        # moves = self._cr.dictfetchall()

        report_list = []
        seen_moves = set()

        for rec in moves:
            move_id = rec["move_id"]
            thMove = []
            thMove = [
                x for x in moves if x["move_id"] == move_id
            ]  # Reemplazo de .filtered()
            if len(thMove) > 1:
                for m in thMove:
                    thdone_qty = 0
                    if location_id.id:
                        if rec["location_id"] == location_id.id:
                            thdone_qty = -rec["qty_done"]
                    else:
                        if self.env["stock.location"].browse(
                            rec["location_id"]
                        ).usage in ["internal", "transit"] and self.env[
                            "stock.location"
                        ].browse(
                            rec["location_dest_id"]
                        ).usage not in [
                            "internal",
                            "transit",
                        ]:
                            thdone_qty = -rec["qty_done"]
                        if (
                            self.env["stock.picking.type"]
                            .browse(rec["picking_type_id"])
                            .code
                            == "internal"
                        ):
                            thdone_qty += 0
                        else:
                            thdone_qty += done_qty
                    m["total_cost"] = m["unit_cost"] * thdone_qty

            # if move_id in seen_moves:
            #    continue
            # seen_moves.add(move_id)

            done_qty = rec["qty_done"]
            if location_id.id:
                if rec["location_id"] == location_id.id:
                    done_qty = -rec["qty_done"]
                total += done_qty
            else:
                if self.env["stock.location"].browse(rec["location_id"]).usage in [
                    "internal",
                    "transit",
                ] and self.env["stock.location"].browse(
                    rec["location_dest_id"]
                ).usage not in [
                    "internal",
                    "transit",
                ]:
                    done_qty = -rec["qty_done"]
                if (
                    self.env["stock.picking.type"].browse(rec["picking_type_id"]).code
                    == "internal"
                ):
                    total += 0
                else:
                    total += done_qty
            origin = rec["origin"]
            if origin:
                origin = textwrap.shorten(rec["origin"], width=80, placeholder="...")

            cost = rec["unit_cost"] if rec["unit_cost"] else 0
            total_cost = rec["total_cost"] if rec["total_cost"] else 0
            thTipoMov = ""
            xTipoMov = ""
            xTipoMov = (
                self.env["stock.picking.type"].browse(rec["picking_type_id"]).code
            )
            if xTipoMov == "incoming":
                thTipoMov = "Recepción"
            elif xTipoMov == "outgoing":
                thTipoMov = "Entrega"
            elif xTipoMov == "mrp_operation":
                thTipoMov = "Fabricación"
            elif xTipoMov == "internal":
                thTipoMov = "Transferencia Interna"
            else:
                thTipoMov = "Indefinido o Ajuste de Invnetario"

            line = {
                "move_id": rec["move_id"],
                "product_id": rec["product_id"],
                "product_uom_id": rec["product_uom_id"],
                "owner_id": rec["owner_id"],
                "package_id": rec["package_id"],
                "qty_done": done_qty,
                "location_id": rec["location_id"],
                "location_dest_id": rec["location_dest_id"],
                "tipo_mov": thTipoMov,
                "date": rec["date"],
                "balance": total,
                "origin": origin,
                "reference": rec["reference"],
                "user_id": rec["write_uid"],
                "update_at": rec["write_date"],
                "picking_type_id": rec["picking_type_id"],
                "cost": cost,
                "total_cost": total_cost,
            }
            report_list.append(line)

        self.env["stock.kardex.report"].create(report_list)

        tree_view_id = self.env.ref(
            "stock_kardex_report.stock_kardex_report_tree_view"
        ).id
        action = {
            "type": "ir.actions.act_window",
            "views": [(tree_view_id, "list")],
            "view_id": tree_view_id,
            "view_mode": "list",
            "name": _("Stock Report"),
            "res_model": "stock.kardex.report",
        }
        return action
