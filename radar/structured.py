import json
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser

MAX_HTML = 5_000_000


class JsonLD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.parts = []
        self.docs = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and (dict(attrs).get("type") or "").lower() == "application/ld+json":
            self.active = True
            self.parts = []

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.active:
            self.docs.append("".join(self.parts))
            self.active = False


def walk(value, depth=0):
    if depth > 12:
        return
    if isinstance(value, list):
        for item in value:
            yield from walk(item, depth + 1)
    elif isinstance(value, dict):
        kinds = value.get("@type", [])
        if isinstance(kinds, str):
            kinds = [kinds]
        if isinstance(kinds, list) and any(isinstance(kind, str) and kind.rsplit("/", 1)[-1] == "Product" for kind in kinds):
            yield value
        if "@graph" in value:
            yield from walk(value["@graph"], depth + 1)


def parse_product_jsonld(html: str) -> dict:
    if len(html) > MAX_HTML:
        raise ValueError("Snapshot too large")
    parser = JsonLD()
    parser.feed(html)
    rows = []
    for doc in parser.docs[:30]:
        try:
            data = json.loads(doc)
        except (ValueError, RecursionError):
            continue
        for product in walk(data):
            offers = product.get("offers", [])
            if isinstance(offers, dict):
                offers = [offers]
            if not isinstance(offers, list):
                continue
            for offer in offers[:20]:
                if not isinstance(offer, dict):
                    continue
                try:
                    price = Decimal(str(offer.get("price")))
                except (InvalidOperation, ValueError):
                    continue
                currency = str(offer.get("priceCurrency", "")).upper()
                if not price.is_finite() or not 0 < price <= Decimal(1000000000):
                    continue
                if currency not in ("INR", "AED", "RUB", "USD", "EUR"):
                    continue
                rows.append({"name": str(product.get("name", ""))[:160],
                             "sku": str(product.get("sku", ""))[:80],
                             "price": str(price), "currency": currency,
                             "availability": str(offer.get("availability", ""))[:120]})
                if len(rows) >= 20:
                    return {"verified": False, "source": "supplied_snapshot", "offers": rows}
    return {"verified": False, "source": "supplied_snapshot", "offers": rows}


class ProductMeta(HTMLParser):
    """Collect explicit HTML metadata only, never guess price from page text."""

    def __init__(self):
        super().__init__()
        self.values = {}

    def handle_starttag(self, tag, attrs):
        if tag not in ("meta", "link"):
            return
        a = dict(attrs)
        key = a.get("property") or a.get("itemprop") or a.get("name")
        value = a.get("content") or (a.get("href") if tag == "link" else None)
        if key and value and len(value) <= 500:
            self.values.setdefault(key.lower(), set()).add(value)


def parse_product_meta(html: str) -> dict:
    if len(html) > MAX_HTML:
        raise ValueError("Snapshot too large")
    parser = ProductMeta()
    parser.feed(html)

    def unique(*keys):
        values = set().union(*(parser.values.get(k, set()) for k in keys))
        return next(iter(values)) if len(values) == 1 else ""

    # Require a product title or explicit product type, plus one price/currency.
    name = unique("og:title")
    if not name and unique("og:type") != "product":
        return {"offers": []}
    price = unique("product:price:amount", "og:price:amount", "price")
    currency = unique("product:price:currency", "og:price:currency", "pricecurrency").upper()
    try:
        value = Decimal(price)
    except InvalidOperation:
        return {"offers": []}
    if not value.is_finite() or not 0 < value <= Decimal(1000000000):
        return {"offers": []}
    if currency not in ("INR", "AED", "RUB", "USD", "EUR"):
        return {"offers": []}
    return {"offers": [{"name": name[:160], "sku": unique("sku", "product:retailer_item_id")[:80],
                        "price": str(value), "currency": currency,
                        "availability": unique("availability", "product:availability")[:120]}]}
