from odoo import fields, models, api


class StockInventoryBackdateWizard(models.TransientModel):
    _name = "stock.inventory.backdate.wizard"
    _inherit = "abstract.inventory.backdate.wizard"
    _description = "Stock Inventory Backdate Wizard"

    date = fields.Datetime(string="Inventory Date")
    accounting_date = fields.Date(
        string="Accounting Date",
        help="Leave it empty to apply the Accounting Date specified on the Inventory Adjustment"
        " document, or the Inventory Date if the Accounting Date is not specified.",
    )
    # aqui esta el fallo picking Alex 16 08 2024
    picking_id = fields.Many2one(
        "stock.picking", string="Picking", required=True, ondelete="cascade"
    )
    # inventory_id = fields.Many2one('stock.inventory', string="Inventory Adjustment", required=True, ondelete='cascade')

    @api.onchange("date")
    def _onchange_date(self):
        self.accounting_date = self.date.date()

    def process(self):
        self.ensure_one()
        accounting_date = (
            self.accounting_date or self.picking_id.accounting_date or self.date.date()
        )
        self.picking_id.write(
            {
                "date": self.date,
                "accounting_date": accounting_date,
            }
        )

        return self.picking_id.with_context(
            manual_validate_date_time=self.date
        ).button_validate()
