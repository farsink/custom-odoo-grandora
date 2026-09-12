# Grandora Partner Type

Adds explicit customer and vendor flags to Contacts in Odoo 18 Community. A partner can be both.

## Features

- Customer and vendor checkboxes in the **Sales & Purchase** tab.
- Labeled native Customer and Vendor toggles in the partner form header.
- Optional Customer and Vendor columns in the Contacts list, plus search filters.
- Contacts ▸ Customers and Contacts ▸ Vendors menus, each with a matching domain and defaults for new contacts.
- One-way synchronization to Odoo's native partner ranks, so ticking a flag includes the partner in Odoo's standard Sales/Purchase customer or vendor flows.

## Fields

| Model | Field | Type | Stored | Consumers |
|---|---|---|---|---|
| `res.partner` | `is_customer` | Boolean | Yes | Partner form/list/search and Contacts ▸ Customers; syncs `customer_rank` to at least 1 when ticked. |
| `res.partner` | `is_vendor` | Boolean | Yes | Partner form/list/search and Contacts ▸ Vendors; syncs `supplier_rank` to at least 1 when ticked. |

Unticking a flag does not reduce the matching rank: Odoo uses ranks as historical counters and other modules may update them.

## Cross-addon links

- Depends on Odoo's `contacts`, `sale_management`, and `purchase` modules.
- Does not depend on, or expose fields for, another custom addon.

## Downstream dependents

None.

## Verification

```bash
./odoo/venv/bin/python -m py_compile custom-addons/grandora_partner_type/models/res_partner.py
./odoo/venv/bin/python -c "import lxml.etree as ET; ET.parse('custom-addons/grandora_partner_type/views/res_partner_views.xml')"
./odoo/venv/bin/python ./odoo/odoo-bin -c ./odoo.conf -d odoo18_dev -i grandora_partner_type --stop-after-init
```
