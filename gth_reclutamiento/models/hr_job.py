from odoo import models, fields, api
from odoo.tools.translate import html_translate


class Job(models.Model):
    _inherit = "hr.job"

    competencia_puesto = fields.One2many(
        "hr.job.competencia.puesto", "puesto_id", string="Competencias", store=True
    )
    factor_puesto = fields.One2many(
        "hr.job.factor.puesto", "job_id", string="Factores", store=True
    )
    codigo = fields.Text(string="Código", store=True)
    version = fields.Float(string="Versión", store=True)
    fecha_emision = fields.Date(string="Fecha de Emisión", store=True)
    requisitos = fields.Text(string="Requisitos")
    ofrecimientos = fields.Text(string="Ofrecimientos")
    funciones_especificas = fields.Html(string="Funciones Especificas")
    funcion_principal = fields.Text(string="Función Principal")
    responsabilidades = fields.Html(string="Responsabilidades")
    rango_minimo = fields.Integer(string="Mínimo", store=True)
    rango_maximo = fields.Integer(string="Máximo", store=True)
    rango_actual = fields.Integer(
        string="Actual", store=True, compute="_compute_rango_actual"
    )
    puesto_reporta = fields.Many2one("hr.job", string="Puesto que reporta", store=True)
    # puestos_supervisa = fields.One2many('hr.job.supervisa', 'x_job_id', string="Puestos que supervisa", store=True)
    # funcion_principal = fields.Text(string="Función principal", store=True)
    # funciones_especificas = fields.One2many('x_funciones', 'x_rel', string="Funciones específicas", store=True)
    # responsabilidades = fields.One2many('x_respon', 'x_par', string="Responsabilidades", store=True)
    # comunicacion_interna = fields.One2many('x_interna', 'x_inter', string="Comunicación interna", store=True)
    # comunicacion_externa = fields.One2many('x_comunicacion', 'x_exter', string="Comunicación externa", store=True)

    @api.depends(
        "funcion_principal", "funciones_especificas", "requisitos", "ofrecimientos"
    )
    @api.onchange(
        "funcion_principal", "funciones_especificas", "requisitos", "ofrecimientos"
    )
    def _compute_website_description(self):
        for record in self:
            # Define el contenido HTML
            html_content = f"""
                    <section class="mb32">
                        <div class="container">
                            <h2 style="font-weight: bold;">Función Principal:</h2>
                            <p class="mt0 lead">{record.funcion_principal}</p>
                        </div>
                    </section>
                    <section class="mb32">
                        <div class="container">
                            <h3 style="font-weight: bold;">Funciones Específicas:</h3>
                            {record.funciones_especificas}
                """
            if record.ofrecimientos:
                ofrecimientos_con_br = record.ofrecimientos.replace("\n", "<br>")
                html_content += f"""
                    <section class="mb32">
                        <div class="container">
                            <h3 style="font-weight: bold;">Ofrecemos:</h3>
                            <p class="lead mt0">{ofrecimientos_con_br}</p>
                        </div>
                    </section>
                    """
            if record.requisitos:
                ofrecimientos_con_br = record.requisitos.replace("\n", "<br>")
                html_content += f"""
                    <section class="mb32">
                        <div class="container">
                            <h3 style="font-weight: bold;">Requisitos:</h3>
                            <p class="lead mt0">{ofrecimientos_con_br}</p>
                        </div>
                    </section>
                    """
            # # Edvin 28 12 2023 Aqui estoy trabajando en agregar la lógica para publicar en
            tiene_factores_publicables = any(
                linea.publicar_en_web for linea in record.factor_puesto
            )

            # # Verifica si hay factores publicables antes de generar el contenido
            if tiene_factores_publicables:
                html_content += f"""
                    <section class="mb32">
                        <div class="container">
                            <h3 style="font-weight: bold;">Factores:</h3>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Factor</th>
                                        <th>Descripción</th>
                                    </tr>
                                </thead>
                                <tbody>
                                """
                for linea in record.factor_puesto:
                    factor = linea.factor_id
                    description = linea.factor_descripcion
                    if linea.publicar_en_web:
                        html_content += f"""
                                    <tr>
                                        <td>{factor.name}</td>
                                        <td>{description.name}</td>
                                    </tr>
                                """
                html_content += f"""
                                        </tbody>
                                </table>
                            </div>
                        </section>
                    """
            tiene_competencias_publicables = any(
                comp.publicar_web for comp in record.competencia_puesto
            )
            # # Verifica si hay factores publicables antes de generar el contenido
            if tiene_competencias_publicables:
                html_content += f"""
                                <section class="mb32">
                                    <div class="container">
                                        <h3 style="font-weight: bold;">Competencias:</h3>
                                        <table>
                                            <thead>
                                                <tr>
                                                    <th>Competencia</th>
                                                    <th>Descripción</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                            """
                for comp in record.competencia_puesto:
                    competencias = comp.competencia_id
                    description_c = comp.competencia_descripcion
                    if comp.publicar_web:
                        html_content += f"""
                                                <tr>
                                                    <td>{competencias.name}</td>
                                                    <td>{description_c.name}</td>
                                                </tr>
                                            """
                html_content += f"""
                                                    </tbody>
                                            </table>
                                        </div>
                                    </section>
                                """
            # Asigna el HTML resultante al campo website_description
            record.website_description = html_content

    website_description = fields.Html(
        "Website description",
        translate=html_translate,
        sanitize_attributes=False,
        compute=_compute_website_description,
        store=True,
    )

    @api.depends("factor_puesto", "competencia_puesto")
    def _compute_rango_actual(self):
        for record in self:
            record.rango_actual = 0
            for factor in record.factor_puesto:
                record.rango_actual += factor.punteo
            for competencia in record.competencia_puesto:
                record.rango_actual += competencia.punteo @ api.onchange(
                    "factor_puesto", "competencia_puesto"
                )

    def _compute_rango_actual(self):
        for record in self:
            record.rango_actual = 0
            for factor in record.factor_puesto:
                record.rango_actual += factor.punteo
            for competencia in record.competencia_puesto:
                record.rango_actual += competencia.punteo

    def copy(self, default=None):
        # Llamar al método copy original para duplicar el registro principal
        default = dict(default or {})
        default["competencia_puesto"] = []
        default["factor_puesto"] = []

        # Crear una copia del registro original
        nuevo_puesto = super(Job, self).copy(default)

        # Duplicar las competencias asociadas
        for competencia in self.competencia_puesto:
            competencia.copy({"puesto_id": nuevo_puesto.id})

        # Duplicar los factores asociados
        for factor in self.factor_puesto:
            factor.copy({"job_id": nuevo_puesto.id})

        return nuevo_puesto
