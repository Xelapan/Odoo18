# -*- coding: utf-8 -*-
{
    "name": "GTH Reclutamiento",
    "summary": """ Reclutamiento GTH """,
    "description": """
        Adiciones a modulo empleados
    """,
    "author": "Edvin Canastuj",
    "website": "",
    "version": "17.1",
    "category": "Human Resources/Employees",
    "sequence": 95,
    "depends": [
        "web",
        "hr",
        "base",
        "website_partner",
        "website_mail",
        #'website_hr_recruitment',
        'hr_recruitment',
        "hr_payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_job_inherit_form.xml",
        "views/website_hr_recruitment_inner_apply.xml",
    ],
    "application": False,
}
