{
    "name": "Grandora Invoice Report",
    "version": "18.0.1.0.1",
    "summary": "Grandora commercial invoice layout and sales invoice metadata.",
    "category": "Accounting/Accounting",
    "author": "Local Development",
    "license": "LGPL-3",
    "depends": ["account", "sale_management", "stock", "web"],
    "data": [
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "report/invoice_report.xml",
        "report/grandora_sales_invoice.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "grandora_invoice_report/static/src/invoice_preview/invoice_preview.js",
            "grandora_invoice_report/static/src/invoice_preview/invoice_preview.xml",
            "grandora_invoice_report/static/src/invoice_preview/invoice_preview.scss",
        ],
    },
    "application": False,
    "installable": True,
}
