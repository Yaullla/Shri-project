# Verification and installation

GitHub Actions runs dependency installation and tests in ephemeral Linux runners.
It does not spend model tokens, deploy a server or configure your actual Codex
workspace. The CI optimizer matrix installs one tool at a time in a temporary
home and deletes it afterward.

- FastMCP 4.2.6: uv sync --python 3.13
- RTK OSS 1.2.1: verified Linux archive SHA-256 in scripts/verify_optimizer.sh.
- Serena 2.1.0: pinned Git commit 5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc.
- Context Mode 2.2.3: pinned npm version; Node >=24.15.0.
- Codex CLI 0.172.0: npm package for isolated setup check.

In a network-enabled Codex workspace, from the repository root:
    uv sync --python 3.13
    uv run pytest -q
    uv run python scripts/mcp_smoke.py
    codex mcp add radar -- uv run python -m radar.server
    codex mcp list

Run the isolated checks individually on Linux x86-64:
    bash scripts/verify_optimizer.sh rtk
    bash scripts/verify_optimizer.sh serena
    bash scripts/verify_optimizer.sh context-mode

These are preflight checks, not a security audit or a persistent install. For
persistent use, install approved packages into the target development environment
after reviewing logs and licenses; register MCPs with the target Codex client.
RTK OSS avoids the BUSL engine. Context Mode's Elastic license restricts hosted
service use; keep it internal. Serena is GPL. No provider proxy or AI credentials
are needed for the tests. Generate and review uv.lock before production deployment.

Upstream references:
https://github.com/rtk-ai/rtk/tree/v1.2.1
https://github.com/oraios/serena/tree/v2.1.0
https://github.com/mksglu/context-mode/tree/v2.2.3
https://github.com/PrefectHQ/fastmcp/tree/v4.2.6
