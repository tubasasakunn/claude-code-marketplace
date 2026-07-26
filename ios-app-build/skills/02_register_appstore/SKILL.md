---
name: 02_register_appstore
description: App Store Connect の初期登録を API で全部済ませます。価格（無料）、配信地域、年齢レーティング、コンテンツ配信権、審査連絡先、そしてアプリのプライバシー宣言（データ収集なし）。01_create_xcode_cicd でアプリレコードを作った直後に実行してください。ブラウザ操作は不要です。
---

# App Store Connect の初期登録 (02_register_appstore)

## このスキルの位置

```
00_setup_repo → 01_create_xcode_cicd → [02_register_appstore] → 03_implement_app → ...
```

`01` で **appId** が取れていることが前提。

## 何をするか

App Store の審査に出すには、アプリレコードの他に以下が全部埋まっている必要がある。ASC の画面でポチポチする作業だが、**すべて API でできる**（プライバシーだけは iris 経由。後述）。

| 項目 | 経路 | 冪等か |
|---|---|---|
| 価格（無料） | 公式 API `appPriceSchedules` | 再実行で上書き |
| 配信地域 | 公式 API `v2/appAvailabilities` | 再実行で上書き |
| 年齢レーティング | 公式 API `ageRatingDeclarations` | 冪等（PATCH） |
| コンテンツ配信権 | 公式 API `apps` の PATCH | 冪等 |
| 審査連絡先 | 公式 API `appStoreReviewDetails` | 既にあれば 409 |
| **アプリのプライバシー** | **harness の iris プロキシ** | 冪等 |

## 準備

```bash
export ASC_API=${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js
export HARNESS_TOKEN=$(grep '^API_TOKEN=' ~/workspace/harness/.env | cut -d= -f2-)

APP_ID=<01 で取得した appId>
```

`${CLAUDE_PLUGIN_ROOT}/scripts/README.md` の認証設定を先に済ませておくこと。

## JSON:API の「ローカル ID」記法 ★Step 1・2 の前に必ず読む

まだ存在しないリソースを同じリクエストで一緒に作るとき、ASC は **`${なにか}` という形の仮 ID** を要求する。
`$` と `{}` を含む**リテラル文字列**であって、シェルやテンプレートの変数展開ではない。

```json
"manualPrices": { "data": [{ "type": "appPrices", "id": "${price1}" }] },
"included": [{ "type": "appPrices", "id": "${price1}", ... }]
```

`"price1"` のように素朴な文字列にすると次のエラーで弾かれる。

```
409 ENTITY_ERROR.INCLUDED.INVALID_ID
must be a local id with the format '${local-id}'
```

以下のスニペットで `\${price1}` と書いてあるのは、**bash のダブルクォート内で `$` をエスケープして
`${price1}` という文字列を Python に渡すため**。この `\` を外してはいけない。

## Step 1. 価格を設定する（無料）

`appPricePoints` から `customerPrice == "0"` の id を探し、それで価格スケジュールを作る。ベース地域は日本（`JPN`）。

```bash
node $ASC_API GET "/v1/apps/$APP_ID/appPricePoints?filter%5Bterritory%5D=JPN&limit=1" | python3 -c "
import json, sys
status, body = sys.stdin.read().split('\n', 1)
pp = json.loads(body)['data'][0]
assert pp['attributes']['customerPrice'] == '0', pp['attributes']
body = {'data': {'type': 'appPriceSchedules', 'relationships': {
  'app': {'data': {'type': 'apps', 'id': '$APP_ID'}},
  'baseTerritory': {'data': {'type': 'territories', 'id': 'JPN'}},
  'manualPrices': {'data': [{'type': 'appPrices', 'id': '\${price1}'}]}
}}, 'included': [{'type': 'appPrices', 'id': '\${price1}', 'attributes': {'startDate': None},
  'relationships': {'appPricePoint': {'data': {'type': 'appPricePoints', 'id': pp['id']}}}}]}
open('/tmp/price_body.json', 'w').write(json.dumps(body))
print('free price point ok')
"

node $ASC_API POST /v1/appPriceSchedules "$(cat /tmp/price_body.json)" | head -1
```

`201` が返れば成功。

> `appPricePoints` の id は非常に長い base64。**必ず API から取った値をそのまま使う**（手で組み立てない）。

## Step 2. 配信地域を設定する（全世界）

```bash
node $ASC_API GET "/v1/territories?limit=200" | python3 -c "
import json, sys
status, body = sys.stdin.read().split('\n', 1)
ids = [t['id'] for t in json.loads(body)['data']]
body = {'data': {'type': 'appAvailabilities', 'attributes': {'availableInNewTerritories': True},
  'relationships': {
    'app': {'data': {'type': 'apps', 'id': '$APP_ID'}},
    'territoryAvailabilities': {'data': [{'type': 'territoryAvailabilities', 'id': f'\${{ta{i}}}'} for i in range(len(ids))]}
  }},
  'included': [{'type': 'territoryAvailabilities', 'id': f'\${{ta{i}}}', 'attributes': {'available': True},
    'relationships': {'territory': {'data': {'type': 'territories', 'id': t}}}} for i, t in enumerate(ids)]}
open('/tmp/avail_body.json', 'w').write(json.dumps(body))
print(f'{len(ids)} territories')
"

# v2 であることに注意（v1 ではない）
node $ASC_API POST /v2/appAvailabilities "$(cat /tmp/avail_body.json)" | head -1
```

## Step 3. 年齢レーティングを設定する

レーティングは **appInfos 経由**でしか触れない。`/v1/ageRatingDeclarations/{id}` を直接 GET すると 403 になる。

```bash
# appInfo id を取る（これが ageRatingDeclaration の id でもある）
node $ASC_API GET "/v1/apps/$APP_ID/appInfos?limit=1" | python3 -c "
import json,sys; s,b=sys.stdin.read().split('\n',1); print(json.loads(b)['data'][0]['id'])
"
# → APPINFO_ID

# 現在の属性一覧を取り、全部「無害」の値で埋めた PATCH を組み立てる
node $ASC_API GET "/v1/appInfos/<APPINFO_ID>/ageRatingDeclaration" | python3 -c "
import json, sys
status, body = sys.stdin.read().split('\n', 1)
d = json.loads(body)['data']
attrs = d['attributes']
answers = {}
BOOLEAN_KEYS = {'gambling','lootBox','unrestrictedWebAccess','advertising','userGeneratedContent',
                'messagingAndChat','parentalControls','ageAssurance','healthOrWellnessTopics'}
SKIP = {'ageRatingOverride','ageRatingOverrideV2','kidsAgeBand','koreaAgeRatingOverride'}
for k in attrs:
    if k in SKIP: continue
    if k == 'developerAgeRatingInfoUrl': answers[k] = None
    elif k in BOOLEAN_KEYS: answers[k] = False
    else: answers[k] = 'NONE'
open('/tmp/rating.json','w').write(json.dumps({'data':{'type':'ageRatingDeclarations','id':d['id'],'attributes':answers}}))
print('keys:', len(answers))
"

node $ASC_API PATCH "/v1/ageRatingDeclarations/<APPINFO_ID>" "$(cat /tmp/rating.json)" | head -1
```

`200` なら成功（4+ 相当）。

> **2025年以降に増えた設問は Boolean と文字列が混在している。** `healthOrWellnessTopics` などは `NONE` を送ると
> `Expected a BOOLEAN but got STRING` で 409 になる。上のスクリプトのように、実際に GET した属性一覧をもとに
> 型を振り分けること。**属性を一部だけ送ると「必須属性が足りない」で 409 になる**ので、必ず全部送る。

## Step 4. コンテンツ配信権

第三者コンテンツを含まないアプリなら:

```bash
node $ASC_API PATCH "/v1/apps/$APP_ID" '{"data":{"type":"apps","id":"'"$APP_ID"'","attributes":{"contentRightsDeclaration":"DOES_NOT_USE_THIRD_PARTY_CONTENT"}}}' | head -1
```

BGM・フォント・スタンプなど他人の素材を収録するなら `USES_THIRD_PARTY_CONTENT`。

## Step 5. 審査連絡先

版（appStoreVersion）に紐づく。**既存のリリース済みアプリから実値をそのまま写す**（新規に考えない）。

```bash
REF_APP=6789139306   # 既存アプリ（Nagasu）の appId。GET しかしない

# 1) 既存アプリの版 id
REF_VID=$(node $ASC_API GET "/v1/apps/$REF_APP/appStoreVersions?limit=1" | python3 -c "
import json,sys; s,b=sys.stdin.read().split('\n',1); print(json.loads(b)['data'][0]['id'])
")

# 2) 連絡先を読む。エンドポイントは単数形 appStoreReviewDetail（作成時の複数形とは別物）
node $ASC_API GET "/v1/appStoreVersions/$REF_VID/appStoreReviewDetail" | python3 -c "
import json,sys; s,b=sys.stdin.read().split('\n',1); a=json.loads(b)['data']['attributes']
import pathlib; pathlib.Path('/tmp/contact.json').write_text(json.dumps(a))
print(a['contactFirstName'], a['contactLastName'], a['contactEmail'])
"

# 3) 対象アプリの版 id
VID=$(node $ASC_API GET "/v1/apps/$APP_ID/appStoreVersions?limit=1" | python3 -c "
import json,sys; s,b=sys.stdin.read().split('\n',1); print(json.loads(b)['data'][0]['id'])
")

# 4) 写して作る。作成は複数形 appStoreReviewDetails
python3 -c "
import json
a = json.load(open('/tmp/contact.json'))
body = {'data': {'type': 'appStoreReviewDetails', 'attributes': {
  'contactFirstName': a['contactFirstName'], 'contactLastName': a['contactLastName'],
  'contactPhone': a['contactPhone'], 'contactEmail': a['contactEmail'],
  'demoAccountRequired': False,
  'notes': 'This app is a fully offline personal utility. No account, no server communication. All data stays on device.'
}, 'relationships': {'appStoreVersion': {'data': {'type': 'appStoreVersions', 'id': '$VID'}}}}}
open('/tmp/review_detail.json','w').write(json.dumps(body))
"
node $ASC_API POST /v1/appStoreReviewDetails "$(cat /tmp/review_detail.json)" | head -1
```

- **読み取りは単数形 `appStoreReviewDetail`、作成は複数形 `appStoreReviewDetails`。** 間違えると 404
- 電話番号は **E.164 形式**（`+81` 始まり）でないと弾かれる
- 既に作られていれば 409。その場合は PATCH で更新する

## Step 6. アプリのプライバシー宣言 ★公式 API に存在しない

**ここだけは公式 API にエンドポイントが無い**（`GET /v1/apps/{id}/appDataUsages` は 404）。
ASC の内部 API（iris）にはあるが、**iris は ASC API キーの JWT を受け付けない**（401）。ログイン Cookie でしか認証できない。

そこで harness に保管したセッションを経由する。

```bash
# セッションが生きているか
curl -s https://harness.basaapp.com/api/asc/session/validate -H "Authorization: Bearer $HARNESS_TOKEN"
# → {"valid":true,"status":200}
```

`valid: false` なら Cookie が切れている。**下の「セッションの再取得」を先にやる。**

```bash
# データ収集なしを宣言して公開する（冪等。既に宣言済みなら作成をスキップする）
curl -s -X POST https://harness.basaapp.com/api/asc/privacy/data-not-collected \
  -H "Authorization: Bearer $HARNESS_TOKEN" -H "Content-Type: application/json" \
  -d "{\"appId\":\"$APP_ID\"}" | python3 -c "
import json,sys; d=json.load(sys.stdin)
print('ok:', d.get('ok'), '| created:', d.get('created'), '| count:', d.get('dataUsageCount'), '| published:', d.get('published'))
"

# 必ず独立したエンドポイントで裏を取る
curl -s "https://harness.basaapp.com/api/asc/privacy/state?appId=$APP_ID" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys; d=json.load(sys.stdin); print('published:', d['published'], '| count:', d['dataUsageCount'])
"
```

`published: true` かつ `dataUsageCount: 1` なら完了。

> POST のレスポンスの `published` は、最後の確認 GET が ASC 側の 5xx で失敗すると `null` になりうる。
> **`published: null` は「失敗」ではない。** 上の `privacy/state` で確かめること。

> **この宣言は「アプリが一切データを収集しない」場合のみ正しい。** サーバ通信・解析 SDK・広告 SDK を1つでも入れているなら、
> このエンドポイントを使ってはいけない（虚偽申告になる）。その場合は ASC の画面で正直に回答する。

### セッションの再取得（Cookie は30日程度で切れる）

Apple ID のログインが要る。2FA があるので**自動化できない。ユーザに依頼する**。

```bash
# 1) リレーのセッションを作る
curl -s -X POST https://harness.basaapp.com/api/relay/session -H "Authorization: Bearer $HARNESS_TOKEN" -H "Content-Type: application/json" -d '{}'
# → {"key":"...","url":"https://harness.basaapp.com/relay/..."}

# 2) ログイン済み Chrome を CDP 付きで起動しておく（ポート 9222）
#    ${CLAUDE_PLUGIN_ROOT}/skills/canva-image-gen/scripts/launch_chrome.sh

# 3) ローカルエージェントを起動して Mac の画面をリレーする
cd ~/workspace/harness
HARNESS_TOKEN=$HARNESS_TOKEN node scripts/relay-agent.mjs --key <key> \
  --base https://harness.basaapp.com --cdp http://localhost:9222 --url-match appstoreconnect.apple.com

# 4) ユーザに URL を LINE で送る（スマホでログインしてもらう）
curl -s -X POST https://harness.basaapp.com/api/line/push -H "Authorization: Bearer $HARNESS_TOKEN" \
  -H "Content-Type: application/json" -d '{"messages":[{"type":"text","text":"ASCログインをお願いします: <url>"}]}'

# 5) ログイン後、Cookie を harness に保管する
HARNESS_TOKEN=$HARNESS_TOKEN node scripts/asc-session-capture.mjs --base https://harness.basaapp.com --cdp http://localhost:9222

# 6) リレーを破棄する（パスワードが通る経路なので放置しない）
curl -s -X DELETE https://harness.basaapp.com/api/relay/session/<key> -H "Authorization: Bearer $HARNESS_TOKEN"
```

## Step 7. 全部入ったか確認する

**`GET /v1/apps/{id}/appPriceSchedule` のような「関連リソース」への GET は、中身が空でも 200 を返す。**
件数まで見ないと検証にならない。下は中身を数えるところまでやる。

```bash
echo "--- 価格（1件あるか）"
node $ASC_API GET "/v1/appPriceSchedules/$APP_ID/manualPrices?limit=5" | tail -n +2 | python3 -c "
import json,sys; d=json.load(sys.stdin); print('prices:', len(d['data']))"

echo "--- 配信地域（175件前後あるか）"
node $ASC_API GET "/v2/appAvailabilities/$APP_ID/territoryAvailabilities?limit=200" | tail -n +2 | python3 -c "
import json,sys; d=json.load(sys.stdin); print('territories:', d['meta']['paging']['total'])"

echo "--- 配信権"
node $ASC_API GET "/v1/apps/$APP_ID?fields%5Bapps%5D=contentRightsDeclaration" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data']['attributes'])"

echo "--- レーティング（全部 NONE/false か）"
APPINFO=$(node $ASC_API GET "/v1/apps/$APP_ID/appInfos?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
node $ASC_API GET "/v1/appInfos/$APPINFO/ageRatingDeclaration" | tail -n +2 | python3 -c "
import json,sys; a=json.load(sys.stdin)['data']['attributes']
bad = {k: v for k, v in a.items() if v not in (None, 'NONE', False)}
print('non-default:', bad or 'none')"

echo "--- 審査連絡先"
VID=$(node $ASC_API GET "/v1/apps/$APP_ID/appStoreVersions?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
node $ASC_API GET "/v1/appStoreVersions/$VID/appStoreReviewDetail" | tail -n +2 | python3 -c "
import json,sys; a=json.load(sys.stdin)['data']['attributes']; print(a['contactEmail'], a['contactPhone'][:5] + '****')"

echo "--- プライバシー"
curl -s "https://harness.basaapp.com/api/asc/privacy/state?appId=$APP_ID" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys; d=json.load(sys.stdin); print('published:', d['published'], '| count:', d['dataUsageCount'])"
```

## 完了条件

- [ ] 価格スケジュールが作成されている（無料）
- [ ] 配信地域が設定されている
- [ ] 年齢レーティングの PATCH が 200
- [ ] `contentRightsDeclaration` が設定されている
- [ ] 審査連絡先が作成されている（201 か、既存で 409）
- [ ] プライバシー: `published: true` / `dataUsageCount: 1`

## トラブルシューティング

### ASC API が 500 を返す

**どのエンドポイントでも起こる。** 実測では `appPricePoints` の GET、`ageRatingDeclarations` の PATCH、
`apps` の PATCH、`appStoreReviewDetail` の GET、iris プロキシまで、断続的に 500 が出た（多いもので6回連続）。
数秒〜十数秒のリトライで解消する。**全ての呼び出しをリトライ前提で書くこと。**

「作成済みかを GET で確認 → 無ければ作成」の順にすれば、二重作成せずに再試行できる。

```bash
retry() {  # retry <回数> <コマンド...>
  local n=$1; shift
  for i in $(seq 1 "$n"); do "$@" && return 0; sleep 5; done
  return 1
}
retry 6 node $ASC_API GET "/v1/apps/$APP_ID"
```

`asc_api.js` は 4xx/5xx で終了コード 1 を返すので、上のように `retry` で包める。

### レーティングの PATCH が 409

エラーメッセージの `detail` を読む。`You must provide a value for the attribute 'X'` なら、その属性が抜けている（全部送る）。
`Expected a BOOLEAN but got STRING` なら、その属性を `false` に変える。

### プライバシーが 401

`{"error":"ASC session expired or invalid"}` が返る。Cookie 切れ。上の「セッションの再取得」へ。

## 次のスキル

`03_implement_app` — CONCEPT.md / DESIGN.md に沿って P0 を実装する。
