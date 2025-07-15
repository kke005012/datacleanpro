# pricing.py

FREE_ROW_ALLOWANCE = 100

PRICING_TIERS = [
    (500, 0.02),     # $0.02 per row up to 500 rows
    (1500, 0.015),   # $0.015 per row from 501 to 1500
    (10000, 0.01),  # $0.01 per row from 1501 to 10,000
    (25000, 0.008),  # $0.008 per row from 10,001 to 25,000
    (100000, 0.007),  # $0.007 per row from 25,001 to 100,000
    (float('inf'), 'custom')  # Beyond this, ask user to contact
]


def calculate_price(row_count):
    if row_count <= FREE_ROW_ALLOWANCE:
        return 0.0, row_count, 0  # Free tier

    remaining_rows = row_count - FREE_ROW_ALLOWANCE
    total_cost = 0.0
    tier_base = FREE_ROW_ALLOWANCE

    for max_rows, price_per_row in PRICING_TIERS:
        if remaining_rows <= 0:
            break

        rows_in_tier = min(remaining_rows, max_rows - tier_base)
        if price_per_row == 'custom':
            return 'custom', row_count, remaining_rows
        tier_cost = (rows_in_tier / 1000) * price_per_row
        total_cost += tier_cost
        remaining_rows -= rows_in_tier
        tier_base = max_rows

    return round(total_cost, 2), row_count, row_count - FREE_ROW_ALLOWANCE
