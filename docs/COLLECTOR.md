# Price collector v0.1

Fixed public-page probes for a watch across India, UAE and Russia, plus two
Indian products. Requests use a declared user agent, obey robots.txt, do not
follow redirects, do not bypass access controls, and have size/time bounds.
The operator must confirm site terms and permission before recurring use.
No marketplace account, cookies, proxies, credentials or model calls.

    uv run python -m scripts.collect_prices casio-in casio-ae casio-ru --fx

If data is returned, it is recorded in SQLite as an unreviewed candidate.
No candidate becomes an actionable deal until an operator verifies exact
product identity, variant, condition, availability and seller and imports a
reviewed observation. The CI network probe is diagnostic, not an uptime SLA.
There is no guarantee a page exposes JSON-LD or permits automated access.
A blocked or missing result is explicit; there is no fabricated price.

MCP reads bounded history and ranks reviewed snapshots only. Network collection
is deliberately operator-side, not an arbitrary URL tool exposed to the model.

Alternate retailers: Watch House UAE, i-Watch and Time Team. A metadata fallback accepts only explicit, unambiguous price and currency fields. Missing or conflicting fields are rejected. All resulting records remain unreviewed.

CI saves the diagnostic JSONL and any SQLite observations as an artifact for
seven days. This is not a production database; do not store personal or private
data in artifacts in a public repository. Download the artifact and set
RADAR_DB to its SQLite path to inspect history. For a specific, manually
verified observation only:

    uv run python -m scripts.review_observation SOURCE URL ISO_TIMESTAMP --confirmed

The flag represents actual human verification; never use it on unverified
records. No recurring collection or client data storage is enabled.
