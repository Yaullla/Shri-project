# Local publication queue
Zero extra hosting cost, provided your Windows PC remains online. Python standard library only.
1. Copy queue.example.json to a private directory OUTSIDE the Git repository, as queue.json.
2. Set SAM_MARKETING_PRIVATE_DIR to that absolute directory, and TELEGRAM_BOT_TOKEN securely in the local environment. Vercel's sensitive secret is not downloaded or copied.
3. From parcel-store/marketing, run python scheduler.py for a dry-run. No messages are sent.
4. For each approved job record chat_id, approval reference, expiration, contact username and explicit date/time. Use only free placements expressly approved by admins for the bot and campaign. Apply stricter group rules. Never store private approvals or credentials in Git.
5. Run python scheduler.py --send --watch for a local persistent scheduler. It checks once per minute, sends at most one job per tick, skips expired jobs, and uses the same SQLite duplicate guard as publisher.py. Do not run multiple instances. Stop using Ctrl+C or by creating the STOP file in the private directory. Setting enabled=false pauses the queue. No automatic recurrence.
6. Images require a Telegram photo_file_id from this bot; do not insert a guessed value. Unknown send results must be inspected manually.
Current queue example intentionally has no jobs. No actual sending or continuous runner is provisioned.
