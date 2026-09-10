# 共通スクリプトと認証情報

番号付きスキル（`01_create_xcode_cicd` 以降）が共通で使う道具置き場。

## asc_api.js — App Store Connect 公式 API クライアント

```bash
node ${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js GET  "/v1/apps?limit=5"
node ${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js POST "/v1/bundleIds" '{"data":{...}}'
```

出力は **1行目がHTTPステータス、2行目以降がボディ**。パースするときは:

```bash
node asc_api.js GET "/v1/apps?limit=1" | python3 -c "
import json,sys
status, body = sys.stdin.read().split('\n', 1)
d = json.loads(body)
print(d['data'][0]['id'])
"
```

4xx/5xx のときは終了コード 1 を返す。

### 認証情報の設定（初回のみ）

環境変数、または `~/.asc-key.json` に置く。

```bash
export ASC_KEY_ID=XXXXXXXXXX
export ASC_ISSUER_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
export ASC_P8=~/.appstoreconnect/private_keys/AuthKey_XXXXXXXXXX.p8
```

```json
// ~/.asc-key.json
{ "keyId": "XXXXXXXXXX", "issuerId": "xxxxxxxx-...", "p8": "/Users/you/.appstoreconnect/private_keys/AuthKey_XXXXXXXXXX.p8" }
```

`ASC_P8` を省くと `~/.appstoreconnect/private_keys/AuthKey_<KEY_ID>.p8` を見る。

**キーは App Manager ロールで作ること。** App Store Connect → ユーザとアクセス → 統合 → App Store Connect API → チームキー。Sales/Reports ロールだと読み取り専用になり、`bundleIds` の作成や `ciWorkflows` の変更が 403 になる。`.p8` のダウンロードは1回きり。

このリポジトリでの実際の値は `~/workspace/harness/.env` の `ASC_RW_KEY_ID` / `ASC_RW_ISSUER_ID` にある（`ASC_RW_PRIVATE_KEY` は .p8 の base64）。

## harness の API トークン

`~/workspace/harness/.env` の `API_TOKEN`。`https://harness.basaapp.com/api/*` を叩くときの Bearer。

```bash
export HARNESS_TOKEN=$(grep '^API_TOKEN=' ~/workspace/harness/.env | cut -d= -f2-)
curl -s https://harness.basaapp.com/api/health -H "Authorization: Bearer $HARNESS_TOKEN"
```

## AppleScript で Xcode の UI を調べる

想定外のダイアログに出くわしたら、要素を列挙して構造を掴む。シートは**入れ子になることがある**（`sheet 1 of sheet 1 of window ...`）。

```bash
W="Nagasu — Nagasu.xcodeproj"

# 何階層目にシートがあるか
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to return count of sheets of window \"$W\""
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to return count of sheets of sheet 1 of window \"$W\""

# シート内の要素を役割で列挙する（これが最も確実）
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to tell sheet 1 of window \"$W\" to return role of every UI element"
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to tell sheet 1 of window \"$W\" to return name of every button"

# コンテナの中を掘る
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to tell group 1 of sheet 1 of window \"$W\" to return name of every button"
```

> **`entire contents` は当てにならない。** Xcode のシートに対して 0 件を返すことがある。上のような個別プロパティのクエリ（`role of every UI element` / `name of every button`）を使うこと。

ボタンが `button "Cancel" of sheet 1 of window "$W"` で見つからない（`-1728` エラー）場合、`group 1` や `splitter group 1` などのコンテナに入っている。名前が取れない要素は `UI element N` のインデックスで掴む。

```bash
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to click UI element 3 of group 1 of sheet 1 of sheet 1 of window \"$W\""
```

## 画面がスリープしていると UI が取れない

`osascript` が `windows = 0` を返したり、`screencapture` が真っ黒になるときは、ディスプレイがスリープしている。

```bash
caffeinate -u -t 2
```

で起こしてから再取得する。スクリーンショットは最前面を撮るので、先に `osascript -e 'tell application "Xcode" to activate'` すること。
