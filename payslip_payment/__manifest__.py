# -*- coding: utf-8 -*-
{
    "name": "Payslip Payment",
    "version": "18.0",
    "category": "HR",
    "currency": "EUR",
    "license": "AGPL-3",
    "website": "https://www.inteslar.com",
    "images": ["static/images/main_screenshot.png"],
    "author": "Alex Martínez",
    "summary": "Pago de Nóminas",
    "description": """
Key Features
------------
* Batchwise Payslips Register Payment
        """,
    "depends": [
        "base",
        "hr",
        "account",
        "hr_payroll_account",
        "hr_payroll",
        "account_payment",
    ],
    "data": [
        "wizard/hr_payroll_register_payment.xml",
        "wizard/hr_payroll_batchwise_register_payment.xml",
        "views/hr_payslip_views.xml",
        # "views/salary_voucher_report.xml",
        "security/ir.model.access.csv",
        "views/account_payment_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
