from decimal import Decimal, ROUND_HALF_UP
from math import isfinite


def calculate_margin(purchase_rub: float, sale_rub: float, shipping_rub: float = 0,
                     customs_rub: float = 0, other_cost_rub: float = 0,
                     fee_percent: float = 0) -> dict:
    values = (purchase_rub, sale_rub, shipping_rub, customs_rub, other_cost_rub, fee_percent)
    if not all(isfinite(v) and v >= 0 for v in values):
        raise ValueError("Inputs must be finite and nonnegative")
    if sale_rub <= 0 or fee_percent >= 100:
        raise ValueError("Positive sale price and fee below 100% required")
    p, s, sh, c, o, f = map(lambda v: Decimal(str(v)), values)
    landed = p + sh + c + o
    fees = s * f / 100
    profit = s - landed - fees
    def money(v: Decimal) -> float:
        return float(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {"landed_rub": money(landed), "fees_rub": money(fees),
            "profit_rub": money(profit), "margin_percent": money(profit / s * 100),
            "break_even_rub": money(landed / (1 - f / 100))}


def competitive_price(market_min_rub: float, discount_percent: float = 5) -> float:
    if not isfinite(market_min_rub) or market_min_rub <= 0:
        raise ValueError("Positive market price required")
    if not isfinite(discount_percent) or not 0 <= discount_percent <= 5:
        raise ValueError("Discount must be between 0 and 5 percent")
    return float((Decimal(str(market_min_rub)) * (1 - Decimal(str(discount_percent)) / 100))
                 .quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def source_health() -> list[dict]:
    return [{"source": s, "status": "not_connected", "live_prices": False}
            for s in ("Amazon.in", "Amazon.ae", "Flipkart", "Noon", "Avito", "Ozon",
                      "Wildberries", "Yandex Market")]
