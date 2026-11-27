# Radar Business / Editions integration

The single-seller storefront is a separate deployment package, not the local buyer
workspace. Keep customer records, passwords and backups out of this public repo.
The store reads a separate Radar observations SQLite file in read-only mode using
RADAR_OFFERS_DB. The two approved exact mappings for initial catalog research are:

- GA-2100-1A1 -> casio|ga-2100-1a1|watch|new
- RPI5-8GB -> raspberry-pi|pi-5|8gb-board|new

An observation is not an offer. Do not treat unreviewed/old snapshots as current
or auto-publish a price. The new read-only MCP tool estimate_customer_quote
calculates a proposed RUB sale price from actual acquisition currency, effective
exchange rate, shipping, import costs, other costs, sale fees and target margin.
It performs no order or write. Customer CRM data must not be sent to this MCP.
The store package has its own local quote calculator and requires separate
operator confirmation before publication.

No external production deployment, payments, or live intake is enabled here.
