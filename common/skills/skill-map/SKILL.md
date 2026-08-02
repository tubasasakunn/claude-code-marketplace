---
name: skill-map
description: この marketplace の全スキルの索引と使い分け。どんなスキルがあるか分からない・どれを使うか迷う・似た名前のスキルの違いを知りたい・スキルを追加や修正したいときに最初に読む。プラグインごとの一覧は自動生成なので常に実態と一致する。
---

# スキルの地図

## ★ スキルを直すときは、必ずこの marketplace リポジトリを直す

```bash
cd ~/workspace/claude-code-marketplace   # ここが唯一の正本
# 編集 → commit → push → 各リポジトリは次のセッション開始時に pull で取り込む
python3 common/scripts/build_skill_map.py     # スキルを増減したらこの索引を再生成
```

**`~/.claude/plugins/cache/` 配下を直接編集しても、次の `plugin marketplace update` で消える。**
アプリや workspace の `.claude/skills/` にスキルを置かない（そこは空のまま維持する）。

コード資産（`.github/workflows/`・`fastlane/`・`ci_scripts/`・`scripts/`・`.claude/rules/`・
`ResultKit`）は CI がリポジトリ内のファイルを実行するため marketplace では配れない。
**正本は swift-base で、配布は `/swift-app:sync-base`** が担う。この非対称に注意する。

## どこで何が使えるか

| 開いているリポジトリ | 有効なプラグイン |
|---|---|
| アプリリポジトリ（hioto / hanasu / mamezukan …） | `common` + `swift-app` |
| ios-app-build-workspace | `common` + `ios-app-build` |
| app-store-optimize-workspace | `common` + `app-store-optimize` |
| sns-marketing-workspace / marketing | `common` + `sns-marketing` |
| どこでも（user スコープで導入） | `cloudflare` + `canva` + `writing` |

`cloudflare`（Workers / Wrangler / D1 / Durable Objects / Email / Turnstile / web-perf）と
`canva`（AI 画像生成）は、以前 `~/.claude/skills/` に直接置いていたものを marketplace へ
移した。リポジトリを問わず使うので user スコープで入れてある。

スキルが見えないときは、そのリポジトリの `.claude/settings.json` の `enabledPlugins` を疑う。

## 外部プラグイン（この marketplace が参照しているだけ・中身は他人のリポジトリ）

下の自動生成一覧には出ない（`skills/` の実体がここに無いため）。**中身の更新は相手側で行われ、
`claude plugin marketplace update` で追従する。**

| プラグイン | 出所 | 中身 |
|---|---|---|
| `ui-ux-pro-max` | `nextlevelbuilder/ui-ux-pro-max-skill` | UI/UX の大規模リファレンス（7スキル。84スタイル・192配色・22スタック） |
| `RevenueCat` | `RevenueCat/ai-toolkit` の `revenuecat` | 課金実装一式（16スキル。ペイウォール・購入フロー・テスト） |
| `revenuecat-play-billing` | 同上の `revenuecat-play-billing` | Google Play Billing 固有 |
| `frontend-design` | `anthropics/claude-plugins-official` の `plugins/frontend-design` | 視覚デザインの方向づけ |
| `gopls-lsp` | 同上の `plugins/gopls-lsp` | Go の LSP 連携 |
| `using-cmux` | `hummer98/using-cmux` | cmux 内での操作 |
| `last30days` | `mvanhorn/last30days-skill` | 直近30日の Reddit / HN / YouTube / Polymarket / GitHub を engagement 実数順で収集。**APIキー不要**（TikTok/Instagram だけ ScrapeCreators キーが要る） |
| `marketing-skills` | `coreyhaines31/marketingskills` | マーケ 49 スキル（CRO・コピー・ペイウォール・価格・A/B・ローンチ） |
| `tiktok-video-skills` | `iart-ai/tiktok-video-skills` | 短尺縦動画の構成知見 4 本（フック→リテンション→ループ、9:16 セーフエリア、単語単位キャプション、カウントダウン） |

**`last30days` は「想像で書く」を潰すために入れてある。** SNS のネタ出し（`/sns-marketing:sns-post`）、
ASO のキーワード源泉（`/app-store-optimize:aso` の 1-1）、アプリ企画のインサイト取り
（`/ios-app-build:concept-crafting` の第2章前）で、各スキル側から明示的に呼ぶよう書いてある。

**`tiktok-video-skills` は知見だけ取って実装は流用しない。** 中身は全部 Remotion（ヘッドレス Chrome）前提で、
`/sns-marketing:promo-video` の「ブラウザや外部サービスに依存しない（PIL でフレーム合成 → ffmpeg）」
という設計方針と正面から衝突する。**構成の文法だけ読んで、描画は promo-video のエンジンで書く。**

`marketing-skills` は英語圏 SaaS 前提で 49 本ある。日本語ストア文言をそのまま任せる相手ではなく、
設計判断（価格の刻み方・ペイウォールの位置・A/B の回し方）の材料として引く。
`app-store-optimize` にだけ入れてあるのは、`sns-marketing` にも入れると自作の `sns-post` /
`tone-post` と description が競合するため。

**見送ったもの**：`renezander030/capcut-cli`（CapCut / 剪映のドラフト直編集）。この Mac に CapCut が
無く、かつ `promo-video` が GUI を介さない完全プログラム生成なので、量産パイプラインの方向と逆。
さらに SessionStart フックが毎回無言で `npm i -g capcut-cli` を実行する作りだった。

他人のプラグインを足すときは `.claude-plugin/marketplace.json` に参照を書くだけでよい
（コピーしない）:

```json
{ "name": "x", "source": { "source": "github", "repo": "owner/repo" } }
{ "name": "y", "source": { "source": "git-subdir", "url": "https://github.com/owner/repo.git",
                           "path": "plugins/y", "ref": "main" } }
```

相手の破壊的変更を避けたいときは `"sha": "..."` でピン留めする（今は `ref: main` で追従）。
新しいプラグインを探すときは `claude-plugins-official`（273本のカタログ）を見る。

## 場面別の引き方

**新しいアプリを1本作る** → `/ios-app-build:08_run_pipeline` を呼ぶだけ。中で 00〜07 と
コンセプト出し・デザイン仕様を順に委譲する。途中から再開・1工程だけやり直すときは番号を直接指定。

**既存アプリのコードを触る** → 書く前に `/swift-app:conventions` の該当領域を読む →
書いた後に `/swift-app:verify-build` → コミット前に `/swift-app:bug-check` と
`/swift-app:audit-conventions` → 設計を決めたら `/swift-app:adr`。

**リリースする** → `/swift-app:release-version`（仕組みと手順）→ 素材は
`/swift-app:release-assets` → 全部任せるなら `/swift-app:submit-for-review`。

**ストア素材を作る** → `/app-store-optimize:aso`（何を訴求するか）→
`/app-store-optimize:screenshot-crafting`（何を写すか）→ `/swift-app:store-layouts`（どう並べるか）
→ `/swift-app:capture-screens`（素材を撮る）→ `/swift-app:release-assets`（置いて反映）。

**SNS に投稿する** → `/sns-marketing:carousel-craft`（デザインの正本）→
`/sns-marketing:sns-post`（1本作る）→ `/sns-marketing:tiktok-post` `lemon8-post`（実投稿）。
毎日回すなら `/sns-marketing:sns-daily-pipeline`。

**仕組みが分からなくなった** → `/swift-app:architecture`（ブランチ運用・ディレクトリ規約・CI の罠）。

**iOS で何ができるか調べる** → `/swift-app:ios-capabilities`（iOS 26 の能力カタログ）。

**日本語の文章を書く・推敲する** → `/writing:japanese-tech-writing`（技術文書の規範）。
平坦でおもしろくないと感じたら `/writing:cognitive-rhythm-writing`（緩急の設計）。
ストア文言・SNS 本文・ADR・README のどれにも効く。

**判断に確信が持てない** → `/common:adversarial-panel`（多モデルで殴り合わせる）。
**ユーザに聞く・報告する** → `/common:talk_to_user`（LINE）。

## 迷いやすいペアの判別

| 迷う組 | 違い |
|---|---|
| `release-version` と `06_submit_review` | 前者は2本目以降の日常リリース、後者は**初回**審査提出 |
| `release-version` と `submit-for-review` | 前者は仕組みの説明（ランブック）、後者は「言われたら全部やる」実行レーン |
| `screenshot-crafting` と `store-layouts` | 何を写すか決める / どう並べるか決める |
| `capture-screens` と `release-assets` | アプリの生スクショを撮る / ストア用に加工して置く |
| `conventions` と `audit-conventions` | 規約を読む（書く前）/ 違反を走査する（書いた後） |
| `bug-check` と `audit-conventions` | 動かすと壊れる挙動バグ / 規約違反 |
| `architecture` と 各アプリの `CLAUDE.md` | 共通の仕組み（正本）/ そのアプリ固有の罠とファイル地図 |
| `sync-base` と marketplace の pull | コード資産の配布（能動）/ スキルの取得（自動） |

<!-- BEGIN GENERATED — python3 common/scripts/build_skill_map.py で再生成する -->

**全 67 スキル / 9 プラグイン**

### `common`（11本） — 全リポジトリで有効化

| スキル | 何をするか |
|---|---|
| `/common:adversarial-panel` | Run a multi-model adversarial mutual review with facilitator synthesis — the "Fable 5-style" metacognition pattern, reproducible on Opus or any Claud… |
| `/common:cloud-routines` | Claude Code の Routines（クラウド上でスケジュール/API/GitHub イベントにより自動実行されるエージェント）の作成・管理・設計を支援します。 |
| `/common:commit` | 現在の変更を確認し、全てステージングして日本語のConventional Commitsでコミット。 |
| `/common:find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skill that can...", or … |
| `/common:local-cron` | このマシンの crontab を操作して、定期ジョブや「指定時刻に1回だけ走って自分の登録を消すワンショット」を仕込みます。 |
| `/common:new-routine-site` | ~/workspace/routine 配下に、Claude Code Routine が定期実行でコンテンツを追加する新しいサイトを 0 から立ち上げます（Hono+Vite+bun+Cloudflare Workers、xxx.basaapp.com、記事台帳による重複防止、cloud rou… |
| `/common:plugin-guide` | Claude Codeプラグインの作成、インストール、管理について説明します。 |
| `/common:push` | 現在のブランチをリモートにpush。 |
| `/common:skill-creator` | Claude Code用のスキルを作成・修正します。 |
| `/common:skill-map` | この marketplace の全スキルの索引と使い分け。 |
| `/common:talk_to_user` | LINE 越しにユーザへ報告し、質問し、返信を待ちます。 |

### `swift-app`（15本） — 各アプリリポジトリで有効化

| スキル | 何をするか |
|---|---|
| `/swift-app:adr` | アーキテクチャ・データモデル・並行性方針・依存ライブラリなどの意思決定をしたとき、docs/adr/ に ADR（意思決定の記録）を起こす。 |
| `/swift-app:architecture` | swift-base 由来の iOS アプリの構成の正本。 |
| `/swift-app:audit-conventions` | コーディング規約（Tokens / Strings / DisplayDate / 強制アンラップ禁止など）への違反をリポジトリ全体から走査して報告する。 |
| `/swift-app:bug-check` | コミット直前に diff をバグ観点で精査する。 |
| `/swift-app:capture-screens` | アプリの全画面スクリーンショットを material/screens/ に撮り揃える。 |
| `/swift-app:codex-app-server-swift` | Codex CLI の app-server（JSON-RPC 2.0 サーバー）を、ChatGPTアカウントのOAuthログイン経由でSwift(iOS/macOS)アプリから使うための知識リファレンス。 |
| `/swift-app:conventions` | Swift / SwiftUI のコーディング規約の正本（7領域・628行）。 |
| `/swift-app:icon-crafting` | Icon Composer の `.icon` バンドル（Liquid Glass アプリアイコン）を、GUIアプリを一切開かずスクリプトで生成し、actool でコンパイル検証し、Xcodeプロジェクトへ組み込みます。 |
| `/swift-app:ios-capabilities` | 最新iOS（現在はiOS 26世代）でサードパーティアプリができること（新API・制約・最低OSバージョン・エンタイトルメント要否・審査上の注意）の調査知識を提供します。 |
| `/swift-app:release-assets` | App Store 提出用のリリース素材一式（メタデータ .txt とストア画像）を release/<version>/ に用意・更新する。 |
| `/swift-app:release-version` | 新バージョンとして App Store に出すための一連の手順（バージョン番号上げ → メタデータ → main マージで自動反映＆審査PR → Xcode Cloud ビルド → production マージで審査自動提出 → 通過後に自動公開）をまとめた運用ランブック。 |
| `/swift-app:store-layouts` | App Store のストア画像を「構図」から設計・制作する。 |
| `/swift-app:submit-for-review` | 「審査提出して」「リリースして」「ship して」と言われたら、この一連を最後まで自動で回す ── 作業ブランチ→main へ PR 作成＆マージ→Xcode Cloud ビルド完成を harness API で待つ→失敗なら修正して最初へ戻る→main→production の審査PRをマージ→… |
| `/swift-app:sync-base` | swift-base の雛形資産（.claude/rules・GitHub Actions・fastlane・ci_scripts・scripts・post・ResultKit）が各アプリでどれだけ古いかを表にし、逆流と配布を判断する。 |
| `/swift-app:verify-build` | xcodebuild でビルド検証し、.swift 由来の warning / error をベースライン（0 / 0）と比較する。 |

### `ios-app-build`（11本） — ios-app-build-workspaceで有効化

| スキル | 何をするか |
|---|---|
| `/ios-app-build:00_setup_repo` | 新規iOSアプリのリポジトリを作ります。 |
| `/ios-app-build:01_create_xcode_cicd` | 新規iOSアプリの「App Store Connect アプリレコード作成」と「Xcode Cloud の CI/CD 設定」を、AppleScript で Xcode の GUI を自動操作して一度に完了させます。 |
| `/ios-app-build:02_register_appstore` | App Store Connect の初期登録を API で全部済ませます。 |
| `/ios-app-build:03_implement_app` | CONCEPT.md と DESIGN.md に沿って iOS アプリの P0 機能を実装します。 |
| `/ios-app-build:04_build_front` | アプリの利用規約・プライバシーポリシー・サポートページを Hono + Vite + Cloudflare Workers で生成し、(アプリ名).basaapp.com へデプロイします。 |
| `/ios-app-build:05_release_assets` | App Store のストア文言（アプリ名・サブタイトル・キーワード・説明文）とストアスクリーンショットを release/<version>/ に用意します。 |
| `/ios-app-build:06_submit_review` | iOSアプリを App Store の審査に提出します。 |
| `/ios-app-build:07_watch_review` | App Store の審査結果を監視し、リジェクトに対応し、リリース後のユーザレビューを読んで返信します。 |
| `/ios-app-build:08_run_pipeline` | アイデア一言を受け取り、コンセプト出しから App Store の審査提出までを一気に走らせる指揮役です。 |
| `/ios-app-build:concept-crafting` | 漠然としたアイデアを、新しい価値をひとつの言葉で言い当てる「コンセプト」へと磨き上げるためのワークフロー(問いを立てる→ストーリーを設計する→1行に凝縮する→用途に最適化する)とチェックリストを提供します。 |
| `/ios-app-build:design-crafting` | コンセプト文書(CONCEPT.md)とデザインの基礎嗜好(DESIGN_BASE.md)から、そのアプリ固有のビジュアルデザイン仕様書(DESIGN.md)を作り上げるワークフロー(コンセプトを色・形・動きへ翻訳する→カラー/タイポ/モチーフ/モーション/画面ムード/AppIconを決める→アー… |

### `app-store-optimize`（6本） — app-store-optimize-workspaceで有効化

| スキル | 何をするか |
|---|---|
| `/app-store-optimize:aso` | ASO（App Store 最適化）の観点で「何を調査し、どんな文言・画像にするか」を決めるプレイブック。 |
| `/app-store-optimize:aso-appstore-screenshots` | Generate high-converting App Store screenshots by analyzing your app's codebase, discovering core benefits, and creating ASO-optimized screenshot ima… |
| `/app-store-optimize:ppo-experiment` | App Store の Product Page Optimization（PPO）でストア画像を A/B テストする。 |
| `/app-store-optimize:review-reply` | リリース後のユーザレビューを読み、返信し、そこから ASO を直す。 |
| `/app-store-optimize:screenshot-build` | App Store のストアスクリーンショットを HTML+CSS で組み、Playwright で PNG に書き出すための道具一式とサンプル。 |
| `/app-store-optimize:screenshot-crafting` | App Storeのストアスクリーンショット一式（画像セット）を設計・制作するためのワークフローと知識（Apple公式仕様、ストーリーボード3幕構成、レイアウトパターン、押させる日本語コピーの型、審査リジェクト回避、ASC API/fastlane自動化）を提供します。 |

### `sns-marketing`（8本） — sns-marketing-workspaceで有効化

| スキル | 何をするか |
|---|---|
| `/sns-marketing:carousel-craft` | SNSカルーセル画像(TikTokフォトモード/Lemon8)の品質を上げるためのデザイン正本。 |
| `/sns-marketing:image-gen-techniques` | Claude CodeがPython(Pillow/numpy)で画像を生成・自己レビューするときの汎用テクニック集を提供します。 |
| `/sns-marketing:lemon8-post` | Post an image carousel + title + body + hashtags to Lemon8 on a USB-debugging Android phone via adb UI automation. Use when the user wants to publish… |
| `/sns-marketing:promo-video` | target/<app> の宣伝動画（無音・縦9:16・~30秒・かっこいい系）を作る。 |
| `/sns-marketing:sns-daily-pipeline` | target/配下のアプリ(Hioto / Tone など apps.json 登録のいずれか)の SNS 運用を毎日まわす本番パイプライン。 |
| `/sns-marketing:sns-post` | TikTok / Lemon8 向けの「複数画像（カルーセル）投稿」を新規に1本作る。 |
| `/sns-marketing:tiktok-post` | Post a photo carousel (multiple images) + caption + hashtags to TikTok on a USB-debugging Android phone via adb UI automation. Use when the user want… |
| `/sns-marketing:tone-post` | Tone（メンズメイク診断アプリ / target/mensmakeupadvisor）の TikTok・Lemon8 向けカルーセル画像投稿を1本作って実際に公開する。 |

### `note`（4本） — note-workspaceで有効化

| スキル | 何をするか |
|---|---|
| `/note:note-craft` | note.com 記事の設計正本。 |
| `/note:note-post` | note.com の記事を新規に1本作って下書き保存まで持っていく。 |
| `/note:note-publish` | note.com の下書きを公開する。 |
| `/note:note-setup` | note-workspace で note.com への接続（note-mcp）を用意する。 |

### `cloudflare`（9本） — 全リポジトリ（user スコープ）で有効化

| スキル | 何をするか |
|---|---|
| `/cloudflare:agents-sdk` | Build AI agents on Cloudflare Workers using the Agents SDK. Load when creating stateful agents, durable workflows, real-time WebSocket apps, schedule… |
| `/cloudflare:cloudflare` | Comprehensive Cloudflare platform skill covering Workers, Pages, storage (KV, D1, R2), AI (Workers AI, Vectorize, Agents SDK), feature flags (Flagshi… |
| `/cloudflare:cloudflare-email-service` | Send and receive transactional emails with Cloudflare Email Service (Email Sending + Email Routing). Use when building email sending (Workers binding… |
| `/cloudflare:durable-objects` | Create and review Cloudflare Durable Objects. Use when building stateful coordination (chat rooms, multiplayer games, booking systems), implementing … |
| `/cloudflare:sandbox-sdk` | Build sandboxed applications for secure code execution. Load when building AI code execution, code interpreters, CI/CD systems, interactive dev envir… |
| `/cloudflare:turnstile-spin` | Set up Cloudflare Turnstile end-to-end in a project — scan the codebase, create the widget via the Cloudflare API, deploy the managed siteverify Work… |
| `/cloudflare:web-perf` | Analyzes web performance using Chrome DevTools MCP. Measures Core Web Vitals (LCP, INP, CLS) and supplementary metrics (FCP, TBT, Speed Index), ident… |
| `/cloudflare:workers-best-practices` | Reviews and authors Cloudflare Workers code against production best practices. Load when writing new Workers, reviewing Worker code, configuring wran… |
| `/cloudflare:wrangler` | Cloudflare Workers CLI for deploying, developing, and managing Workers, KV, R2, D1, Vectorize, Hyperdrive, Workers AI, Containers, Queues, Workflows,… |

### `canva`（1本） — 全リポジトリ（user スコープ）で有効化

| スキル | 何をするか |
|---|---|
| `/canva:canva-image-gen` | Canva の AI 画像生成（Dream Lab / 旧 Magic Media）を、ログイン済みの普段使い Chrome をブラウザ操作（CDP）して CLI から実行し、画像をダウンロードします。 |

### `writing`（2本） — 全リポジトリ（user スコープ）で有効化

| スキル | 何をするか |
|---|---|
| `/writing:cognitive-rhythm-writing` | 説明的な文章に緩急を設計するための規範。 |
| `/writing:japanese-tech-writing` | 日本語の技術文書・書籍原稿の文章規範。 |

<!-- END GENERATED -->

## 索引を更新する

スキルを追加・削除・description を変えたら:

```bash
python3 common/scripts/build_skill_map.py          # 一覧を再生成
python3 common/scripts/build_skill_map.py --check   # ズレていたら exit 1
```

上の手書き部分（使い分け・迷いやすいペア）は自動生成の対象外なので、**新しいスキルが
既存と紛らわしいなら「迷いやすいペア」に1行足す**こと。
