#!/usr/bin/env bash
# Optional remote development check; no deployment, credentials or global config.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
if [[ "$(uname -s)" != Linux ]]; then
  echo "Run inside Cloud Shell or another Linux development environment." >&2
  exit 2
fi
for tool in git uv curl; do
  command -v "$tool" >/dev/null || {
    echo "Missing prerequisite: $tool. See docs/GSHELL.md." >&2
    exit 2
  }
done
echo "Commit: $(git rev-parse --short HEAD)"
df -h "$root"
uv --version
curl -fsSI --connect-timeout 10 --max-time 20 https://github.com/ >/dev/null
echo "GitHub HTTPS reachable"
if [[ -f uv.lock ]]; then
  uv sync --locked --python 3.13
else
  echo "No uv.lock yet; dependency resolution is for development only." >&2
  uv sync --python 3.13
fi
uv run --no-sync pytest -q
uv run --no-sync python scripts/mcp_smoke.py
uv run --no-sync ruff check radar tests scripts
echo "Cloud development checks passed; no services deployed."
