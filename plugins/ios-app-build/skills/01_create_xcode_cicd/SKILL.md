---
name: 01_create_xcode_cicd
description: 新規iOSアプリの「App Store Connect アプリレコード作成」と「Xcode Cloud の CI/CD 設定」を、AppleScript で Xcode の GUI を自動操作して一度に完了させます。GitHubリポジトリと .xcodeproj を用意した直後、他のどのASC作業よりも先に実行してください。Xcode Cloud のビルドが審査用ビルドとして ASC に入るところまで面倒を見ます。
---

# Xcode Cloud CI/CD とアプリレコードの作成 (01_create_xcode_cicd)

## このスキルが解決する問題

App Store Connect の **アプリレコード作成** と **Xcode Cloud の product 作成** は、どちらも公式 API から実行できない。

- `POST /v1/apps` → 403（`apps` は CREATE 不許可）
- `POST /v1/ciProducts` → 403（許可されるのは DELETE / GET のみ）

Xcode Cloud は App Store Connect とは**別のバックエンド**（`api.cirrus.apple.com`、社内名 Skywagon）で動いており、product 作成の `createProductV2` は Xcode.app 内蔵のクライアントにしか実装されていない。fastlane にも実装が無い。

しかし **Xcode の GUI を AppleScript（System Events）で自動操作すれば、正規のフローを踏んで両方を一度に作れる**。Xcode Cloud のオンボーディングウィザードは、bundle id に一致するアプリレコードが無ければ**自分で作る**（Apple 公式ドキュメント記載の挙動）。

だからこのスキルは、**アプリ作成の最初の一手**として実行する。他の ASC 作業（価格・レーティング等）はアプリレコードが存在しないと始められない。

## 前提条件

`${CLAUDE_PLUGIN_ROOT}/scripts/README.md` を先に読むこと（`asc_api.js` の場所と認証情報の設定方法が書いてある）。

コマンドで確認できるもの:

```bash
# Xcode が使えるか
xcodebuild -version

# アクセシビリティ権限（true でなければユーザに許可を依頼する）
osascript -e 'tell application "System Events" to return UI elements enabled'

# .xcodeproj があるか（xcodegen 運用なら先に xcodegen generate）
ls -d *.xcodeproj || xcodegen generate

# GitHub に push 済みか
git remote -v && git status --short

# bundle id と team が設定されているか
grep -E "PRODUCT_BUNDLE_IDENTIFIER|DEVELOPMENT_TEAM" project.yml
```

コマンドで確認できないもの:

- **Xcode に Apple ID がサインイン済みであること**（Xcode → Settings → Accounts）。これを事前に検査する信頼できるコマンドは無い。未サインインだと Step 2 でサインイン用のシートが出るので、**そのときはユーザに依頼して中断する**（自動化しようとしない。2FA が必要）

### ★罠: `osascript` の Accessibility 権限は正しいのに `count of windows` が 0 を返し続ける

**症状**: `tell application "System Events" to tell process "Xcode" to return count of windows` が
一貫して `0` を返すのに、`tell application "Xcode" to return name of every window`（Xcode 自身の
AppleScript 辞書を直叩き）は正しくウィンドウ名を返す。System Settings の Accessibility / Automation は
両方とも対象アプリ（ターミナル）で ON になっている。

**真因**: **Xcode のウィンドウが、ターミナルが今いる Mission Control の Space（仮想デスクトップ）と別の
Space にある。** System Events 経由の `windows`（内部的に `AXWindows` 属性、かつ「オンスクリーン」判定）は
**現在アクティブな Space 上のウィンドウしか見えない**。一方 Xcode 自身の AppleScript ブリッジは
`NSApp.windows` を直接参照するため Space に関係なく成功する。これが「直叩きは成功するのに
System Events 経由だけ失敗する」非対称性の正体。TCC 権限は最初から正しく、ここで疑うだけ時間を失う。

**対処（再起動不要）**: Dock の Xcode アイコンを control-click →「オプション」→
「割り当て先：すべてのデスクトップ」にする。これで Xcode のウィンドウがどの Space からでも見えるようになり、
再発しない。副次的にディスプレイスリープでも同様にウィンドウが「オンスクリーンでない」扱いになるため、
自動操作セッション中は `caffeinate -d -i`（`-i` だけでなく **`-d` が必須**）を常駐させる。

**切り分け方**: `tell application "Xcode" to return name of every window` は成功するが
`tell application "System Events" to tell process "Xcode" to return count of windows` だけ失敗する場合、
99% これが原因。TCC.db（`~/Library/Application Support/com.apple.TCC/TCC.db` と
`/Library/Application Support/com.apple.TCC/TCC.db`、実は両方 sudo 無しで `sqlite3` から読める）を見て
`auth_value=2`（許可済み）なのに動かない、という状態ならなおさら疑うべきはここ。

## Step 0. 分岐判定 ★最初に必ずやる

**このスキルの GUI ウィザードは「ciProduct がまだ無いアプリ」専用である。**

判定は **bundle id を起点に**行う。ciProduct の名前は Xcode のプロジェクト名（例 `Nagasu`）で、ASC 上のアプリ表示名（例 `Nagasu：手放す記録帳`）とは**別物**なので、名前一致で判定してはいけない。

```bash
export ASC_API=${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js
BUNDLE_ID=com.basaapp.<appname>   # project.yml の PRODUCT_BUNDLE_IDENTIFIER と同じ値

# 1) アプリレコードがあるか
node $ASC_API GET "/v1/apps?filter%5BbundleId%5D=$BUNDLE_ID&fields%5Bapps%5D=name,bundleId" | python3 -c "
import json,sys
status, body = sys.stdin.read().split('\n', 1)
data = json.loads(body)['data']
print('APP_ID=' + data[0]['id'] if data else 'NO_APP')
"
```

- `NO_APP` → アプリレコードが無い。**確実に新規。Step 1 へ進む**
- `APP_ID=...` が出たら、その appId で ciProduct の有無を見る

```bash
# 2) そのアプリに ciProduct が紐付いているか（apps/{id}/ciProduct が使える）
node $ASC_API GET "/v1/apps/<appId>/ciProduct?fields%5BciProducts%5D=name" 2>&1 | head -1
```

- **HTTP 200** → ciProduct がある。**Step 1〜3 を飛ばして Step 4 へ**（GUI 操作は不要）
- **HTTP 404** → ciProduct が無い。**Step 1 へ進む**（アプリレコードだけ先にある状態。ウィザードは `Confirm App` を出して紐付ける）

`ciProducts` の一覧を舐める必要は無い（ページネーションで取りこぼす）。必ず `apps/{id}/ciProduct` を使う。

## Step 1. Xcode を再起動し、対象プロジェクトだけを開く ★事故防止

**複数のプロジェクトを開いたまま実行してはいけない。** Xcode Cloud のウィザードは、既存の ciProduct を
**別のアプリに付け替えてしまうこと**がある（実測: Nagasu 用の product が、Bide のウィザード実行で
名前・アプリ・リポジトリごと Bide に上書きされ、Nagasu の CI が消えた）。

必ず Xcode を終了し、対象プロジェクトだけを開き直す。そして**実行前に現状を記録する**。

```bash
# 実行前のスナップショット（アプリ → ciProduct の対応表）
${CLAUDE_PLUGIN_ROOT}/scripts/ciproduct_snapshot.sh > /tmp/ciproduct_before.txt

osascript -e 'tell application "Xcode" to quit'; sleep 5

open -a Xcode /path/to/App.xcodeproj
sleep 20
osascript -e 'tell application "System Events" to tell process "Xcode" to return name of every window'
```

**ウィンドウが1つだけであることを確認する。** 2つ以上あれば、他を閉じてからやり直す。

ウィンドウ名は `<スキーム名> — <プロジェクトファイル名>` の形（例 `Nagasu — Nagasu.xcodeproj`）。複数のプロジェクトを開いている場合は、**`.xcodeproj` のファイル名を含むもの**が対象。以降 `$W` として使う。

対象ウィンドウを前面に出す。

```bash
W="Nagasu — Nagasu.xcodeproj"
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to perform action \"AXRaise\" of window \"$W\""
osascript -e 'tell application "Xcode" to activate'
```

## Step 2. ウィザードを起動する

**押す前に、メニュー項目が有効かを必ず確認する。** 無効なメニュー項目をクリックしても AppleScript は**エラーを返さず何も起きない**（成功したように見える）。

```bash
osascript -e 'tell application "System Events" to tell process "Xcode" to return enabled of menu item "Create Workflow…" of menu 1 of menu bar item "Integrate" of menu bar 1'
```

- `true` → クリックしてよい
- `false` → **クリックしない。** 原因は3つある。上から順に潰す:
  1. **プロジェクトのウィンドウが開いていない**（設定ウィンドウが前面、など）。Step 1 をやり直す
  2. **そのアプリには既に ciProduct がある**。Step 0 の判定に戻る。この場合の無効化は正常
  3. **Xcode の Apple ID セッションが切れている**。1・2 を除外してもなお無効ならこれ。ユーザに **Xcode → Settings → Accounts でサインインし直す**よう依頼して中断する。2FA が要るので自動化できない

```bash
osascript -e 'tell application "System Events" to tell process "Xcode" to click menu item "Create Workflow…" of menu 1 of menu bar item "Integrate" of menu bar 1'
sleep 8
```

メニュー項目名は `Create Workflow…`（末尾は三点リーダ `…` 1文字。ハイフン3つではない）。

**サインインを求めるシートが出たら中断してユーザに依頼する。** 2FA が必要で自動化できない。

> このメニュー構造は **Xcode 26.x** で確認したもの。バージョンが上がって項目名や階層が変わったら、`${CLAUDE_PLUGIN_ROOT}/scripts/README.md` の「AppleScript で Xcode の UI を調べる」で実際の構造を列挙すること。

## Step 3. シートを1枚ずつ進める

各シートは `sheet 1 of window "$W"` に現れる。タイトルは `static text 1` の値。

**必ず `Next` が `enabled` になるまで待ってから押す。** シートは非同期にロードされるため、待たずに押すと無視される。

```bash
wait_for_next() {
  for i in $(seq 1 12); do
    EN=$(osascript -e "tell application \"System Events\" to tell process \"Xcode\" to return enabled of button \"Next\" of sheet 1 of window \"$W\"" 2>/dev/null)
    [ "$EN" = "true" ] && return 0
    sleep 3
  done
  return 1
}

sheet_title() {
  osascript -e "tell application \"System Events\" to tell process \"Xcode\" to tell sheet 1 of window \"$W\" to return value of static text 1"
}
```

**1枚進めるたびに `sheet_title` を読み、下の表と照合する。想定外のタイトルが出たら Next を押さずに止まり、状況を報告すること。** 想定外の画面で Next を押すと、意図しないアプリレコードを作りうる。

| # | タイトル | 内容 | 操作 |
|---|---|---|---|
| 1 | `Select a Product` | 対象アプリが1件表示される | Next |
| 1.5 | `Resolve Initial Setup Issues` | **新規アプリでは高確率で出る。** アプリ名が既に使われている等 | 下の「アプリ名の衝突」へ |
| 2 | `Review Workflow` | 起動条件（main への push）と Archive アクション | Next |
| 3 | `Grant Access to Your Source Code` | GitHub リポジトリに緑チェック | Next |
| 4 | `Create App on App Store Connect` | **アプリレコードを新規作成する画面** | Next |
| 4' | `Confirm App on App Store Connect` | アプリレコードが既にある場合。紐付けるだけ | Next |
| 5 | `... is now configured for Xcode Cloud` | 完了。**ボタンは `Next` ではなく `Close`** | Close |

`Select a Product` の直後に `Resolve Initial Setup Issues` が割り込むことが多い。表の順に出るとは限らない。

最後:

```bash
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to click button \"Close\" of sheet 1 of window \"$W\""
```

### アプリ名の衝突（`Resolve Initial Setup Issues`）★新規アプリでは必ず読む

**App Store Connect のアプリ名は全世界で一意**でなければならない。ウィザードは既定で **Xcode のプロジェクト名**（例 `Bide`）をアプリ名として使おうとするため、一般的な英単語だとほぼ確実に「already taken」になる。

Web 検索で「同名アプリは無い」と確認しても意味がない。**Apple の内部登録との衝突は、このウィザードで実際に試すまで分からない。**

対処: **プロジェクト名ではなく、CONCEPT.md の「ストア表示」名を使う**（例 `Bide：待ち方の記録`）。30文字以内。

シート内の `Update…` ボタンを押すと、入れ子のシート（`sheet 1 of sheet 1`）にテキストフィールドが出る。

```bash
# 症状を確認する
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to tell sheet 1 of window \"$W\" to return value of every static text"
# → 「The app name "Bide" is already taken. ...」

# 名前変更ダイアログを開く
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to click button \"Update…\" of sheet 1 of window \"$W\""
sleep 3

# 入れ子シートのテキストフィールドに新しい名前を入れる
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to set value of text field 1 of sheet 1 of sheet 1 of window \"$W\" to \"Bide：待ち方の記録\""

# ボタン名を確認してから押す（Update / OK など環境で異なる）
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to return name of every button of sheet 1 of sheet 1 of window \"$W\""
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to click button \"Update\" of sheet 1 of sheet 1 of window \"$W\""
sleep 4
```

名前を変えると `Next` が有効になる。有効にならなければ、その名前もまだ取られている。別名で繰り返す。

**入れ子シートのボタンが `button "..." of sheet 1 of sheet 1 of window` で掴めない（`-1728`）ことがある。** その場合はコンテナ（`group 1` や `splitter group 1`）の中にいる。

```bash
# 何が入っているかを役割で列挙する（entire contents は 0 件を返すことがあるので使わない）
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to tell sheet 1 of sheet 1 of window \"$W\" to return role of every UI element"
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to tell group 1 of sheet 1 of sheet 1 of window \"$W\" to return name of every button"
```

名前が取れない要素は `UI element N` のインデックスで掴む。

**アプリ名を勝手に決めない。** CONCEPT.md のストア表示名を使う。それも取られていたら、ユーザに相談する（プロダクト判断）。

## Step 4. 作成されたことを API で確認する ★他アプリを壊していないかも確認する

**GUI が「できた」と言っても、必ず API で裏を取る。**

```bash
BUNDLE_ID=com.basaapp.<appname>   # project.yml の PRODUCT_BUNDLE_IDENTIFIER と同じ値

# アプリレコード（appId を控える）
node $ASC_API GET "/v1/apps?filter%5BbundleId%5D=$BUNDLE_ID&fields%5Bapps%5D=name,bundleId"

# ciProduct（ciProductId を控える）
node $ASC_API GET "/v1/apps/<appId>/ciProduct?fields%5BciProducts%5D=name"
```

### 付け替え事故のチェック ★必須

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/ciproduct_snapshot.sh > /tmp/ciproduct_after.txt
diff /tmp/ciproduct_before.txt /tmp/ciproduct_after.txt
```

**差分は「対象アプリの行が1行増える」だけであるべき。**

既存アプリの行が消えていたり、別の bundle id に変わっていたら、**その既存アプリの product が奪われている**。
すぐに止めてユーザに報告する。`ciProducts` は公式 API で作成も更新もできないため、奪われた側は
**Xcode のウィザードを再実行して作り直すしかない**。

`ciProductId` が `/tmp/ciproduct_before.txt` に既出の id と同じだったら、それは新規作成ではなく付け替えである。

**appId と ciProductId と workflowId をメモに残す**（以降のスキルで使う）。

### `primaryLocale` を直す ★ここを飛ばすと審査提出で必ず落ちる

**Xcode のウィザードが作ったアプリは `primaryLocale` が `en-US` になる。**
日本語アプリなら `ja` に直す。放置すると、空の英語ロケールが作られ、審査提出時に
`appStoreVersions ... is not in valid state` +「en-US の description / keywords / supportUrl / privacyPolicyUrl が無い」で弾かれる。

```bash
node $ASC_API GET "/v1/apps/<appId>?fields%5Bapps%5D=name,primaryLocale" | tail -n +2 | python3 -c "
import json,sys; a=json.load(sys.stdin)['data']['attributes']; print(a['primaryLocale'], '|', a['name'])"

# en-US なら直す
node $ASC_API PATCH "/v1/apps/<appId>" '{"data":{"type":"apps","id":"<appId>","attributes":{"primaryLocale":"ja"}}}'
```

### ★罠: `primaryLocale` の PATCH が `409 MISSING_SCREENSHOTS_PRIMARY_LOCALE` で拒否される

**症状**: 上の PATCH がスクリーンショット不足を理由に 409 で弾かれる。「スクリーンショットが無いから直せない」ように読めるが、実際に画像を用意する必要はない（Tazuneruで実測）。

**真因**: このエラーは「新しい primaryLocale（`ja`）の `appStoreVersionLocalization` レコードがまだ存在しない」ことを指しているだけで、画像の有無は無関係。ウィザードが作った直後の版には `en-US` の `appStoreVersionLocalization` しか無く、`ja` のレコード自体がまだ無い状態で PATCH しようとすると起きる。

**対処**: 先に `ja` の `appStoreVersionLocalization` を POST で作ってから、改めて `primaryLocale` を PATCH する（非破壊。既存の `en-US` レコードは残る。後述の「余計な空ロケール」の掃除で消せばよい）。

```bash
VID=$(node $ASC_API GET "/v1/apps/<appId>/appStoreVersions?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")

node $ASC_API POST "/v1/appStoreVersionLocalizations" '{"data":{"type":"appStoreVersionLocalizations","attributes":{"locale":"ja"},"relationships":{"appStoreVersion":{"data":{"type":"appStoreVersions","id":"'"$VID"'"}}}}}'

# これで primaryLocale の PATCH が通るようになる
node $ASC_API PATCH "/v1/apps/<appId>" '{"data":{"type":"apps","id":"<appId>","attributes":{"primaryLocale":"ja"}}}'
```

そのうえで、**余計な空ロケールが残っていないか**確認して消す。

```bash
VID=$(node $ASC_API GET "/v1/apps/<appId>/appStoreVersions?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
node $ASC_API GET "/v1/appStoreVersions/$VID/appStoreVersionLocalizations?limit=5" | tail -n +2 | python3 -c "
import json,sys
for l in json.load(sys.stdin)['data']: print(l['id'], l['attributes']['locale'])"

# ja 以外が残っていたら消す
node $ASC_API DELETE "/v1/appStoreVersionLocalizations/<en-US の id>"
```

## Step 5. ワークフローを「審査用ビルド」設定に直す ★必須

**ここを飛ばすと、ビルドは緑になるのに ASC にビルドが1件も現れない。** 最も気づきにくい失敗。

Xcode が作った直後のワークフローは `buildDistributionAudience` が `null` で、Archive しても成果物が ASC に配信されない。

```bash
# workflowId を取得
node $ASC_API GET "/v1/ciProducts/<ciProductId>/workflows?limit=10&fields%5BciWorkflows%5D=name,isEnabled"

# 現在の actions を読む。scheme は actions[0].scheme に入っている
node $ASC_API GET "/v1/ciWorkflows/<workflowId>" | python3 -c "
import json,sys
status, body = sys.stdin.read().split('\n', 1)
a = json.loads(body)['data']['attributes']
print('audience:', a['actions'][0]['buildDistributionAudience'])
print('scheme  :', a['actions'][0]['scheme'])
"
```

`audience` が `APP_STORE_ELIGIBLE` なら何もしない。`None` なら PATCH する。

```bash
node $ASC_API PATCH "/v1/ciWorkflows/<workflowId>" '{"data":{"type":"ciWorkflows","id":"<workflowId>","attributes":{"actions":[{"name":"Archive - iOS","actionType":"ARCHIVE","destination":null,"buildDistributionAudience":"APP_STORE_ELIGIBLE","testConfiguration":null,"scheme":"<上で読んだ scheme>","platform":"IOS","isRequiredToPass":true}]}}}'
```

`actions` は**配列まるごと差し替え**になる。必ず GET した値をベースにして `buildDistributionAudience` だけ変えること。

## Step 6. ビルドを起動して疎通確認する

product さえできれば、**ビルド起動は公式 API でできる**（GUI 不要）。

```bash
node $ASC_API POST /v1/ciBuildRuns '{"data":{"type":"ciBuildRuns","relationships":{"workflow":{"data":{"type":"ciWorkflows","id":"<workflowId>"}}}}}'
```

完了を待つ。**`sort=-number` を必ず付ける。** 付けないと古い順に返り、いつまでも #1 を見ることになる。

```bash
node $ASC_API GET "/v1/ciProducts/<ciProductId>/buildRuns?limit=1&sort=-number&fields%5BciBuildRuns%5D=number,executionProgress,completionStatus"
```

`COMPLETE` / `SUCCEEDED` になったら、ASC にビルドが入ったか確認する（数分遅れることがある）。

```bash
node $ASC_API GET "/v1/builds?filter%5Bapp%5D=<appId>&limit=5&sort=-uploadedDate&fields%5Bbuilds%5D=version,processingState"
```

`processingState: VALID` のビルドが見えれば CI/CD は完成。

ビルドが失敗したら、原因は harness 経由で読める。

```bash
curl -s "https://harness.basaapp.com/api/appstore/ci/builds/<buildRunId>" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys
d = json.load(sys.stdin)
for a in d.get('actions', []):
    print(a['name'], a['completionStatus'])
    for i in (a.get('issues') or []): print('  ', i['issueType'], i['message'][:200])
"
```

## トラブルシューティング

### `Untitled Workflow` という画面が開いた

対象アプリに **既に ciProduct がある**。`Create Workflow…` は「既存 product へのワークフロー追加」として動いている。目的の画面ではないので中止する。

このシートは**二重の入れ子**（`sheet 1 of sheet 1`）で、ボタンは `splitter group 1` の中にある。

```bash
osascript -e "tell application \"System Events\" to tell process \"Xcode\" to click button \"Cancel\" of splitter group 1 of sheet 1 of sheet 1 of window \"$W\""
```

パスが違う場合は `${CLAUDE_PLUGIN_ROOT}/scripts/README.md` の「AppleScript で Xcode の UI を調べる」で実際の構造を列挙する。

中止したら Step 0 の判定に戻り、Step 4 以降へ進む。

### `ci_post_clone.sh script failed (exited with code 1)` でビルドが落ちる

xcodegen 運用のリポジトリで最も多い。`.xcodeproj` を git 管理していないため、Xcode Cloud が clone した直後には存在せず、pbxproj を書き換えようとして失敗する。

`ci_scripts/ci_post_clone.sh` の冒頭で生成させる。

```sh
if [ ! -d "$REPO/$XCODEPROJ" ] && [ -f "$REPO/project.yml" ]; then
    command -v xcodegen >/dev/null 2>&1 || brew install xcodegen
    (cd "$REPO" && xcodegen generate)
fi
```

### `Resolve Initial Setup Issues` が出て Next が押せない

Step 3 の「アプリ名の衝突」を見る。`Update…` から名前を変えればその場でリトライできる。

どうしても進めないときは `Cancel` で抜ける。**このシートで Cancel すれば副作用ゼロ**（bundle id もアプリレコードも作られない。API と git の両方で実測確認済み）。

### ウィンドウが取得できない / `windows = 0`

ディスプレイがスリープしていると System Events からウィンドウが見えない。`caffeinate -u -t 2` で起こしてから再取得する。

### スクリーンショットにターミナルが写る

`screencapture` は最前面を撮る。`osascript -e 'tell application "Xcode" to activate'` してから撮ること。

## やってはいけないこと

- **Step 0 を飛ばさない。** 既存 product に対して GUI ウィザードを回すと、想定外の画面で迷う
- **`Next` を機械的に連打しない。** 毎回タイトルを読んで照合する
- **Step 5 を飛ばさない。** ビルドが緑なのに ASC にビルドが無い、という最も分かりにくい失敗を招く
- **検証を GUI の見た目で済ませない。** 必ず API で ciProduct と app の存在を確認する
- **サインインシートが出たら自動化しようとしない。** ユーザに依頼する

## 完了条件

- [ ] `/v1/apps?filter[bundleId]=...` が1件返る（アプリレコードが存在する）
- [ ] `/v1/ciProducts` に対象アプリ名の product がある
- [ ] そのワークフローの `buildDistributionAudience` が `APP_STORE_ELIGIBLE`
- [ ] API 経由で起動したビルドが `COMPLETE` / `SUCCEEDED`
- [ ] `/v1/builds?filter[app]=...` に `processingState: VALID` のビルドがある
- [ ] **appId / ciProductId / ciWorkflowId をメモに残した**（次のスキルで使う）

## 次のスキル

`02_register_appstore` — 価格・配信国・レーティング・配信権・審査連絡先を API で登録する。
