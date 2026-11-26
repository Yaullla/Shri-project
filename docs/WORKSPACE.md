# Buyer workspace v0.4

Open web/index.html directly for offline use or run:

    uv sync --python 3.13
    uv run uvicorn radar.web:app --host 127.0.0.1 --port 8000

Then visit http://127.0.0.1:8000. API docs: /docs.
The UI uses the existing margin engine and reads the local SQLite database
when the API is available. Empty database: two archived observations from
CI run 45862565971 are shown as unreviewed, not current prices.
Scenario prices are explicitly fictional. Local favorites, booking requests
and financial entries live in browser storage only. No real reservations,
payments, subscriptions, authentication or multi-tenant isolation.
Do not deploy this development server publicly. HTML/CSS/JS is temporary;
React/shadcn migration remains pending. Calendar dates requiring verification
are labeled accordingly. No LLM requests or external UI CDN dependencies.
