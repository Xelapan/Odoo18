from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = "account.move"

    # editar mettodo create
    @api.model
    def create(self, vals):
        res = super(AccountMove, self).create(vals)
        svl = self.env["stock.valuation.layer"].search(
            [("account_move_id", "=", res.id)]
        )
        if svl:
            for svline in svl:
                thStock = svline.stock_move_id
                if any(sml.analytic_account_id for sml in thStock.move_line_ids):
                    for sml in thStock.move_line_ids:
                        thProducto = res.line_ids.filtered(
                            lambda l: l.product_id.id == sml.product_id.id
                            and (
                                l.quantity == sml.qty_done
                                or (l.quantity * -1) == sml.qty_done
                            )
                        )
                        if thProducto:
                            thAnalityc_Account = {sml.analytic_account_id.id: 100}
                            thProducto.write(
                                {"analytic_distribution": thAnalityc_Account}
                            )
        return res

    # def _get_unbalanced_moves(self, container):
    #     moves = container['records'].filtered(lambda move: move.line_ids)
    #     if not moves:
    #         return
    #
    #     # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
    #     # are already done. Then, this query MUST NOT depend on computed stored fields.
    #     # It happens as the ORM calls create() with the 'no_recompute' statement.
    #     self.env['account.move.line'].flush_model(['debit', 'credit', 'balance', 'currency_id', 'move_id'])
    #     self._cr.execute('''
    #         SELECT line.move_id,
    #                ROUND(SUM(line.debit), currency.decimal_places) debit,
    #                ROUND(SUM(line.credit), currency.decimal_places) credit
    #           FROM account_move_line line
    #           JOIN account_move move ON move.id = line.move_id
    #           JOIN res_company company ON company.id = move.company_id
    #           JOIN res_currency currency ON currency.id = company.currency_id
    #          WHERE line.move_id IN %s
    #       GROUP BY line.move_id, currency.decimal_places
    #         HAVING ROUND(SUM(line.balance), currency.decimal_places) != 0
    #     ''', [tuple(moves.ids)])
    #     auxa = self._cr.fetchall()
    #     return self._cr.fetchall()


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    @api.model
    def create(self, vals_list):
        res = super(StockValuationLayer, self).create(vals_list)
        if "stock_move_id" in vals_list:
            tStock = vals_list["stock_move_id"]
            # tMove = vals_list['account_move_id']
            thStock = self.env["stock.move"].search([("id", "=", tStock)])
            thMove = self.env["account.move"].search(
                [("id", "=", res.account_move_id.id)]
            )
            # REvisar si algun stock.move.line tiene cuenta analitica
            if any(sml.analytic_account_id for sml in thStock.move_line_ids):
                for sml in thStock.move_line_ids:
                    thProducto = thMove.line_ids.filtered(
                        lambda l: l.product_id.id == sml.product_id.id
                        and (
                            l.quantity == sml.qty_done
                            or (l.quantity * -1) == sml.qty_done
                        )
                    )
                    if thProducto:
                        thAnalityc_Account = {sml.analytic_account_id.id: 100}
                        thProducto.write({"analytic_distribution": thAnalityc_Account})

        return res
