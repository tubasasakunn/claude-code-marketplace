#!/usr/bin/env bash
#
# 自動化用プロファイル（コピー済み）でデバッグ起動。
# 普段使いの Chrome とは別ディレクトリなので、普段の Chrome を閉じる必要はない。
#
# 前提: 先に ./setup_profile.sh を1回実行してコピーを作っておくこと。
#
set -euo pipefail

PORT="${CDP_PORT:-9222}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DST="${HOME}/Library/Application Support/Google/Chrome-automation"

if curl -s "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  echo "既にポート ${PORT} で待ち受け中です。"
  exit 0
fi

if [ ! -d "${DST}/Default" ]; then
  echo "自動化用プロファイルがありません。先に ./setup_profile.sh を実行してください。" >&2
  exit 1
fi

# 自動化用ポートを掴む古いプロセスがあれば終了
pkill -f "user-data-dir=${DST}" 2>/dev/null || true
sleep 1

echo "デバッグ起動（ポート ${PORT}）…"
"${CHROME}" \
  --remote-debugging-port="${PORT}" \
  --user-data-dir="${DST}" \
  --profile-directory="Default" \
  --no-first-run --no-default-browser-check \
  about:blank >/dev/null 2>&1 &

for _ in $(seq 1 40); do
  if curl -s "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
    echo "✅ 起動完了。ポート ${PORT} で接続できます。"
    exit 0
  fi
  sleep 0.4
done

echo "❌ デバッグポートの待ち受け確認に失敗しました。" >&2
exit 1
