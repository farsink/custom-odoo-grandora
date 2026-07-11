{
    "name": "Business Inventory/Sales Starter",
    "version": "18.0.1.0.0",
    "summary": "Starter customizations for Inventory and Sales development.",
    "category": "Inventory/Sales",
    "author": "Local Development",
    "license": "LGPL-3",
    "depends": ["sale_management", "stock"],
    "data": [
        "security/ir.model.access.csv",
        "views/business_inventory_sales_views.xml",
        "views/product_template_views.xml",
    ],
    "application": True,
    "installable": True,
}
