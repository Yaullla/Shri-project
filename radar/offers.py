"""Timestamped observations. Reviewed snapshots are not live offers."""
import os
import sqlite3
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

SOURCES = {
    'Amazon.in': ('IN', 'INR', 'amazon.in'),
    'Flipkart': ('IN', 'INR', 'flipkart.com'),
    'Amazon.ae': ('AE', 'AED', 'amazon.ae'),
    'Noon': ('AE', 'AED', 'noon.com'),
    'Avito': ('RU', 'RUB', 'avito.ru'),
    'Ozon': ('RU', 'RUB', 'ozon.ru'),
    'Wildberries': ('RU', 'RUB', 'wildberries.ru'),
    'Yandex Market': ('RU', 'RUB', 'market.yandex.ru'),
}


def number(value, *, positive=False):
    try:
        n = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('Invalid number') from None
    if not n.is_finite() or n < 0 or n > 10**9 or (positive and n == 0):
        raise ValueError('Number outside allowed range')
    return n


def moment(value):
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError('Timestamp must include timezone')
    return dt.astimezone(UTC)


def db_path():
    return Path(os.environ.get('RADAR_DB', 'radar.sqlite3')).resolve()


def connect(path=None):
    db = sqlite3.connect(path or db_path())
    db.row_factory = sqlite3.Row
    db.execute('''CREATE TABLE IF NOT EXISTS offers (
        source TEXT NOT NULL, url TEXT NOT NULL, observed_at TEXT NOT NULL,
        product_key TEXT NOT NULL, region TEXT NOT NULL, currency TEXT NOT NULL,
        price TEXT NOT NULL, available INTEGER NOT NULL, reviewed INTEGER NOT NULL,
        PRIMARY KEY(source,url,observed_at))''')
    db.execute('CREATE INDEX IF NOT EXISTS offers_product ON offers(product_key, observed_at)')
    return db


def ingest(db, row, *, now=None):
    source = row['source']
    region, currency, domain = SOURCES[source]
    if row['currency'] != currency:
        raise ValueError('Currency mismatch')
    url = urlsplit(row['url'])
    host = url.hostname or ''
    if url.scheme != 'https' or url.username or url.password or url.port not in (None, 443) or not (host == domain or host.endswith('.' + domain)):
        raise ValueError('URL does not match source')
    if type(row['available']) is not bool or type(row['reviewed']) is not bool:
        raise ValueError('Status flags must be booleans')
    key = row['product_key'].strip().casefold()
    if not key or len(key) > 200 or len(row['url']) > 2000:
        raise ValueError('Invalid product key or URL')
    dt = moment(row['observed_at'])
    if dt > (now or datetime.now(UTC)) + timedelta(minutes=5):
        raise ValueError('Future observation')
    db.execute('''INSERT INTO offers VALUES (?,?,?,?,?,?,?,?,?)
        ON CONFLICT(source,url,observed_at) DO NOTHING''',
        (source, row['url'], dt.isoformat(timespec='microseconds'), key, region, currency,
         str(number(row['price'], positive=True)), int(row['available']), int(row['reviewed'])))


def history(db, key, limit=30):
    if not 1 <= limit <= 100:
        raise ValueError('Limit must be 1..100')
    return [dict(r) for r in db.execute('SELECT * FROM offers WHERE product_key=? ORDER BY observed_at DESC LIMIT ?', (key.strip().casefold(), limit))]


def find_deals(db, rates, costs, *, min_margin=20, discount=5, fee=12, max_age_hours=24, limit=10, now=None):
    """Compare reviewed, available, latest snapshots using exact operator-assigned product keys.
    Costs are explicit per product/region totals in RUB, including shipping and import expenses."""
    if not 1 <= limit <= 100 or not 1 <= max_age_hours <= 168:
        raise ValueError('Invalid limits')
    margin, disc, commission = map(number, (min_margin, discount, fee))
    if margin > 100 or disc > 5 or commission >= 100:
        raise ValueError('Invalid percentage')
    fx = {c: number(v, positive=True) for c, v in rates.items()}
    cutoff = ((now or datetime.now(UTC)) - timedelta(hours=max_age_hours)).isoformat(timespec='microseconds')
    rows = db.execute('''SELECT o.* FROM offers o JOIN (
        SELECT source,url,MAX(observed_at) AS ts FROM offers GROUP BY source,url
        ) l ON o.source=l.source AND o.url=l.url AND o.observed_at=l.ts
        WHERE o.observed_at>=? AND o.available=1 AND o.reviewed=1''', (cutoff,)).fetchall()
    ru = {}
    for r in rows:
        if r['region'] == 'RU' and (r['product_key'] not in ru or Decimal(r['price']) < Decimal(ru[r['product_key']]['price'])):
            ru[r['product_key']] = r
    out = []
    for r in rows:
        key = r['product_key']
        target = ru.get(key)
        cost_key = r['region'] + ':' + key
        if r['region'] == 'RU' or not target or cost_key not in costs or r['currency'] not in fx:
            continue
        purchase = Decimal(r['price']) * fx[r['currency']]
        landed = purchase + number(costs[cost_key])
        sale = Decimal(target['price']) * (1 - disc/100)
        profit = sale * (1 - commission/100) - landed
        pct = profit / sale * 100
        if pct >= margin:
            out.append({'product_key': key, 'region': r['region'], 'buy_url': r['url'], 'ru_url': target['url'],
                        'buy_observed_at': r['observed_at'], 'ru_observed_at': target['observed_at'],
                        'purchase_rub': round(float(purchase), 2), 'landed_rub': round(float(landed), 2),
                        'sale_rub': round(float(sale), 2), 'profit_rub': round(float(profit), 2),
                        'margin_percent': round(float(pct), 2), 'status': 'reviewed_snapshot_estimate'})
    return sorted(out, key=lambda x: x['profit_rub'], reverse=True)[:limit]
