"""Bounded, operator-configured public-page collector. No bypass of access controls."""
from contextlib import closing
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from radar.offers import SOURCES, connect, ingest
from radar.structured import parse_product_jsonld

USER_AGENT = "RadarPriceMonitor/0.1"
MAX_BYTES = 2_000_000

# Fixed URLs: external content cannot choose new targets or trigger arbitrary requests.
TARGETS = {
    "casio-in": ("Casio India", "https://www.casio.com/in/watches/gshock/product.GA-2100-1A1/", "casio|ga-2100-1a1|watch|new"),
    "casio-ae": ("Noon", "https://www.noon.com/uae-en/men-s-stylish-analog-digital-quartz-watch-ga-2100-1a1/N37769673A/p/", "casio|ga-2100-1a1|watch|new"),
    "casio-ru": ("Watches RU", "https://www.watches.ru/Casio/GA-2100-1A1.html", "casio|ga-2100-1a1|watch|new"),
    "pi-in": ("Robocraze", "https://robocraze.com/products/raspberry-pi-5-8gb", "raspberry-pi|pi-5|8gb-board|new"),
    "amazon-in": ("Amazon.in", "https://www.amazon.in/dp/B0DFMS17RG", "mattel|jbj17|doll|new"),
}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_page(url, limit=MAX_BYTES):
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"})
    with build_opener(NoRedirect()).open(req, timeout=12) as response:
        if response.headers.get("Content-Encoding", "identity").lower() != "identity":
            raise ValueError("Unsupported encoding")
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Response too large")
        return data.decode(response.headers.get_content_charset() or "utf-8", errors="replace")


def collect(target_id, *, reader=read_page):
    source, url, key = TARGETS[target_id]
    _, currency, _ = SOURCES[source]
    observed_at = datetime.now(UTC).isoformat()
    result = {"target": target_id, "source": source, "url": url,
              "observed_at": observed_at, "status": "unknown", "offers": []}
    origin = urlsplit(url)
    robots_url = f"{origin.scheme}://{origin.netloc}/robots.txt"
    parser = RobotFileParser()
    try:
        parser.parse(reader(robots_url, 500_000).splitlines())
    except HTTPError as exc:
        # Conservative: even a missing robots file needs operator review.
        return result | {"status": f"robots_http_{exc.code}"}
    except (URLError, TimeoutError, ValueError, OSError):
        return result | {"status": "robots_unavailable"}
    if not parser.can_fetch(USER_AGENT, url):
        return result | {"status": "robots_disallowed"}
    try:
        html = reader(url)
        parsed = parse_product_jsonld(html)
    except HTTPError as exc:
        return result | {"status": f"page_http_{exc.code}"}
    except (URLError, TimeoutError, ValueError, OSError):
        return result | {"status": "page_unavailable"}
    offers = [r for r in parsed["offers"] if r["currency"] == currency]
    # All remote data stays unreviewed. Multiple variants must be manually resolved.
    if len(offers) != 1:
        return result | {"status": "no_offer" if not offers else "ambiguous_offers",
                         "offer_count": len(offers)}
    item = offers[0]
    availability = item["availability"].rsplit("/", 1)[-1].lower()
    row = {"source": source, "url": url, "observed_at": observed_at,
           "product_key": key, "currency": currency, "price": item["price"],
           "available": availability == "instock", "reviewed": False}
    return result | {"status": "candidate_unreviewed", "offers": [row]}


def collect_and_store(target_id, *, path=None, reader=read_page):
    result = collect(target_id, reader=reader)
    if result["offers"]:
        with closing(connect(path)) as db, db:
            for row in result["offers"]:
                ingest(db, row)
    return result
