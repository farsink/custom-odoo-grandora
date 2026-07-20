# Landing Cost Entry Mode

## Scope

Let product landing cost be entered as either a fixed QAR amount or a percentage of base cost.

## Data model

- Keep `landing_cost` as the entered value.
- Add `landing_cost_type` (`fixed`/`percentage`), defaulting to `fixed` so existing records retain their QAR meaning.
- Add a stored computed effective-QAR field. It equals `landing_cost` in fixed mode, or `base_cost * landing_cost / 100` in percentage mode.
- Calculate `total_cost` and synchronize Odoo's `standard_price` from base cost plus the effective-QAR amount.
- Update downstream sales-margin computation to use the effective-QAR amount.

## Interaction

- The product form places a QAR/% selector beside Landing Cost.
- Fixed mode shows a monetary QAR input; percentage mode shows a numeric percentage input.
- Switching modes converts the entered value to preserve the total cost. A nonzero fixed amount cannot be converted to a percentage when base cost is zero; saving raises a validation error.
- Product lists display the effective QAR landing cost, not a percentage treated as currency.

## Verification

Add ORM tests covering fixed and percentage totals, standard-price synchronization, mode conversion in both directions, and the zero-base conversion rejection.
