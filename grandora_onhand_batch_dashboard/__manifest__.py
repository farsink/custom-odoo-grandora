{
    "name": "Grandora On-hand Batch Cost Dashboard",
    "version": "18.0.1.0.0",
    "summary": "Batch-level on-hand stock, expiry, cost, sale price, and margin reporting.",
    "category": "Inventory/Inventory",
    "author": "Grandora",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "stock_account",
        "account",
        "sale_management",
        "product_expiry",
        "grandora_inventory_product_features",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/onhand_batch_dashboard_views.xml",
    ],
    "application": False,
    "installable": True,
}
