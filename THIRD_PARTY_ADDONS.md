# Third-Party Addons

This repository vendors the following Odoo 18 Community Association (OCA) modules so the Grandora Docker transfer package can run with a single `custom-addons` mount and no client-side source checkout.

| Module | Upstream repository | Branch | Version |
|---|---|---|---|
| `partner_statement` | `https://github.com/OCA/account-financial-reporting` | `18.0` | - |
| `report_xlsx` | `https://github.com/OCA/reporting-engine` | `18.0` | - |
| `report_xlsx_helper` | `https://github.com/OCA/reporting-engine` | `18.0` | - |
| `product_lot_sequence` | `https://github.com/OCA/product-attribute` | `18.0` | - |
| `muk_web_theme` | `https://apps.odoo.com/apps/modules/18.0/muk_web_theme/` | `18.0` | 1.2.5 |
| `muk_web_appsbar` | (dependency of muk_web_theme) | `18.0` | - |
| `muk_web_chatter` | (dependency of muk_web_theme) | `18.0` | - |
| `muk_web_colors` | (dependency of muk_web_theme) | `18.0` | - |
| `muk_web_dialog` | (dependency of muk_web_theme) | `18.0` | - |

All vendored modules retain their upstream AGPL-3 license and copyright notices.

## Grandora changes

`partner_statement` contains local changes that add Contact smart buttons and browser-based Activity/Outstanding statement previews. The previews use OCA statement data and browser printing rather than wkhtmltopdf.

## Updating

A developer must manually merge the required OCA 18.0 updates into these vendored module directories, preserve Grandora changes, upgrade the modules, and verify a clean Docker restore before release. Do not have end users clone OCA repositories or edit `addons_path`.
