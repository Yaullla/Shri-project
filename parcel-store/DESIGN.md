# Самобранка — design system v0.4

## Direction
A warm, quiet grocery storefront and a precise, neutral CRM. Original brand; references are principles, not copied brand assets. Inspired by Russian Gzhel porcelain: cobalt floral accents on a warm porcelain ground, Airbnb's discovery flow, Linear's calm workspaces, and Wise's clear money presentation.

## Tokens
- Canvas #F8F7F3; surface #FFFFFF; ink #193251; muted #58697C; primary #234E91; soft #EDF2FA; border #DCE3ED; warm accent #B69A64.
- System sans-serif for UI; Georgia for editorial hero only. Numeric data tabular. No gradients, unnecessary shadows or decorative badges.
- 4/8/12/16/24/32 spacing; 9px controls; 14px cards. 44px interactive controls where practical. Visible focus; readable contrast; reduced motion by default.

## Storefront
Mobile-first, two columns on phones, 3–4 on wider screens. Show availability and pricing certainty, weight, and obvious next step. Preorder request is not paid checkout. Cold-chain items require confirmation. Prototype: external product photo references with fallback; verify exact SKU and secure permission or use own photographs before publishing. No fabricated product ratings.

## CRM
Separate protected admin interface in production. Filters by time and attribution source; track requests, confirmed orders, payments and issued orders separately. Show forecast vs actual; never call preorder pipeline revenue actual revenue. SKU cost, weight, sourcing, batch expenses, gross margin and cash gap. Export CSV with formula-injection protection. Empty states and clearly labeled demo data.

## Implementation roadmap
Prototype: self-contained HTML/CSS/JS and localStorage; no third-party dependencies. Production: React/TypeScript/Vite, shadcn/ui, TanStack Table, Recharts, PostgreSQL/Supabase with RLS and verified server-side admin identity, Telegram initData validation, PWA manifest/service worker under HTTPS. Tauri/Rust optional later.

## Reference repositories
- https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
- https://github.com/VoltAgent/awesome-design-md
- https://github.com/Leonxlnx/taste-skill
- https://github.com/shadcn-ui/ui
- https://github.com/TanStack/table
- https://github.com/recharts/recharts
- https://github.com/supabase/supabase
- https://github.com/tauri-apps/tauri

Third-party skills were researched, not installed or executed. Review individual skill and dependency licenses and security before adoption. No personal-use import exemption is assumed for resale.

## v0.3 — parcels and tracking (25 November 2026)
- One active collection batch; show its usable weight and remaining capacity above the catalogue and on the checkout screen. Use a single quiet cobalt progress bar with numeric labels, not colour alone. Reserve integer gross grams on submission. Closed batches do not reopen automatically on cancellation. An order that does not fit may move as a whole to a new batch only after explicit consent; the old batch closes. An order exceeding total capacity is rejected. Packaging allowance is separate from the gross weight of individual products. Cold-chain products are unconfirmed wishes only.
- Status, dispatch date, estimated date range and carrier events have independent fields. Empty ETA means unknown. Show the source and dates of events. Never imply live GPS or a guaranteed delivery date. Display calendar days in Asia/Colombo.
- Parcel cards and single-column mobile layout use the quiet, minimal hierarchy of the Linear and Notion references from Awesome DESIGN.md. UI UX Pro Max accessibility/resilient layout principles: readable numeric labels, native form inputs, reduced motion, progressbar semantics, keyboard focus.
- Browser tests: Microsoft Playwright (actual use) with Chromium, at desktop 1440px and mobile 390px. Tested exact capacity, overflow rejection, explicit next-batch consent, insufficient residual capacity, cancellation, manual tracking visibility, demo isolation, all admin tabs and mobile overflow. Browser policy blocked direct local file and localhost navigation in the test environment; tests used set_content, so persistence across sessions and public deployment remain untested.
- Production architecture: PostgreSQL transactional capacity check with a row lock or equivalent, a unique open batch per direction, idempotent order submissions, reservation expiry, per-batch carrier polling with server-only credentials, event deduplication and client authorization. Never expose carrier API credentials or buyers' personal details. No production concurrency guarantees in local prototype.

## Additional researched repositories (not installed in this prototype)
- https://github.com/TanStack/query — cache/refetch server tracking and catalogue data
- https://github.com/lucide-icons/lucide — consistent line icons
- https://github.com/GoogleChrome/lighthouse — performance checks
- https://github.com/dequelabs/axe-core — accessibility checks
- https://github.com/wxt-dev/wxt — future Chrome extension (Manifest V3)
- https://github.com/tremorlabs/tremor — optional React dashboard patterns
- https://github.com/microsoft/playwright — browser testing, used in this iteration

Carrier reference: https://info.pochta.ru/support/business/api ; live access not configured. The site is not publicly hosted, all product prices/limits are demo assumptions, and the admin interface has no real authentication. Confirm carrier acceptance and lawful import before launching sales.

## v0.4 — Samobranka (27 November 2026)
- Brand approved: Самобранка; tagline «Всё, по чему скучали». Original cloche and botanical mark in the spirit of Gzhel; no claim of affiliation or use of existing artwork. Restrict ornament to identity and hero; keep product cards and CRM clean.
- Catalogue is visible directly on home; mobile 2 columns, desktop 4, responsive search and filters, five customer navigation items. Demo admin remains in footer, separate production auth pending.
- Product detail dialog includes brand, pack size, ingredients, storage, allergens, nutrition, gross weight estimate, source URL and fulfilment status. Admin can edit detail fields and image URL. Unconfirmed handling requirements are interest-only, not weight reservations. Data and image rights require SKU-level confirmation before public commercial launch.
- EMS remains manual in publicly viewed HTML; carrier adapter is local-only and credentials are not configured. JavaScript syntax checked. Full browser retest and actual remote photo availability remain outstanding.
