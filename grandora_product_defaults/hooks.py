def _post_init_hook(env):
    """Create and configure the default Grandora F&B product category."""
    category = env.ref("grandora_product_defaults.product_category_grandora_food", raise_if_not_found=False)
    all_category = env.ref("product.product_category_all", raise_if_not_found=False)
    fefo = env.ref("product_expiry.removal_fefo", raise_if_not_found=False)

    if not category:
        category = env["product.category"].sudo().create({
            "name": "Grandora F&B / FIFO / FEFO",
            "parent_id": all_category.id if all_category else False,
            "grandora_sku_prefix": "PRD",
        })
        env["ir.model.data"].sudo().create({
            "module": "grandora_product_defaults",
            "name": "product_category_grandora_food",
            "model": "product.category",
            "res_id": category.id,
            "noupdate": True,
        })

    values = {
        "grandora_sku_prefix": category.grandora_sku_prefix or "PRD",
        "property_cost_method": "fifo",
        "property_valuation": "real_time",
    }
    if all_category:
        for field_name in (
            "property_stock_account_input_categ_id",
            "property_stock_account_output_categ_id",
            "property_stock_valuation_account_id",
            "property_stock_journal",
        ):
            account_or_journal = all_category[field_name]
            if account_or_journal:
                values[field_name] = account_or_journal.id
    if fefo:
        values["removal_strategy_id"] = fefo.id
    category.sudo().write(values)
    category._grandora_ensure_product_sequence()

    # Make the main stock location prefer FEFO too, so sales/delivery reservations
    # can use expiry dates even when a product category is later changed.
    for warehouse in env["stock.warehouse"].search([]):
        if fefo and warehouse.lot_stock_id:
            warehouse.lot_stock_id.removal_strategy_id = fefo.id
