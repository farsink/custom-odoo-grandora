{
    "name": "MuK Auto App Switcher",
    "summary": "Open the MuK app switcher when the backend loads.",
    "version": "18.0.1.0.0",
    "category": "Tools/UI",
    "author": "Local Development",
    "license": "LGPL-3",
    "depends": ["muk_web_theme"],
    "assets": {
        "web.assets_backend": [
            (
                "after",
                "muk_web_theme/static/src/webclient/appsmenu/appsmenu.js",
                "muk_auto_app_switcher/static/src/webclient/apps_menu_auto_open.js",
            ),
        ],
    },
    "application": False,
    "installable": True,
}
