---
name: new-routine-site
description: ~/workspace/routine 配下に、Claude Code Routine が定期実行でコンテンツを追加する新しいサイトを 0 から立ち上げます（Hono+Vite+bun+Cloudflare Workers、xxx.basaapp.com、記事台帳による重複防止、cloud routine 登録まで）。「新しい routine サイト/プロジェクトを作って」「定期更新サイトを立ち上げて」と言われたときに使用してください。
---

# new-routine-site（routine 駆動サイトの新規立ち上げ）

## 概要
`~/workspace/routine/` 配下に独立リポジトリのコンテンツサイトを作り、毎日 routine が記事を追加する状態（cloud routine 登録）まで一気通貫で構築する。技術前提は workspace 共通: **Hono + Vite + bun → Cloudflare Workers、ドメイン `<sub>.basaapp.com`、main push で自動デプロイ**。リファレンス実装は `~/workspace/routine/news-routine/`（迷ったら構造をそのまま踏襲する）。

## ワークフロー

### 1. 要件確定（AskUserQuestion）
最低限ヒアリング: **サブドメイン名** / **ジャンル・テーマ** / **言語** / **情報源の集め方**（ホワイトリスト軸＋Web検索 など）/ **1回あたり記事数と頻度**。回答は CLAUDE.md とメモリに記録する。

### 2. プロジェクト雛形を作成
`news-routine` の構成をテンプレートとして踏襲（`_templates/` ではなく news-routine がリファレンス）。必須ファイル:
- `package.json`（bun スクリプト: dev/build/preview/deploy/typecheck、deps: hono, marked / devDeps: @hono/vite-build, @hono/vite-dev-server, vite, wrangler, typescript, @cloudflare/workers-types）
- `tsconfig.json`（`jsx: react-jsx`, `jsxImportSource: hono/jsx`）
- `vite.config.ts`（`@hono/vite-build/cloudflare-workers` + `@hono/vite-dev-server`）
- `wrangler.jsonc`（`name`, `main: dist/index.js`, `compatibility_flags: ["nodejs_compat"]`, `routes` に `{pattern: "<sub>.basaapp.com", custom_domain: true}`）
- `src/index.tsx`（一覧 `/`・詳細 `/articles/:slug`・`/topics`・`/topics/:topic`、SEO 系 `/robots.txt`・`/sitemap.xml`・`/feed.xml`・`/llms.txt`〔ニュースなら `/news-sitemap.xml`〕、**CSS は `/style.css` を Worker から直接配信**＝`import css from "./style.css?raw"`）
- `src/articles.ts`（`import.meta.glob("../content/articles/*.md", {query:"?raw", eager:true, import:"default"})` でビルド時バンドル＋簡易 frontmatter パーサ）
- `src/seo.ts`（`_templates/seo-llmo/seo.ts.template` をコピーし `SITE` を編集。JSON-LD・robots・sitemap・RSS・llms.txt 生成）
- `src/components/Layout.tsx`（サイト名/タグライン/フォント/ナビ＋ canonical/OG/Twitter/robots meta/JSON-LD。news-routine の Layout がリファレンス）
- `src/style.css`、`content/articles/`（サンプル1本）、`data/articles.json`（`[]`→サンプル）、`.gitignore`（node_modules/dist/.wrangler）、`README.md`、`CLAUDE.md`

**frontmatter パーサの制約（重要）**: 対応は `key: value` と `key: [a, b, c]` のみ。記事はこの形式に厳密に揃える。

### 3. 共通スキル（重複防止）を同梱
`~/workspace/routine/_templates/article-registry/` を `<project>/.claude/skills/article-registry/`（SKILL.md + scripts/registry.ts）にコピー。台帳は `data/articles.json`（コミット管理）。詳細は [[cloud-routines-skill]] ではなく article-registry スキル本体参照。
さらに `~/workspace/routine/_templates/seo-llmo/SKILL.md` を `<project>/.claude/skills/seo-llmo/SKILL.md` にコピーし、`seo.ts.template` を `src/seo.ts` として `SITE` を編集。SEO/LLMO のベストプラクティス維持はこのスキルに従う。

### 4. プロジェクト固有の収集スキルを作成
`<project>/.claude/skills/<topic>-collection/SKILL.md` を新規作成。news-routine の `news-collection` を雛形に、要件の領域へ書き換える。必ず盛り込む編集方針:
- 事実と意見の分離 / 出典必須（一次情報優先）/ 憶測排除 / 煽らないタイトル
- 機微なジャンル（政治・国際・紛争等）では中立・多角的視点、当事者の主張は帰属明示、数値は出典と留保
- **出典URLは WebFetch で実在確認してから載せる**（推測 URL 禁止）
- ワークフロー（収集→重複チェック→裏取り→執筆→台帳登録→同一コミットで push）と記事フォーマット・記事構成の型

### 5. UI を作り込む
`ui-ux-pro-max` スキルでデザインシステムを生成し、`Layout.tsx` + `style.css` に反映（ライト/ダーク・レスポンシブ・アクセシビリティ）。

### 6. 検証
`bun install` → `bun run typecheck` → `bun run build`。ビルド済み `dist/index.js` を import して全ルートの 200/404 をスモークテスト（news-routine の検証手順を踏襲）。

### 7. リポジトリ作成 & main へ push（標準で実施）
このスキルは**リポジトリ作成と main への push まで行う**（「サイトを作って」と頼まれた時点で許可とみなし、明示的に止められた場合のみスキップ）。
- `cd <project>` → `git init` → `git branch -M main` → 全追加 → コミット（末尾に `Co-Authored-By: Claude ...` トレーラ）。
- private リポジトリ作成して push（既存サイトと同じ規約: リポジトリ名＝ディレクトリ名＝wrangler の `name`、SSH、private）:
  ```bash
  ACCT=$(gh api user --jq .login)   # 通常 tubasasakunn
  gh repo create "$ACCT/<dir>" --private --source=. --remote=origin
  git remote set-url origin "git@github.com:$ACCT/<dir>.git"
  git push -u origin main
  ```
- `node_modules`/`dist` が追跡されないこと、`bun.lock` が追跡されることを確認。

### 8. 初日コンテンツ生成（任意）
routine を想定し、サブエージェント（general-purpose）に当日分の記事を収集スキル通り生成させる。**公開（push）前に必ず**核心事実を独立検証し、全 `sources` URL を WebFetch で実在確認、偽 URL は差し替える（[[verify-sources-before-publish]]）。

### 9. cloud routine 登録（標準で実施）
`RemoteTrigger`（schedule スキル）で登録まで行う。**まず既存 trigger を `RemoteTrigger get`（例 ai-news の trigger）で1つ取得し、その `job_config` 構造をそのまま雛形にする**のが最も確実。要点:
- `cron_expression` は **UTC**・**最小間隔1時間**。ローカル時刻→UTC 変換を確認。既存サイトと時刻が被らないようずらし、:00/:30 を避け数分オフセット（例: 06:06 JST=`6 21 * * *`）。
- `job_config.ccr.environment_id`: 既存サイトと同じ環境を使う（例 `env_014mMa4t7UzEZwmdrcJH9m3D`。不明ならユーザーに確認）。
- `job_config.ccr.session_context`（**ここに入れる**）:
  - `model`: `"claude-sonnet-4-6"` … **`model` は session_context 直下。`ccr` 直下に置くと API が 400 `unknown field "model"` を返す**。
  - `allowed_tools`: `["Bash","Read","Write","Edit","Glob","Grep","WebSearch","WebFetch"]`
  - `sources`: `[{"git_repository":{"url":"https://github.com/<acct>/<repo>","allow_unrestricted_git_push":true}}]` … **main への push 許可（unrestricted push）はこの API フィールドで設定できる**（Web UI 必須ではない）。
  - `outcomes`: `[{"git_repository":{"git_info":{"repo":"<acct>/<repo>"}}}]`、`autofix_on_pr_create`: `false`。
- `events[0].data`: `{uuid:<新規v4 UUID>, session_id:"", parent_tool_use_id:null, type:"user", message:{role:"user", content:<自己完結プロンプト>}}`。
- プロンプトは **自己完結**（fresh clone・bun 無ければ install・skills を読む・既出把握→重複チェック→裏取り→執筆→台帳→typecheck/build→main へ push）。
- **Web UI 側で要確認**: 「無制限ネットアクセス」は環境/routine 設定側にあり、API の `allow_unrestricted_git_push` を立てても bun install 等のネット取得が環境ポリシーで止まる場合は claude.ai/code/routines で無制限ネットを有効化するようユーザーに案内。GitHub 連携（push 権限）も前提。

## 重要な落とし穴（再掲）
- 台帳 `data/articles.json` を更新せず記事だけコミットしない（重複検出が壊れる）。
- routine は fresh clone・実行間の状態なし → 台帳もスキルも**リポジトリにコミット**が必須。ローカル MCP / ローカルファイルは使えない。
- main への push 許可は API の `session_context.sources[].git_repository.allow_unrestricted_git_push: true` で設定する（これを忘れると push が `claude/` ブランチに制限される）。**無制限ネットアクセス**は環境/routine 設定側で、必要なら Web UI で有効化を案内。
- 公開前の出典検証を省略しない。

## 終了条件
- [ ] 要件をヒアリングし CLAUDE.md/メモリに記録
- [ ] 雛形 + article-registry + seo-llmo + 固有収集スキルを配置
- [ ] UI 作り込み・build/typecheck/スモークテスト通過
- [ ] git init→private repo 作成→main push（標準で実施。明示的に止められた時のみスキップ）
- [ ] cloud routine 登録（RemoteTrigger）＋ 必要なら Web UI 側の無制限ネット設定を案内
