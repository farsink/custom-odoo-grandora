{
    "name": "Custom Admin Home",
    "version": "18.0.1.0.0",
    "summary": "Admin-only installed apps grid for the Odoo backend home screen.",
    "category": "Administration",
    "author": "Local Development",
    "license": "LGPL-3",
    "depends": ["web", "base"],
    "data": [
        "views/custom_admin_home_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "custom_admin_home/static/src/admin_home/admin_home.js",
            "custom_admin_home/static/src/admin_home/admin_home.xml",
            "custom_admin_home/static/src/admin_home/admin_home.scss",
        ],
    },
    "application": True,
    "installable": True,
    "post_init_hook": "_post_init_hook",
}
