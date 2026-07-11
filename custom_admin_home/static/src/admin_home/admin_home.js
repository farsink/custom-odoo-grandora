/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class CustomAdminHome extends Component {
    static template = "custom_admin_home.AdminHome";
    static props = { ...standardActionServiceProps };

    setup() {
        this.menuService = useService("menu");
    }

    get isAdmin() {
        return Boolean(user.isSystem || user.isAdmin);
    }

    get apps() {
        if (!this.isAdmin) {
            return [];
        }
        return this.menuService
            .getApps()
            .filter((app) => app.actionID && app.xmlid !== "custom_admin_home.menu_admin_home_root")
            .sort((a, b) => a.name.localeCompare(b.name));
    }

    get subtitle() {
        return _t("Choose an installed application to continue.");
    }

    async openApp(app) {
        await this.menuService.selectMenu(app);
    }
}

registry.category("actions").add("custom_admin_home.admin_home", CustomAdminHome);
