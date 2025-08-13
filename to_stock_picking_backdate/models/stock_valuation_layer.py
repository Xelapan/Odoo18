from datetime import datetime
from psycopg2.extensions import AsIs

from odoo import models, api, fields


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    org_create_date = fields.Datetime(
        string="Origin Create Date",
        readonly=True,
        help="A technical field to store the original create date. "
        "When backdate is applied, we change the value of create_date, "
        "so this field is important to store its original value.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        now = fields.Datetime.now()
        for vals in vals_list:
            vals["org_create_date"] = now
        records = super(StockValuationLayer, self).create(vals_list)

        # force create_date and write_date with context's manual_validate_date_time
        manual_validate_date_time = self._context.get(
            "manual_validate_date_time", False
        )
        if manual_validate_date_time:
            if isinstance(manual_validate_date_time, datetime):
                manual_validate_date_time = fields.Datetime.to_string(
                    manual_validate_date_time
                )

            # We use SQL to write create_date and write_date
            # since Odoo does not allow changing those using its API
            if records.ids:
                query = """
                    UPDATE %s
                    SET create_date = %%s, write_date = %%s
                    WHERE id IN %%s
                """ % AsIs(
                    self._table
                )
                self.env.cr.execute(
                    query,
                    (
                        manual_validate_date_time,
                        manual_validate_date_time,
                        tuple(records.ids),
                    ),
                )
        return records
