# Radar MCP — development preview

Install uv, then run from the repository root:

    uv sync
    uv run pytest -q
    uv run python -m radar.server

For Codex (run in repository root):

    codex mcp add radar -- uv run python -m radar.server
    codex mcp list

The server uses stdio. No public endpoint or purchasing tool.
Seven tools: calculate_margin, competitive_price, source_health, inspect_snapshot,
price_history, find_deals, get_exchange_rates. Marketplace observations are imported
by a trusted operator, not collected live. CBR adapter needs network access.
Set RADAR_DB to a local database path outside source control.

Import a JSON array with:

    uv run python -m radar.import_offers observations.json

Each observation contains source, url, currency, price, observed_at (ISO 8601 with
timezone), product_key (operator-confirmed brand|mpn|variant|condition), available
and reviewed (booleans). Mark reviewed only after confirming exact identity, seller,
condition, price and availability. Never import fake data as reviewed market data.
URLs must match the source registry. Avoid credentials or personal data in URLs.
The latest observation per source/URL supersedes earlier snapshots. The ranking
uses exact keys, the lowest reviewed Russian snapshot and an explicit freshness
window. It skips products without rates or additional cost inputs. The output is a
scenario estimate, not a confirmed live trade. FX rates are caller inputs: verify
date and actual conversion fees. Import costs must include applicable taxes, duties,
shipping and compliance. No marketplace is connected yet.

Before production: lock dependencies, run full tests and MCP handshake, add
authorized live adapters and rate limits, persistent provenance, canonical product
registry, robust URL normalization, data isolation and PostgreSQL.
Upstream: https://github.com/PrefectHQ/fastmcp/tree/v4.2.6
