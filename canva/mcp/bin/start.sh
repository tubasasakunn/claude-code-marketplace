#!/usr/bin/env bash
#
# canva-mcp の起動口。marketplace は node_modules を配らないので、
# 依存が無ければここで入れてから server.mjs を exec する（uv run 相当の役割）。
#
# stdout は MCP の JSON-RPC チャネルなので、npm の出力は必ず stderr へ逃がす。
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

if [ ! -d "node_modules/@modelcontextprotocol/sdk" ]; then
  echo "[canva-mcp] 依存を取得します（初回のみ）…" >&2
  npm install --omit=dev --no-fund --no-audit >&2
fi

exec node server.mjs
