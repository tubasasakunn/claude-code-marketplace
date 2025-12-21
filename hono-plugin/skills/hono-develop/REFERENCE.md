# Cloudflare D1 + Hono 包括的リファレンス

## 1. エッジネイティブ・コンピューティングの背景

### 技術スタック選定の論理的根拠

**究極の低レイテンシーとスケーラビリティ**
- D1はHTTPベースのプロトコルとCloudflare内部ネットワークを通じて最適化
- ユーザーに最も近い場所でデータを処理・配信

**Web標準への準拠と型安全性**
- HonoはRequest/ResponseといったWeb標準APIベース
- RPC機能でエンドツーエンドの型安全性を実現

**コスト効率と運用負荷の低減**
- D1は読み取り・書き込み回数とストレージ容量の従量課金
- アイドル時のコストなし
- サーバープロビジョニングやOSパッチ適用が不要

---

## 2. アーキテクチャ設計

### クリーンアーキテクチャの適用

#### レイヤー構成

**プレゼンテーション層 (Interface Adapters)**
- Honoのルーターとハンドラー
- HTTPリクエストの受け取り、入力バリデーション
- ビジネスロジックは記述しない

**アプリケーション層 (Use Cases / Services)**
- ビジネスルールの実装
- トランザクション境界の定義
- 特定のWebフレームワークやDB詳細に依存しない

**ドメイン層 (Entities)**
- ビジネスの中核となるデータ構造とルール
- TypeScriptの型定義やインターフェース

**インフラストラクチャ層 (Infrastructure)**
- データ永続化（D1へのアクセス）
- Repositoryパターンを適用

### 推奨ディレクトリ構造

```
src/
├── index.ts                # エントリーポイント
├── pkg/                    # 共有ライブラリ
│   ├── env.ts              # 環境変数の型定義
│   └── errors.ts           # カスタムエラークラス
├── domain/                 # ドメイン層
│   ├── models/             # ドメインモデル
│   │   ├── User.ts
│   │   └── Post.ts
│   └── repositories/       # リポジトリインターフェース
│       └── IUserRepository.ts
├── application/            # アプリケーション層
│   ├── usecases/           # ユースケース
│   │   ├── CreateUser.ts
│   │   └── GetUser.ts
│   └── services/           # ドメインサービス
├── infrastructure/         # インフラ層
│   ├── db/
│   │   ├── schema.ts       # Drizzleスキーマ
│   │   ├── migrations/     # マイグレーション
│   │   └── client.ts       # DBクライアント初期化
│   └── repositories/       # リポジトリ実装
│       └── D1UserRepository.ts
├── interface/              # プレゼンテーション層
│   ├── routes/
│   │   └── v1/
│   │       ├── users.ts
│   │       └── auth.ts
│   └── middleware/
│       ├── auth.ts
│       └── validator.ts
└── tests/
    ├── integration/
    └── unit/
```

### 依存性注入 (DI) パターン

Workers環境ではenvオブジェクトがリクエストごとに渡されるため、ミドルウェアでDIを行う:

```typescript
import { Hono } from 'hono';
import { drizzle } from 'drizzle-orm/d1';
import { D1UserRepository } from './infrastructure/repositories/D1UserRepository';
import { UserService } from './application/services/UserService';

type Bindings = { DB: D1Database };
type Variables = { userService: UserService };

const app = new Hono<{ Bindings: Bindings; Variables: Variables }>();

// DIミドルウェア
app.use('*', async (c, next) => {
  const db = drizzle(c.env.DB);
  const userRepository = new D1UserRepository(db);
  const userService = new UserService(userRepository);
  c.set('userService', userService);
  await next();
});

// ハンドラーでの利用
app.post('/users', async (c) => {
  const userService = c.get('userService');
  const body = await c.req.json();
  const user = await userService.createUser(body);
  return c.json(user);
});
```

**メリット**:
- テスタビリティ向上（モック注入が容易）
- 型安全性の確保
- ステートレスなWorkers環境の原則に従う

---

## 3. Honoフレームワーク活用詳細

### Hono RPCによる型安全性

**サーバー側**:
```typescript
import { Hono } from 'hono';
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

const userSchema = z.object({
  name: z.string().min(1),
  email: z.string().email(),
});

const app = new Hono()
  .post(
    '/',
    zValidator('json', userSchema),
    async (c) => {
      const data = c.req.valid('json');
      return c.json({ ok: true, message: 'User created', userId: 123 });
    }
  );

export default app;
```

**クライアント側**:
```typescript
import { hc } from 'hono/client';
import type { AppType } from './server/index';

const client = hc<AppType>('https://api.example.com');

const res = await client.users.$post({
  json: { name: 'Alice', email: 'alice@example.com' }
});
```

**RPC利用時の注意点**:

1. **Cookieの処理**: クロスオリジン環境では`credentials: 'include'`を設定
```typescript
const client = hc<AppType>('https://api.example.com', {
  init: { credentials: 'include' }
});
```

2. **ファイルアップロードの制限**: FileオブジェクトやFormDataの型推論に制限あり。署名付きURLパターンを推奨

### バリデーション戦略

```typescript
import { zValidator } from '@hono/zod-validator';
import { z } from 'zod';

// 共通エラーレスポンス形式
const validationHook = (result: any, c: any) => {
  if (!result.success) {
    return c.json({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        details: result.error.flatten().fieldErrors,
      }
    }, 400);
  }
};

app.post(
  '/posts',
  zValidator('json', z.object({ title: z.string() }), validationHook),
  (c) => {
    const { title } = c.req.valid('json');
    return c.json({ title });
  }
);
```

### グローバルエラーハンドリング

```typescript
import { HTTPException } from 'hono/http-exception';

app.onError((err, c) => {
  console.error(`[Error] ${err.message}`, err);

  if (err instanceof HTTPException) {
    return err.getResponse();
  }

  return c.json({
    success: false,
    message: 'Internal Server Error',
    requestId: c.req.header('cf-ray'), // CloudflareのRequest ID
  }, 500);
});
```

---

## 4. データ層設計

### ORM選定比較: Drizzle vs Kysely

| 特徴 | Drizzle ORM | Kysely |
|------|-------------|--------|
| 型安全性 | 極めて高い（スキーマから推論） | 高い（インターフェース定義必要） |
| ランタイムオーバーヘッド | ゼロに近い | 非常に低い |
| 学習コスト | 独自クエリ構文 | SQLに近い |
| マイグレーション | drizzle-kitで自動生成 | 独自実装が必要 |
| リレーション操作 | `query.findMany({ with:... })`で容易 | 手動でjoin記述 |
| 推奨ユースケース | 新規開発、生産性重視 | SQL細かい制御重視 |

**推奨**: 多くの新規プロジェクトではDrizzle ORM

### Drizzleスキーマ定義

```typescript
// schema.ts
import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
import { sql } from 'drizzle-orm';

export const users = sqliteTable('users', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`(unixepoch())`),
});

export const posts = sqliteTable('posts', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  title: text('title').notNull(),
  content: text('content'),
  authorId: integer('author_id')
    .notNull()
    .references(() => users.id),
  createdAt: integer('created_at', { mode: 'timestamp' })
    .notNull()
    .default(sql`(unixepoch())`),
});
```

### drizzle.config.ts

```typescript
import { defineConfig } from 'drizzle-kit';

export default defineConfig({
  schema: './src/infrastructure/db/schema.ts',
  out: './drizzle/migrations',
  dialect: 'sqlite',
  driver: 'd1-http',
});
```

### マイグレーションワークフロー

1. **スキーマ変更**: TypeScriptでschema.tsを修正
2. **SQL生成**: `drizzle-kit generate`
3. **ローカル適用**: `wrangler d1 migrations apply <DB_NAME> --local`
4. **本番適用**: `wrangler d1 migrations apply <DB_NAME> --remote`

**重要**: `drizzle-kit migrate`ではなく`wrangler`経由でマイグレーション適用

### リードレプリケーションと一貫性

D1のSessions APIでRead-your-writes一貫性を担保:

```typescript
app.use('*', async (c, next) => {
  const db = c.env.DB as D1Database;
  const bookmark = c.req.header('x-d1-bookmark');

  // @ts-ignore
  const session = db.session ? db.session(bookmark) : db;
  c.set('db', session);

  await next();

  if (session.getBookmark) {
    c.header('x-d1-bookmark', session.getBookmark());
  }
});
```

---

## 5. テスト戦略

### Vitest設定

```typescript
// vitest.config.ts
import { defineWorkersConfig } from "@cloudflare/vitest-pool-workers/config";

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: "./wrangler.toml" },
        isolatedStorage: true, // テストごとにD1隔離
        singleWorker: true,
        miniflare: {
          compatibilityDate: "2024-01-01",
          compatibilityFlags: ["nodejs_compat"],
        }
      },
    },
  },
});
```

### 統合テスト例

```typescript
import { env } from 'cloudflare:test';
import { describe, it, expect, beforeAll } from 'vitest';
import app from '../src/index';

describe('User API Integration Test', () => {
  beforeAll(async () => {
    await env.DB.exec(`
      CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT);
    `);
    await env.DB.prepare('INSERT INTO users (name, email) VALUES (?,?)')
      .bind('Test User', 'test@example.com')
      .run();
  });

  it('GET /users returns list of users', async () => {
    const res = await app.request('/users', {}, env);

    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body).toEqual(expect.arrayContaining([]));
  });

  it('should verify DB state directly', async () => {
    const user = await env.DB.prepare('SELECT * FROM users WHERE name = ?')
      .bind('Test User')
      .first();
    expect(user).not.toBeNull();
  });
});
```

---

## 6. パフォーマンス最適化

### Smart Placement

D1のプライマリに近いデータセンターでWorkerを起動:

```toml
# wrangler.toml
[placement]
mode = "smart"
```

### キャッシュ戦略

1. **Cache API**: HTMLやJSONレスポンス全体のキャッシュ
2. **Workers KV**: セッション情報、マスタデータのキャッシュ（D1より低レイテンシー）

---

## 7. ファイルアップロード (R2連携)

### 署名付きURLパターン

```typescript
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { getSignedUrl } from '@aws-sdk/s3-request-presigner';

const r2 = new S3Client({
  region: 'auto',
  endpoint: `https://${accountId}.r2.cloudflarestorage.com`,
  credentials: { accessKeyId, secretAccessKey }
});

app.post('/upload-url', async (c) => {
  const { filename, contentType } = await c.req.json();
  const key = `uploads/${crypto.randomUUID()}-${filename}`;

  const command = new PutObjectCommand({
    Bucket: 'my-bucket',
    Key: key,
    ContentType: contentType,
  });

  const url = await getSignedUrl(r2, command, { expiresIn: 60 });

  return c.json({ url, key });
});
```

**メリット**: Workerのメモリ制限を回避、GB単位のファイルも処理可能

---

## 8. 環境ごとの設定

### wrangler.toml

```toml
name = "my-api"

# 本番環境
[env.production]
d1_databases = [
  { binding = "DB", database_name = "my-db-prod", database_id = "xxx" }
]

# プレビュー環境
[env.preview]
d1_databases = [
  { binding = "DB", database_name = "my-db-preview", database_id = "yyy" }
]
```
