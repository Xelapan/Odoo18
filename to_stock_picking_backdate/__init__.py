from . import models
from . import wizard


def post_init_hook(env):
    env.cr.execute(
        """
    UPDATE stock_valuation_layer SET org_create_date = create_date
    """
    )
