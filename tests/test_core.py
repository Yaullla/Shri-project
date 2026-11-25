import pytest
from radar.core import calculate_margin, competitive_price, source_health
from radar.structured import parse_product_jsonld


def test_margin():
    r = calculate_margin(10000, 20000, 1000, 2000, 500, 12)
    assert r["landed_rub"] == 13500
    assert r["profit_rub"] == 4100
    assert r["margin_percent"] == 20.5


@pytest.mark.parametrize("purchase,sale,fee", [(-1, 100, 0), (1, 0, 0),
    (float("nan"), 100, 0), (1, 100, 100)])
def test_bad_inputs(purchase, sale, fee):
    with pytest.raises(ValueError):
        calculate_margin(purchase, sale, fee_percent=fee)


def test_competitive():
    assert competitive_price(10000, 5) == 9500
    with pytest.raises(ValueError):
        competitive_price(10000, 10)


def test_sources_not_live():
    assert all(not x["live_prices"] for x in source_health())


def test_jsonld():
    html = '<script type="application/ld+json">{"@type":"Product","name":"Demo","sku":"TEST","offers":{"price":"42.50","priceCurrency":"AED"}}</script>'
    r = parse_product_jsonld(html)
    assert r["offers"][0]["price"] == "42.50"
    assert not r["verified"]


def test_invalid_price():
    html = '<script type="application/ld+json">{"@type":"Product","offers":{"price":"NaN","priceCurrency":"AED"}}</script>'
    assert parse_product_jsonld(html)["offers"] == []
