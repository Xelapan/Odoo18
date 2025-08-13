/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { ListView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

class AccountAccountVListController extends ListController {
    setup() {
        super.setup();
    }

    renderButtons() {
        super.renderButtons();

        if (this.hasButtons && this.buttonsTarget && !this.buttonsTarget.querySelector('.btn-datos-fecha')) {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-primary btn-datos-fecha';
            button.textContent = 'Datos a la Fecha';

            button.addEventListener('click', () => {
                this.actionService.doAction('fin.action_account_account_v_wizard', {
                    onClose: () => {
                        this.model.root.load(); // Recarga la vista si es necesario
                    },
                });
            });

            this.buttonsTarget.appendChild(button);
        }
    }
}

export const AccountAccountVListView = {
    ...ListView,
    Controller: AccountAccountVListController,
};

registry.category("views").add("account_account_v_list", AccountAccountVListView);
