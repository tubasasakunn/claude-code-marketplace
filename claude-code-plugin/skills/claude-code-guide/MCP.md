# Claude Code MCP (Model Context Protocol)

## 概要

MCPは外部ツール・データソースへの接続プロトコル。Claude Codeに以下を可能にする:
- イシュートラッカーから機能実装
- 監視データ分析
- データベースクエリ
- デザイン統合
- ワークフロー自動化

---

## サーバーの追加

### HTTP（推奨）

```bash
claude mcp add --transport http <name> <url>

# 例: Notion
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Bearerトークン付き
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

### SSE（非推奨）

```bash
claude mcp add --transport sse <name> <url>

# 例: Asana
claude mcp add --transport sse asana https://mcp.asana.com/sse
```

### stdio（ローカル）

```bash
claude mcp add --transport stdio <name> -- <command> [args...]

# 例: Airtable
claude mcp add --transport stdio airtable --env AIRTABLE_API_KEY=YOUR_KEY \
  -- npx -y airtable-mcp-server
```

**`--`について**: Claudeのフラグとサーバーコマンドを分離

---

## サーバー管理

```bash
# 一覧表示
claude mcp list

# 詳細取得
claude mcp get github

# 削除
claude mcp remove github

# ステータス確認（Claude Code内）
/mcp
```

---

## スコープ

| スコープ | 場所 | 共有 |
|----------|------|------|
| `local`（デフォルト） | プロジェクト設定 | 自分のみ |
| `project` | `.mcp.json` | チーム |
| `user` | ユーザー設定 | 全プロジェクト・自分のみ |

```bash
claude mcp add --transport http github --scope project https://...
```

### 優先順位

local > project > user

---

## .mcp.json

チーム共有用設定ファイル。

```json
{
  "mcpServers": {
    "shared-server": {
      "command": "/path/to/server",
      "args": [],
      "env": {}
    }
  }
}
```

### 環境変数展開

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

**構文**:
- `${VAR}` - 変数展開
- `${VAR:-default}` - デフォルト値付き

---

## 認証（OAuth 2.0）

```
/mcp
```

ブラウザでログイン。トークンは自動保存・更新。

---

## JSONから追加

```bash
claude mcp add-json weather-api '{"type":"http","url":"https://api.weather.com/mcp"}'
```

---

## Claude Desktopからインポート

```bash
claude mcp add-from-claude-desktop
```

macOSとWSLのみ対応。

---

## Claude CodeをMCPサーバーとして使用

```bash
claude mcp serve
```

Claude Desktop設定:
```json
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

---

## リソースとプロンプト

### リソース参照

```
@server:protocol://resource/path
```

例:
```
Can you analyze @github:issue://123?
```

### プロンプト（スラッシュコマンド）

```
/mcp__github__list_prs
/mcp__github__pr_review 456
```

---

## 出力制限

- 警告閾値: 10,000トークン
- デフォルト上限: 25,000トークン

```bash
export MAX_MCP_OUTPUT_TOKENS=50000
claude
```

---

## タイムアウト

```bash
MCP_TIMEOUT=10000 claude  # 10秒
```

---

## エンタープライズ設定

### managed-mcp.json

| OS | 場所 |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/managed-mcp.json` |
| Windows | `C:\ProgramData\ClaudeCode\managed-mcp.json` |
| Linux | `/etc/claude-code/managed-mcp.json` |

### 許可/拒否リスト

`managed-settings.json`:

```json
{
  "allowedMcpServers": [
    { "serverName": "github" }
  ],
  "deniedMcpServers": [
    { "serverName": "filesystem" }
  ]
}
```

---

## Windows注意

ネイティブWindows（WSL以外）では`cmd /c`ラッパーが必要:

```bash
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

---

## トラブルシューティング

**接続エラー**:
1. URLを確認
2. 認証を確認（`/mcp`）
3. タイムアウトを増やす

**サーバーが起動しない**:
1. コマンドパスを確認
2. 依存関係をインストール
3. 環境変数を確認
