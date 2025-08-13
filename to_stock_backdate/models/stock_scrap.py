from odoo import models, fields


class StockScrap(models.Model):
    _inherit = "stock.scrap"

    date_expected = fields.Datetime(string="Expected Date", default=fields.Datetime.now)

    def do_scrap(self):
        res = super(StockScrap, self).do_scrap()
        manual_validate_date_time = self._context.get("manual_validate_date_time")
        if manual_validate_date_time:
            self.write({"date_done": manual_validate_date_time})
        return res

    def action_validate(self):
        self.ensure_one()
        manual_validate_date_time = self._context.get("manual_validate_date_time")
        if not manual_validate_date_time and self.env.user.has_group(
            "to_backdate.group_backdate"
        ):
            view = self.env.ref(
                "to_stock_backdate.stock_scrap_backdate_wizard_form_view"
            )
            ctx = dict(self._context or {})
            ctx.update({"default_scrap_id": self.id})
            return {
                "type": "ir.actions.act_window",
                "view_mode": "form",
                "res_model": "stock.scrap.backdate.wizard",
                "views": [(view.id, "form")],
                "view_id": view.id,
                "target": "new",
                "context": ctx,
            }
        res = super(StockScrap, self).action_validate()
        if isinstance(res, dict):
            if "context" not in res:
                res["context"] = {}
            res["context"]["default_scrap_backdate"] = manual_validate_date_time
        return res
