# -*- coding: utf-8 -*-
{
    "name": "VTS Ventas",
    "summary": """ Modulo de Ventas """,
    "description": """
        Adiciones a modulo de ventas
    """,
    "author": "Alex Martínez",
    "website": "https://odoocorporativo.xelapan.com",
    "version": "17.1",
    "category": "Sales/Sales",
    "sequence": 95,
    "depends": [
        "sales_team",
        "account_payment",  # -> account, payment, portal
        "utm",
    ],
    "data": [
        #'views/sale_order_views.xml',
    ],
    "application": False,
}
