from odoo import models, fields, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError


class AccountTaxPython(models.Model):
    _inherit = "account.tax"

    def _compute_amount(
        self,
        base_amount,
        price_unit,
        quantity=1.0,
        product=None,
        partner=None,
        fixed_multiplicator=1,
    ):
        res = super(AccountTaxPython, self)._compute_amount(
            base_amount, price_unit, quantity, product, partner, fixed_multiplicator
        )
        self.ensure_one()
        if product and product._name == "product.template":
            product = product.product_variant_id
        if self.amount_type == "code":
            company = self.env.company
            localdict = {
                "base_amount": base_amount,
                "price_unit": price_unit,
                "quantity": quantity,
                "product": product,
                "partner": partner,
                "company": company,
            }
            try:
                safe_eval(self.python_compute, localdict, mode="exec", nocopy=True)
            except Exception as e:
                raise UserError(
                    _("You entered invalid code %r in %r taxes\n\nError : %s")
                    % (self.python_compute, self.name, e)
                ) from e
            return localdict["result"]
        return super(AccountTaxPython, self)._compute_amount(
            base_amount, price_unit, quantity, product, partner, fixed_multiplicator
        )
