import textwrap
from datetime import timedelta, datetime, time

from odoo import models, fields, api, _
from odoo.http import request


class StockInventoryAdjustmentWizard(models.Model):
    _name = "stock.inventory.adjustment.wizard"
    _description = "Visor de Ajustes de Inventario Consolidado"

    date_start = fields.Date(string="Fecha Inicio")
    date_end = fields.Date(string="Fecha Fin", required=True)
    ref = fields.Char(string="Referencia")
    location_id = fields.Many2one("stock.location", string="Ubicación")
    product_id = fields.Many2one("product.product", string="Producto")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    def open_inventory_adjustment(self):
        self.ensure_one()
        return self.env["stock.inventory.adjustment"].open_adjustment_inventory_report(
            datetime.combine(self.date_end, time(23, 59, 59)) + timedelta(hours=6),
            self.date_start,
            self.location_id,
            self.product_id,
            self.company_id,
            request.session.sid,
        )
        # self.env['stock.inventory.adjustment.line'].search([('session_identifier', '=', request.session.sid)])
        # return {
        #     'type': 'ir.actions.act_window',
        #     'name': 'Visor de Ajustes de Inventario Consolidado',
        #     'view_mode': 'tree,form',
        #     'res_model': 'stock.inventory.adjustment',
        #     'session_identifier': request.session.sid,
        #     'context': {'search_default_session_identifier': request.session.sid},
        #     'target': 'current',
        # }


class StockInventoryAdjustmentLineWizard(models.Model):
    _name = "stock.inventory.adjustment.line.wizard"
    _description = "Visor de Ajustes de Inventario Desglozado"

    ref = fields.Char(string="Referencia")
    location_id = fields.Many2one("stock.location", string="Ubicación")
    product_id = fields.Many2one("product.product", string="Producto")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )

    def open_table_adjustment(self):

        if (
            self.env.context.get("default_location")
            and self.env.context.get("default_ref")
            and self.env.context.get("default_company_id")
            and self.env.context.get("default_date_to")
            and self.env.context.get("default_session_identifier")
        ):
            location_id = self.env["stock.location"].browse(
                self.env.context.get("default_location")
            )
            company_id = self.env["res.company"].browse(
                self.env.context.get("default_company_id")
            )
            ref = self.env.context.get("default_ref")
            date_to = self.env.context.get("default_date_to")
            session_identifier = self.env.context.get("default_session_identifier")
        self.env["stock.inventory.adjustment.line"].search(
            [("session_identifier", "=", session_identifier)]
        ).unlink()
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
                    sml.id as stock_move_line_id, 
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
                    
                    sm.company_id = %s
                    and sml.reference = %s
            ),
            two AS (
                SELECT *
                FROM one
                WHERE location_id = %s OR location_dest_id = %s
            )
            SELECT two.*, svl.unit_cost, svl.value AS total_cost -- (two.qty_done * svl.unit_cost) AS total_cost
            FROM two
            LEFT JOIN stock_valuation_layer svl ON svl.stock_move_id = two.move_id and svl.unit_cost != 0 and svl.quantity != 0
            WHERE 
              
              two.state = 'done'
            ORDER BY two.date;
            """,
                [company_id.id, ref, location_id.id, location_id.id],
            )
        # else:
        #     # Obtener movimientos y costos
        #     self._cr.execute("""
        #     WITH one AS (
        #         SELECT
        #             sml.product_id,
        #             sml.product_uom_id,
        #             sml.owner_id,
        #             sml.package_id,
        #             sml.qty_done,
        #             sml.move_id,
        #             sml.location_id,
        #             sml.location_dest_id,
        #             sm.date,
        #             sm.origin,
        #             sml.reference,
        #             sm.state,
        #             sm.write_uid,
        #             sm.write_date,
        #             sm.picking_type_id
        #         FROM stock_move_line sml
        #         INNER JOIN stock_move sm ON sml.move_id = sm.id
        #         WHERE sm.date <= %s AND sm.company_id = %s
        #     ),
        #     two AS (
        #         SELECT *
        #         FROM one
        #     )
        #     SELECT two.*, svl.unit_cost, svl.value AS total_cost -- (two.qty_done * svl.unit_cost) AS total_cost
        #     FROM two
        #     LEFT JOIN stock_valuation_layer svl ON svl.stock_move_id = two.move_id and svl.unit_cost != 0 and svl.quantity != 0
        #     WHERE two.product_id = %s AND two.state = 'done'
        #     ORDER BY two.date;
        #     """, [
        #         date_to, company_id.id,
        #         product_id.id
        #     ])
        moves = self._cr.dictfetchall()

        report_list = []
        seen_moves = set()

        for rec in moves:
            move_id = rec["move_id"]
            if move_id in seen_moves:
                continue
            seen_moves.add(move_id)

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
                thTipoMov = "Ajuste de Inventario"

            line = {
                "stock_move_line_id": rec["stock_move_line_id"],
                "product_id": rec["product_id"],
                "product_uom_id": rec["product_uom_id"],
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
                "cost": cost,
                "total_cost": total_cost,
                "session_identifier": session_identifier,
            }
            report_list.append(line)

        self.env["stock.inventory.adjustment.line"].create(report_list)

        tree_view_id = self.env.ref(
            "stock_kardex_report.stock_inventory_adjustment_line_tree_view"
        ).id
        action = {
            "type": "ir.actions.act_window",
            "views": [(tree_view_id, "list")],
            "view_id": tree_view_id,
            "view_mode": "list",
            "name": _("Ajustes de Inventario"),
            "res_model": "stock.inventory.adjustment.line",
            "domain": [("session_identifier", "=", session_identifier)],
            "context": {"search_default_session_identifier": session_identifier},
        }
        return action
