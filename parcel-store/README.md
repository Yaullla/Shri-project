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


## Samobranka v0.5 — storefront refresh

Brand: Самобранка. Seven hash-addressable views, product detail cards, original cobalt porcelain ornament, independent parcel overview, native CSS motion and optional pinned local Anime.js. Download index.html to open the CSS-only preview; serve the directory over HTTP for optional Anime.js. Do not deploy as a production store. EMS remains inactive outside the localhost integration preview; shared database/auth and public hosting are outstanding. See DESIGN.md for motion budget and limitations. Run `node --test test_motion.mjs` for the synthetic DOM smoke tests. Real-browser testing and product-photo verification are still required.

Next milestone: mobile browser validation (390/768/1440px), reviewed/licensed product assets, authenticated shared database and transactional parcel capacity, Telegram bot/Mini App, then approved community advertising and opt-in notifications.


## v0.6 — authenticated Telegram pilot

Separate live-pilot client at `/miniapp`; existing `index.html` is still the browser-only demo. Do not confuse demo localStorage with real customer data. The full storefront and full admin panel have not yet been migrated to the pilot backend.

### Local run (Python 3.10+, no third-party runtime packages)

From parcel-store: `python -m unittest -v test_pilot test_tracking`, `node --test test_motion.mjs`, then `python pilot_api.py`. Open http://127.0.0.1:8081/miniapp. Anonymous visitors can inspect the catalogue but not submit or view private orders. The default catalogue has 13 interest-only items with no verified price/weight. Default net capacity is 29,000 g (demo assumption, configurable on first DB initialization). Keep real DB on a persistent, access-controlled disk; do not commit DB files.

### Telegram setup (after TLS hosting is configured)

1. Create bot at https://t.me/BotFather. Use the selected brand Самобранка; check username availability. Set TELEGRAM_BOT_TOKEN and SAM_ADMIN_IDS (comma-separated verified Telegram numeric IDs) via secret manager, not Git.
2. Bind HTTPS reverse proxy to pilot_api.py at localhost:8081. Set SAM_DB to a protected persistent path. Add TLS, request/rate limits, backups and access-log redaction; do not expose the stdlib HTTP server directly.
3. Set SAM_MINIAPP_URL to the HTTPS /miniapp URL; run `python bot.py --configure` then `python bot.py` with a supervised process. Configure Main Mini App in BotFather for startapp links; the bot responds to private /start, /help and /id only. It does not send unsolicited advertising.
4. Verify image rights, exact product labels, import and carrier eligibility, pricing, storage, data notice and admin workflow. Add approved local SKU WebP images (<2MB) and JSON with ingredients/storage/allergens/nutrition/source to SAM_ASSETS_DIR (default private-assets). No invented photos. Use `python manage_pilot.py approve SKU GRAMS PRICE_KOPECKS --verified` for reviewed product data, or keep interest-only. `python manage_pilot.py parcel ID closed|sent|arrived|ready` controls manual tracking, optional --track, --sent, --eta-from, --eta-to. Dates YYYY-MM-DD.
5. Only after acceptance testing, set SAM_ACCEPT_REQUESTS=1 and restart server. Do not enable payment yet. EMS API remains off. The API verifies Telegram initData HMAC and freshness, uses SQLite BEGIN IMMEDIATE and a unique open-parcel index, stores order snapshots and idempotency keys, and enforces owner/admin access. Source attribution reads signed start_param, not untrusted URL values.
6. Pilot CRM currently includes read-only aggregate demand, requests, clients, source and parcel metrics; real product edits and manual parcel status use local operator CLI. Full financial dashboard, expense ledger, website login and shared storefront, notification delivery, PostgreSQL migration, reservation expiry, and privacy/data retention policy remain outstanding. SQLite pilot is one host only; do not scale horizontally or use an ephemeral filesystem.

Official Telegram docs: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app ; https://core.telegram.org/bots/api#setchatmenubutton .

Separate CI workflow .github/workflows/parcel-store-verify.yml added. Tests are synthetic and no live tokens or API calls are required. Live Telegram and browser verification still pending.
