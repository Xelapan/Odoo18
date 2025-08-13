/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { ListView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

class AccountAssetViaceqListController extends ListController {
    setup() {
        super.setup();
    }

    renderButtons() {
        super.renderButtons();

        if (this.hasButtons) {
            // Evitar duplicar botón
            if (this.buttonsTarget.querySelector('.o_list_button_add_asset')) {
                return;
            }

            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-primary o_list_button_add_asset';
            button.textContent = 'Nueva Consulta';

            button.addEventListener('click', () => {
                this.actionService.doAction('fin.action_account_asset_viaceq_wizard', {
                    onClose: () => {
                        this.model.root.load();
                    },
                });
            });

            this.buttonsTarget.appendChild(button);
        }
    }
}

export const AccountAssetViaceqListView = {
    ...ListView,
    Controller: AccountAssetViaceqListController,
};

registry.category("views").add("AccountAssetViaceqTreeView", AccountAssetViaceqListView);
