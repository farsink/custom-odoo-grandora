{
    "name": "Grandora Invoice Report",
    "version": "18.0.1.0.0",
    "summary": "Grandora commercial invoice layout and sales invoice metadata.",
    "category": "Accounting/Accounting",
    "author": "Local Development",
    "license": "LGPL-3",
    "depends": ["account", "sale_management", "stock"],
    "data": [
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "report/invoice_report.xml",
        "report/grandora_sales_invoice.xml",
    ],
    "application": False,
    "installable": True,
}
