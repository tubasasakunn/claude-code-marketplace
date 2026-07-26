#!/bin/bash
# LINE でユーザに問いを投げ、返信が来るまで待って、その本文を返す。
#
#   ./line_ask.sh "アプリ名 Bide が取られています。別案は？"
#   ./line_ask.sh --wait-only            送信せず、新しい返信だけ待つ
#   ./line_ask.sh --timeout 1800 "..."   待つ上限（既定 1800 秒）
#
# 仕組み: 送信の直前に「今の最新メッセージの timestamp」を控え、
# それより新しいメッセージが現れるまでポーリングする。harness 側に既読管理は要らない。
#
# 返信が来たら本文を stdout に出して 0 で終了。時間切れなら 1 で終了。
#
# **フォアグラウンドで長く待たない。** バックグラウンド実行して、完了通知で起きること。

set -uo pipefail

HARNESS="${HARNESS_BASE:-https://harness.basaapp.com}"
TOKEN="${HARNESS_TOKEN:-$(grep '^API_TOKEN=' ~/workspace/harness/.env | cut -d= -f2-)}"
USER_ID="${LINE_USER_ID:-Ud7ce4f62dfa2a91ad878e6ee1a63e2a6}"
INTERVAL="${LINE_POLL_INTERVAL:-20}"
TIMEOUT=1800
WAIT_ONLY=0

while [ $# -gt 0 ]; do
  case "$1" in
    --wait-only) WAIT_ONLY=1; shift ;;
    --timeout) TIMEOUT="$2"; shift 2 ;;
    *) break ;;
  esac
done

latest_ts() {
  curl -s "$HARNESS/api/line/users/$USER_ID/messages?limit=1" \
    -H "Authorization: Bearer $TOKEN" \
    | python3 -c "
import json,sys
try:
    ms = json.load(sys.stdin)['messages']
    print(ms[0]['timestamp'] if ms else 0)
except Exception:
    print(0)
"
}

BASE_TS=$(latest_ts)

if [ "$WAIT_ONLY" -eq 0 ]; then
  [ $# -ge 1 ] || { echo "usage: line_ask.sh [--wait-only] [--timeout N] <message>" >&2; exit 2; }
  MSG="$1"
  BODY=$(python3 -c "
import json,sys
print(json.dumps({'messages': [{'type': 'text', 'text': sys.argv[1]}]}, ensure_ascii=False))
" "$MSG")
  curl -s -X POST "$HARNESS/api/line/push" \
    -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -d "$BODY" > /dev/null || { echo "push に失敗しました" >&2; exit 2; }
fi

DEADLINE=$(( $(date +%s) + TIMEOUT ))
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  sleep "$INTERVAL"
  REPLY=$(curl -s "$HARNESS/api/line/users/$USER_ID/messages?limit=5" \
    -H "Authorization: Bearer $TOKEN" \
    | python3 -c "
import json,sys
base = int(sys.argv[1])
try:
    ms = json.load(sys.stdin)['messages']
except Exception:
    sys.exit(1)
# 新しい順に並ぶ。base より新しいテキストのうち、最も古いもの（＝最初の返信）を返す。
fresh = [m for m in ms if int(m.get('timestamp', 0)) > base and m.get('message', {}).get('type') == 'text']
if not fresh:
    sys.exit(1)
print(fresh[-1]['message']['text'])
" "$BASE_TS") && { printf '%s\n' "$REPLY"; exit 0; }
done

echo "TIMEOUT: ${TIMEOUT}秒待ちましたが返信がありません" >&2
exit 1
