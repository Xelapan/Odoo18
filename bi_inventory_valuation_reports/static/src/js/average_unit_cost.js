odoo.define('bi_inventory_valuation_reports.AverageUnitCost', function (require) {
    "use strict";

    var ListController = require('web.ListController');
    var core = require('web.core');
    var _t = core._t;

    ListController.include({
        _update: function () {
            console.log("ListController _update called");
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._computeAndDisplayAverage();
            });
        },
        _computeAndDisplayAverage: function () {
            console.log("Computing average...");
            var self = this;
            var $groups = this.$el.find('.o_group_header');
            console.log("Groups found:", $groups.length);

            $groups.each(function () {
                var $group = $(this);
                var dataIds = $group.data('group-data-ids');
                console.log("Data IDs:", dataIds);
                if (dataIds && dataIds.length) {
                    self._rpc({
                        model: 'stock.valuation.layer',
                        method: 'read_group',
                        domain: [['id', 'in', dataIds]],
                        fields: ['unit_cost'],
                        groupby: [],
                        lazy: false,
                    }).then(function (result) {
                        console.log("RPC Result:", result);
                        if (result.length) {
                            var total = 0;
                            var count = result.length;
                            result.forEach(function (record) {
                                total += record.unit_cost || 0;
                            });
                            var average = total / count;
                            var $averageEl = $('<span>', {
                                text: _t(' | Average Unit Cost: ') + average.toFixed(2),
                                class: 'badge badge-info ml-2',
                            });
                            $group.find('.o_group_name').append($averageEl);
                        }
                    });
                }
            });
        },
    });
});
