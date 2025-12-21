# CI/CD設定ガイド

## GitHub Actionsワークフロー

### 完全なデプロイワークフロー

```yaml
# .github/workflows/deploy.yml
name: Deploy API

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test # Vitestによるテスト実行

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci

      # D1マイグレーションの適用（リモート）
      - name: Apply D1 Migrations
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: d1 migrations apply my-db-prod --remote

      # Workerのデプロイ
      - name: Deploy Worker
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

### プレビュー環境へのデプロイ

```yaml
# .github/workflows/preview.yml
name: Preview Deploy

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  preview:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm test

      # プレビュー環境へのマイグレーション
      - name: Apply Preview Migrations
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: d1 migrations apply my-db-preview --remote --env preview

      # プレビュー環境へのデプロイ
      - name: Deploy to Preview
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: deploy --env preview
```

---

## 必要なGitHub Secrets

| Secret名 | 説明 |
|----------|------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare APIトークン（Workers編集権限） |
| `CLOUDFLARE_ACCOUNT_ID` | CloudflareアカウントID |

### APIトークン作成手順

1. Cloudflareダッシュボード → My Profile → API Tokens
2. "Create Token" → "Edit Cloudflare Workers" テンプレート使用
3. 必要な権限:
   - Account: Cloudflare Workers Scripts:Edit
   - Account: Cloudflare D1:Edit
   - Zone: Workers Routes:Edit（カスタムドメイン使用時）

---

## wrangler.toml 環境設定

```toml
name = "my-api"
main = "src/index.ts"
compatibility_date = "2024-01-01"
compatibility_flags = ["nodejs_compat"]

# Smart Placement有効化
[placement]
mode = "smart"

# 本番環境
[env.production]
name = "my-api-prod"
d1_databases = [
  { binding = "DB", database_name = "my-db-prod", database_id = "prod-db-id" }
]

# プレビュー環境
[env.preview]
name = "my-api-preview"
d1_databases = [
  { binding = "DB", database_name = "my-db-preview", database_id = "preview-db-id" }
]

# ローカル開発環境
[[d1_databases]]
binding = "DB"
database_name = "my-db-local"
database_id = "local-db-id"
```

---

## package.json スクリプト

```json
{
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy",
    "deploy:prod": "wrangler deploy --env production",
    "deploy:preview": "wrangler deploy --env preview",
    "test": "vitest",
    "test:ci": "vitest run",
    "db:generate": "drizzle-kit generate",
    "db:migrate:local": "wrangler d1 migrations apply my-db-local --local",
    "db:migrate:preview": "wrangler d1 migrations apply my-db-preview --remote --env preview",
    "db:migrate:prod": "wrangler d1 migrations apply my-db-prod --remote --env production",
    "db:studio": "drizzle-kit studio",
    "typecheck": "tsc --noEmit",
    "lint": "eslint src"
  }
}
```

---

## ブランチ戦略

```
main (本番)
  │
  ├── develop (開発統合)
  │     │
  │     ├── feature/xxx (機能開発)
  │     └── fix/xxx (バグ修正)
  │
  └── release/x.x.x (リリース準備)
```

### 推奨フロー

1. `feature/*` → `develop`: 機能開発完了時
2. `develop` → `main`: リリース時（本番デプロイ）
3. PRマージ時に自動テスト・デプロイ実行

---

## ロールバック手順

### 1. Workers のロールバック

```bash
# 以前のバージョン一覧
wrangler deployments list

# 特定バージョンへロールバック
wrangler rollback <deployment-id>
```

### 2. D1 のロールバック (Time Travel)

```bash
# 特定時点のデータを復元
wrangler d1 time-travel restore my-db-prod \
  --timestamp "2024-01-15T10:00:00Z"
```

---

## モニタリング

### Cloudflareダッシュボード

- Workers Analytics: リクエスト数、エラー率、レイテンシー
- D1 Metrics: クエリ数、読み書き回数

### ログ確認

```bash
# リアルタイムログ
wrangler tail

# 本番環境のログ
wrangler tail --env production
```

### Sentry連携（オプション）

```typescript
import { Toucan } from 'toucan-js';

app.use('*', async (c, next) => {
  const sentry = new Toucan({
    dsn: c.env.SENTRY_DSN,
    context: c.executionCtx,
    request: c.req.raw,
  });
  c.set('sentry', sentry);

  try {
    await next();
  } catch (err) {
    sentry.captureException(err);
    throw err;
  }
});
```
