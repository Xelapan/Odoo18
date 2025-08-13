odoo.define('mto.SaleOrder13VTreeView', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var viewRegistry = require('web.view_registry');
    var ListView = require('web.ListView');

    var SaleOrder13ListController = ListController.extend({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('.o_list_button_add_account').remove();
            }
            var self = this;
            var $button = $('<button type="button" class="btn btn-primary o_list_button_add_account">Actualizar Consolidado</button>');
            $button.on('click', function () {
                self.do_action('mto.action_sale_order_13_wizard', {
                    on_close: self.reload.bind(self, {}),
                });
            });
            this.$buttons.append($button);
        }
    });

    var SaleOrder13ListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: SaleOrder13ListController,
        }),
    });

    viewRegistry.add('SaleOrder13VTreeView', SaleOrder13ListView);
});