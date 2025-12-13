---
name: claude-code-guide
description: Claude Codeの仕様、設定、機能について詳しく説明します。Claude Codeの使い方、設定方法、機能、コンテキストウィンドウ、MCP、メモリ、出力スタイル、ステータスラインなどについて質問された場合に使用してください。
---

# Claude Code 仕様ガイド

## 概要

Claude Codeは、Anthropic公式のCLIツールです。ソフトウェアエンジニアリングタスクを支援し、ファイル操作、コマンド実行、Web検索などの機能を提供します。

## 主要機能

### メモリ管理

Claude Codeは複数のメモリ階層を持ちます：

| タイプ | 場所 | 用途 |
|--------|------|------|
| エンタープライズ | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | 組織全体のポリシー |
| プロジェクト | `./CLAUDE.md` または `./.claude/CLAUDE.md` | チーム共有の指示 |
| プロジェクトルール | `./.claude/rules/*.md` | モジュール式のルール |
| ユーザー | `~/.claude/CLAUDE.md` | 個人設定（全プロジェクト） |
| ローカル | `./CLAUDE.local.md` | 個人設定（現プロジェクト） |

**初期化**: `/init` でCLAUDE.mdを生成

**インポート**: `@path/to/file` 構文で他ファイルを参照可能

詳細は[MEMORY.md](MEMORY.md)を参照。

### モデル設定

**エイリアス**:
- `default` - 推奨モデル
- `sonnet` - 日常のコーディング
- `opus` - 複雑な推論
- `haiku` - 高速・低コスト
- `sonnet[1m]` - 100万トークンコンテキスト
- `opusplan` - プラン時opus、実行時sonnet

**設定方法**:
```bash
# セッション中
/model opus

# 起動時
claude --model opus

# 環境変数
export ANTHROPIC_MODEL=opus
```

詳細は[MODEL-CONFIG.md](MODEL-CONFIG.md)を参照。

### コンテキストウィンドウ

- 標準: 200Kトークン
- 1M拡張: ベータ（層4以上）
- 拡張思考: 思考トークンは出力のみ課金

**Claude 4.5のコンテキスト認識**:
残りトークン数を自動追跡し、長時間タスクで効率的に動作。

詳細は[CONTEXT-WINDOW.md](CONTEXT-WINDOW.md)を参照。

### MCP (Model Context Protocol)

外部ツール・データソースへの接続プロトコル。

**サーバー追加**:
```bash
# HTTP
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# SSE
claude mcp add --transport sse asana https://mcp.asana.com/sse

# stdio
claude mcp add --transport stdio airtable -- npx -y airtable-mcp-server
```

**スコープ**:
- `local` (デフォルト): 現プロジェクト・自分のみ
- `project`: `.mcp.json`でチーム共有
- `user`: 全プロジェクト・自分のみ

詳細は[MCP.md](MCP.md)を参照。

### 出力スタイル

システムプロンプトを変更してClaudeの動作を調整。

**組み込みスタイル**:
- `default` - 標準のソフトウェアエンジニアリング向け
- `explanatory` - 教育的なインサイト付き
- `learning` - 協調学習モード（TODO(human)を追加）

**設定**:
```
/output-style
/output-style explanatory
/output-style:new I want an output style that ...
```

**保存場所**:
- ユーザー: `~/.claude/output-styles/`
- プロジェクト: `.claude/output-styles/`

### ステータスライン

カスタムステータスライン表示。

**設定** (`.claude/settings.json`):
```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 0
  }
}
```

**入力データ**（JSON via stdin）:
- `model.display_name` - モデル名
- `workspace.current_dir` - 現在のディレクトリ
- `cost.total_cost_usd` - コスト
- `context_window.*` - トークン使用量

詳細は[STATUSLINE.md](STATUSLINE.md)を参照。

### サブエージェント

特化したタスク用のAIアシスタント。

**場所**:
- プロジェクト: `.claude/agents/`
- ユーザー: `~/.claude/agents/`

**形式**:
```markdown
---
name: agent-name
description: 説明
tools: Read, Bash
model: sonnet
---

システムプロンプト
```

**管理**: `/agents` コマンド

### スキル

モジュール式の機能拡張。

**場所**:
- 個人用: `~/.claude/skills/`
- プロジェクト: `.claude/skills/`

**形式**:
```markdown
---
name: skill-name
description: 説明
---

# スキル名

## Instructions
指示内容
```

## コマンド一覧

| コマンド | 説明 |
|----------|------|
| `/help` | ヘルプ表示 |
| `/model` | モデル切り替え |
| `/memory` | メモリ編集 |
| `/mcp` | MCPサーバー管理 |
| `/agents` | サブエージェント管理 |
| `/output-style` | 出力スタイル変更 |
| `/statusline` | ステータスライン設定 |
| `/config` | 設定メニュー |
| `/init` | CLAUDE.md初期化 |
| `/status` | 現在の状態表示 |

## 環境変数

| 変数 | 説明 |
|------|------|
| `ANTHROPIC_MODEL` | デフォルトモデル |
| `ANTHROPIC_API_KEY` | APIキー |
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | opusエイリアスのモデル |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | sonnetエイリアスのモデル |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | haikuエイリアスのモデル |
| `CLAUDE_CODE_SUBAGENT_MODEL` | サブエージェントモデル |
| `MCP_TIMEOUT` | MCPタイムアウト（ms） |
| `MAX_MCP_OUTPUT_TOKENS` | MCP出力制限 |
| `DISABLE_PROMPT_CACHING` | キャッシュ無効化 |

## 設定ファイル

### settings.json

```json
{
  "permissions": {},
  "model": "sonnet",
  "statusLine": {}
}
```

### .mcp.json

```json
{
  "mcpServers": {
    "server-name": {
      "type": "http",
      "url": "https://example.com/mcp"
    }
  }
}
```

## よくある質問

**Q: モデルを変更するには？**
A: `/model opus` または `claude --model opus`

**Q: MCPサーバーを追加するには？**
A: `claude mcp add --transport http name url`

**Q: メモリを編集するには？**
A: `/memory` コマンド

**Q: コンテキストウィンドウの使用量を確認するには？**
A: `/status` コマンド

**Q: サブエージェントを作成するには？**
A: `/agents` → 「新しいエージェントを作成」
