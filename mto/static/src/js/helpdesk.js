odoo.define('mto.helpdesk', function (require) {
    'use strict';

    var core = require('web.core');
    var form_relational = require('web.form_relational');

    var _t = core._t;
    var QWeb = core.qweb;

    form_relational.FieldOne2Many.include({
        init: function () {
            this._super.apply(this, arguments);
            // Escucha el evento 'on_button_refresh' para refrescar el campo
            this.on('on_button_refresh', this, this.on_button_refresh);
        },

        on_button_refresh: function () {
            // Reemplaza 'x_ventas' con el nombre del campo one2many que deseas refrescar
            var field_name = 'x_ventas';

            // Lógica para recargar el campo one2many
            this.dataset.trigger('change', { dataPointID: this.dataPointID, changes: {} });
        },
    });
});