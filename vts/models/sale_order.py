# -*- coding: utf-8 -*-
from odoo import models, fields, api

# WhatsApp
from zeep import Client
import json
import logging

logger = logging.getLogger()
import html2text

# from utilerias.log import logger
# Fin WhatsApp


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # x_ticket_ms = fields.Integer(string="Ticket", store=True)

    def EnviarMensaje(self, idchat, mensaje, urlimagen):
        try:
            json_str = (
                '{"numero": "' + idchat + '", '
                '"texto": "' + mensaje + '", '
                '"url": "' + str(urlimagen) + '"}'
            )
            data = json.loads(json_str)
            #wsdl = "http://mix.xelapan.com:55/Alertas.asmx?WSDL"
            wsdl = "http://ws.xelapan.net/Alertas.asmx?WSDL"
            client = Client(wsdl=wsdl)
            client.service.EnviarMsj(str(data))

        except Exception as x:
            print("error al consultar datos")
            logger.exception(str(x))

    def HtmlTexto(self, html):
        try:
            return str(html2text.html2text(html))
        except Exception as x:
            print("error al convertir datos")
            logger.exception(str(x))
