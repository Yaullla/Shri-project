"""Official CBR daily rates; never silently substitute a stale quote."""
from datetime import date, datetime
from decimal import Decimal
from urllib.request import urlopen
from xml.etree import ElementTree


def parse_rates(payload: bytes) -> dict:
    if len(payload) > 2_000_000:
        raise ValueError('XML too large')
    if b'<!DOCTYPE' in payload.upper() or b'<!ENTITY' in payload.upper():
        raise ValueError('XML declarations not allowed')
    root = ElementTree.fromstring(payload)
    as_of = datetime.strptime(root.attrib['Date'], '%d.%m.%Y').date().isoformat()
    rates = {}
    for item in root.findall('Valute'):
        code = item.findtext('CharCode')
        if code in ('INR', 'AED'):
            value = Decimal(item.findtext('Value').replace(',', '.'))
            nominal = Decimal(item.findtext('Nominal'))
            if not value.is_finite() or not nominal.is_finite() or value <= 0 or nominal <= 0:
                raise ValueError('Invalid CBR value')
            rates[code] = str(value / nominal)
    if set(rates) != {'INR', 'AED'}:
        raise ValueError('Required CBR currencies missing')
    return {'as_of': as_of, 'rub_per_unit': rates, 'source': 'CBR'}


def fetch_rates(day: str) -> dict:
    d = date.fromisoformat(day)
    url = 'https://www.cbr.ru/scripts/XML_daily.asp?date_req=' + d.strftime('%d/%m/%Y')
    with urlopen(url, timeout=15) as response:
        data = response.read(2_000_001)
    return parse_rates(data)
