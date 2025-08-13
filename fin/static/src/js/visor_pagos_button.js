/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { ListView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

class AccountPaymentVListController extends ListController {
    setup() {
        super.setup();
    }

    renderButtons() {
        super.renderButtons();

        if (this.hasButtons) {
            // Evitar agregar múltiples veces el botón
            if (this.buttonsTarget.querySelector('.o_list_button_add_account')) {
                return;
            }

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-primary o_list_button_add_account';
            button.textContent = 'Pagos a la Fecha';

            button.addEventListener('click', () => {
                this.actionService.doAction('fin.action_account_payment_v_wizard', {
                    onClose: () => {
                        this.model.root.load();
                    },
                });
            });

            this.buttonsTarget.appendChild(button);
        }
    }
}

export const AccountPaymentVListView = {
    ...ListView,
    Controller: AccountPaymentVListController,
};

registry.category("views").add("AccountPaymentVTreeView", AccountPaymentVListView);
