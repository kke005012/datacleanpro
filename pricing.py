FREE_ROW_ALLOWANCE = 100

PRICING_TIERS = [
    (5000, 0.01),
    (25000, 0.008),
    (100000, 0.005),
    (float("inf"), "custom")
]

def calculate_price(row_count):
    if row_count <= FREE_ROW_ALLOWANCE:
        return 0.0, row_count, 0

    remaining_rows = row_count - FREE_ROW_ALLOWANCE
    total_cost = 0.0
    tier_base = FREE_ROW_ALLOWANCE

    for max_rows, price_per_1000 in PRICING_TIERS:
        if remaining_rows <= 0:
            break

        rows_in_tier = min(remaining_rows, max_rows - tier_base)
        if price_per_1000 == "custom":
            return "custom", row_count, remaining_rows
        tier_cost = (rows_in_tier / 1000) * price_per_1000
        total_cost += tier_cost
        remaining_rows -= rows_in_tier
        tier_base = max_rows

    return round(total_cost, 2), row_count, row_count - FREE_ROW_ALLOWANCE
