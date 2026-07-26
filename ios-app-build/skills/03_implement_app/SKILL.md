---
name: 03_implement_app
description: CONCEPT.md と DESIGN.md に沿って iOS アプリの P0 機能を実装します。オンボーディング、設定画面（ダークモード切替・規約リンク・バージョン5回タップ）、集約レイヤ（Tokens/Strings/AppStorageKeys/Haptics）といった共通部分の型も含みます。シミュレータでのビルド・起動・スクリーンショット取得まで行います。
---

# アプリ本体の実装 (03_implement_app)

## このスキルの位置

```
02_register_appstore → [03_implement_app] → 04_build_front → 05_release_assets → ...
```

`00_setup_repo` で「ビルドが通る最小のアプリ」までできている前提。ここで中身を作る。

## 読むもの（この順で）

1. `CONCEPT.md`（リポジトリ直下）— **P0 だけを実装する。P1/P2 には手を出さない**
2. `DESIGN.md`（同）— 色・タイポ・モチーフ・モーション・画面ごとのムード
3. `${CLAUDE_PLUGIN_ROOT}/skills/design-crafting/DESIGN_BASE.md` — 全アプリ共通のデザイン原則。Tokens の初期値とサンプルコード
4. `.claude/rules/`（リポジトリ内）— Swift のコーディング規約
5. `~/workspace/hioto/hioto/Onboarding/` と `Settings/SettingsView.swift` — **構造だけ真似る。コードはコピーしない**

## 必ず入れる共通部分

アプリ固有の機能とは別に、**全アプリに入れる決まり**のものがある。

### 集約レイヤ（`.claude/rules/` が前提としている）

| ファイル | 役割 |
|---|---|
| `Design/Tokens.swift` | 色・余白・角丸・影。色は `Color(hex:)` の dynamic provider で light/dark を出し分ける |
| `Strings.swift` | 全文言。`enum` × `String(localized:)` + `Localizable.xcstrings`（日英） |
| `AppStorageKeys.swift` | `@AppStorage` のキーを1箇所に集める |
| `Haptics.swift` | 触覚フィードバックの薄いラッパ |
| `DisplayDate.swift` | 日付表示の共通化 |

**文字列リテラルを View に直書きしない。色を `Color(red:...)` で直書きしない。** 規約違反になる。

### オンボーディング

- 数枚のページ + 自前のページインジケータ + スキップ
- `@AppStorage(AppStorageKeys.hasCompletedOnboarding)` で制御し、`.fullScreenCover` で出す
- **「診断でもセラピーでもない、私的なユーティリティである」旨を明示する**（審査リスク回避）

### 設定画面

これらを**必ず**入れる。

1. **外観の切替**: ライト / ダーク / システム準拠。`@AppStorage` + `.preferredColorScheme`
2. **利用規約・プライバシーポリシーへのリンク**: `Link` で外部 Safari。URL は `https://<appname>.basaapp.com/terms` と `/privacy`（`04_build_front` で実際に建てる）
3. **バージョン表示**
4. **バージョン行を1秒以内に5回タップでオンボーディング再表示**（隠し機能）

5回タップの実装（hioto の `registerVersionTap()` 相当）:

```swift
@State private var tapCount = 0
@State private var firstTapAt: Date?

private func registerVersionTap() {
    let now = Date()
    if let first = firstTapAt, now.timeIntervalSince(first) > 1.0 {
        tapCount = 0
        firstTapAt = nil
    }
    if firstTapAt == nil { firstTapAt = now }
    tapCount += 1
    if tapCount >= 5 {
        tapCount = 0
        firstTapAt = nil
        hasCompletedOnboarding = false   // @AppStorage
        Haptics.success()
    }
}
```

### シグネチャのアニメーション

DESIGN.md の「シグネチャ要素」を実装する。**Lottie は入れない**（依存が増え、素材の `ip`/`op`/`st` 欠落で全滅する罠がある）。
SwiftUI 標準の `Canvas` / `TimelineView` / `withAnimation` で書く。

**`accessibilityReduceMotion` が有効なときは簡略版に落とす。**

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion
```

## 実装しないもの

- テストターゲット（swift-base の ADR 方針。`project.pbxproj` の自動編集が危険なため）
- P1 / P2 の機能
- `front/`（`04_build_front` の担当）
- 本番の AppIcon（プレースホルダのままでよい。差し替えは `icon-crafting` スキルで行う）

## 手順

### Step 1. ディレクトリを切る

```
<App>/
  <App>App.swift          @main
  ContentView.swift       オンボーディングのゲート + タブ
  Design/                 Tokens.swift, シグネチャのアニメーション
  Onboarding/             OnboardingView.swift + 各ページ
  Settings/               SettingsView.swift
  Models/                 SwiftData の @Model
  Home/ Archive/ ...      CONCEPT.md の画面一覧に対応
  Resources/              Localizable.xcstrings
  Info.plist
  Assets.xcassets
```

xcodegen は `sources: [<App>]` を丸ごと拾うので、**ファイルを置くだけでターゲットに入る**。
ただし `.xcodeproj` は git 管理外なので、**ファイルを追加したら `xcodegen generate` を再実行する**。

### Step 2. 実装する

`Tokens` → `Strings` → モデル → 画面、の順が手戻りが少ない。

### Step 3. ビルドを通す ★警告ゼロまで

```bash
xcodegen generate
xcodebuild -project <App>.xcodeproj -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro Max' build 2>&1 | tail -40
```

`** BUILD SUCCEEDED **` かつ警告ゼロを目指す。失敗したら `error:` 行を読む。

### Step 4. シミュレータで実際に動かす ★見た目を確認する

**ビルドが通っただけで「できた」と言わない。** 起動して、画面を見る。

```bash
xcrun simctl boot "iPhone 17 Pro Max" 2>/dev/null || true
open -a Simulator

APP_PATH=$(xcodebuild -project <App>.xcodeproj -scheme <App> \
  -destination 'platform=iOS Simulator,name=iPhone 17 Pro Max' \
  -showBuildSettings 2>/dev/null | awk -F' = ' '/ BUILT_PRODUCTS_DIR /{d=$2} / FULL_PRODUCT_NAME /{n=$2} END{print d"/"n}')

xcrun simctl install booted "$APP_PATH"
xcrun simctl launch booted com.basaapp.<appname>
sleep 3
xcrun simctl io booted screenshot material/screenshot_dev_1.png
```

**オンボーディング・メイン・設定・シグネチャ演出・ダークモード**の5枚以上を撮り、
`Read` ツールで**実際に画像を見て**、DESIGN.md の指定と合っているか確認する。

### デモデータは「ストア画像に写る」前提で書く ★審査リスク

スクリーンショットを撮るために、`#if DEBUG` の `DemoSeeder` でサンプルデータを流し込むとよい。
**そのサンプル文が、そのままストア画像に載る。**

- **医療・健康・診断を連想させる文言を入れない**（「健康診断の再検査」など）。ガイドライン 2.3.x のリジェクト理由になる
- 実在の企業名・人名・商標を入れない
- コンセプトが一目で伝わる、日常的で無害な例にする

タップ操作は CLI から自動化できない。演出のフレームを撮りたいときは、
DEBUG 限定の環境変数フックを仕込む（hioto と同じ方式。Release には含めない）。

```swift
#if DEBUG
if ProcessInfo.processInfo.environment["APP_DEMO_RITUAL"] != nil { /* 自動再生 */ }
#endif
```

```bash
xcrun simctl launch --terminate-running-process booted com.basaapp.<appname> \
  --setenv APP_DEMO_RITUAL=1
```

ダークモードのスクリーンショット:

```bash
xcrun simctl ui booted appearance dark
xcrun simctl io booted screenshot material/screenshot_dev_6_dark.png
xcrun simctl ui booted appearance light
```

### Step 4.5. 敵対的レビューにかける

コミットする前に、`adversarial-panel` スキルで実装方針を敵対的レビューにかける。
狙うのはコードの機械的なバグ検出（それは `/code-review` の役割）ではなく、**設計判断・スコープ判断の妥当性**。

- 実装が CONCEPT.md / DESIGN.md の要求（コア体験・画面一覧・モチーフ・シグネチャ要素）を実際に満たしているか
- P0 の線引きが妥当か（削りすぎ・盛りすぎがないか）
- 審査リジェクトリスク（デモデータの医療・診断連想文言、実在の商標・人名、規約リンク切れ等）が残っていないか

パネリストには CONCEPT.md / DESIGN.md と、実装のディレクトリ構成・主要ファイル・撮ったスクリーンショットを brief として渡す。

### Step 5. コミットする

```bash
git add -A
git commit -m "$(cat <<'EOF'
<App>: P0 実装（オンボーディング・<コア体験>・設定）

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
git push origin main
```

**main に push すると Xcode Cloud が自動ビルドする**（`01` で設定済み）。
ビルド結果を確認すること。

```bash
export ASC_API=${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js
node $ASC_API GET "/v1/ciProducts/<ciProductId>/buildRuns?limit=1&sort=-number" | tail -n +2 | python3 -c "
import json,sys
b=json.load(sys.stdin)['data'][0]['attributes']
print('#'+str(b['number']), b['executionProgress'], b.get('completionStatus'), b.get('startReason'))
"
```

**自動起動しないことがある。** 最新の buildRun の `sourceCommit` が自分の commit でなければ、手で起動する。

```bash
RID=$(node $ASC_API GET "/v1/ciProducts/<ciProductId>/buildRuns?limit=1&sort=-number" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
curl -s "https://harness.basaapp.com/api/appstore/ci/builds/$RID" -H "Authorization: Bearer $HARNESS_TOKEN" | python3 -c "
import json,sys; b=json.load(sys.stdin)['buildRun']
print('commit:', (b.get('sourceCommit') or {}).get('commitSha','')[:8])"
git rev-parse --short HEAD

# 違っていたら手動起動
node $ASC_API POST /v1/ciBuildRuns '{"data":{"type":"ciBuildRuns","relationships":{"workflow":{"data":{"type":"ciWorkflows","id":"<ciWorkflowId>"}}}}}'
```

## 罠

### 実機ビルドで落ちる SwiftUI コード

シミュレータで通っても Xcode Cloud（実機向けアーカイブ）で落ちることがある。
`main` に push したあと **必ず buildRun の結果を見る**こと。

### Lottie を使いたくなったら

素材の JSON は、**1レイヤーでも `ip` / `op` / `st` が欠けていると部分的に壊れるのではなく丸ごと真っ白になる**。
このスキルでは使わない方針だが、どうしても必要なら全レイヤーを検証してから入れる。

### ファイルを消したとき

`.xcodeproj` は生成物なので `xcodegen generate` を打ち直す。
git の `deleted:` を確認して、消し忘れ・消しすぎがないか見る。

## 完了条件

- [ ] `xcodebuild build` が `BUILD SUCCEEDED`、警告ゼロ
- [ ] シミュレータで起動し、クラッシュしない
- [ ] スクリーンショットを5枚以上撮り、**画像を実際に見て** DESIGN.md と照合した
- [ ] 設定画面に「外観切替」「規約リンク」「バージョン」「5回タップでオンボーディング復帰」が全部ある
- [ ] 文言が `Strings` に集約され、色が `Tokens` に集約されている
- [ ] `adversarial-panel` スキルで敵対的レビューをかけた（CONCEPT.md/DESIGN.mdとの整合性・P0の線引き・審査リジェクトリスク)
- [ ] main に push し、Xcode Cloud のビルドが `SUCCEEDED`

## 次のスキル

`04_build_front` — 利用規約・プライバシーポリシー・サポートのサイトを建てる（設定画面のリンク先）。
