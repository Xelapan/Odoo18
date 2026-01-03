# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2023 SIESA
#
##############################################################################

{
    "name": "Contabilidad Finanzas Xelapan Guatemala",
    "category": "Account",
    "version": "18.0.1.1",
    "author": "Alex Martinez",
    "description": """
        Funcionalidades especificas para contabilidad en Guatemala.
    """,
    "summary": """Partidas Contables Guatemala""",
    "depends": [
        "base",
        "bolson",
        "account",
        "fel_infile_varios",
        "account_asset",
        "account_payment",
    ],
    "price": 500,
    "currency": "EUR",
    "license": "OPL-1",
    "website": "",
    "depends": [
        "base",
        "account",
        "fel_infile_varios",
        "account_asset",
        "account_payment",
        "account_accountant",
    ],
    "data": [
        #'wizard/wizard_mes_bloqueado_view.xml',
        "views/account_move_views.xml",
        'views/account_payment_views.xml',
        "security/ir.model.access.csv",
        #'data/account_mes_bloqueado_sequence.xml',
        "wizard/account_account_v_wizard.xml",
        "wizard/account_asset_v_wizard.xml",
        "wizard/account_asset_d_wizard.xml",
        "wizard/account_asset_viaceq_wizard.xml",
        "views/account_account_v_views.xml",
        "views/numeracion_partidas_views.xml",
        "views/account_asset_views.xml",
        "data/ir_cron_data.xml",
        "wizard/account_payment_v_wizard.xml",
        "wizard/account_inventory_v_wizard.xml",
        "views/account_payment_v_views.xml",
        "views/comprobante_pago.xml",
        "report/comprobante_pago_report.xml",
        "views/account_inventory_v_views.xml",
        #"views/res_partner_views.xml",
        #"views/account_move_line_list_bank_rec_widget_views.xml",
        "views/account_move_line_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            # "fin/static/src/js/visor_cuentas_contables_button.js",
            #"fin/static/src/js/visor_activos_button.js",
            #"fin/static/src/js/visor_activos_depresiacion_button.js",
            #"fin/static/src/js/visor_activos_equipo_button.js",
            #"fin/static/src/js/visor_pagos_button.js",
            #"fin/static/src/js/visor_inventario_button.js",
            # 'nomina/static/src/js/hr_payslip_prestaciones_list_view.js',
            # 'nomina/static/src/js/simple_button_list_controller.js',
            # 'nomina/static/src/js/simple_button_list_view.js',
        ],
    },
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "auto_install": False,
    "application": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
