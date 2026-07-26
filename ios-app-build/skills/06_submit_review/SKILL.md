---
name: 06_submit_review
description: iOSアプリを App Store の審査に提出します。production ブランチへのマージで GitHub Actions が Xcode Cloud のビルドを掴んで提出する正規フローと、API で直接提出する手動フローの両方を扱います。提出前の必須チェックリストも含みます。
---

# 審査への提出 (06_submit_review)

## このスキルの位置

```
05_release_assets → [06_submit_review] → 07_watch_review
```

## 提出前チェック ★1つでも欠けると弾かれる

```bash
export ASC_API=${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js
export HARNESS_TOKEN=$(grep '^API_TOKEN=' ~/workspace/harness/.env | cut -d= -f2-)
APP_ID=<appId>

echo "--- 1. 審査用ビルドが VALID で入っているか"
node $ASC_API GET "/v1/builds?filter%5Bapp%5D=$APP_ID&limit=3&sort=-uploadedDate&fields%5Bbuilds%5D=version,processingState" | tail -n +2 | python3 -c "
import json,sys
for b in json.load(sys.stdin)['data']: print(' build', b['attributes']['version'], b['attributes']['processingState'])"

echo "--- 2. プライバシー宣言が公開済みか"
curl -s "https://harness.basaapp.com/api/asc/privacy/state?appId=$APP_ID" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys; d=json.load(sys.stdin); print(' published:', d['published'])"

echo "--- 3. 価格・配信地域"
node $ASC_API GET "/v1/appPriceSchedules/$APP_ID/manualPrices?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(' prices:', len(json.load(sys.stdin)['data']))"
node $ASC_API GET "/v2/appAvailabilities/$APP_ID/territoryAvailabilities?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(' territories:', json.load(sys.stdin)['meta']['paging']['total'])"

echo "--- 4. 規約・サポートURLが開けるか"
for u in privacy support; do
  curl -s -o /dev/null -w " /$u: %{http_code}\n" "https://<appname>.basaapp.com/$u"
done

echo "--- 5. 版の状態"
node $ASC_API GET "/v1/apps/$APP_ID/appStoreVersions?limit=1&fields%5BappStoreVersions%5D=versionString,appStoreState" | tail -n +2 | python3 -c "
import json,sys; a=json.load(sys.stdin)['data'][0]['attributes']; print(' v'+a['versionString'], a['appStoreState'])"

echo "--- 6. primaryLocale と、空ロケールが残っていないか ★最頻の失敗原因"
node $ASC_API GET "/v1/apps/$APP_ID?fields%5Bapps%5D=primaryLocale" | tail -n +2 | python3 -c "
import json,sys; print(' primaryLocale:', json.load(sys.stdin)['data']['attributes']['primaryLocale'])"

echo "--- 7. 全ロケールの文言が埋まっているか"
VID=$(node $ASC_API GET "/v1/apps/$APP_ID/appStoreVersions?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
node $ASC_API GET "/v1/appStoreVersions/$VID/appStoreVersionLocalizations?limit=10" | tail -n +2 | python3 -c "
import json,sys
for l in json.load(sys.stdin)['data']:
    a=l['attributes']
    print(' ', a['locale'], 'desc:', len(a.get('description') or ''), 'kw:', len(a.get('keywords') or ''), 'support:', bool(a.get('supportUrl')))"
AIID=$(node $ASC_API GET "/v1/apps/$APP_ID/appInfos?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
node $ASC_API GET "/v1/appInfos/$AIID/appInfoLocalizations?limit=10" | tail -n +2 | python3 -c "
import json,sys
for l in json.load(sys.stdin)['data']:
    a=l['attributes']; print(' ', a['locale'], 'name:', bool(a.get('name')), 'privacyUrl:', bool(a.get('privacyPolicyUrl')))"
```

- ビルドが `VALID`（**提出する版に紐づくビルド**を見ること。最新3件に VALID があるだけでは不十分）
- プライバシーが `published: true`
- 価格 1件、配信地域 175件前後
- 規約・サポートが 200（ドメインは `appstore.config.json` の `marketing_domain` から取る）
- 版が `PREPARE_FOR_SALE` / `PREPARE_FOR_SUBMISSION`
- **`primaryLocale` が `ja`**（アプリの主要言語と一致）
- **ロケールが `ja` の1つだけで、`description` / `keywords` / `supportUrl` / `privacyPolicyUrl` が空でない**

`WAITING_FOR_REVIEW` や `IN_REVIEW` なら**既に提出済み**。二重提出はできない。

> **`en-US` の空ロケールが残っていると、必ず提出が弾かれる。**
> Xcode のウィザードで作ったアプリは `primaryLocale` が `en-US` になるため。
> `01_create_xcode_cicd` の「`primaryLocale` を直す」を済ませておくこと。

## 方法A. production マージで出す（正規フロー）

`appstore-release.yml` が `production` への push で発火し、fastlane が
「最新の処理済みビルドを選ぶ → メタデータ反映 → 審査提出 → 通過後に自動公開」を行う。

```bash
git checkout production
git merge main --no-edit
git push origin production
git checkout main

RUN=$(gh run list --workflow=appstore-release.yml --limit 1 --json databaseId -q '.[0].databaseId')
gh run watch "$RUN" --exit-status
```

### 落ちたときの読み方

```bash
gh run view "$RUN" --log-failed 2>&1 | grep -iE "error|Spaceship|UnexpectedResponse" | head
```

よくある失敗:

| メッセージ | 原因 | 対処 |
|---|---|---|
| `appStoreVersions with id '...' is not in valid state` + `description / keywords / supportUrl / privacyPolicyUrl が無い`、`App screenshot missing (APP_IPHONE_65)` | **`primaryLocale` が `en-US` のままで、空の英語ロケールが残っている**（実際に起きた。最頻） | `primaryLocale` を `ja` に PATCH し、`en-US` の `appStoreVersionLocalizations` を DELETE してから再実行 |
| `You must provide a value for the attribute 'contactFirstName'` | `ASC_CONTACT_*` の Secrets が未設定 | `00_setup_repo` Step 6 |
| `FileNotFoundError: .../project.pbxproj` | `sync_fastlane_metadata.py` が xcodegen 未対応 | `00_setup_repo` Step 4-2 |
| `version_already_live` でスキップ | その版は公開済み | バージョンを上げる |
| `already submitted` 系 | 既に審査中 | 下の「取り下げ」を見る |
| precheck の `support URL en-US: empty url` 警告 | 英語ロケールを使わないなら無害 | 無視してよい |

**このワークフローは何度でも安全に再実行できる**（提出済みならスキップする）。

ASC 側の設定を直しただけで再提出したいときは、**空コミットを作らずに再実行する**。

```bash
gh workflow run appstore-release.yml --ref production
gh run watch $(gh run list --workflow=appstore-release.yml --limit 1 --json databaseId -q '.[0].databaseId') --exit-status
```

## 方法B. API で直接出す（CI を通さない）

CI が使えないときや、ビルドの紐付けを自分で制御したいとき。

```bash
# 1) 版に審査用ビルドを紐付ける
VID=$(node $ASC_API GET "/v1/apps/$APP_ID/appStoreVersions?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
BUILD=$(node $ASC_API GET "/v1/builds?filter%5Bapp%5D=$APP_ID&limit=1&sort=-uploadedDate" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")

node $ASC_API PATCH "/v1/appStoreVersions/$VID/relationships/build" \
  "{\"data\":{\"type\":\"builds\",\"id\":\"$BUILD\"}}"     # 204 が返る

# 2) 審査提出を作る
SUB=$(node $ASC_API POST /v1/reviewSubmissions \
  "{\"data\":{\"type\":\"reviewSubmissions\",\"attributes\":{\"platform\":\"IOS\"},\"relationships\":{\"app\":{\"data\":{\"type\":\"apps\",\"id\":\"$APP_ID\"}}}}}" \
  | tail -n +2 | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['id'])")

# 3) 版を提出物として追加する
node $ASC_API POST /v1/reviewSubmissionItems \
  "{\"data\":{\"type\":\"reviewSubmissionItems\",\"relationships\":{\"reviewSubmission\":{\"data\":{\"type\":\"reviewSubmissions\",\"id\":\"$SUB\"}},\"appStoreVersion\":{\"data\":{\"type\":\"appStoreVersions\",\"id\":\"$VID\"}}}}}"

# 4) 提出する
node $ASC_API PATCH "/v1/reviewSubmissions/$SUB" \
  "{\"data\":{\"type\":\"reviewSubmissions\",\"id\":\"$SUB\",\"attributes\":{\"submitted\":true}}}"
```

最後の PATCH が 200 で `state: WAITING_FOR_REVIEW` になれば提出完了。

## 提出済みのものを取り下げる

**審査キューの順番を失う。** やり直しが本当に必要なときだけ。

```bash
# 進行中の提出を探す
node $ASC_API GET "/v1/apps/$APP_ID/reviewSubmissions?limit=5&fields%5BreviewSubmissions%5D=state,submittedDate" | tail -n +2 | python3 -c "
import json,sys
for s in json.load(sys.stdin)['data']: print(s['id'], s['attributes']['state'])"

# 取り下げる
node $ASC_API PATCH "/v1/reviewSubmissions/<submissionId>" \
  '{"data":{"type":"reviewSubmissions","id":"<submissionId>","attributes":{"canceled":true}}}'
```

`IN_REVIEW`（審査中）になってからの取り下げは、次回の審査が遅くなる可能性がある。

## 提出後の確認

```bash
curl -s "https://harness.basaapp.com/api/appstore/review-status?appId=$APP_ID" -H "Authorization: Bearer $HARNESS_TOKEN"
```

`appStoreState: WAITING_FOR_REVIEW` になっていれば提出できている。

## 完了条件

- [ ] 提出前チェックの5項目が全て通った
- [ ] `appStoreState` が `WAITING_FOR_REVIEW`
- [ ] （方法Aなら）`appstore-release.yml` の run が緑

## 次のスキル

`07_watch_review` — 審査結果を待ち、リジェクトに対応し、ユーザレビューに返信する。
