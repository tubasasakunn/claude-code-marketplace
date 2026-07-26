# プラグイン実践例

## 例1: シンプルなスキルプラグイン

コードレビュースキルを提供するプラグイン。

### ディレクトリ構造

```
code-reviewer/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    ├── review/
    │   └── SKILL.md
    └── review-pr/
        └── SKILL.md
```

### .claude-plugin/plugin.json

```json
{
  "name": "code-reviewer",
  "description": "コードレビュー用スキルを提供",
  "version": "1.0.0",
  "author": {
    "name": "Your Team"
  }
}
```

### skills/review/SKILL.md

```yaml
---
name: review
description: 指定ファイルのコードレビューを実行。コード品質チェック、セキュリティ分析時に使用。
disable-model-invocation: true
allowed-tools: Read, Grep, Glob
argument-hint: [filepath]
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

### skills/review-pr/SKILL.md

```yaml
---
name: review-pr
description: PRの変更をレビュー。プルリクエストレビュー時に使用。
disable-model-invocation: true
allowed-tools: Read, Grep, Glob, Bash(git:*)
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
├── skills/
│   └── migrate/
│       └── SKILL.md
└── agents/
    └── migration-planner.md
```

### agents/migration-planner.md

```markdown
---
name: migration-planner
description: データベースマイグレーションを計画・実行します。スキーマ変更、マイグレーション作成、データベース構造の変更について質問された場合に使用してください。
capabilities: ["schema-analysis", "migration-planning", "rollback-design"]
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
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint.sh $CLAUDE_FILE_PATH"
          }
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format-check.sh $CLAUDE_FILE_PATH"
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

## 例4: MCPサーバー統合プラグイン

外部サービス連携用MCPサーバーを含むプラグイン。

### ディレクトリ構造

```
external-services/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
└── skills/
    └── fetch-data/
        └── SKILL.md
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

## 例5: LSPサーバープラグイン

言語サーバーを設定するプラグイン。

### ディレクトリ構造

```
go-lsp/
├── .claude-plugin/
│   └── plugin.json
└── .lsp.json
```

### .claude-plugin/plugin.json

```json
{
  "name": "go-lsp",
  "description": "Go言語のコードインテリジェンスを提供",
  "version": "1.0.0",
  "author": {
    "name": "Your Team"
  }
}
```

### .lsp.json

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  }
}
```

> **注意**: `gopls`は別途インストールが必要：`go install golang.org/x/tools/gopls@latest`

---

## 例6: フルスタックプラグイン

すべてのコンポーネントを含む包括的なプラグイン。

### ディレクトリ構造

```
full-stack-toolkit/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
├── .lsp.json
├── skills/
│   ├── scaffold/
│   │   └── SKILL.md
│   ├── deploy/
│   │   └── SKILL.md
│   └── test/
│       └── SKILL.md
├── agents/
│   ├── architect.md
│   └── debugger.md
├── hooks/
│   └── hooks.json
└── scripts/
    ├── pre-deploy.sh
    └── post-test.sh
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
  "homepage": "https://docs.example.com/full-stack-toolkit",
  "repository": "https://github.com/example/full-stack-toolkit",
  "license": "MIT",
  "keywords": ["fullstack", "scaffold", "deploy", "testing"]
}
```

---

## 例7: Exploreエージェントを使ったリサーチスキル

サブエージェントでコードベース探索を行うスキル。

### skills/code-explorer/SKILL.md

```yaml
---
name: code-explorer
description: コードベースを探索して構造を理解。コードベースの構造、アーキテクチャ、ファイル配置について質問された場合に使用。
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

$ARGUMENTSについてコードベースを探索:

1. Globで関連ファイルパターンを検索
2. Grepでキーワードを検索
3. Readで重要ファイルを分析
4. ファイル参照付きで要約

ファイルの変更は行わない。
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
      "source": {
        "source": "github",
        "repo": "team/quality-guard"
      },
      "description": "品質チェックツール",
      "version": "1.2.0"
    },
    {
      "name": "api-toolkit",
      "source": {
        "source": "github",
        "repo": "team/api-toolkit",
        "ref": "v2.0.0"
      },
      "description": "API開発ツール",
      "version": "2.0.0"
    }
  ]
}
```

### リポジトリ設定（.claude/settings.json）

```json
{
  "extraKnownMarketplaces": {
    "team-marketplace": {
      "source": {
        "source": "github",
        "repo": "company/claude-plugins"
      }
    }
  },
  "enabledPlugins": {
    "quality-guard@team-marketplace": true,
    "api-toolkit@team-marketplace": true
  }
}
```
