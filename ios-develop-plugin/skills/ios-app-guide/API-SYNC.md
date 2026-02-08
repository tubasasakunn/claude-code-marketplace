# API / バックエンド連携

## Hono + Cloudflare Workers 構成

```
project-api/
├── src/
│   ├── index.ts          # ルーティング + CORS + エラーハンドラ
│   ├── routes/           # エンドポイント
│   ├── services/         # ビジネスロジック
│   └── types/            # 型定義
├── migrations/           # D1 マイグレーション SQL
└── wrangler.jsonc        # D1 バインディング + 環境変数
```

## iOS 側の同期パターン

```
SwiftData（source of truth）
    │
    ├── 保存/編集 → syncUpsert() → PUT /endpoint
    ├── 削除    → syncDelete() → DELETE /endpoint/...
    └── 全て fire-and-forget（Task.detached）
```

## Zod バリデーション

```typescript
import { z } from 'zod'
import { zValidator } from '@hono/zod-validator'

const upsertSchema = z.object({
    userId: z.string(),
    tmdbId: z.number(),
    title: z.string(),
    comment: z.string().optional(),
    rating: z.number().min(0).max(5),
    watchedAt: z.string(),
})

app.put('/', zValidator('json', upsertSchema), async (c) => { ... })
```

## 注意点

- `HTTPMethod` enum に `.patch` を追加する必要がある場合がある
- フロントエンド側の色パレットは iOS 側と合わせる
- `escapeHtml` で XSS 対策を必ず行う
- D1 バインディングエラーは wrangler.jsonc の database_id 設定を確認
