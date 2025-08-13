/** @odoo-module **/

import { ListController } from "@web/views/list/list_controller";
import { ListView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";

export class HrPayslipPrestacionesListController extends ListController {
    setup() {
        super.setup();
    }

    /**
     * Agrega botón después de que los botones han sido renderizados
     */
    renderButtons() {
        super.renderButtons();

        if (this.hasButtons) {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "btn btn-primary o_list_button_add_prestaciones";
            button.textContent = "Prestaciones a la Fecha";

            button.addEventListener("click", () => {
                this.actionService.doAction("nomina.action_prestaciones_wizard", {
                    onClose: () => this.model.root.load(),
                });
            });

            this.buttonsTarget.appendChild(button);
        }
    }
}

export const HrPayslipPrestacionesListView = {
    ...ListView,
    Controller: HrPayslipPrestacionesListController,
};

registry.category("views").add("hrPayslipPrestacionesTreeView", HrPayslipPrestacionesListView);
