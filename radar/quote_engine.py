"""Deterministic quote calculation for the single-seller business."""
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal, InvalidOperation


def decimal(value):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError("Invalid number") from None
    if not n.is_finite() or not 0 <= n <= 100_000_000:
        raise ValueError("Number outside permitted range")
    return n


def calculate_quote(purchase, rate, shipping, import_cost, other, fee_percent, margin_percent):
    p, fx, ship, tax, misc, fee, margin = map(
        decimal, (purchase, rate, shipping, import_cost, other, fee_percent, margin_percent)
    )
    if p <= 0 or fx <= 0 or fee + margin >= 100:
        raise ValueError("Check purchase, FX, and total percentages")
    cent = Decimal("0.01")
    cost = (p * fx + ship + tax + misc).quantize(cent, rounding=ROUND_HALF_UP)
    if cost <= 0:
        raise ValueError("Rounded cost must be positive")
    sale = (cost / (1 - (fee + margin) / 100)).quantize(cent, rounding=ROUND_CEILING)
    if sale > 100_000_000:
        raise ValueError("Sale outside permitted range")
    fees = (sale * fee / 100).quantize(cent, rounding=ROUND_HALF_UP)
    profit = sale - cost - fees
    return {
        "landed": str(cost), "sale": str(sale), "fees": str(fees),
        "profit": str(profit),
        "margin": str((profit / sale * 100).quantize(cent, rounding=ROUND_HALF_UP)),
        "status": "estimate_only",
    }
