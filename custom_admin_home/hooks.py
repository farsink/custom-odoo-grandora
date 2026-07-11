def _post_init_hook(env):
    """Set the custom admin home as the default home action for system admins."""
    action = env.ref("custom_admin_home.action_admin_home", raise_if_not_found=False)
    group = env.ref("base.group_system", raise_if_not_found=False)
    if not action or not group:
        return
    group.users.filtered(lambda user: user.active and not user.share).sudo().write({"action_id": action.id})
