import json
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser

MAX_HTML = 2_000_000


class JsonLD(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.active = False
        self.parts = []
        self.docs = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
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
        if isinstance(kinds, list) and "Product" in kinds:
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
