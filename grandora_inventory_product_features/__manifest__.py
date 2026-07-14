{
    "name": "Grandora Inventory Product Features",
    "summary": "Product references, landed cost components, lot tracking defaults, brand and item group fields.",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "author": "Grandora",
    "license": "LGPL-3",
    "depends": ["stock"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/product_brand_views.xml",
        "views/product_item_group_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "application": False,
}
