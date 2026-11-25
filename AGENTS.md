# Engineering rules

Use deterministic Python/SQL for price matching, filters and cost arithmetic.
Use agents only for ambiguous matching, research and development. Keep output
bounded and do not load entire logs when a focused excerpt suffices.
GitHub-first: compare mature projects, recent maintenance, licenses, security
and relevant tests; stars alone are not proof. Pin approved releases and hashes.
Before integrating a tool, measure baseline and individual impact. RTK OSS is
the first CLI candidate. Serena and Context Mode are isolated development tools;
do not combine automatic hooks before testing conflicts. Do not connect model
proxies or export context without approval. Do not store credentials, client
data, or private strategy in Git. No n8n. Separate live data from reviewed
snapshots and demo data. Never claim unverified sources or installations work.
