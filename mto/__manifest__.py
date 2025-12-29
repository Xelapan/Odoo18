# -*- coding: utf-8 -*-
{
    "name": "mto helpdesk",
    "summary": """ Mesa de Ayuda Mantenimiento """,
    "description": """
        Adiciones a mesa de ayuda
    """,
    "author": "Alex Martínez",
    "website": "https://odoocorporativo.xelapan.com",
    "version": "18.1",
    "category": "Services/Helpdesk",
    "sequence": 110,
    "depends": ["helpdesk", "mrp", "sale", "stock"],
    "data": [
        "security/security.xml",
        "views/helpdesk_ticket_views.xml",
        "views/project_views.xml",
        #"security/ir.model.access.csv",
        #'views/mrp_production_views.xml',
        #'views/project_views.xml',
        "views/sale_order_views.xml",
        #'views/datos_odoo_13_views.xml',
        #'wizard/datos_odoo_13_wizard.xml',
        "data/ir_cron_data.xml",
    ],
    # 'web.assets_frontend': [
    #         'mto/static/src/js/helpdesk.js',
    # ],
    # 'assets': {
    #             'web.assets_backend': [
    #                 'mto/static/src/js/botton_consolidado_tickets.js',
    #             ],
    #         },
    "application": False,
}
