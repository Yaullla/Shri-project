# Zero-cost pilot deployment

Decision: no paid resources, no Railway deployment. The existing Python/SQLite pilot remains available locally and tested; it is not compatible with ephemeral static hosting as a persistent API.

## Static technical preview
Root directory: parcel-store. Build command: node build-preview.mjs. Output: dist. No package installation or credentials needed. Only the browser demo, its original MIT animation dependency, and robots.txt are exported. The demo uses localStorage, cannot transmit orders and accepts no payments. Do not enter real client data. Noindex is not access control. Product image links are references pending rights and SKU verification.

Vercel: vercel.json supplies the settings. Hobby is limited to personal non-commercial use. Use it only for a qualifying personal technical preview; do not launch a commercial shop or lead collection there on Hobby. Confirm account eligibility if unclear. https://vercel.com/docs/plans/hobby

Cloudflare Pages: same root/build/output settings. Use a Free project and confirm applicable terms/limits before opening to customers. https://developers.cloudflare.com/pages/platform/limits/

## Shared application
Migrate the tested Python API's contract and transactional weight logic to a serverless runtime (Cloudflare Workers + PostgreSQL/Supabase Free or D1 after concurrency review). The current SQLite file must not be used on ephemeral storage. The Telegram bot should use a verified webhook instead of continuous polling. Keep signing tokens server-side; use authenticated access, idempotency, backups and atomic reservation. Real order submission remains disabled until that implementation is tested, products/permissions are verified and a secure shared database is configured. EMS and payments stay off.

No provider account, subscription, domain purchase or deployment has been created by these files.
