{
    "name": "Grandora Product Defaults",
    "summary": "Default F&B product configuration, SKU sequencing, and purchase receipt batch generation",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "author": "Grandora",
    "license": "LGPL-3",
    "depends": ["purchase_stock", "stock_account", "product_expiry"],
    "data": [
        "data/ir_sequence_data.xml",
        "views/product_category_views.xml",
        "views/product_template_views.xml",
        "views/stock_lot_views.xml",
        "views/stock_move_line_views.xml",
    ],
    "post_init_hook": "_post_init_hook",
    "installable": True,
    "application": False,
}
