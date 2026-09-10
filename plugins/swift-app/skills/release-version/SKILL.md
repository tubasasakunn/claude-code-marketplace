---
name: release-version
description: 新バージョンとして App Store に出すための一連の手順（バージョン番号上げ → メタデータ → main マージで自動反映＆審査PR → Xcode Cloud ビルド → production マージで審査自動提出 → 通過後に自動公開）をまとめた運用ランブック。バージョンアップ時・リリースの仕組みを確認したいときに使う。
argument-hint: "[新しいバージョン番号 例: 1.2.0]"
allowed-tools: Read, Edit, Bash, Grep, Glob
---

# リリース手順（バージョンアップ → 審査提出 → 自動公開）

新バージョンを App Store に出すまでの運用ランブック。ストア文言・画像の作成は
`/swift-app:release-assets`、文字数上限や Secrets の詳細は `release/README.md` が正本。
ここは「どのブランチに何をマージすると何が自動で起きるか」を一望するための入口。
アプリ固有値（xcodeproj 名・bundle id・連絡先）は `appstore.config.json` を参照。

## 0. 全体像（誰が何をやるか）

| 役割 | 担い手 |
|---|---|
| バイナリ（ipa）のビルド・アップロード | **Xcode Cloud**（GitHub の CI ではやらない） |
| メタデータ・スクショの ASC 反映 | `appstore-metadata.yml`（main の `release/**` 変更で起動） |
| 審査PR（main→production）の自動作成 | `release-pr.yml`（main push で、production に無い版を検出） |
| 最新ビルドを選んで審査へ提出 | `appstore-release.yml`（**production への push**で起動）→ `fastlane submit_latest_build` |
| 審査通過後のストア公開 | **自動**（`automatic_release: true`。手動にしたいなら Fastfile を false に） |

ブランチの意味：
- **main** … 反映・プレビューと審査PRの起点。
- **production** … 「審査に出した／出す版」。ここに入ると審査提出が走る。
  production の `release/` に無い版＝まだ出していない版、という判定で審査PRが立つ。

```
release/<ver>/ を main へ
  → appstore-metadata.yml: メタデータ反映（プレビュー）
  → release-pr.yml: 「<ver> 審査PR」(main→production) を自動作成/更新
Xcode Cloud: <ver> のビルドをアップロード
「<ver> 審査PR」を production へマージ
  → appstore-release.yml: 処理済み最新ビルドを待って submit_for_review
審査通過 → 自動公開（automatic_release: true）
```

## 0.5 依存を更新したリリースなら、先に課金を確認する

**RevenueCat SDK のバージョンを上げるなら、リリース前に `/swift-app:purchase-health` を通す。**
ダッシュボードのペイウォールに眠っていた設定が SDK 更新で有効になり、購入ボタンが
エラーも出さずに無反応になることがある。コードは 1 行も変わらないので、
リリース後に気づくまで数か月かかる（実際に 3 か月分の売上を失った事故がある）。

リリース後の動作確認は**新規インストール**で行う。ペイウォールの A/B テストは
`only_new` で配信されるため、既存アカウントでは新規ユーザーだけが踏むバグを再現できない。

## 1. バージョン番号を上げる

`<xcodeproj>/project.pbxproj` の **`MARKETING_VERSION`**（アプリ・拡張の全コンフィグ）
を上げる。`CURRENT_PROJECT_VERSION`（ビルド番号）も上げておくが、**Xcode Cloud では
`ci_scripts/ci_post_clone.sh` が `CI_BUILD_NUMBER` で上書き**するので最終的な
ビルド番号は Xcode Cloud 側で一意になる。

```bash
sed -i 's/MARKETING_VERSION = <old>;/MARKETING_VERSION = <new>;/g' \
  <xcodeproj>/project.pbxproj
grep -n "MARKETING_VERSION" <xcodeproj>/project.pbxproj
```

- 全コンフィグ（アプリ＋ウィジェット等の App 拡張）で同じ値になることを確認
  （`sync_fastlane_metadata.py` は `MARKETING_VERSION` が一意でないと止まる）。
- **重要なのは後述の `release/<version>/` ディレクトリ名が `MARKETING_VERSION` と
  完全一致すること**。

## 2. リリース素材（release/<version>/）

`/swift-app:release-assets` を使う。骨子だけ再掲：

- 前バージョンを丸ごとコピーして始める：`cp -r release/<prev> release/<new>`。
  **`sync_fastlane_metadata.py` は必要なテキスト＋スクショが全部揃っていないと止まる**
  ため、差分が無いファイル（説明・キーワード・URL・スクショ等）も必ず同梱する
  （CI は毎回フルセットを ASC に再送する）。
- バージョン固有で必ず書き換えるのは **`whats_new.txt`**（そのバージョンの変更点）。
  画面が変わったときは `material/` を撮り直して `make_store_images.py` で `img/` を再生成。
- 検証：`python3 scripts/check_release_metadata.py <version>` が `PASS`。

サポート／プライバシー URL のサイト（マーケティングサイト）に出すべき変更があれば
それも先にデプロイする（審査時に開けないと却下）。

## 3. コミット → main へマージ（あなたがマージ）

コミットしてマージすると main で 2 つ自動で動く：

1. `appstore-metadata.yml` … メタデータ・スクショを ASC へ反映（バイナリ・提出はしない）。
2. `release-pr.yml` … production に無い `release/<version>/` を検出し、
   **「<version> 審査PR」(main→production) を作成／更新**。

> どちらも main 上のワークフロー定義で動く。新規ワークフロー自体を入れた回は、
> その変更を含む push から評価される。

## 4. Xcode Cloud でビルドをアップロード

当該 `MARKETING_VERSION` の archive を Xcode Cloud でアップロード。
処理（ASC 側の "PROCESSING"）が終わると TestFlight に出る。

## 5. 「<version> 審査PR」を production へマージ → 審査提出

production への push で `appstore-release.yml` → `fastlane submit_latest_build`：

- ASC のバイナリ処理完了を**最大 45 分ポーリング**で待つ。
- 処理済み最新ビルドを当バージョンに紐付け、メタデータ反映 ＋ `submit_for_review`。
- 提出申告（`submission_information`）は Fastfile の既定：輸出コンプラ=暗号化なし
  （Info.plist の `ITSAppUsesNonExemptEncryption=false` と一致）／第三者コンテンツなし
  ／IDFA 不使用。**アプリの実態に合わせて Fastfile で調整**（BGM・フォント等を収録するなら
  `content_rights_contains_third_party_content: true` にし、ASC の「コンテンツ配信権」も設定）。

## 6. 審査通過 → 自動公開

`automatic_release: true` なので、**審査通過後に自動でストア公開**される。
手動公開（通過後に ASC で「リリース」を押す運用）にしたいなら `fastlane/Fastfile` の
`submit_latest_build` を `automatic_release: false` に変える。

## 前提（一度だけ／毎回）

- **GitHub Secrets**（毎回使う）：`ASC_KEY_ID` / `ASC_ISSUER_ID` / `ASC_KEY_CONTENT`
  （.p8 の base64）と連絡先 `ASC_CONTACT_FIRST_NAME` / `_LAST_NAME` / `_PHONE` / `_EMAIL`。
  **審査提出には電話番号が必須**。`ASC_CONTACT_PHONE` は国内表記（070/080/090…）で可
  ── Fastfile が先頭 0 を外して `+81` を付け E.164 へ正規化する。
- **初回のみの ASC 画面設定**（更新版では再要求されない）：価格・コンテンツ配信権・
  「アプリのプライバシー」（`release/<ver>/app_privacy.md`）。詳細は `release/README.md`。
- production ブランチが存在すること（無いと `release-pr.yml` はスキップ）。
- **GitHub リポジトリ設定**：Settings → Actions → General → Workflow permissions の
  「**Allow GitHub Actions to create and approve pull requests**」を ON にする。
  OFF だと `release-pr.yml` の PR 作成が
  `GitHub Actions is not permitted to create or approve pull requests` で失敗する
  （その場合は審査PRを手動で作る：base=production / head=main / タイトル「<version> 審査PR」）。

## 罠・注意

- **ディレクトリ名 = `MARKETING_VERSION` 完全一致**。ずれると sync が止まる／
  別バージョン扱いになる。
- **`release/` の全ファイルが必須**（差分が無くても同梱）。`whats_new.txt` だけは
  毎回そのバージョンの内容へ。
- ビルド番号は Xcode Cloud（`ci_post_clone.sh`）が上書きするので、pbxproj の
  `CURRENT_PROJECT_VERSION` 手上げはローカル/直アーカイブ時の保険。
- ワークフローは**そのブランチに定義が存在しないと起動しない**
  （main: metadata/release-pr、production: appstore-release）。main→production の
  マージで production 側に appstore-release.yml が乗る。
- fastlane はリモートセッションで実走できない。Fastfile を触ったら
  `ruby -c fastlane/Fastfile` の構文チェックに留め、初回は production への本番マージ前に
  `appstore-release.yml` を workflow_dispatch で 1 度試すのが安全。
- 審査PRは main→production の 1 本のみ（同 head/base）。複数版が溜まると
  最新版のタイトルに更新される。

## 関連ファイル

```
<xcodeproj>/project.pbxproj          ─ MARKETING_VERSION / CURRENT_PROJECT_VERSION
<app>/Info.plist                     ─ ITSAppUsesNonExemptEncryption=false（輸出コンプラ）
ci_scripts/ci_post_clone.sh          ─ Xcode Cloud でビルド番号を CI_BUILD_NUMBER に上書き
release/<version>/                    ─ メタデータ＋スクショ（/swift-app:release-assets で用意）
scripts/check_release_metadata.py    ─ 文字数チェック
scripts/sync_fastlane_metadata.py    ─ release/ → fastlane/ 変換（全ファイル必須）
fastlane/Fastfile                    ─ push_metadata / submit_latest_build レーン
.github/workflows/appstore-metadata.yml ─ main の release/** で metadata 反映
.github/workflows/release-pr.yml        ─ main push で main→production 審査PR を自動作成
.github/workflows/appstore-release.yml  ─ production push で最新ビルドを審査提出→自動公開
release/README.md                    ─ Secrets・初回セットアップ・提出ブロッカーの正本
.claude/skills/release-assets/       ─ メタデータ／ストア画像の作成スキル
```

## チェックリスト

- [ ] `MARKETING_VERSION` を全コンフィグで上げた（値が一意）。
- [ ] `release/<MARKETING_VERSION>/` を作り、`whats_new.txt` を更新、他は同梱した。
- [ ] `check_release_metadata.py <version>` = PASS。
- [ ] 必要ならマーケティング／サポートサイトを更新・デプロイ。
- [ ] main へマージ（→ metadata 反映＋審査PR 自動作成を確認）。
- [ ] Xcode Cloud で当該バージョンのビルドをアップロード。
- [ ] 審査PR を production へマージ（→ appstore-release.yml の提出成功を確認）。
- [ ] 審査通過後、自動公開されたことを ASC で確認。
