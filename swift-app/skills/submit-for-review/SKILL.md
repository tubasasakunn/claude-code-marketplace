---
name: submit-for-review
description: 「審査提出して」「リリースして」「ship して」と言われたら、この一連を最後まで自動で回す ── 作業ブランチ→main へ PR 作成＆マージ→Xcode Cloud ビルド完成を harness API で待つ→失敗なら修正して最初へ戻る→main→production の審査PRをマージ→審査提出の完了を確認→LINE で完了報告（途中の進捗は Slack）。バージョン上げ・メタデータ整備の手順は /swift-app:release-version と /swift-app:release-assets が正本で、ここは「言われたら全部やる」実行レーン。
argument-hint: "[任意: 新バージョン番号 例 1.2.0]"
allowed-tools: Read, Edit, Write, Bash, Grep, Glob
---

# 審査提出オートパイロット

ユーザーが **「審査提出して」** と言ったら、**PR 作成から App Store 審査提出の完了確認まで**を
自分で回しきる。節目は **Slack**、最後に **LINE** で報告する。Xcode Cloud ビルドが失敗したら
issue を読んで直し、ビルドのステップに戻る（成功するか、直せない原因が判明するまで）。

> 仕組みの正本は `/swift-app:architecture`（ブランチと3ワークフローの対応）と
> `/swift-app:release-version`（バージョン上げの手順）、素材は `/swift-app:release-assets`。
> **ここは実行と監視に徹する。**

## 0. 設定を読む（毎回いちばん最初）

**アプリ固有の値をこのスキルに書かない。** 全部リポジトリから読む。

```bash
CFG=appstore.config.json
BUNDLE=$(python3 -c "import json;print(json.load(open('$CFG'))['app']['bundle_id'])")
GH=$(python3     -c "import json;print(json.load(open('$CFG'))['appstore']['github_repo'])")
OWNER=${GH%%/*}; REPO=${GH##*/}
ASC_APP_ID=$(python3 -c "import json;print(json.load(open('$CFG'))['appstore'].get('asc_app_id',''))")
CI_PRODUCT=$(python3 -c "import json;print(json.load(open('$CFG'))['appstore'].get('ci_product_id',''))")

# トークンは git 管理された private リポジトリ内の secrets から読む
# （Claude Code のオンライン版=サンドボックスでも clone されるので、ホーム配置に頼らない）
set -a; . ./.claude/secrets.env; set +a     # HARNESS_TOKEN を供給する
H="https://harness.basaapp.com"
auth=(-H "Authorization: Bearer $HARNESS_TOKEN" -H "Content-Type: application/json")
Q="owner=$OWNER&repo=$REPO"
```

- `.claude/secrets.env` が無ければユーザーに聞く。**このスキルにトークンを書き込まない**
  （marketplace は public）
- `asc_app_id` / `ci_product_id` が `appstore.config.json` に無ければ ASC API で引き、
  **config に書き足してコミットする**（次回ここで止まらないように）:
  ```bash
  node ${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js \
    GET "/v1/apps?filter[bundleId]=$BUNDLE&fields[apps]=name,bundleId"
  ```
  （`asc_api.js` は `ios-app-build` プラグイン側にある。無いときは harness の
  `/api/appstore/proxy/v1/apps?filter[bundleId]=...` で代替する）
- **`/api/github/*` はクエリに `?$Q` が必須**（書き込み系は body にも `owner`/`repo`）。
  付けないと `{"error":"owner/repo required ..."}` で 400。ASC 系と LINE/Slack は不要

## 全体フロー

```
1. 準備    バージョン上げ + release/<ver>/ + ビルド静的検証（必要なら）
2. main へ  作業ブランチ → main に PR 作成 → マージ              ┐ Slack 進捗
3. ビルド待ち Xcode Cloud のビルド完成を harness CI API でポーリング │
4. 失敗時   issue を読んで修正 → push → 3 に戻る                  ┘
5. 審査PR   release-pr.yml が立てた main→production PR をマージ     ┐ Slack 進捗
6. 提出確認 appstore-release.yml 成功 + ASC が WAITING_FOR_REVIEW   ┘
7. 完了報告 LINE に最終結果（各節目は Slack）
```

## 1. 準備（新バージョンとして出すなら）

審査提出には「production に存在しない `release/<MARKETING_VERSION>/`」が要る。

1. 現状確認: `grep -m1 MARKETING_VERSION <xcodeproj>/project.pbxproj` と `ls release/`
2. 新バージョンが必要なら **`/swift-app:release-version` の手順**で版を上げ、`release/<new>/` を
   用意（前版コピー＋`whats_new.txt` 更新、`python3 scripts/check_release_metadata.py <new>` = PASS）。
   引数で版が渡されたらそれを使う
3. macOS なら `/swift-app:verify-build`。ビルド不可な環境なら diff の静的レビューで代替し、
   「ビルド未検証（Xcode Cloud が本ビルド）」を明記する
4. 作業ブランチにコミットする

> 既に版・素材が揃っていて「提出だけ」なら 1 を飛ばして 2 へ。

```bash
curl -sS "${auth[@]}" -X POST "$H/api/slack/post" \
  -d '{"text":"🚀 <ver> 審査提出を開始。準備OK、main へ PR を作ります。"}'
```

## 2. main へ PR 作成 → マージ

```bash
curl -sS "${auth[@]}" -X POST "$H/api/github/pulls?$Q" \
  -d "{\"owner\":\"$OWNER\",\"repo\":\"$REPO\",\"title\":\"<ver>: <要約>\",\"head\":\"<branch>\",\"base\":\"main\",\"body\":\"...\"}"
# → { "pull": { "number": N, ... } }

# マージ（コミット粒度を残すため merge。squash しない）
curl -sS "${auth[@]}" -X PUT "$H/api/github/pulls/N/merge?$Q" \
  -d "{\"owner\":\"$OWNER\",\"repo\":\"$REPO\",\"method\":\"merge\"}"
# → { "body": { "merged": true } }
```

マージ後 main で `appstore-metadata.yml`（ASC 反映）と `release-pr.yml`（main→production の
審査PR 作成、数十秒）が走る。

## 3. Xcode Cloud ビルド完成を待つ

**production をマージする前に、当該バージョンのビルドが COMPLETE/SUCCEEDED になっているのが
理想**（`appstore-release.yml` は処理済みビルドを最大45分待つので即失敗はしないが、先に確認
しておくと安全）。

```bash
curl -sS "${auth[@]}" "$H/api/appstore/ci/products/$CI_PRODUCT/builds?limit=10"   # 先頭が最新
curl -sS "${auth[@]}" "$H/api/appstore/ci/builds/<buildId>"
# buildRun.executionProgress: PENDING|RUNNING|COMPLETE
# buildRun.completionStatus : SUCCEEDED|FAILED|ERRORED|CANCELED|SKIPPED
```

- **RUNNING/PENDING**: ビルドは ~10〜20分。短時間ポーリングで張り付かない。節目で再確認する
- **SUCCEEDED**: 5 へ
- **FAILED/ERRORED**: 4 へ

> Xcode Cloud は GitHub Actions ではなく ASC 側の CI。トリガ条件はワークフロー設定に依存する。

## 4. ビルド失敗 → 修正して 3 に戻る

```bash
curl -sS "${auth[@]}" "$H/api/appstore/ci/builds/<buildId>?issues=all"
# actions[].issues[].message / fileSource / category で原因特定
```

1. 原因を特定する（コンパイルエラー・署名・テスト失敗）
2. 修正して push（main にマージ済みなら修正ブランチ → main へ PR → マージ）
3. 新しい push で再ビルド → **3 に戻る**
4. **直せない／スコープ外なら深追いしない。** 原因つきで Slack と LINE に報告して止める
   （無限ループにしない）

```bash
curl -sS "${auth[@]}" -X POST "$H/api/slack/post" \
  -d '{"text":"⚠️ <ver> Xcode Cloud ビルド失敗（build #NN）。原因: ... → 修正して再ビルドします。"}'
```

## 5. 審査PR（main→production）をマージ

```bash
curl -sS "${auth[@]}" "$H/api/github/pulls?$Q&state=open&base=production&head=main"
curl -sS "${auth[@]}" -X PUT "$H/api/github/pulls/<N>/merge?$Q" \
  -d "{\"owner\":\"$OWNER\",\"repo\":\"$REPO\",\"method\":\"merge\"}"
```

無ければ自分で作る（base=production / head=main）。

## 6. 審査提出の完了を確認

`appstore-release.yml` が `submit_latest_build` を実行する。**run の完了**と **ASC の版状態**の
両方で確認する。

```bash
# (a) production の最新 run
curl -sS "${auth[@]}" "$H/api/github/runs?$Q&branch=production&limit=5"
curl -sS "${auth[@]}" "$H/api/github/runs/<runId>?$Q"    # status=completed / conclusion=success

# (b) ASC 側の独立確認（決め手）
curl -sS "${auth[@]}" "$H/api/appstore/proxy/v1/apps/$ASC_APP_ID/appStoreVersions?limit=5" \
  | python3 -c 'import sys,json;[print(v["attributes"]["versionString"],v["attributes"]["appStoreState"]) for v in json.load(sys.stdin)["body"]["data"]]'
```

当該 `versionString` の `appStoreState` が **`WAITING_FOR_REVIEW`** なら提出成功
（`PREPARE_FOR_SUBMISSION` は未提出、`IN_REVIEW`/`READY_FOR_SALE` はその先）。

ならない場合は原因（メタデータ不備・申告漏れ・ビルド未処理）を読んで直し、必要なら main 経由で
修正して production を再マージする。**4 と同じ精神で、詰まったら原因つきで報告して止める。**

## 7. 完了報告

```bash
curl -sS "${auth[@]}" -X POST "$H/api/line/push" -d '{
  "messages": "✅ <アプリ名> <ver> 審査提出 完了\n\n・選択ビルド: <ver> (<build>)\n・状態: WAITING_FOR_REVIEW（審査待ち）\n・通過後は自動公開（automatic_release=true）\n\n<一言サマリ>"
}'
```

Slack には各節目（開始 / main マージ / ビルド完成 / production マージ / 提出完了）で1行ずつ。
**LINE は最終1通に集約**して通知過多を避ける。

## harness エンドポイント早見表

| 目的 | メソッド・パス |
|---|---|
| Slack 進捗 | `POST /api/slack/post` `{ "text" }` |
| LINE 完了通知 | `POST /api/line/push` `{ "messages" }` |
| PR 作成 | `POST /api/github/pulls?owner=&repo=` `{ owner, repo, title, head, base, body? }` |
| PR 一覧 | `GET /api/github/pulls?owner=&repo=&state=&base=&head=` |
| PR マージ | `PUT /api/github/pulls/{n}/merge?owner=&repo=` `{ owner, repo, "method":"merge" }` |
| Actions run 一覧 | `GET /api/github/runs?owner=&repo=&branch=&status=&limit=` |
| run ＋ジョブ詳細 | `GET /api/github/runs/{id}?owner=&repo=` |
| Xcode Cloud ビルド一覧 | `GET /api/appstore/ci/products/{productId}/builds?limit=` |
| Xcode Cloud ビルド結果 | `GET /api/appstore/ci/builds/{id}` (`?issues=all`) |
| ASC バージョン状態 | `GET /api/appstore/proxy/v1/apps/{ascAppId}/appStoreVersions` |

全 API は `Authorization: Bearer $HARNESS_TOKEN` 必須。エラーは `{ "error": ... }` ＋ HTTP
ステータス（401 認証 / 502 上流透過）。詳細仕様は `GET /llms.txt`。

## 注意・罠

- **トークンをこのファイルに書かない。** marketplace は public。`.claude/secrets.env` から読む
- **マージは merge 法**（squash しない）。solo dev はコミット粒度がセーフティネット
- **production まで突き抜けるのは「審査提出して」と言われたときだけ。** 通常の機能 PR で
  production をマージしない
- **無限ループ禁止**: 試行錯誤は「直せる見込みがある間」だけ。Apple 側・Secrets 欠落・
  設計判断なら報告して止める
- **短時間ポーリングで張り付かない**: ビルドは10〜20分、提出は最大45分
- 初回は `production` ブランチと Actions の PR 作成権限が要る → `/swift-app:architecture`
- ビルド番号は `ci_scripts/ci_post_clone.sh` が `CI_BUILD_NUMBER` で採番する
