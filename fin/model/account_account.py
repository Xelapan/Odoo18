from odoo import models, fields, api
from datetime import datetime, timedelta

from odoo.exceptions import ValidationError


class NumeracionPartidas(models.Model):
    _name = "numeracion.partidas"
    _description = "Numeracion de Partidas Contables"

    name = fields.Char(string="Nombre", required=True, compute="_compute_name")
    company_id = fields.Many2one(
        "res.company",
        string="Compañía",
        required=True,
        default=lambda self: self.env.company,
    )
    date = fields.Date(string="Fecha", required=True)
    correlativo = fields.Integer(string="Correlativo", required=True, default=1)
    move_ids = fields.One2many(
        "account.move", "partida_id", string="Asientos Contables"
    )
    cierre_apertura = fields.Boolean(
        string="Cierre/Apertura", default=False, store=True
    )

    def _compute_name(self):
        for record in self:
            meses = [
                "Ene",
                "Feb",
                "Mar",
                "Abr",
                "May",
                "Jun",
                "Jul",
                "Ago",
                "Sep",
                "Oct",
                "Nov",
                "Dic",
            ]
            record.name = "%s-%s" % (meses[record.date.month - 1], record.correlativo)

    def _check_unique_fecha(self):
        for record in self:
            existing_record = self.search(
                [
                    ("date", "=", record.date),
                    ("company_id", "=", record.company_id.id),
                    ("id", "!=", record.id),
                    ("cierre_apertura", "=", record.cierre_apertura),
                ]
            )
            if existing_record:
                return True
            else:
                return False
                # if (
                #         (len(existing_record) >= 0 or len(existing_record) <= 2)
                #         and ((record.date.month == 1 and record.date.day == 1) or (record.date.month == 12 and record.date.day == 31))
                #    ):
                #     return True
                # else:
                #     return False

    def create(self, vals_list):
        if self._check_unique_fecha():
            raise ValidationError(
                "Ya existe un registro con la misma fecha en la compañía %s."
                % self.company_id.name
            )
        return super(NumeracionPartidas, self).create(vals_list)

    # def comprobar_correlativo(self, anio, mes, company_id):
    #     first_day_of_month = datetime.strptime('%s-%s-01' % (anio, mes), '%Y-%m-%d')
    #     last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1))
    #     AuxCorrelativo = 1
    #     thPartidas = self.search([
    #         ('date', '>=', first_day_of_month),
    #         ('date', '<=', last_day_of_month),
    #         ('company_id', '=', company_id.id),
    #         ('cierre_apertura', '=', False)
    #     ], order='date ASC', limit=1)
    #     for thPartida in thPartidas:
    #         if (
    #                 (AuxCorrelativo != thPartida.correlativo)
    #                 or (thPartida.date.month == 1 and thPartida.date.day== 1 and thPartidas.move_ids[0].journal_id.name in ['Partida de Apertura'] and thPartida.correlativo != AuxCorrelativo+1)
    #                 or (thPartida.date.month ==12 and thPartida.date.day==31 and thPartidas.move_ids[0].journal_id.name in ['Partida de Cierre'] and thPartida.correlativo != AuxCorrelativo + 1)
    #         ):
    #             thPostPartidas = self.env['numeracion.partidas'].search([
    #                 ('date', '>=', thPartida.date),
    #                 ('date', '<=', last_day_of_month),
    #                 ('company_id', '=', company_id.id)
    #             ])
    #             x_AuxCorrelativo = AuxCorrelativo
    #             for thPostPartida in thPostPartidas:
    #                 thPostPartida.correlativo = x_AuxCorrelativo
    #                 x_AuxCorrelativo += 1
    #         AuxCorrelativo += 1

    def cron_calcular_partidas(self, anio):
        # Definimos el dominio para obtener los movimientos contables del año específico
        domain = [
            ("date", ">=", "%s-01-01" % anio),
            ("date", "<=", "%s-12-31" % anio),
            ("state", "=", "posted"),
            ("company_id", "=", self.env.company.id),
        ]

        # Agrupamos los movimientos por mes y luego por día usando `read_group`
        thMoves = self.env["account.move"].read_group(
            domain=domain,
            fields=["date", "company_id"],  # Solo necesitamos el campo de fecha
            groupby=["date:month", "date"],  # Agrupar por mes y luego por día
            orderby="date",
        )

        for group in thMoves:
            # Obtenemos la fecha del grupo actual
            aux_correlativo = 0

            thCurrentDia = self.env["account.move"].search(
                group["__domain"], order="date ASC"
            )

            if thCurrentDia:
                AuxDia = 0
                for thMove in thCurrentDia:
                    if (
                        thMove.journal_id.name == "Partida de Apertura"
                        and thMove.date.month == 1
                        and thMove.date.day == 1
                    ):
                        # aux_correlativo = 1
                        thPartida = None
                        AuxDia = 1
                        thPartida = self.search(
                            [
                                ("date", "=", thMove.date),
                                ("company_id", "=", thMove.company_id.id),
                                ("correlativo", "=", 1),
                                ("cierre_apertura", "=", True),
                            ],
                            limit=1,
                        )
                        if thPartida:
                            thMove.write(
                                {
                                    "partida_id": thPartida.id,
                                    "partida_contable": thPartida.name,
                                }
                            )
                            continue
                        else:
                            thNewPartida = self.create(
                                {
                                    "date": thMove.date,
                                    "correlativo": 1,
                                    "company_id": thMove.company_id.id,
                                    "cierre_apertura": True,
                                }
                            )
                            thMove.write(
                                {
                                    "partida_id": thNewPartida.id,
                                    "partida_contable": thNewPartida.name,
                                }
                            )
                            thNextPartida = None
                            thNextPartida = self.env["numeracion.partidas"].search(
                                [
                                    ("date", "=", thMove.date + timedelta(days=1)),
                                    ("company_id", "=", thMove.company_id.id),
                                    ("cierre_apertura", "=", False),
                                ]
                            )
                            if not thNextPartida:
                                thPostPartidas = self.env["numeracion.partidas"].search(
                                    [
                                        ("date", ">=", thMove.date),
                                        (
                                            "date",
                                            "<=",
                                            thMove.date.replace(
                                                month=thMove.date.month % 12 + 1, day=1
                                            ),
                                        ),
                                        ("company_id", "=", thMove.company_id.id),
                                        ("cierre_apertura", "=", False),
                                        ("id", "!=", thNewPartida.id),
                                    ]
                                )
                                for thPostPartida in thPostPartidas:
                                    thPostPartida.correlativo = (
                                        thPostPartida.correlativo + 1
                                    )
                                    thPostPartida._compute_name()
                                    for thMove in thPostPartida.move_ids:
                                        thMove.partida_contable = thPostPartida.name
                            continue
                    elif (
                        thMove.journal_id.name in "Partida de Cierre"
                        and thMove.date.month == 12
                        and thMove.date.day == 31
                    ):
                        thPartida = None
                        thPartida = self.search(
                            [
                                ("date", "=", thMove.date),
                                ("company_id", "=", thMove.company_id.id),
                                ("cierre_apertura", "=", True),
                            ],
                            limit=1,
                        )
                        if thPartida:
                            thAuxDateMove = thMove.date
                            thLastCorrelativo = (
                                self.env["numeracion.partidas"]
                                .search(
                                    [
                                        ("date", ">=", thAuxDateMove.replace(day=1)),
                                        ("date", "<=", thMove.date),
                                        ("company_id", "=", thMove.company_id.id),
                                        ("cierre_apertura", "=", False),
                                    ],
                                    order="date DESC",
                                    limit=1,
                                )
                                .correlativo
                            )
                            if thPartida.correlativo != thLastCorrelativo + 1:
                                thPartida.correlativo = thLastCorrelativo + 1
                            thMove.write(
                                {
                                    "partida_id": thPartida.id,
                                    "partida_contable": thPartida.name,
                                }
                            )
                            continue
                        else:
                            thLastCorrelativo = self.search(
                                [
                                    ("date", ">=", thMove.date.replace(day=1)),
                                    ("date", "<=", thMove.date),
                                    ("company_id", "=", thMove.company_id.id),
                                ],
                                order="date DESC",
                                limit=1,
                            ).correlativo
                            thNewPartida = self.create(
                                {
                                    "date": thMove.date,
                                    "correlativo": thLastCorrelativo + 1,
                                    "company_id": thMove.company_id.id,
                                    "cierre_apertura": True,
                                }
                            )
                            thMove.write(
                                {
                                    "partida_id": thNewPartida.id,
                                    "partida_contable": thNewPartida.name,
                                }
                            )
                            continue
                    else:
                        if AuxDia != thMove.date.day:
                            if thMove.date.month == 1 and thMove.date.day == 1:
                                aux_correlativo = 2
                            if thMove.date.month == 1 and aux_correlativo == 0:
                                aux_correlativo = 2
                            else:
                                aux_correlativo += 1

                            AuxDia = thMove.date.day
                            thPartida = None
                            thPartida = self.search(
                                [
                                    ("date", "=", thMove.date),
                                    ("company_id", "=", thMove.company_id.id),
                                    ("correlativo", "=", aux_correlativo),
                                    ("cierre_apertura", "=", False),
                                ],
                                limit=1,
                            )
                            if thPartida:
                                self.env["account.move"].search(
                                    [
                                        ("date", "=", thMove.date),
                                        ("company_id", "=", thMove.company_id.id),
                                        ("state", "=", "posted"),
                                        (
                                            "journal_id.name",
                                            "not in",
                                            [
                                                "Partida de Apertura",
                                                "Partida de Cierre",
                                            ],
                                        ),
                                    ]
                                ).write(
                                    {
                                        "partida_id": thPartida.id,
                                        "partida_contable": thPartida.name,
                                    }
                                )
                                continue
                            else:
                                thPartida = None
                                thPartida = self.search(
                                    [
                                        ("date", "=", thMove.date),
                                        ("company_id", "=", thMove.company_id.id),
                                        ("cierre_apertura", "=", False),
                                    ],
                                    limit=1,
                                )
                                if thPartida:
                                    thPartida.correlativo = aux_correlativo
                                    thPartida._compute_name()
                                    self.env["account.move"].search(
                                        [
                                            ("date", "=", thMove.date),
                                            ("company_id", "=", thMove.company_id.id),
                                            ("state", "=", "posted"),
                                        ]
                                    ).write(
                                        {
                                            "partida_id": thPartida.id,
                                            "partida_contable": thPartida.name,
                                        }
                                    )
                                else:
                                    thNewPartida = self.create(
                                        {
                                            "date": thMove.date,
                                            "correlativo": aux_correlativo,
                                            "company_id": thMove.company_id.id,
                                        }
                                    )
                                    self.env["account.move"].search(
                                        [
                                            ("date", "=", thMove.date),
                                            ("company_id", "=", thMove.company_id.id),
                                            ("state", "=", "posted"),
                                            (
                                                "journal_id.name",
                                                "not in",
                                                [
                                                    "Partida de Apertura",
                                                    "Partida de Cierre",
                                                ],
                                            ),
                                        ]
                                    ).write(
                                        {
                                            "partida_id": thNewPartida.id,
                                            "partida_contable": thNewPartida.name,
                                        }
                                    )

    # def calcular_partida(self, move_id, metodo, state):
    #     if metodo in ['create']:
    #         if state == 'draft':
    #             thMoves = self.env['account.move'].search([
    #                 ('partida_id', '=', move_id.partida_id.id),
    #                 ('state', '=', 'posted')
    #             ])
    #             if not thMoves:
    #                 self.env['numeration.partidas'].search([('id', '=', move_id.partida_id.id)]).unlink()
    #                 first_day_of_month = move_id.date.replace(day=1)
    #                 last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1))
    #                 thPostPartidas = self.env['numeracion.partidas'].search([
    #                     ('date', '>', move_id.date),
    #                     ('date', '<=', last_day_of_month),
    #                     ('company_id', '=', move_id.company_id.id)
    #                 ])
    #                 for thPartida in thPostPartidas:
    #                     thPartida.correlativo = thPartida.correlativo - 1
    #         self.comprobar_correlativo(move_id.date.year, move_id.date.month, move_id.company_id)
    #     if metodo in ['write']:
    #         if state == 'draft':
    #             thMoves = self.env['account.move'].search([
    #                 ('partida_id', '=', move_id.partida_id.id),
    #                 ('state', '=', 'posted')
    #             ])
    #             if not thMoves:
    #                 self.env['numeration.partidas'].search([('id', '=', move_id.partida_id.id)]).unlink()
    #                 first_day_of_month = move_id.date.replace(day=1)
    #                 last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1))
    #                 thPostPartidas = self.env['numeracion.partidas'].search([
    #                     ('date', '>', move_id.date),
    #                     ('date', '<=', last_day_of_month),
    #                     ('company_id', '=', move_id.company_id.id)
    #                 ])
    #                 for thPartida in thPostPartidas:
    #                     thPartida.correlativo = thPartida.correlativo - 1
    #         if state == 'posted':
    #             thPartida = self.env['numeracion.partidas'].search([
    #                 ('date', '=', move_id.date),
    #                 ('company_id', '=', move_id.company_id.id)
    #             ], limit=1)
    #             if thPartida:
    #                 move_id.partida_id = thPartida.id
    #             if not thPartida:
    #                 first_day_of_month = move_id.date.replace(day=1)
    #                 last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1))
    #                 thPrePartida = self.env['numeracion.partidas'].search([
    #                     ('date', '>', first_day_of_month),
    #                     ('date', '<', last_day_of_month),
    #                     ('company_id', '=', move_id.company_id.id)
    #                 ], order='date DESC', limit=1)
    #
    #                 thPostPartida = self.env['numeracion.partidas'].search([
    #                     ('date', '>', move_id.date),
    #                     ('date', '<=', last_day_of_month),
    #                     ('company_id', '=', move_id.company_id.id)
    #                 ], order='date DESC', limit=1)
    #
    #                 if thPostPartida:
    #                     for thPartida in thPostPartida:
    #                         thPartida.correlativo = thPartida.correlativo + 1
    #                 thPartida = self.env['numeracion.partidas'].create({
    #                     'date': move_id.date,
    #                     'correlativo': thPrePartida.correlativo + 1 if thPrePartida else 1,
    #                     'company_id': move_id.company_id.id
    #                 })
    #                 move_id.partida_id = thPartida.id
    #         self.comprobar_correlativo(move_id.date.year, move_id.date.month, move_id.company_id)
    #     if metodo in ['unlink']:
    #         thMoves = self.env['account.move'].search([
    #             ('partida_id', '=', move_id.partida_id.id),
    #             ('state', '=', 'posted')
    #         ])
    #         if not thMoves:
    #             self.env['numeration.partidas'].search([('id', '=', move_id.partida_id.id)]).unlink()
    #             first_day_of_month = move_id.date.replace(day=1)
    #             last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1))
    #             thPostPartidas = self.env['numeracion.partidas'].search([
    #                 ('date', '>', move_id.date),
    #                 ('date', '<=', last_day_of_month),
    #                 ('company_id', '=', move_id.company_id.id)
    #             ])
    #             for thPartida in thPostPartidas:
    #                 thPartida.correlativo = thPartida.correlativo - 1
    #         self.comprobar_correlativo(move_id.date.year, move_id.date.month, move_id.company_id)


class AccountMove(models.Model):
    _inherit = "account.move"

    partida_id = fields.Many2one(
        "numeracion.partidas", string="Numero Partida", store=True
    )
    partida_contable = fields.Char(string="Partida Contable", store=True)

    def _get_name_partida(self):
        for record in self:
            if record.partida_id:
                record.partida_contable = record.partida_id.name
            else:
                record.partida_contable = None

    # @api.depends('partida_id')
    # def _onchange_partida_id(self):
    #     for record in self:
    #         if record.partida_id:
    #             record.partida_contable = record.partida_id.name
    #         else:
    #             record.partida_contable = None

    # if record.date.month == 1 and record.journal_id.name != 'Partida de Apertura':
    #     record.partida_contable = '%s-%s' % (record.partida_id.name, record.correlativo_partida+1)
    # elif record.date.month == 12 and record.date.day == 31 and record.journal_id.name == 'Partida de Cierre':
    #     record.partida_contable = '%s-%s' % (record.partida_id.name, record.correlativo_partida+1)
    # else:
    #     record.partida_contable = '%s-%s' % (record.partida_id.name, record.correlativo_partida)

    def write(self, vals):
        res = super(AccountMove, self).write(vals)
        if "state" in vals or "date" in vals:
            for record in self:
                if vals.get("state") == "posted":
                    if (
                        record.journal_id.name == "Partida de Apertura"
                        and record.date.month == 1
                        and record.date.day == 1
                    ):
                        thPartidaApertura = None
                        thPartidaApertura = self.env["numeracion.partidas"].search(
                            [
                                ("date", "=", record.date),
                                ("company_id", "=", record.company_id.id),
                                ("cierre_apertura", "=", True),
                                ("correlativo", "=", 1),
                            ],
                            limit=1,
                        )
                        if thPartidaApertura:
                            record.partida_id = thPartidaApertura.id
                            record.partida_id._compute_name()
                            record._get_name_partida()
                            # record.partida_contable = thPartidaApertura.name
                        else:
                            thNewPartida = self.env["numeracion.partidas"].create(
                                {
                                    "date": record.date,
                                    "correlativo": 1,
                                    "company_id": record.company_id.id,
                                    "cierre_apertura": True,
                                }
                            )
                            record.partida_id = thNewPartida.id
                            record._get_name_partida()
                            # record.partida_contable = thNewPartida.name
                    elif (
                        record.journal_id.name == "Partida de Cierre"
                        and record.date.month == 12
                        and record.date.day == 31
                    ):
                        thPartidaCierre = None
                        thPartidaCierre = self.env["numeracion.partidas"].search(
                            [
                                ("date", "=", record.date),
                                ("company_id", "=", record.company_id.id),
                                ("cierre_apertura", "=", True),
                            ],
                            limit=1,
                        )
                        if thPartidaCierre:
                            thAuxDateMove = record.date
                            thLastCorrelativo = (
                                self.env["numeracion.partidas"]
                                .search(
                                    [
                                        ("date", ">=", thAuxDateMove.replace(day=1)),
                                        ("date", "<=", record.date),
                                        ("company_id", "=", record.company_id.id),
                                        ("cierre_apertura", "=", False),
                                    ],
                                    order="date DESC",
                                    limit=1,
                                )
                                .correlativo
                            )
                            if thPartidaCierre.correlativo != thLastCorrelativo + 1:
                                thPartidaCierre.correlativo = thLastCorrelativo + 1

                            record.partida_id = thPartidaCierre.id
                            record._get_name_partida()
                            # record.partida_contable = thPartidaCierre.name
                        else:
                            thLastCorrelativo = (
                                self.env["numeracion.partidas"]
                                .search(
                                    [
                                        ("date", ">=", record.date.replace(day=1)),
                                        ("date", "<=", record.date),
                                        ("company_id", "=", record.company_id.id),
                                    ],
                                    order="date DESC",
                                    limit=1,
                                )
                                .correlativo
                            )

                            thNewPartida = self.env["numeracion.partidas"].create(
                                {
                                    "date": record.date,
                                    "correlativo": thLastCorrelativo + 1,
                                    "company_id": record.company_id.id,
                                    "cierre_apertura": True,
                                }
                            )
                            record.partida_id = thNewPartida.id
                            record._get_name_partida()
                            # record.partida_contable = thNewPartida.name
                            # self.env.cr.commit()
                    elif (
                        record.journal_id.name != "Partida de Apertura"
                        and record.date.month == 1
                        and record.date.day == 1
                    ):
                        thPartida = None
                        thPartida = self.env["numeracion.partidas"].search(
                            [
                                ("date", "=", record.date),
                                ("company_id", "=", record.company_id.id),
                                ("cierre_apertura", "=", False),
                            ],
                            limit=1,
                        )
                        if thPartida:
                            record.partida_id = thPartida.id
                            record._get_name_partida()
                            # record.partida_contable = thPartida.name
                        else:
                            thNewPartida = self.env["numeracion.partidas"].create(
                                {
                                    "date": record.date,
                                    "correlativo": 2,
                                    "company_id": record.company_id.id,
                                }
                            )
                            record.partida_id = thNewPartida.id
                            record._get_name_partida()
                            # record.partida_contable = thNewPartida.name
                            thPosPartidas = None
                            thPosPartidas = self.env["numeracion.partidas"].search(
                                [
                                    ("date", ">", record.date),
                                    (
                                        "date",
                                        "<=",
                                        record.date.replace(
                                            month=record.date.month % 12 + 1, day=1
                                        ),
                                    ),
                                    ("company_id", "=", record.company_id.id),
                                ]
                            )
                            if thPosPartidas:
                                for thPosPartida in thPosPartidas:
                                    thPosPartida.correlativo += 1
                                    thPosPartida._compute_name()
                                    # auxname = thPosPartida.name
                                    for movi in thPosPartida.move_ids:
                                        movi._get_name_partida()
                                    #     .write({
                                    #     'partida_contable': thPosPartida.name
                                    # })
                    else:
                        thPartida = None
                        thPartida = self.env["numeracion.partidas"].search(
                            [
                                ("date", "=", record.date),
                                ("company_id", "=", record.company_id.id),
                                ("cierre_apertura", "=", False),
                            ],
                            limit=1,
                        )
                        if thPartida:
                            record.partida_id = thPartida.id
                            record._get_name_partida()
                            # record.partida_contable = thPartida.name
                        else:
                            thLastCorrelativo = (
                                self.env["numeracion.partidas"]
                                .search(
                                    [
                                        ("date", ">=", record.date.replace(day=1)),
                                        ("date", "<", record.date),
                                        ("company_id", "=", record.company_id.id),
                                    ],
                                    order="date DESC",
                                    limit=1,
                                )
                                .correlativo
                            )
                            thPosPartidas = None
                            thPosPartidas = self.env["numeracion.partidas"].search(
                                [
                                    ("date", ">", record.date),
                                    (
                                        "date",
                                        "<=",
                                        record.date.replace(
                                            month=record.date.month % 12 + 1, day=1
                                        ),
                                    ),
                                    ("company_id", "=", record.company_id.id),
                                ]
                            )
                            if thPosPartidas:
                                for thPosPartida in thPosPartidas:
                                    thPosPartida.correlativo = (
                                        thPosPartida.correlativo + 1
                                    )
                                    thPosPartida._compute_name()
                                    record._get_name_partida()
                                    thPosPartida.move_ids._get_name_partida()
                                    # thPosPartida.move_ids.write({
                                    #     'partida_contable': thPosPartida.name
                                    # })
                            thNewPartida = self.env["numeracion.partidas"].create(
                                {
                                    "date": record.date,
                                    "correlativo": thLastCorrelativo + 1,
                                    "company_id": record.company_id.id,
                                    "cierre_apertura": False,
                                }
                            )
                            record.partida_id = thNewPartida.id
                            record.partida_id._compute_name()
                            record._get_name_partida()
                            # record.partida_contable = thNewPartida.name
                elif vals.get("state") == "draft":
                    if record.partida_id:
                        if not any(
                            [x.state == "posted" for x in record.partida_id.move_ids]
                        ):
                            record.partida_id.unlink()
                            first_day_of_month = record.date.replace(day=1)
                            last_day_of_month = first_day_of_month.replace(
                                month=first_day_of_month.month % 12 + 1, day=1
                            ) - timedelta(days=1)
                            thPostPartidas = self.env["numeracion.partidas"].search(
                                [
                                    ("date", ">", record.date),
                                    ("date", "<=", last_day_of_month),
                                    ("company_id", "=", record.company_id.id),
                                ]
                            )
                            for thPartida in thPostPartidas:
                                thPartida.correlativo = thPartida.correlativo - 1
                                for thMove in thPartida.move_ids:
                                    thMove._get_name_partida()
                                    # thMove.partida_contable = thPartida.name
        return res

    def unlink(self):
        for record in self:
            if record.partida_id:
                if not any([x.state == "posted" for x in record.partida_id.move_ids]):
                    record.partida_id.unlink()
                    first_day_of_month = record.date.replace(day=1)
                    last_day_of_month = first_day_of_month.replace(
                        month=first_day_of_month.month % 12 + 1, day=1
                    ) - timedelta(days=1)
                    thPostPartidas = self.env["numeracion.partidas"].search(
                        [
                            ("date", ">", record.date),
                            ("date", "<=", last_day_of_month),
                            ("company_id", "=", record.company_id.id),
                        ]
                    )
                    for thPartida in thPostPartidas:
                        thPartida.correlativo = thPartida.correlativo - 1
                        for thMove in thPartida.move_ids:
                            thMove.partida_contable = thPartida.name
        return super(AccountMove, self).unlink()
