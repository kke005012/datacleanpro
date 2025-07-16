# pricing.py

def calculate_price(row_count):
    FREE_ROW_ALLOWANCE = 100

    PRICING_TIERS = [
        (500, 0.02),
        (1500, 0.015),
        (10000, 0.01),
        (25000, 0.008),
        (100000, 0.007),
        (float('inf'), 'custom')
    ]

    if row_count <= FREE_ROW_ALLOWANCE:
        return 0.0, row_count, 0  # Free

    # Find the correct tier based on total row count
    price_per_row = None
    for max_rows, rate in PRICING_TIERS:
        if row_count <= max_rows:
            price_per_row = rate
            break

    if price_per_row == 'custom':
        return 'custom', row_count, row_count - FREE_ROW_ALLOWANCE

    billable_rows = row_count - FREE_ROW_ALLOWANCE
    total_cost = billable_rows * price_per_row
    return round(total_cost, 2), row_count, billable_rows
