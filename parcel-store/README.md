# Parcel Store / storefront and CRM prototype

This is the isolated v0.3 browser prototype. Open index.html locally. It has demo-only catalogue, orders, parcel capacity, manual tracking and CRM. It is NOT a production shop. Do not enter real client data or secrets. The existing radar project is untouched.

## Engineering next steps

1. Preserve the mobile/desktop flows and DESIGN.md while migrating the UI to React + TypeScript + Vite. Use shadcn/ui selectively for dialog, forms, tables and accessible navigation. Avoid adding dependencies to the static prototype just for appearance.
2. Introduce a server API and PostgreSQL migrations. Entities: product, customer, order, order_item, parcel, reservation, carrier_event, expense, payment, attribution_event. Derive gross weight from server-owned SKU data in integer grams; reserve weight atomically in a DB transaction; enforce one open parcel per route; idempotency; cancellation/expiry; no silent split. Historical prices and weights are snapshots.
3. Protect customer/order access and admin routes on the server. Validate Telegram initData server-side; never trust client-supplied roles. Keep credentials server-only. Use a private database, least-privilege policies, backups, and no personal information in Git.
4. Carrier adapter: official tracking API, poll once per parcel, deduplicate events, expose last verified event and update timestamp. ETA is optional and distinct from scan history; no simulated GPS presented as real. Validate carrier eligibility and permitted contents before actual sales.
5. CRM: separate requests, accepted orders, payments and issued goods. Per-source funnel (visit -> request -> confirmation -> payment -> issue), unique customer counts, SKU demand, expenses, profit per kg, expected vs actual. Use TanStack Table and Recharts only where they improve interaction.
6. PWA and Telegram Mini App first; WXT Chrome extension and Tauri mobile packaging after backend stabilization. No checkout payments until legal and provider requirements are confirmed.

## Acceptance tests

- Exact capacity closes the collection and opens a new parcel; concurrent reservations cannot overbook.
- Oversized baskets rejected; whole-order move requires explicit consent; cancellation and expiry release only eligible reservations.
- Duplicate request does not double reserve. Prices and weight computed from server snapshots.
- Customers cannot read other customers' orders, and cannot read admin costs or credentials.
- Tracking events never duplicate; unknown ETA stays unknown.
- Playwright mobile and desktop; keyboard focus and responsive layout; Lighthouse baseline; no horizontal overflow at 390px.
- CSV formula injection protection, input validation, audit log for administrative edits.

## Reviewed upstream candidates (2026-11-26)

GitHub repository metadata was queried directly. Stars change; reported SPDX license is repo-level only. Review individual dependencies/assets and pin a reviewed version or commit before installing. No third-party skill scripts installed or executed in this commit.

| Repository | Stars | GitHub SPDX | Use |
|---|---:|---|---|
| [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 154546 | MIT | Design review |
| [Awesome DESIGN.md](https://github.com/VoltAgent/awesome-design-md) | 129185 | MIT | Reference principles |
| [Taste Skill](https://github.com/Leonxlnx/taste-skill) | 121888 | MIT | Visual QA |
| [shadcn/ui](https://github.com/shadcn-ui/ui) | 129158 | MIT | UI components |
| [Supabase](https://github.com/supabase/supabase) | 115543 | Apache-2.0 | Database/auth candidate |
| [Tauri](https://github.com/tauri-apps/tauri) | 113203 | Apache-2.0 | Native packaging candidate |
| [Playwright](https://github.com/microsoft/playwright) | 101116 | Apache-2.0 | Browser tests |
| [TanStack Table](https://github.com/TanStack/table) | 28632 | MIT | CRM tables |
| [Recharts](https://github.com/recharts/recharts) | 27766 | MIT | Charts |
| [WXT](https://github.com/wxt-dev/wxt) | 10782 | MIT | Browser extension |

The existing HTML is dependency-free. This commit imports the prototype and its design specification, not a React migration or hosted service.


## EMS tracking preview (v0.3.1)

- tracking.py: server-side SOAP history adapter with per-process caching (15 minutes), XML validation, deduplication, and stale-data fallback. No API ETA field is assumed.
- preview_server.py: localhost-only server at port 8080, with an explicit tracking-number allowlist. Not a production service.
- test_tracking.py: synthetic tests (no calls to the carrier).
- index.html: manual tracking remains available; "Обновить EMS" fetches from same-origin server. Order history tries to refresh on opening and every 15 minutes while visible. Manual ETA range remains separate.
- Official API overview: https://info.pochta.ru/support/business/api and tracking portal https://tracking.pochta.ru/. SOAP format cross-checked against published implementations; the detailed official specification was unavailable in this research session. Live credentials and a real authorized tracking number are required to confirm endpoint compatibility.

Local setup from parcel-store directory:
1. Obtain tracking API access at the official carrier portal. Do not send or commit credentials.
2. Set environment variables POCHTA_TRACK_LOGIN, POCHTA_TRACK_PASSWORD, POCHTA_ALLOWED_TRACKS (comma-separated real shipment identifiers you are authorized to track).
3. Run python -m unittest -v test_tracking and python preview_server.py. Open http://127.0.0.1:8080.
4. In demo admin > supplies select parcel, enter the same tracking number and actual dispatch date. Save and click "Обновить EMS". Customer history reads the same parcel data in this browser only.

Production blockers: shared database, server authorization by order ownership, durable cached tracking snapshots, scheduled background synchronization, notification consent, validated carrier credentials and actual service response. A local browser prototype is not a live shop and must not be exposed publicly.
