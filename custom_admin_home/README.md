# custom_admin_home

Admin-only "Installed Apps" grid for the Odoo backend home screen.

## Behavior
- Replaces the default home action for system admins (`base.group_system`) via `post_init_hook` (`hooks.py`), which sets the admin home action as users' default `action_id`.
- OWL app grid in `static/src/admin_home/` (js/xml/scss), loaded through `web.assets_backend`.
- Action defined in `views/custom_admin_home_views.xml`.

No model or field changes. Depends on `web`, `base`.
