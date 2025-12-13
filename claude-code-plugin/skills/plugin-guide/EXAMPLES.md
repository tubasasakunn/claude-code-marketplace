# プラグイン実践例

## 例1: シンプルなコマンドプラグイン

コードレビューコマンドを提供するプラグイン。

### ディレクトリ構造

```
code-reviewer/
├── .claude-plugin/
│   └── plugin.json
└── commands/
    ├── review.md
    └── review-pr.md
```

### .claude-plugin/plugin.json

```json
{
  "name": "code-reviewer",
  "description": "コードレビュー用コマンドを提供",
  "version": "1.0.0",
  "author": {
    "name": "Your Team"
  }
}
```

### commands/review.md

```markdown
---
description: 指定ファイルのコードレビューを実行
allowed-tools: Read, Grep, Glob
---

# コードレビュー

以下のファイルをレビューしてください: $ARGUMENTS

## チェックポイント

1. **コード品質**: 可読性、命名規則、構造
2. **バグの可能性**: エラー処理、エッジケース
3. **パフォーマンス**: 非効率なコード、N+1問題
4. **セキュリティ**: 入力検証、SQL注入、XSS

## 出力形式

各問題を以下の形式で報告:
- 重要度: 高/中/低
- 場所: ファイル名:行番号
- 問題: 説明
- 提案: 改善案
```

### commands/review-pr.md

```markdown
---
description: PRの変更をレビュー
allowed-tools: Read, Grep, Glob, Bash
---

# PRレビュー

## 手順

1. `git diff main...HEAD`で変更を確認
2. 変更されたファイルをレビュー
3. レビューコメントをまとめる

## フォーカスポイント

- 変更の目的が明確か
- テストが追加されているか
- ドキュメントが更新されているか
```

---

## 例2: エージェント付きプラグイン

データベースマイグレーション用の特化エージェントを含むプラグイン。

### ディレクトリ構造

```
db-tools/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── migrate.md
└── agents/
    └── migration-planner.md
```

### agents/migration-planner.md

```markdown
---
name: migration-planner
description: データベースマイグレーションを計画・実行します。スキーマ変更、マイグレーション作成、データベース構造の変更について質問された場合に使用してください。
allowed-tools: Read, Grep, Glob, Bash
---

# マイグレーションプランナー

## 目的

安全なデータベースマイグレーションを計画・実行する。

## 手順

1. **現状分析**
   - 既存のマイグレーションファイルを確認
   - 現在のスキーマを把握

2. **計画作成**
   - 必要な変更をリスト化
   - 依存関係を確認
   - ロールバック手順を計画

3. **マイグレーション作成**
   - 適切な命名規則に従う
   - up/downの両方を実装

4. **検証**
   - ドライランで確認
   - テストデータで検証

## 出力

マイグレーション計画を以下の形式で報告:
- 変更内容の要約
- 実行順序
- リスク評価
- ロールバック手順
```

---

## 例3: フック付きプラグイン

コード品質を自動チェックするフックを含むプラグイン。

### ディレクトリ構造

```
quality-guard/
├── .claude-plugin/
│   └── plugin.json
├── hooks/
│   └── hooks.json
└── scripts/
    ├── lint.sh
    └── format-check.sh
```

### hooks/hooks.json

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/lint.sh $CLAUDE_FILE_PATH"
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/format-check.sh $CLAUDE_FILE_PATH"
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "echo \"[$(date)] $CLAUDE_NOTIFICATION\" >> ~/.claude/notifications.log"
          }
        ]
      }
    ]
  }
}
```

### scripts/lint.sh

```bash
#!/bin/bash
FILE="$1"

# ファイル拡張子に基づいてリンター実行
case "$FILE" in
  *.ts|*.tsx)
    npx eslint "$FILE" --fix
    ;;
  *.py)
    ruff check "$FILE" --fix
    ;;
  *.go)
    gofmt -w "$FILE"
    ;;
esac
```

---

## 例4: スキル付きプラグイン

API開発スキルを含むプラグイン。

### ディレクトリ構造

```
api-toolkit/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── api-test.md
└── skills/
    └── api-design/
        ├── SKILL.md
        └── PATTERNS.md
```

### skills/api-design/SKILL.md

```markdown
---
name: api-design
description: RESTful APIの設計とドキュメント作成を支援します。API設計、エンドポイント定義、OpenAPI仕様について質問された場合に使用してください。
---

# API設計スキル

## 設計原則

1. リソース指向URL
2. 適切なHTTPメソッド使用
3. 一貫したレスポンス形式
4. バージョニング戦略

## エンドポイント設計

```
GET    /api/v1/users          # 一覧取得
GET    /api/v1/users/:id      # 詳細取得
POST   /api/v1/users          # 作成
PUT    /api/v1/users/:id      # 更新
DELETE /api/v1/users/:id      # 削除
```

## レスポンス形式

```json
{
  "data": {},
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  },
  "errors": []
}
```

詳細なパターンは[PATTERNS.md](PATTERNS.md)を参照。
```

---

## 例5: MCPサーバー統合プラグイン

外部サービス連携用MCPサーバーを含むプラグイン。

### ディレクトリ構造

```
external-services/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
└── commands/
    └── fetch-data.md
```

### .mcp.json

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_TOKEN": "${SLACK_TOKEN}"
      }
    }
  }
}
```

---

## 例6: フルスタックプラグイン

すべてのコンポーネントを含む包括的なプラグイン。

### ディレクトリ構造

```
full-stack-toolkit/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
├── commands/
│   ├── scaffold.md
│   ├── deploy.md
│   └── test.md
├── agents/
│   ├── architect.md
│   └── debugger.md
├── skills/
│   ├── testing/
│   │   └── SKILL.md
│   └── deployment/
│       └── SKILL.md
└── hooks/
    └── hooks.json
```

### .claude-plugin/plugin.json

```json
{
  "name": "full-stack-toolkit",
  "description": "フルスタック開発のための包括的ツールキット",
  "version": "2.0.0",
  "author": {
    "name": "DevTeam",
    "email": "dev@example.com"
  },
  "repository": "https://github.com/example/full-stack-toolkit",
  "license": "MIT",
  "keywords": ["fullstack", "scaffold", "deploy", "testing"]
}
```

---

## マーケットプレイス設定例

### ローカル開発用

```json
{
  "name": "dev-marketplace",
  "owner": { "name": "Developer" },
  "plugins": [
    {
      "name": "code-reviewer",
      "source": "./plugins/code-reviewer",
      "description": "コードレビューツール"
    },
    {
      "name": "db-tools",
      "source": "./plugins/db-tools",
      "description": "データベースツール"
    }
  ]
}
```

### チーム配布用

```json
{
  "name": "team-marketplace",
  "owner": { "name": "Engineering Team" },
  "description": "社内標準プラグイン集",
  "plugins": [
    {
      "name": "quality-guard",
      "source": "https://github.com/team/quality-guard.git",
      "description": "品質チェックツール",
      "version": "1.2.0"
    },
    {
      "name": "api-toolkit",
      "source": "https://github.com/team/api-toolkit.git#v2.0.0",
      "description": "API開発ツール",
      "version": "2.0.0"
    }
  ]
}
```

### リポジトリ設定（.claude/settings.json）

```json
{
  "plugin_marketplaces": [
    "team/internal-marketplace",
    "https://github.com/company/claude-plugins.git"
  ],
  "plugins": [
    "quality-guard@team",
    "api-toolkit@team",
    "code-reviewer@company"
  ]
}
```
