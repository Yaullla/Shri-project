from contextlib import closing
from datetime import UTC, datetime, timedelta

import pytest

from radar.fx import parse_rates
from radar.offers import connect, find_deals, history, ingest

NOW = datetime(2026, 11, 25, 12, tzinfo=UTC)


def observation(source, url, currency, price, **kwargs):
    return {'source': source, 'url': url, 'currency': currency, 'price': price,
            'product_key': 'brand|mpn|variant|new', 'available': True, 'reviewed': True,
            'observed_at': NOW.isoformat()} | kwargs


@pytest.fixture
def db():
    with closing(connect(':memory:')) as d:
        yield d


def seed(db):
    ingest(db, observation('Amazon.in', 'https://www.amazon.in/dp/DEMO', 'INR', 1000), now=NOW)
    ingest(db, observation('Ozon', 'https://ozon.ru/product/demo', 'RUB', 3000), now=NOW)


def deals(db):
    return find_deals(db, {'INR': 1}, {'IN:brand|mpn|variant|new': 500}, now=NOW)


def test_deal(db):
    seed(db)
    result = deals(db)[0]
    assert result['sale_rub'] == 2850
    assert result['profit_rub'] == 1008
    assert result['margin_percent'] == 35.37
    assert result['status'] == 'reviewed_snapshot_estimate'


def test_latest_unavailable(db):
    seed(db)
    ingest(db, observation('Amazon.in', 'https://www.amazon.in/dp/DEMO', 'INR', 1000,
                           available=False, observed_at=(NOW + timedelta(seconds=1)).isoformat()), now=NOW)
    assert deals(db) == []


def test_no_match_and_no_cost(db):
    seed(db)
    assert find_deals(db, {'INR': 1}, {}, now=NOW) == []
    assert find_deals(db, {'INR': 1}, {'IN:brand|mpn|variant|new': 500}, now=NOW+timedelta(days=2)) == []
    assert len(history(db, 'brand|mpn|variant|new')) == 2


def test_unreviewed(db):
    ingest(db, observation('Amazon.in', 'https://www.amazon.in/dp/DEMO', 'INR', 1000, reviewed=False), now=NOW)
    ingest(db, observation('Ozon', 'https://ozon.ru/product/demo', 'RUB', 3000), now=NOW)
    assert deals(db) == []


def test_bad_source_url(db):
    with pytest.raises(ValueError):
        ingest(db, observation('Amazon.in', 'https://amazon.in.evil.example/x', 'INR', 1000), now=NOW)


def test_cbr_nominal():
    xml = b'<ValCurs Date="25.11.2026"><Valute><CharCode>INR</CharCode><Nominal>100</Nominal><Value>90,00</Value></Valute><Valute><CharCode>AED</CharCode><Nominal>1</Nominal><Value>22,00</Value></Valute></ValCurs>'
    assert parse_rates(xml)['rub_per_unit'] == {'INR': '0.90', 'AED': '22.00'}


def test_cbr_missing():
    with pytest.raises(ValueError):
        parse_rates(b'<ValCurs Date="25.11.2026"/>')
