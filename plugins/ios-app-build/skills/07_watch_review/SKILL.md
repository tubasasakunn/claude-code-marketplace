---
name: 07_watch_review
description: App Store の審査結果を監視し、リジェクトに対応し、リリース後のユーザレビューを読んで返信します。Apple からの通知メールは Cloudflare Email Routing 経由で D1 に入るので、harness の API から読めます。審査提出後に使ってください。
---

# 審査の監視とレビュー対応 (07_watch_review)

## 仕組み

Apple からの通知メールは、Gmail から `claude@basaapp.com` に転送され、
Cloudflare Email Routing → harness の Email Worker → D1（`harness-mail`）に保存される。

```
Apple → Gmail → 転送 → Email Routing → harness Worker → D1
                                                          ↓
                                        GET /api/mail/summary で拾う
```

## 準備

```bash
export HARNESS_TOKEN=$(grep '^API_TOKEN=' ~/workspace/harness/.env | cut -d= -f2-)
APP_ID=<appId>
```

ASC の API を直接叩きたくなったら `${CLAUDE_PLUGIN_ROOT}/scripts/README.md` を読んで `asc_api.js` の認証を設定する。
このスキルの通常の手順は harness の API だけで完結する。

## Step 0. メールの経路が生きているか確認する ★最初にやる

**「未処理メールが0件」は「何も起きていない」ではなく「経路が死んでいる」かもしれない。** 区別すること。

```bash
# カテゴリ問わず、これまでに届いた全メールを見る
curl -s "https://harness.basaapp.com/api/mail?limit=20" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('total received:', d['count'])
for e in d['emails']:
    print(' ', e['receivedAt'][:19], e['category'], '|', (e.get('subject') or '(no subject)')[:60])
"
```

`category` は3種類。`apple`（`from` に apple.com / appstoreconnect を含む）、`gmail_confirmation`、`other`。

**`apple` のメールが1通も無いのに、アプリを提出済み・公開済みなら、転送が動いていない。**
下の「罠: メールが D1 に来ない」へ。

## Step 1. 審査ステータスを見る

```bash
curl -s "https://harness.basaapp.com/api/appstore/review-status?appId=$APP_ID" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for v in d['versions']:
    print('v' + v['versionString'], '->', v['appStoreState'])
"
```

レスポンスは `{"appId": "...", "versions": [{"id":..., "versionString":"1.0", "appStoreState":"...", ...}]}`。

| `appStoreState` | 意味 |
|---|---|
| `PREPARE_FOR_SUBMISSION` | まだ提出していない |
| `WAITING_FOR_REVIEW` | 審査待ち行列 |
| `IN_REVIEW` | 審査中 |
| `PENDING_DEVELOPER_RELEASE` | 承認済み。手動公開待ち |
| `PENDING_APPLE_RELEASE` | 承認済み。Apple の公開待ち |
| `READY_FOR_SALE` | 公開済み |
| `REJECTED` | リジェクト |
| `METADATA_REJECTED` | メタデータ（文言・スクショ）起因のリジェクト |
| `INVALID_BINARY` | バイナリが不正 |
| `DEVELOPER_REJECTED` | こちらから取り下げた |
| `PROCESSING_FOR_APP_STORE` | 公開処理中 |

## Step 2. 未読メールを拾う

```bash
# 軽量なサマリ（ポーリング用）
curl -s "https://harness.basaapp.com/api/mail/summary" -H "Authorization: Bearer $HARNESS_TOKEN"
# → {"unprocessed_total":2,"unprocessed_by_category":{"apple":2},"latest_received_at":"..."}

# 未処理の Apple メールを一覧（subject は null になりうるのでガードする）
curl -s "https://harness.basaapp.com/api/mail?processed=0&category=apple&limit=20" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys
for e in json.load(sys.stdin)['emails']:
    print(e['id'], e['receivedAt'][:19], '|', (e.get('subject') or '(no subject)')[:70])
"

# full=1 を付ければ一覧の時点で本文を全部持ってこられる（1件ずつ取りに行かなくてよい）
curl -s "https://harness.basaapp.com/api/mail?processed=0&category=apple&limit=5&full=1" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys
for e in json.load(sys.stdin)['emails']:
    print('===', (e.get('subject') or '(no subject)'))
    print((e.get('bodyText') or '')[:1500])
"

# 1件を全文で読む
curl -s "https://harness.basaapp.com/api/mail/<id>" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys; d=json.load(sys.stdin); print(d.get('subject')); print(); print((d.get('bodyText') or '')[:3000])"

# 対応が済んだら既読にする（次のポーリングで拾わない）
curl -s -X POST "https://harness.basaapp.com/api/mail/<id>/processed" -H "Authorization: Bearer $HARNESS_TOKEN"
```

**メールの本文はリジェクト理由の一次情報**。ASC の API はガイドライン番号を返さないことがあるので、必ず本文を読む。

## Step 3. 定期監視する

短時間の張り込みなら `/loop`、数日単位の放置なら **cloud routine（`/schedule`）** を使う。
`GET /api/mail/summary` を叩き、`unprocessed_by_category.apple > 0` なら中身を読む。

**cloud routine で回す前に、環境（environment）が `Default` になっていないか確認する。**
`Default` 環境だと `harness.basaapp.com` への呼び出しが全部 `403 Forbidden`
（`x-deny-reason: host_not_allowed`）で落ちる。しかもリトライしても直らない恒久的な拒否であり、
routine 自体は `Green` ステータスで終わる（インフラは正常に動いたという意味でしかない）ため、
気づかずに何日も「監視しているつもり」で放置しがちな罠。**必ず `OK` という名前の環境を選ぶこと**
（`RemoteTrigger`の`job_config.ccr.environment_id`で確認・修正できる。IDは`CLAUDE.md`の
「踏み抜いた罠」参照）。Web UI（https://claude.ai/code/routines）からでも同じ設定ができる。
詳細は `cloud-routines` スキルと `CLAUDE.md` の「踏み抜いた罠」参照。

## Step 4. リジェクトに対応する

1. メール本文とASCのリジェクト理由を読む
2. 該当のガイドライン番号を特定する（例: `2.3.3 Accurate Metadata` はスクリーンショット起因が多い）
3. 直す。**スクリーンショットが原因なら `screenshot-crafting` スキルを読む**
4. 直したら再提出（`06_submit_review`）

リジェクト後の版は `PREPARE_FOR_SUBMISSION` に戻るので、そのまま出し直せる。

### 審査官への返信（Resolution Center）

**API では書けない。** ASC の画面で返信する必要がある。
harness の遠隔ブラウザリレー（`02_register_appstore` の「セッションの再取得」参照）でユーザに開いてもらうか、
自分で ASC を開いて書く。

## Step 5. ユーザレビューを読む・返信する

公開後。**返信には App Manager ロールのキーが要る**（`${CLAUDE_PLUGIN_ROOT}/scripts/README.md` の設定で満たしている）。

```bash
# レビュー一覧（新しい順）
curl -s "https://harness.basaapp.com/api/appstore/reviews?appId=$APP_ID&limit=20" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for r in d['reviews']:
    print(r['createdDate'][:10], '★'*int(r['rating']), r['territory'], '| 返信済' if r['hasResponse'] else '| 未返信')
    print(' ', (r['title'] or '')[:60])
    print(' ', (r['body'] or '')[:200].replace('\n',' '))
"

# 返信する
curl -s -X POST "https://harness.basaapp.com/api/appstore/reviews/<reviewId>/response" \
  -H "Authorization: Bearer $HARNESS_TOKEN" -H "Content-Type: application/json" \
  -d '{"body":"ご利用ありがとうございます。..."}'
```

**返信は公開される。取り消せない。** 送る前に文面をユーザに見せて確認を取ること。

エラーの読み方:

| ステータス | 意味 |
|---|---|
| 400 | `body` が空、または JSON が壊れている |
| 503 | `ASC_RW_*`（App Manager キー）が harness に設定されていない |
| 502 | ASC 側のエラー。レスポンスの `body` に Apple の理由が入っている |

### 返信の書き方

- **謝罪から入らない。** 事実に答える
- 機能要望には「検討します」と言わない。**入れるか入れないかを、理由とともに言う**
- バグ報告には、再現条件を聞くか、直した版のバージョンを示す
- テンプレの繰り返しは逆効果。1件ずつ書く

## 罠

### メールが D1 に来ない ★実際に起きた

経路は3段ある。**どこで切れているかを切り分ける。**

```
Apple → Gmail(bassa.application@gmail.com) → 転送 → claude@basaapp.com
     → Cloudflare Email Routing → harness Worker → D1
```

**切り分け方**:

```bash
curl -s "https://harness.basaapp.com/api/mail?limit=20" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys; d=json.load(sys.stdin); print('total:', d['count'])
for e in d['emails']: print(' ', e['category'], e['receivedAt'][:19])"
```

- **1通も無い** → Cloudflare の Email Routing のルールが無い、または Worker が繋がっていない。
  ダッシュボードで `claude@basaapp.com` → アクション「Worker に送信」→ `harness` になっているか確認
- **`gmail_confirmation` だけある** → **Gmail の転送が「確認待ち」または「無効」のまま。これが最頻**
- **`apple` がある** → 経路は生きている

**Gmail 転送が有効になっていないときの直し方**（ユーザ操作が要る）:

1. 確認メールが D1 にあれば、その中の確認 URL を叩けば「確認済み」にできる

```bash
curl -s "https://harness.basaapp.com/api/mail?category=gmail_confirmation&limit=1&full=1" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys,re
e=json.load(sys.stdin)['emails'][0]
m=re.search(r'https://mail-settings\.google\.com/\S+', e.get('bodyText') or '')
print(m.group(0) if m else 'URL not found')
"
# 出てきた URL を curl -L で叩く
```

2. **確認しただけでは転送は始まらない。** Gmail の設定画面で、次のどちらかを**ユーザに**やってもらう:
   - 「メール転送と POP/IMAP」→ **「受信メールを ... に転送する」のラジオを選択して保存**
   - または「フィルタとブロック中のアドレス」→ `from:(no_reply@email.apple.com)` のフィルタを作り、転送先を指定

   確認済みアドレスがあるだけで転送先ラジオが未選択だと、**メールは1通も転送されない**。

3. 疎通確認: 自分宛にテストメールを送り、数分後に `GET /api/mail?limit=5` で `other` として届くか見る

### `customerReviews` が 403

`/v1/customerReviews` は**コレクション GET 不可**。アプリ配下のパス（`/v1/apps/{id}/customerReviews`）を使う。
harness の `/api/appstore/reviews` は既にそうしている。

### `appStoreVersions` が 400

このエンドポイントは `sort` パラメータを受け付けない。付けると `PARAMETER_ERROR.ILLEGAL`。

## 完了条件

- [ ] **メール経路が生きている**（`category: apple` のメールが D1 に1通以上ある）。0通なら「罠」節で原因を切り分ける
- [ ] 審査ステータスを取得でき、`appStoreState` を表と照合できる
- [ ] 未処理メールを読んで `processed` にできる
- [ ] （リリース後）レビューを一覧でき、返信のコマンドを組み立てられる

## 前のスキル

`06_submit_review`
