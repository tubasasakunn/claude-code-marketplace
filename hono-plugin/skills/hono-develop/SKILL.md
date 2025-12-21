---
name: hono-develop
description: Cloudflare Workers + Hono + D1を用いたエッジAPI開発のベストプラクティスを提供します。Hono、D1、Cloudflare Workers、エッジAPI、Drizzle ORM、エッジコンピューティングについて質問された場合に使用してください。
---

# Hono + D1 エッジAPI開発ガイド

## 概要

Cloudflare Workers + Hono + D1は次世代エッジAPIの「ゴールデンスタック」です。

- **Hono**: Web標準準拠の超軽量フレームワーク
- **D1**: SQLiteベースの分散エッジデータベース
- **Workers**: V8 Isolateによるミリ秒起動のエッジランタイム

## クイックスタート

### プロジェクト作成

```bash
npm create hono@latest my-api
cd my-api
npm install drizzle-orm
npm install -D drizzle-kit
```

### wrangler.toml設定

```toml
name = "my-api"
compatibility_date = "2024-01-01"

[[d1_databases]]
binding = "DB"
database_name = "my-db"
database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

[placement]
mode = "smart"
```

### 基本的なHonoアプリ

```typescript
import { Hono } from 'hono';
import { drizzle } from 'drizzle-orm/d1';

type Bindings = { DB: D1Database };

const app = new Hono<{ Bindings: Bindings }>();

app.get('/users', async (c) => {
  const db = drizzle(c.env.DB);
  const users = await db.select().from(usersTable);
  return c.json(users);
});

export default app;
```

## アーキテクチャ原則

### レイヤー構成

```
src/
├── index.ts              # エントリーポイント
├── domain/               # ドメイン層（型定義・インターフェース）
├── application/          # アプリケーション層（ユースケース）
├── infrastructure/       # インフラ層（DB実装）
└── interface/            # プレゼンテーション層（ルート・ミドルウェア）
```

### 依存性注入パターン

```typescript
type Variables = { userService: UserService };

app.use('*', async (c, next) => {
  const db = drizzle(c.env.DB);
  const userRepository = new D1UserRepository(db);
  c.set('userService', new UserService(userRepository));
  await next();
});

app.get('/users/:id', async (c) => {
  const service = c.get('userService');
  const user = await service.getUser(c.req.param('id'));
  return c.json(user);
});
```

## 重要なベストプラクティス

### 1. Hono RPC（型安全なクライアント）

```typescript
// サーバー側
const routes = app
  .post('/users', zValidator('json', userSchema), async (c) => {
    const data = c.req.valid('json');
    return c.json({ ok: true, userId: 123 });
  });

export type AppType = typeof routes;

// クライアント側
import { hc } from 'hono/client';
import type { AppType } from './server';

const client = hc<AppType>('https://api.example.com');
const res = await client.users.$post({ json: { name: 'Alice' } });
```

### 2. バリデーション

```typescript
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

app.post('/users', zValidator('json', schema), (c) => {
  const data = c.req.valid('json'); // 型安全
  return c.json(data);
});
```

### 3. グローバルエラーハンドリング

```typescript
import { HTTPException } from 'hono/http-exception';

app.onError((err, c) => {
  console.error(`[Error] ${err.message}`);

  if (err instanceof HTTPException) {
    return err.getResponse();
  }

  return c.json({
    success: false,
    message: 'Internal Server Error',
    requestId: c.req.header('cf-ray'),
  }, 500);
});
```

### 4. Drizzle ORMスキーマ

```typescript
// schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`(unixepoch())`),
});
```

### 5. マイグレーション

```bash
# SQL生成
npx drizzle-kit generate

# ローカル適用
npx wrangler d1 migrations apply my-db --local

# 本番適用
npx wrangler d1 migrations apply my-db --remote
```

## 詳細リファレンス

- 完全なアーキテクチャ設計: [REFERENCE.md](REFERENCE.md)
- CI/CD設定例: [CICD.md](CICD.md)

## チェックリスト

- [ ] `placement.mode = "smart"` を設定（D1への最適化）
- [ ] Zodでバリデーション実装
- [ ] グローバルエラーハンドラー設定
- [ ] Drizzle ORMでスキーマ定義
- [ ] wrangler経由でマイグレーション適用
- [ ] Vitestで統合テスト作成
