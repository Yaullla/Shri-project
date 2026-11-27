# Marketing Hub — initial implementation

30 candidate communities, none approved for automated posting yet. Verify each current description, rules, cost, and administrator approval. No unsolicited private messages, user-account sessions, participant harvesting, joining groups, or automatic retries. No paid posting.

## Connect
Create a bot using https://t.me/BotFather (/newbot). Keep privacy mode enabled; posting does not require disabling it. Store TELEGRAM_BOT_TOKEN in a private secret manager (never chat/Git). Ask admins to add the bot with the minimum posting permissions. Record approval reference, scope, chat ID, free status, time, expiration and stricter group rules privately. Do not grant broad admin privileges unless required for an owned channel.

## Current code
From parcel-store/marketing run python publisher.py (dry-run; no network), and python -m unittest -v test_publisher (mocked Telegram). A real send requires --send, TELEGRAM_BOT_TOKEN, an absolute SAM_MARKETING_DB path on a persistent private disk, and SAM_APPROVED_PUBLICATION JSON. Fields: job_id, chat_id (negative group/channel ID), approved=true, free_confirmed=true, approval_reference, scheduled_at, approval_expires_at (timezone-aware ISO), contact (@public username), optional photo_file_id (from this bot). One explicitly approved job per call, duplicate attempts blocked, minimum three days between attempts in the same chat, unknown result requires review. No automatic recurrence configured. Operator must apply stricter chat rules and verify the advertised items and delivery terms before granting approval. No real token, private approval data, or database in Git.

## Future
Add durable serverless DB and scheduling after the free hosting solution and bot connection are available. GitHub scheduled workflows only run on the default branch, and an ephemeral runner cannot safely hold publication logs. Do not enable cron until durable state, consent, stopping rules and actual credentials are validated. User can schedule authorized personal posts with Telegram's native schedule option meanwhile.
