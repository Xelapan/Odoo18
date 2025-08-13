# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):

    _inherit = "account.move.reversal"

    def _prepare_default_reversal(self, move):
        """Set the default document type and number in the new revsersal move taking into account the ones selected in
        the wizard"""
        res = super()._prepare_default_reversal(move)
        res.update(
            {
                "factura_original_id": move.id,
            }
        )
        return res
