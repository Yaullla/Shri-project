# Samobranka pilot deployment

Status: deployment prepared; no public service created yet. Railway is a candidate, not a purchase authorization.

## Railway dashboard
1. Link Yaullla/Shri-project; branch feat/parcel-store; Root Directory /parcel-store. Use the Dockerfile, not a deprecated railway.toml configuration.
2. Create one web service and persistent volume mounted at /data. Verify the runtime user UID 10001 can write to the volume (use hosting-supported volume ownership setup before launch). Never allow a live database on ephemeral storage. Set a resource spending limit and review charges first.
3. Environment: SAM_BIND=0.0.0.0, SAM_DB=/data/samobranka.sqlite3, SAM_ASSETS_DIR=/data/assets, SAM_ACCEPT_REQUESTS=0. Railway injects PORT; default 8081 locally. Configure healthcheck /health, public HTTPS domain, one replica. No public database or SSH ports.
4. Test /health and /miniapp. No real submissions yet. The old full website remains index.html (local demo), not a production store. The Docker image serves only the backed pilot interface, not that demo.
5. Register the bot via BotFather. Set TELEGRAM_BOT_TOKEN and SAM_ADMIN_IDS in the hosting secret UI, never in Git/chat. Configure Main Mini App with HTTPS /miniapp. Run python bot.py --configure with SAM_MINIAPP_URL, then run bot.py as a separate supervised service or configure a verified webhook. A long-polling service may consume continuous compute. Do not enable a paid service without approval.
6. Check actual SKUs, photo permissions, legal import, storage, privacy notice, backups, request rate limiting, retention, user/admin workflows and real Telegram authentication. Only then set SAM_ACCEPT_REQUESTS=1.
7. EMS API remains disabled. No payment integration or unsolicited advertising.

Official references: https://docs.railway.com/builds/dockerfiles ; https://docs.railway.com/volumes/reference ; https://docs.railway.com/deployments/healthchecks ; https://docs.railway.com/pricing/free-plan

SQLite is a single-host pilot decision; PostgreSQL and the full shared CRM remain future migration items.
