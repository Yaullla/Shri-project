#!/usr/bin/env bash
# Persistent per-project installation. No sudo or API keys. Linux x86-64.
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
if [[ "$(uname -s)" != Linux || "$(uname -m)" != x86_64 ]]; then
  echo "Use Linux x86_64 (including WSL) for this installer." >&2; exit 2
fi
for tool in uv node npm curl git sha256sum tar; do command -v "$tool" >/dev/null || { echo "Missing prerequisite: $tool" >&2; exit 2; }; done
node -e 'let [a,b,c]=process.versions.node.split(".").map(Number); if(a<24||(a===24&&b<15)) process.exit(1)' || { echo "Node >=24.15 required" >&2; exit 2; }
tools="$root/.radar-tools"
mkdir -p "$tools/bin"
export UV_TOOL_DIR="$tools/uv-tools" UV_TOOL_BIN_DIR="$tools/bin"
export PATH="$tools/bin:$tools/npm/node_modules/.bin:$PATH"
uv sync --python 3.13
uv run pytest -q
uv run python scripts/mcp_smoke.py
uv run ruff check radar tests scripts
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
curl -fsSL --retry 2 --max-time 120 https://github.com/rtk-ai/rtk/releases/download/v1.2.1/rtk-oss-x86_64-unknown-linux-musl.tar.gz -o "$tmp/rtk.tar.gz"
echo "44aa460c4827d206d11405c652832c9f7082edccfbc3a9f15a69a851e8a9e8b4  $tmp/rtk.tar.gz" | sha256sum -c -
mkdir "$tmp/extracted"
tar --no-same-owner -xzf "$tmp/rtk.tar.gz" -C "$tmp/extracted"
binary="$(find "$tmp/extracted" -type f \( -name rtk -o -name rtk-oss \) -print -quit)"
test -n "$binary"
install -m 0755 "$binary" "$tools/bin/rtk"
rtk --version
uv tool install --python 3.13 --from 'git+https://github.com/oraios/serena.git@5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc' serena-agent
serena start-mcp-server --help >/dev/null
npm install --prefix "$tools/npm" --no-audit --no-fund @openai/codex@0.172.0 context-mode@2.2.3
codex --version
context-mode --version
printf 'export PATH=%q:$PATH\n' "$tools/bin:$tools/npm/node_modules/.bin" > "$tools/activate.sh"
echo "Installed locally. Activate: source .radar-tools/activate.sh"
echo "No global config or automatic hooks changed."
echo "For Codex registration: bash scripts/register_codex.sh"
