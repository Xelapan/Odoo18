# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import timedelta

from odoo import api, Command, fields, models, _, SUPERUSER_ID


class HrEmployeeTicket(models.Model):
    _name = "hr.employee.ticket"
    _description = "Employee Ticket"

    name = fields.Char(string="Empleado", store=True, required=True)
    employee_id = fields.Integer(string="Employee Database ID")
    company_name = fields.Char(string="Compañia")
    company_id = fields.Integer(string="Company ID")
    department_name = fields.Char(string="Departamento")
    department_id = fields.Integer(string="Department ID")
    job_title = fields.Char(string="Puesto")
    job_id = fields.Integer(string="Job ID")
    team_name = fields.Char(string="Equipo", related="team_id.name")
    team_id = fields.Many2many("helpdesk.team", string="Equipos de Mesa de Ayuda")
    work_contact_id = fields.Integer(string="Contacto", store=True)
    phone = fields.Char(string="Celular", store=True)
    mobile_phone = fields.Char(string="Celular Trabajo", store=True)
    active = fields.Boolean(string="Active", default=True)
    registration_number = fields.Char(
        string="Registration Number", store=True, readonly=True, index=True
    )
    identification_id = fields.Char(
        string="Identification Number", store=True, readonly=True, index=True
    )
    user_id = fields.Many2one("res.users", string="Usuario", store=True)
    hr_parent_id = fields.Integer(string="HrParent ID", store=True)
    parent_id = fields.Many2one("hr.employee.ticket", string="Parent ID", store=True)
    work_email = fields.Char(string="Correo Electrónico", store=True)
    # @api.onchange('hr_parent_id')
    # def compute_parent_id(self):
    #     for record in self:
    #         if record.hr_parent_id:
    #             thParent = self.env['hr.employee.ticket'].search([('employee_id', '=', record.hr_parent_id)], limit=1)
    #             if thParent:
    #                 record.parent_id = thParent


class HelpdeskTeam(models.Model):
    _inherit = "helpdesk.team"
    employee_ids = fields.Many2many("hr.employee.ticket", string="Employees")

    def synchronize_employee_tickets(self):
        # Obtener todos los empleados que tengan menos de 15 dias de ser creados o actualizados
        employees = (
            self.env["hr.employee"]
            .sudo()
            .search([("write_date", ">=", fields.Datetime.now() - timedelta(days=800))])
        )

        # Para cada empleado, buscar si existe un ticket asociado
        for employee in employees:
            emp = self.env["hr.employee.ticket"].search(
                [("employee_id", "=", employee.id)]
            )

            # Si no existe un ticket, crearlo
            if not emp:
                emp = self.env["hr.employee.ticket"].create(
                    {
                        "name": employee.name,
                        "employee_id": employee.id,
                        "company_name": employee.company_id.name,
                        "company_id": employee.company_id.id,
                        "department_name": employee.department_id.name,
                        "department_id": employee.department_id.id,
                        "job_title": employee.job_id.name,
                        "job_id": employee.job_id.id,
                        "active": employee.active,
                        "work_contact_id": employee.work_contact_id.id,
                        "phone": employee.mobile_phone,
                        "mobile_phone": employee.mobile_phone,
                        "registration_number": employee.registration_number,
                        "identification_id": employee.identification_id,
                        "user_id": employee.user_id.id,
                        "hr_parent_id": employee.parent_id.id,
                        "work_email": employee.work_email,
                    }
                )
            # Si existe, actualizar los campos si han cambiado
            else:
                emp.write(
                    {
                        "name": employee.name,
                        "employee_id": employee.id,
                        "company_name": employee.company_id.name,
                        "company_id": employee.company_id.id,
                        "department_name": employee.department_id.name,
                        "department_id": employee.department_id.id,
                        "job_title": employee.job_id.name,
                        "job_id": employee.job_id.id,
                        "active": employee.active,
                        "work_contact_id": employee.work_contact_id,
                        "phone": employee.mobile_phone,
                        "mobile_phone": employee.mobile_phone,
                        "registration_number": employee.registration_number,
                        "identification_id": employee.identification_id,
                        "user_id": employee.user_id.id,
                        "hr_parent_id": employee.parent_id.id,
                        "work_email": employee.work_email,
                    }
                )

                # Query sql para traer la infroamcion del empleado, empresa, departamento y puesto con inner join y todo lo necesario
                # query = """
                #     SELECT
                #         hr_employee.name,
                #         hr_employee.company_id,
                #         hr_employee.active,
                #         res_company.name as company_name,
                #         hr_department.name as department_name,
                #         hr_job.name as job_title,
                #         hr_employee.address_home_id,
                #         res_partner.phone,
                #         hr_employee.mobile_phone,
                #         hr_employee.registration_number,
                #         hr_employee.identification_id,
                #         res_partner.id as address_home_id
                #
                #     FROM hr_employee
                #     INNER JOIN res_company ON hr_employee.company_id = res_company.id
                #     INNER JOIN hr_department ON hr_employee.department_id = hr_department.id
                #     INNER JOIN hr_job ON hr_employee.job_id = hr_job.id
                #     left join res_partner on hr_employee.address_home_id = res_partner.id
                #     WHERE hr_employee.id = %s
                # """
                # if query:
                #     self.env.cr.execute(query, (employee.id,))
                #     employee_data = self.env.cr.dictfetchall()
                #     if employee_data:
                #         emp.write({
                #             'name': employee_data[0]['name'],
                #             'company_name': employee_data[0]['company_name'],
                #             'company_id': employee,
                #             'department_name': employee_data[0]['department_name'],
                #             'department_id': employee,
                #             'job_title': employee_data[0]['job_title'],
                #             'job_id': employee,
                #             'active': employee_data[0]['active'],
                #             'address_home_id': employee_data[0]['address_home_id'],
                #             'phone': employee_data[0]['phone'],
                #             'mobile_phone': employee_data[0]['mobile_phone'],
                #             'registration_number': employee_data[0]['registration_number'],
                #             'identification_id': employee_data[0]['identification_id'],
                #         })

    unassigned_tickets = fields.Integer(
        string="Unassigned Tickets", compute="_compute_unassigned_tickets_new"
    )

    def _compute_unassigned_tickets_new(self):
        ticket_data = self.env["helpdesk.ticket"].read_group(
            [
                ("x_asignado", "=", False),
                ("team_id", "in", self.ids),
                ("stage_id.fold", "=", False),
            ],
            ["team_id"],
            ["team_id"],
        )
        mapped_data = dict(
            (data["team_id"][0], data["team_id_count"]) for data in ticket_data
        )
        for team in self:
            team.unassigned_tickets = mapped_data.get(team.id, 0)
