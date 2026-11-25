# Radar MCP — development preview

Install uv, then run from the repository root:

    uv sync
    uv run pytest -q
    uv run python -m radar.server

For Codex (run in repository root):

    codex mcp add radar -- uv run python -m radar.server
    codex mcp list

The server uses stdio, not a public HTTP endpoint. It is read-only.
Four tools: calculate_margin, competitive_price, source_health, inspect_snapshot.
The HTML input is untrusted and results are explicitly unverified. No marketplace
is connected yet. Do not treat snapshot prices as live or purchase-ready.
Customs and logistics costs are explicit inputs, not legal or tax estimates.
Before production: lock dependencies, audit license and security, test MCP
handshake, add authorized data adapters, rate limits, timestamped provenance,
currency normalization, SKU matching and data isolation. No secrets in Git.
Upstream: https://github.com/PrefectHQ/fastmcp/tree/v4.2.6
