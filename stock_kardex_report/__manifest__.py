# Copyright 2020, Jarsa Sistemas, S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lpgl.html).

{
    "name": "Stock Kardex Report",
    "summary": "Generate Kardex Report",
    "version": "18.0.1.0.0",
    "category": "Reports",
    "author": "Alex Martinez",
    "website": "https://www.linkedin.com/in/baterodedios",
    "license": "LGPL-3",
    "depends": [
        "stock",
    ],
    "data": [
        "views/stock_kardex_report_views.xml",
        "views/stock_inventory_at_date_views.xml",
        "wizard/stock_kardex_report_wizard_view.xml",
        "wizard/inventory_at_date_wizard.xml",
        "security/ir.model.access.csv",
        "views/stock_move_views.xml",
        "views/stock_inventory_adjustment_views.xml",
        "wizard/stock_inventory_adjustment_wizard.xml",
    ],
}
