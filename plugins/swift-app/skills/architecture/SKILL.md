---
name: architecture
description: swift-base 由来の iOS アプリの構成の正本。ブランチ運用（main でメタデータ反映、production で審査提出）と3つの GitHub Actions ＋ Xcode Cloud の役割分担、ディレクトリ規約、appstore.config.json が何を供給するか、release/<version>/ の中身、xcodegen 運用の前提、ビルド番号の採番、CI で踏んだ罠。このリポジトリの仕組みが分からなくなったとき・リリース周りを触る前・新規アプリの土台を確認するときに読む。
---

# swift-base 由来アプリの構成 — 正本

**このスキルが共通構成の正本。** 各アプリの `CLAUDE.md` は「そのアプリ固有の罠とファイル
地図」だけを書き、共通の仕組みはここを参照する（アプリの CLAUDE.md にコピーすると
22アプリで世代が分岐する）。

## 全体像 — 何が何を動かすか

```
git push/merge ──┬─ main ────────→ GitHub Actions（メタデータ反映・審査PR作成）
                 │              └→ Xcode Cloud（バイナリのビルド → ASC へ）
                 └─ production ──→ GitHub Actions（最新ビルドを審査提出 → 通過後 自動公開）
```

**バイナリのビルドは Xcode Cloud、GitHub Actions はメタデータ反映と提出のオーケストレーション。**
この分担を混同すると「ビルドが緑なのに ASC にビルドが無い」の原因を見失う。

| ブランチ操作 | 動くもの | 結果 |
|---|---|---|
| main に `release/**` を含む push | `appstore-metadata.yml` → `fastlane push_metadata` | 文言・スクショを ASC に反映 |
| main push | `release-pr.yml` | main→production の「審査PR」を自動作成／更新 |
| production に push | `appstore-release.yml` → `fastlane submit_latest_build` | 処理済みビルドを待って審査提出 → **通過後に自動公開** |
| main push（Xcode Cloud 側の設定） | Xcode Cloud ワークフロー | archive → ASC にビルドが入る |

- 公開方式は `Fastfile` の `submit_latest_build` の `automatic_release`（既定 `true` = 自動公開）
- `appstore-release.yml` はビルド処理を**最大45分待つ**ので、production マージ前にビルド完成を
  確認しておくと安全
- 日常のリリース手順は `/swift-app:release-version`、「言われたら全部やる」実行レーンは
  `/swift-app:submit-for-review`

## ディレクトリ規約

```
appstore.config.json    アプリ固有値の唯一の正本（scripts / Fastfile / post が読む）
project.yml             xcodegen の定義。★.xcodeproj は git 管理しない
CLAUDE.md               そのアプリ固有の罠とファイル地図（共通構成はこのスキルを参照）
SETUP.md                初回セットアップで人手が要る手順
.claude/rules/          Swift 規約（自動読み込み）。正本は /swift-app:conventions
.claude/settings.json   marketplace 参照（extraKnownMarketplaces / enabledPlugins）
.claude/secrets.env     harness token など（private リポジトリ前提・CLAUDE.md には参照だけ書く）
docs/adr/               意思決定の記録（/swift-app:adr で起こす）
scripts/                check_release_metadata / sync_fastlane_metadata / make_store_images / set_asc_secrets
ci_scripts/             ci_post_clone.sh（Xcode Cloud がビルド前に実行）
fastlane/Fastfile       push_metadata / submit_latest_build
.github/workflows/      appstore-metadata / release-pr / appstore-release
release/<version>/      ストア文言（.txt）・rating.json・img/
material/               画面スクショ素材（/swift-app:capture-screens が撮る）・footage/
post/                   SNS カルーセル投稿エンジン（/sns-marketing:sns-post が使う）
<AppName>/              アプリ本体。図鑑ファミリーは <AppName>/ResultKit/ に共通実装を vendor
```

## appstore.config.json — アプリ固有値の正本

新アプリにコピーしたら**まずこのファイルを全部置き換える**。`scripts/*.py`・
`fastlane/Fastfile`・`post/_brand.py`・`ci_scripts/ci_post_clone.sh` が全部ここを読む。

| 節 | 中身 |
|---|---|
| `app` | name / reading / bundle_id / scheme / xcodeproj / url_scheme / deployment_target |
| `appstore` | primary_locale（**`ja`**）/ contact_email / github_repo / カテゴリ / marketing_domain |
| `brand` | ストア画像・SNS 画像の共通カラートークン（アプリの `DesignTokens` と揃える。RGB 0-255） |
| `fonts` | 見出し用日本語フォント（Noto を実行時取得）・英字ロゴ用 ttf の相対パス |

## release/<version>/ — 提出メタデータ

**ディレクトリ名は `MARKETING_VERSION` と完全一致させる。**

```bash
grep MARKETING_VERSION <xcodeproj>/project.pbxproj | sort -u
```

| ファイル | 上限 | 備考 |
|---|---|---|
| `app_name.txt` | 30字 | **全世界で一意**。取られていたら変える |
| `subtitle.txt` | 30字 | |
| `promotional_text.txt` | 170字 | 審査なしで随時更新できる |
| `description.txt` | 4000字 | |
| `keywords.txt` | 100字 | 半角カンマ区切り・空白なし。**他フィールドと語を重複させない** |
| `whats_new.txt` | 4000字 | **初回リリースでは反映されない**（Apple 仕様。空でも正常） |
| `primary_category.txt` / `secondary_category.txt` | | 例 `PHOTO_AND_VIDEO` / `LIFESTYLE` |
| `copyright.txt` | | 「2026 名義」の形式 |
| `rating.json` | | 年齢制限の回答（fastlane deliver 形式） |
| `support_url.txt` / `privacy_url.txt` | | **必須**。開けないと審査に落ちる |
| `marketing_url.txt` | | 任意 |
| `app_privacy.md` | | 「アプリのプライバシー」の手動回答シート（CI 対象外） |
| `img/` | | ストア用スクリーンショット |

編集したら**必ず** `python3 scripts/check_release_metadata.py <version>` を通す（`PASS` 以外は
コミットしない）。ASC と同じく Unicode 1文字 = 1カウント。

## xcodegen 運用の前提

**`.xcodeproj` は git 管理しない。** 正本は `project.yml`。帰結:

- **CI には `.xcodeproj` が存在しない。** `ci_post_clone.sh` が `project.yml` から生成する
  （`xcodegen` が無ければ `brew install`）。`sync_fastlane_metadata.py` にも同じフォールバックが要る
- 新規 Swift ファイルはディレクトリに置くだけで拾われる（`sources` の1行で配下ごと）
- **SPM 依存があるアプリは Xcode Cloud のビルド#1が必ず落ちる** —
  `a resolved file is required when automatic dependency resolution is disabled`。
  xcodegen 生成の `.xcodeproj` に `Package.resolved` が無いため。対策は
  `swiftpm/Package.resolved` を git 管理し、`ci_post_clone.sh` が生成直後に
  `<xcodeproj>/project.xcworkspace/xcshareddata/swiftpm/` へコピーすること
  （mamezukan `bdb4bd4` で実証。**swift-base 本体には未取り込み** — `/swift-app:sync-base` の逆流候補）

## ビルド番号の採番

`ci_post_clone.sh` が **`CI_BUILD_NUMBER`（Xcode Cloud の単調増加値）を pbxproj の全ターゲットの
`CURRENT_PROJECT_VERSION` に一括置換**する。

- これが無いとビルド番号が固定値のままで、2回目以降の ASC アップロードが「重複」で弾かれる
  （Xcode Cloud 上は `Preparing build for App Store Connect failed` と出るだけで理由が見えない）
- アプリと App 拡張（ウィジェット等）は**ビルド番号一致が必須**なので全ターゲットまとめて置換する
- `MARKETING_VERSION`（表示バージョン）は人手で上げる運用。CI は触らない

## セットアップ（アプリごとに1回だけ）

1. `cp .env.example .env` して ASC の値を埋める（`.env` は gitignore 済み・**コミット禁止**）
2. `./scripts/set_asc_secrets.sh owner/repo` で GitHub Secrets を一括投入
3. Settings → Actions → General → Workflow permissions で
   **「Allow GitHub Actions to create and approve pull requests」を ON**（無いと審査PRが作れない）
4. **`production` ブランチを作る**（無いと `release-pr.yml` がスキップされる）
5. Xcode Cloud のワークフローを用意（`/ios-app-build:01_create_xcode_cicd`）
6. ASC 画面でしかできない初回設定は `/ios-app-build:02_register_appstore`

## 罠（実際に踏んだものだけ）

### ビルドが ASC に現れない
- **新規ワークフローの `buildDistributionAudience` は `null`。** `APP_STORE_ELIGIBLE` に PATCH
  しないと、ビルドが緑になるのに ASC にビルドが1件も現れない
- **ヘッドレスの `xcodebuild -allowProvisioningUpdates`（Apple ID セッション頼み）は CPU ほぼ0で
  永久ハングする**（2回再現）。ASC API キー認証
  （`-authenticationKeyPath` / `-authenticationKeyID` / `-authenticationKeyIssuerID`）に切り替えると即通る

### 審査提出が弾かれる
- **`primaryLocale` が `en-US` のままだと必ず弾かれる**（`is not in valid state`）。
  ウィザードで作ったアプリは既定が `en-US` なので `ja` に直す
- `support_url` / `privacy_url` が開けないと落ちる（`/ios-app-build:04_build_front` が建てる）

### メタデータ・画像
- **fastlane deliver はスクリーンショットを二重アップロードする。** DELETE で掃除する
- **初回リリースは `whatsNew` が反映されない**（Apple 仕様）

### ASC API
- **どのエンドポイントでも断続的に 500 を返す。** 全ての呼び出しをリトライ前提で書く
- **関連リソースへの GET は中身が空でも 200 を返す。** 件数まで数えて検証する
- `name` / `subtitle` は `appInfoLocalizations`、`description` / `keywords` は
  `appStoreVersionLocalizations`

### Sign in with Apple
- **実機で「登録を完了できませんでした」になったら、App ID の capability を Developer Portal の
  GUI で OFF→保存→ON→保存し、その後に新ビルドを作る**（Hanasu で実証）。
  entitlements と ASC API 上の設定が正しくてもこうなる。**ASC API の capability DELETE→POST では
  直らない**（Portal GUI の保存と等価ではない）。トグル後の**新ビルドが必須**

### 完了判定
- **GUI の見た目や `BUILD SUCCEEDED` で完了と判断しない。** 必ず API で裏を取る
  （`appStoreState` が `WAITING_FOR_REVIEW` になったか等）
