# -*- coding: utf-8 -*-
{
    "name": "GTH Empleados",
    "summary": """ Empleados GTH """,
    "description": """
        Adiciones a modulo empleados
    """,
    "author": "Alex Martínez",
    "website": "https://odoocorporativo.xelapan.com",
    "version": "17.1",
    "category": "Human Resources/Employees",
    "sequence": 95,
    "depends": [
        "hr",
        "base_setup",
        "mail",
        "resource",
        "web",
        "hr_contract",
        "hr_payroll",
        "hr_payroll_holidays",
        "hr_holidays"
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_views.xml",
        "views/hr_contract_views_inherit.xml",
        "views/hr_employee_work_history.xml",
        "security/security.xml",
        # "security/hr_request_employee_security.xml",
        # "views/wizard_motivo_rechazo.xml",
        # "data/experiencia_data.xml",
        # "views/hr_request_employee_view.xml",
        "data/departamento_data.xml",
        "data/municipio_data.xml",
    ],
    "application": False,
}
