# Local access setup (v0.5.1)

Run from the repository root in a private Linux/WSL terminal:

    uv sync --python 3.13
    read -rsp 'Admin password (16+ characters): ' RADAR_ADMIN_PASSWORD; echo
    export RADAR_ADMIN_PASSWORD
    read -rsp 'Traveler password (16+ characters): ' RADAR_TRAVELER_PASSWORD; echo
    export RADAR_TRAVELER_PASSWORD
    uv run python -m radar.seed_communities
    uv run uvicorn radar.web:app --host 127.0.0.1 --port 8000

Open /admin with username admin and /travel with username traveler.
Use independent strong passwords, never commit them. Unset the variables
after use. Public buyer page remains local. This is a single-operator preview:
HTTP Basic is only for localhost; do not deploy publicly. Real accounts,
row ownership, sessions, CSRF, HTTPS, rate limits, audit logs and operational
security review remain necessary. No contact details of members are collected.
The seed only records publicly listed community metadata; group descriptions
may change and permission must be confirmed separately. No messages are sent.
