#!/bin/bash
# アプリ → ciProduct の対応表を出力する。
#
# Xcode Cloud のウィザードは、**既存の ciProduct を別のアプリに付け替えてしまうこと**がある
# （実測: Nagasu 用の product が、Bide のウィザード実行で Bide に上書きされた）。
# ウィザードを回す前と後でこれを取り、差分が出ていないか必ず確認すること。
#
#   ./ciproduct_snapshot.sh > /tmp/before.txt
#   （Xcode のウィザードを実行）
#   ./ciproduct_snapshot.sh > /tmp/after.txt
#   diff /tmp/before.txt /tmp/after.txt
#
# 差分は「対象アプリの行が1行増える」だけであるべき。
# 既存アプリの行が消えたり別 bundle id に変わっていたら、付け替えが起きている。

set -euo pipefail
ASC_API="$(dirname "$0")/asc_api.js"

node "$ASC_API" GET "/v1/ciProducts?limit=200&include=app&fields%5BciProducts%5D=name,app&fields%5Bapps%5D=bundleId" \
  | tail -n +2 \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
apps = {i['id']: i['attributes']['bundleId'] for i in d.get('included', []) if i['type'] == 'apps'}
rows = []
for p in d['data']:
    rel = (p.get('relationships') or {}).get('app', {}).get('data')
    bundle = apps.get(rel['id']) if rel else '(no app)'
    rows.append(f\"{bundle}\t{p['id']}\t{p['attributes']['name']}\")
for r in sorted(rows):
    print(r)
"
