#!/usr/bin/env bash
# Use only in an isolated development environment without secrets.
set -euo pipefail
tool="${1:?rtk, serena or context-mode}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
export HOME="$work/home"
export CODEX_HOME="$HOME/.codex"
export XDG_CONFIG_HOME="$HOME/.config"
export XDG_CACHE_HOME="$HOME/.cache"
mkdir -p "$HOME" "$CODEX_HOME" "$work/bin"
export PATH="$work/bin:$PATH"
case "$tool" in
  rtk)
    curl -fsSL --retry 2 --max-time 120       https://github.com/rtk-ai/rtk/releases/download/v1.2.1/rtk-oss-x86_64-unknown-linux-musl.tar.gz       -o "$work/rtk.tar.gz"
    echo "44aa460c4827d206d11405c652832c9f7082edccfbc3a9f15a69a851e8a9e8b4  $work/rtk.tar.gz" | sha256sum -c -
    mkdir "$work/extracted"
    tar --no-same-owner -xzf "$work/rtk.tar.gz" -C "$work/extracted"
    binary="$(find "$work/extracted" -type f \( -name rtk -o -name rtk-oss \) -print -quit)"
    test -n "$binary"
    install -m 0755 "$binary" "$work/bin/rtk"
    rtk --version
    git status --short
    rtk git status
    rtk gain
    ;;
  serena)
    export UV_TOOL_DIR="$work/uv-tools" UV_TOOL_BIN_DIR="$work/bin"
    uv tool install --python 3.13 --from 'git+https://github.com/oraios/serena.git@5e4f5cd173c7ff3eed37ee3f1de6c266b937c5dc' serena-agent
    serena --help
    serena start-mcp-server --help
    ;;
  context-mode)
    npm install --prefix "$work/npm" --no-audit --no-fund @openai/codex@0.172.0 context-mode@2.2.3
    export PATH="$work/npm/node_modules/.bin:$PATH"
    codex --version
    context-mode --help
    context-mode setup --agents codex
    codex mcp list
    ;;
  *) echo "Unknown optimizer" >&2; exit 2 ;;
esac
