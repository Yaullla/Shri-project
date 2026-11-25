#!/usr/bin/env bash
# Register in the active Codex config; never changes existing same-name entries.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
source .radar-tools/activate.sh
uv_bin="$(command -v uv)"
serena_bin="$(command -v serena)"
if ! codex mcp get radar >/dev/null 2>&1; then
  codex mcp add radar -- "$uv_bin" --directory "$root" run python -m radar.server
fi
if ! codex mcp get serena >/dev/null 2>&1; then
  codex mcp add serena -- "$serena_bin" start-mcp-server --context codex --project "$root" --enable-web-dashboard false --enable-gui-log-window false --open-web-dashboard false
fi
codex mcp list
echo "RTK manual: rtk git status; rtk gain"
echo "Context Mode hooks remain opt-in: context-mode setup --agents codex"
echo "Review the plan before applying. Do not enable overlapping hooks blindly."
