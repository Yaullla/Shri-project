# Radar v0.5 — development branch, 2026-11-27

Based on v0.4 commit 16d413bd2333e66164b27aef8d82c22ec09d867b. Previous CI run 45867597584 passed six jobs.
- Local CRM: SQLite, public Telegram links only, manual moderation/contact status,
  ad costs and leads; create/read/update/delete. No actual contacts imported.
- Buyer workspace preserved. Separate /travel and /admin pages; local trip board,
  no identity, matchmaking, bookings, or role-based authorization yet.
- Added Amperka Raspberry Pi 5 8 GB board as an unreviewed collection target.
  Existing collector enforces robots and fixed URLs. Run `uv run python -m scripts.collect_prices pi-in pi-ru --fx`.
- Private Moscow CSV import: `uv run python -m radar.wholesale prices.csv --supplier LABEL`.
  Columns product_key,observed_at,price_rub. Exact brand|mpn|variant|condition,
  timezone-aware timestamp, positive RUB price. Keep CSV and database private.
  Quotes are not public/reviewed offers and are not ranked yet.
- Added CRM, trip and CSV tests. New branch CI must be checked before merge.
- Persistent installation must run in actual Linux x86-64 / WSL Codex environment
  with Node >=24.15. Existing installer and registration scripts remain unchanged.
  Prior CI installs are ephemeral, not evidence of persistent install.
- Token benchmark: no paid inference or credentials. Measure actual model usage
  only with controlled Codex sessions and approved budget. See docs/BENCHMARK.md.
- Do not deploy publicly: no authentication or data isolation; no real payments,
  messaging, or personal customer data. No mass outreach.


## v0.5.1
- Previous PR #5 CI run 45946338555: 32 tests, all six jobs successful.
- Five public Telegram community candidates with provenance notes, no outreach,
  unknown ad cost, zero recorded leads. Opt-in idempotent seed:
  `uv run python -m radar.seed_communities`. Existing edits preserved.
- Separate local Basic Auth gates for administrator and traveler pages and APIs.
  Default disabled until independent 16+ character passwords configured.
  Host restriction and cross-origin write checks added. No production auth,
  individual users, TLS, or tenant isolation. Never expose this dev server.
- Added new API and browser tests including isolated protected workspace,
  screenshots, edit persistence, and trip creation/deletion.
- New CI run pending at commit time. No actual orders, payment or outreach.
