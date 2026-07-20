/** @odoo-module **/

import { useBus } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { AppsMenu } from "@muk_web_theme/webclient/appsmenu/appsmenu";

patch(AppsMenu.prototype, {
    setup() {
        super.setup();
        let initialAction = true;
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => {
            if (initialAction) {
                initialAction = false;
                this.state.open();
            }
        });
    },
});
