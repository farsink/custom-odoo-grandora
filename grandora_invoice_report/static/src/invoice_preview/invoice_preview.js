/** @odoo-module **/

import { Component, useExternalListener } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class GrandoraInvoicePreview extends Component {
    static template = "grandora_invoice_report.InvoicePreview";
    static props = { ...standardActionServiceProps };

    setup() {
        this.actionService = useService("action");
        useExternalListener(window, "message", this.closePreview.bind(this));
    }

    get reportUrl() {
        return `/report/html/grandora_invoice_report.report_invoice_inkjet_print/${this.props.action.params.invoice_id}`;
    }

    closePreview(event) {
        if (
            event.origin === window.location.origin &&
            event.data === "grandora_invoice_report.close_preview"
        ) {
            this.actionService.restore();
        }
    }
}

registry.category("actions").add(
    "grandora_invoice_report.invoice_preview",
    GrandoraInvoicePreview
);
