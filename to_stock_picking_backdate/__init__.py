from . import models
from . import wizard


def post_init_hook(cr, registry):
    cr.execute(
        """
    UPDATE stock_valuation_layer SET org_create_date = create_date
    """
    )
