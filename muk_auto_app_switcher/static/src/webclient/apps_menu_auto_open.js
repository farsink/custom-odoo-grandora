/** @odoo-module **/

import { onMounted } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { AppsMenu } from "@muk_web_theme/webclient/appsmenu/appsmenu";

patch(AppsMenu.prototype, {
    setup() {
        super.setup();
        onMounted(() => this.state.open());
    },
});
