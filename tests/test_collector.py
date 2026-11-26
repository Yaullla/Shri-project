from contextlib import closing
from urllib.error import HTTPError

import pytest

from radar.collector import collect, collect_and_store
from radar.offers import connect, find_deals, history, review_observation

HTML = '<script type="application/ld+json">{"@type":"Product","name":"Demo","sku":"TEST","offers":{"price":"1000","priceCurrency":"INR","availability":"https://schema.org/InStock"}}</script>'


def allowed_reader(url, limit=2_000_000):
    return "User-agent: *\nAllow: /" if url.endswith("robots.txt") else HTML


def test_store_unreviewed(tmp_path):
    path = tmp_path / "test.sqlite3"
    result = collect_and_store("casio-in", path=path, reader=allowed_reader)
    assert result["status"] == "candidate_unreviewed"
    with closing(connect(path)) as db:
        rows = history(db, "casio|ga-2100-1a1|watch|new")
        assert len(rows) == 1
        assert rows[0]["reviewed"] == 0
        assert rows[0]["available"] == 1
        assert find_deals(db, {"INR": 1}, {}) == []


def test_robots_blocks_page():
    calls = []

    def reader(url, limit=2_000_000):
        calls.append(url)
        return "User-agent: *\nDisallow: /"

    assert collect("casio-in", reader=reader)["status"] == "robots_disallowed"
    assert len(calls) == 1


def test_blocked_robots():
    def reader(url, limit=2_000_000):
        raise HTTPError(url, 403, "Forbidden", {}, None)

    assert collect("casio-in", reader=reader)["status"] == "robots_http_403"


def test_currency_mismatch():
    assert collect("casio-ae", reader=allowed_reader)["status"] == "no_offer"


def test_no_fabricated_price():
    def reader(url, limit=2_000_000):
        return "User-agent: *\nAllow: /" if url.endswith("robots.txt") else "<html>no price</html>"

    assert collect("casio-in", reader=reader)["offers"] == []


def test_meta_fallback():
    html = '<meta property="og:type" content="product"><meta property="og:title" content="Demo"><meta property="product:price:amount" content="2000"><meta property="product:price:currency" content="RUB"><link itemprop="availability" href="https://schema.org/InStock">'

    def reader(url, limit=2_000_000):
        return "User-agent: *\nAllow: /" if url.endswith("robots.txt") else html

    r = collect("casio-ru", reader=reader)
    assert r["method"] == "html_meta"
    assert r["offers"][0]["price"] == "2000"
    assert not r["offers"][0]["reviewed"]


def test_ambiguous_meta_rejected():
    html = '<meta property="og:type" content="product"><meta property="product:price:amount" content="2000"><meta itemprop="price" content="3000"><meta property="product:price:currency" content="RUB">'

    def reader(url, limit=2_000_000):
        return "User-agent: *\nAllow: /" if url.endswith("robots.txt") else html

    assert collect("casio-ru", reader=reader)["status"] == "no_offer"


def test_review_requires_explicit_confirmation(tmp_path):
    path = tmp_path / "test.sqlite3"
    observation = collect_and_store("casio-in", path=path, reader=allowed_reader)["offers"][0]
    with closing(connect(path)) as db, db:
        args = (db, observation["source"], observation["url"], observation["observed_at"])
        with pytest.raises(ValueError):
            review_observation(*args)
        review_observation(*args, confirmed=True)
        assert history(db, observation["product_key"])[0]["reviewed"] == 1
