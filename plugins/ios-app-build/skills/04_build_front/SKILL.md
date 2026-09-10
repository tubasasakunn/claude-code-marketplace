---
name: 04_build_front
description: アプリの利用規約・プライバシーポリシー・サポートページを Hono + Vite + Cloudflare Workers で生成し、(アプリ名).basaapp.com へデプロイします。push で自動デプロイされる GitHub Actions も設置します。App Store の審査はこれらの URL が開けないと通りません。
---

# 規約・サポートサイトの構築 (04_build_front)

## なぜ必要か

App Store の審査には **プライバシーポリシー URL** と **サポート URL** が必須で、
審査官が実際に開く。**開けなければリジェクトされる。** アプリの設定画面からもここへリンクする。

ドメインは `<アプリ名>.basaapp.com` 固定（Cloudflare の `basaapp.com` ゾーン）。

## 前提

- `~/workspace/ios-app-build-workspace/.env` に `CLOUDFLARE_DEPLOY_TOKEN` と `CLOUDFLARE_ACCOUNT_ID`
- リポジトリの GitHub Secrets に `CLOUDFLARE_API_TOKEN` / `CLOUDFLARE_ACCOUNT_ID`（`00_setup_repo` で投入済み）
- 手本: `~/workspace/nagasu/front/`（構造をそのまま踏襲する）
- `basaapp.com` ゾーンが Cloudflare にあり、サブドメインのカスタムドメインを作れること

## 先に .gitignore を直す ★忘れると node_modules をコミットする

`00_setup_repo` の時点では `front/` が無いので、`.gitignore` に除外が入っていない。

```bash
cat >> .gitignore <<'EOF'

# front
front/node_modules
front/dist
front/.wrangler
EOF
```

## Step 1. front/ を作る

```
front/
  package.json        hono, vite, @cloudflare/vite-plugin, wrangler(v4)
  vite.config.ts
  tsconfig.json
  wrangler.jsonc
  src/
    index.tsx         ルーティング
    layout.tsx        共通レイアウト + CSS変数 + インラインSVGモチーフ
    pages/
      home.tsx        ランディング
      privacy.tsx
      terms.tsx
      support.tsx
  public/
    favicon.svg
    robots.txt
```

ルートは4つ。`/`（ランディング）、`/privacy`、`/terms`、`/support`。

`wrangler.jsonc`:

```jsonc
{
  "name": "<appname>-front",
  "main": "./dist/index.js",
  "compatibility_date": "2026-06-01",
  "routes": [{ "pattern": "<appname>.basaapp.com", "custom_domain": true }],
  "assets": { "directory": "./public" }
}
```

## Step 2. 中身を書く

**デザインは `DESIGN.md` のカラーパレットを CSS 変数にして反映する。** アプリと同じ世界観にする。
外部リソース（CDN のフォントやスクリプト）は使わない。CSS はインライン。

`DESIGN.md` が無ければ、**実装済みのアプリから実際の色を読む**（こちらの方が確実に一致する）。

```bash
grep -nE "0x|#[0-9A-Fa-f]{6}|Color\(hex" ../<App>/Design/Tokens.swift | head
```

規約・プライバシーポリシーの文面は、**アプリの実装事実に基づいて書く**。
完全オフラインのアプリなら:

- データを一切収集しない、通信を行わない
- 端末内（SwiftData）にのみ保存される
- アカウント登録なし、第三者提供なし、広告なし、課金なし
- 準拠法は日本法、制定日は今日の日付

**実装を確認せずに書かない。** ソースを `grep` して、通信・解析 SDK・権限要求が無いことを確かめる。

```bash
grep -rniE "URLSession|fetch\(|Analytics|Firebase|AdMob|CLLocation|AVCapture" ../<App>/ | head
```

`/support` には連絡先（`bassa.application@gmail.com`）を書く。

## Step 3. ローカルで確認する

```bash
cd front
npm install
npm run build
npx wrangler dev &
sleep 5
for p in / /privacy /terms /support; do
  curl -s -o /dev/null -w "$p: %{http_code}\n" "http://localhost:8787$p"
done
kill %1
```

4つとも 200 になること。

## Step 4. デプロイする

```bash
cd front
npx wrangler deploy
```

`<appname>.basaapp.com (custom domain)` と出れば成功。

### ローカルから deploy できないことがある

```
Cannot use the access token from location: ...  [code: 9109]
```

**Cloudflare のトークンに IP アドレスフィルタが設定されている。**
このときローカルからのデプロイは諦めて、**Step 5 の CI 経由でデプロイする**（GitHub のランナー IP が許可されていれば通る）。
Step 5 を先にやってから、この Step の確認に戻ればよい。

**確認**（DNS 伝播前はローカルの名前解決が失敗することがあるので、エッジ IP を直接叩く）:

```bash
IP=$(dig +short <appname>.basaapp.com @1.1.1.1 | head -1)
for p in / /privacy /terms /support; do
  curl -s -o /dev/null -w "$p: %{http_code}\n" --resolve "<appname>.basaapp.com:443:$IP" "https://<appname>.basaapp.com$p"
done
```

## Step 5. 自動デプロイの workflow を置く

`.github/workflows/front-deploy.yml`:

```yaml
name: Front deploy

on:
  push:
    branches: [main]
    paths: ["front/**"]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: front
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v4
        with:
          node-version: "22"    # wrangler v4 は Node 22 以上が必須
      - run: npm ci
      - run: npm run build
      # wrangler-action@v3 は古い wrangler(v3) を同梱していて wrangler.jsonc を読めない。
      # devDependencies の wrangler(v4) を直接使う。
      - name: Deploy
        run: npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

push して、実際に緑になることを確認する。

```bash
git add front .github/workflows/front-deploy.yml
git commit -m "front/ に利用規約・プライバシーポリシー・サポートサイトを追加"
git push origin main
gh run watch $(gh run list --workflow=front-deploy.yml --limit 1 --json databaseId -q '.[0].databaseId') --exit-status
```

## Step 6. release メタデータに URL を書く

```bash
echo "https://<appname>.basaapp.com"          > release/1.0/marketing_url.txt
echo "https://<appname>.basaapp.com/support"  > release/1.0/support_url.txt
echo "https://<appname>.basaapp.com/privacy"  > release/1.0/privacy_url.txt
```

**アプリの設定画面のリンク先と一致していること**を確認する。

```bash
grep -rn "basaapp.com" ../<App>/Settings/
```

`03_implement_app` の時点で設定画面が URL を決め打ちしていることが多い。
**URL の正本は「このスキルで実際に建てたドメイン」**（`<appname>.basaapp.com`）。
ズレていたら、アプリ側の定数を直す（サイト側のパスを変えない）。

## 罠

### CI が Cloudflare の認証で落ちる

- `Authentication error [code: 10000]` → トークンの権限不足、または**トークンに IP アドレスフィルタが設定されている**（GitHub のランナーから弾かれる）
- `Wrangler requires at least Node.js v22` → `setup-node` の `node-version` を `22` にする
- `Missing entry-point` → `wrangler-action@v3` が同梱の古い wrangler を使っている。`npx wrangler deploy` を直接叩く

### curl が `000` を返す

ローカルの DNS がまだ引けていないだけで、デプロイ自体は成功していることが多い。上の `--resolve` を使う。

## 完了条件

- [ ] `https://<appname>.basaapp.com/` `/privacy` `/terms` `/support` が全部 200
- [ ] 規約の文面が**実装の事実**と一致している（収集していないなら「収集しない」と書く）
- [ ] `front-deploy.yml` の run が緑
- [ ] `release/1.0/` の3つの URL ファイルが更新されている
- [ ] アプリの設定画面のリンク先と URL が一致している

## 次のスキル

`05_release_assets` — ストア文言とスクリーンショットを用意する。
