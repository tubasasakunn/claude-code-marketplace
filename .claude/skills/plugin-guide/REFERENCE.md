# プラグインリファレンス

## plugin.json スキーマ

### 完全なスキーマ

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "プラグインの説明（最大256文字）",
  "author": {
    "name": "作者名",
    "email": "optional@example.com",
    "url": "https://optional-url.com"
  },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/user/repo",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "commands": ["./custom/commands/special.md"],
  "agents": "./custom/agents/",
  "skills": "./custom/skills/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "lspServers": "./.lsp.json",
  "outputStyles": "./styles/"
}
```

### 必須フィールド

| フィールド | 型 | 説明 | 例 |
|:-----------|:---|:-----|:---|
| `name` | string | 一意識別子（kebab-case、スペースなし） | `"deployment-tools"` |

### メタデータフィールド

| フィールド | 型 | 説明 | 例 |
|:-----------|:---|:-----|:---|
| `version` | string | セマンティックバージョン | `"2.1.0"` |
| `description` | string | プラグインの説明（最大256文字） | `"デプロイ自動化ツール"` |
| `author` | object | 作者情報 | `{"name": "Dev Team"}` |
| `homepage` | string | ドキュメントURL | `"https://docs.example.com"` |
| `repository` | string | ソースコードURL | `"https://github.com/user/plugin"` |
| `license` | string | ライセンス識別子 | `"MIT"`, `"Apache-2.0"` |
| `keywords` | array | 検索用タグ | `["deployment", "ci-cd"]` |

### コンポーネントパスフィールド

| フィールド | 型 | 説明 | 例 |
|:-----------|:---|:-----|:---|
| `commands` | string\|array | コマンドファイル/ディレクトリ | `"./custom/cmd.md"` |
| `agents` | string\|array | エージェントファイル | `"./custom/agents/"` |
| `skills` | string\|array | スキルディレクトリ | `"./custom/skills/"` |
| `hooks` | string\|object | フック設定パスまたはインライン | `"./hooks.json"` |
| `mcpServers` | string\|object | MCP設定パスまたはインライン | `"./mcp-config.json"` |
| `lspServers` | string\|object | LSP設定パスまたはインライン | `"./.lsp.json"` |

**パス規則**:
- すべてのパスは`./`で始まる相対パス
- カスタムパスはデフォルトディレクトリに追加（置き換えではない）
- 配列で複数パス指定可能

---

## スキル（skills/）

### ディレクトリ構造

```
skills/
└── my-skill/
    ├── SKILL.md      # メイン定義（必須）
    ├── REFERENCE.md  # 詳細リファレンス（任意）
    └── scripts/      # ユーティリティスクリプト（任意）
```

### SKILL.md形式

```yaml
---
name: skill-name
description: スキルの説明（最大1024文字）。何をするか＋いつ使用するかを説明。
disable-model-invocation: true
allowed-tools: Read, Write, Bash
---

# スキル名

## 指示

Claudeへの指示

## 例

使用例
```

### スキルフロントマター

| フィールド | 必須 | 説明 |
|:-----------|:-----|:-----|
| `name` | 推奨 | スキル識別子（小文字、数字、ハイフン） |
| `description` | 推奨 | 何をするか＋いつ使用するか |
| `disable-model-invocation` | 任意 | `true`で手動呼び出しのみ |
| `user-invocable` | 任意 | `false`で/メニューから非表示 |
| `allowed-tools` | 任意 | 使用可能なツールを制限 |
| `argument-hint` | 任意 | 引数ヒント（例：`[filename]`） |
| `context` | 任意 | `fork`でサブエージェント実行 |
| `agent` | 任意 | サブエージェントタイプ |

スキルの詳細は`skill-creator`スキルを参照。

---

## コマンド（commands/）

### ファイル形式

```markdown
---
description: コマンドの説明
allowed-tools: Read, Grep, Glob
---

# コマンドタイトル

Claudeへの指示をここに記述
```

### 引数の受け取り

`$ARGUMENTS`プレースホルダーを使用：

```markdown
---
description: 指定されたファイルをレビュー
---

以下のファイルをレビューしてください: $ARGUMENTS
```

使用例: `/my-plugin:review src/main.ts`

---

## エージェント（agents/）

### ファイル形式

```markdown
---
name: agent-name
description: エージェントが何をするか、いつ使用するか
capabilities: ["task1", "task2", "task3"]
allowed-tools: Read, Grep, Glob, Bash
---

# エージェント名

## 目的

このエージェントの目的を説明

## 能力
- 特定のタスクに優れている
- 別の特化した能力
- このエージェントを使うべき状況

## コンテキストと例
このエージェントが使用されるべき状況と解決する問題の例を提供
```

### フロントマター

| フィールド | 必須 | 説明 |
|:-----------|:-----|:-----|
| `name` | ✓ | エージェント識別子 |
| `description` | ✓ | エージェントの説明とトリガー条件 |
| `capabilities` | 任意 | 能力のリスト |
| `allowed-tools` | 任意 | 許可するツール |

---

## フック（hooks/）

### hooks.json形式

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint.sh $CLAUDE_FILE_PATH"
          }
        ]
      }
    ]
  }
}
```

### フックイベント

| イベント | タイミング | 用途 |
|:---------|:-----------|:-----|
| `PreToolUse` | ツール実行前 | 検証、確認 |
| `PostToolUse` | ツール実行後 | 後処理、通知 |
| `PostToolUseFailure` | ツール失敗後 | エラー処理 |
| `PermissionRequest` | 許可ダイアログ表示時 | カスタム確認 |
| `UserPromptSubmit` | ユーザー入力時 | 入力処理 |
| `Notification` | 通知発生時 | カスタム通知 |
| `Stop` | 停止時 | クリーンアップ |
| `SubagentStart` | サブエージェント開始時 | 初期化 |
| `SubagentStop` | サブエージェント停止時 | 終了処理 |
| `SessionStart` | セッション開始時 | 初期化 |
| `SessionEnd` | セッション終了時 | 終了処理 |
| `PreCompact` | 履歴圧縮前 | 保存処理 |

### フックタイプ

| タイプ | 説明 |
|:-------|:-----|
| `command` | シェルコマンド/スクリプト実行 |
| `prompt` | LLMでプロンプト評価（`$ARGUMENTS`でコンテキスト） |
| `agent` | 複雑な検証タスク用のエージェント実行 |

### 環境変数

| 変数 | 説明 |
|:-----|:-----|
| `CLAUDE_FILE_PATH` | 対象ファイルパス |
| `CLAUDE_FILE_CONTENT` | ファイル内容 |
| `CLAUDE_NOTIFICATION` | 通知メッセージ |
| `CLAUDE_TOOL_NAME` | ツール名 |
| `CLAUDE_TOOL_INPUT` | ツール入力（JSON） |
| `CLAUDE_TOOL_OUTPUT` | ツール出力（JSON） |
| `CLAUDE_PLUGIN_ROOT` | プラグインルートパス |

---

## MCPサーバー（.mcp.json）

### 形式

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-name"],
      "env": {
        "API_KEY": "${API_KEY}"
      }
    },
    "plugin-database": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": {
        "DB_PATH": "${CLAUDE_PLUGIN_ROOT}/data"
      }
    }
  }
}
```

### フィールド

| フィールド | 必須 | 説明 |
|:-----------|:-----|:-----|
| `command` | ✓ | 実行コマンド |
| `args` | 任意 | コマンド引数配列 |
| `env` | 任意 | 環境変数マッピング |
| `cwd` | 任意 | 作業ディレクトリ |

---

## LSPサーバー（.lsp.json）

### 形式

```json
{
  "go": {
    "command": "gopls",
    "args": ["serve"],
    "extensionToLanguage": {
      ".go": "go"
    }
  },
  "typescript": {
    "command": "typescript-language-server",
    "args": ["--stdio"],
    "extensionToLanguage": {
      ".ts": "typescript",
      ".tsx": "typescriptreact"
    }
  }
}
```

### 必須フィールド

| フィールド | 説明 |
|:-----------|:-----|
| `command` | LSPバイナリ（PATHに存在する必要あり） |
| `extensionToLanguage` | ファイル拡張子と言語識別子のマッピング |

### オプションフィールド

| フィールド | 説明 |
|:-----------|:-----|
| `args` | コマンドライン引数 |
| `transport` | 通信方式: `stdio`（デフォルト）または`socket` |
| `env` | 環境変数 |
| `initializationOptions` | 初期化オプション |
| `settings` | `workspace/didChangeConfiguration`で渡す設定 |
| `workspaceFolder` | ワークスペースフォルダパス |
| `startupTimeout` | 起動タイムアウト（ミリ秒） |
| `shutdownTimeout` | シャットダウンタイムアウト（ミリ秒） |
| `restartOnCrash` | クラッシュ時に自動再起動するか |
| `maxRestarts` | 最大再起動回数 |

> **重要**: 言語サーバーバイナリは別途インストールが必要。

---

## インストールスコープ

| スコープ | 設定ファイル | 用途 |
|:---------|:-------------|:-----|
| `user` | `~/.claude/settings.json` | 全プロジェクトで利用可能（デフォルト） |
| `project` | `.claude/settings.json` | チーム共有（バージョン管理） |
| `local` | `.claude/settings.local.json` | プロジェクト固有（gitignore） |
| `managed` | `managed-settings.json` | 管理者設定（読み取り専用） |

---

## デバッグ

### 構造確認

```bash
# プラグイン構造を確認
ls -la my-plugin/
ls -la my-plugin/.claude-plugin/
cat my-plugin/.claude-plugin/plugin.json

# デバッグモードで起動
claude --debug
```

### 検証コマンド

```bash
claude plugin validate .
```

または：

```shell
/plugin validate .
```

### 一般的な問題

| 問題 | 原因 | 解決策 |
|:-----|:-----|:-------|
| コマンドが表示されない | commands/が間違った場所 | プラグインルートにあるか確認 |
| プラグインがインストールできない | plugin.jsonの構文エラー | JSON構文を確認 |
| フックが動作しない | スクリプト実行権限なし | `chmod +x script.sh` |
| MCPサーバー失敗 | `${CLAUDE_PLUGIN_ROOT}`なし | 変数を使用 |
| パスエラー | 絶対パス使用 | 相対パスに変更 |
| LSP `Executable not found` | 言語サーバー未インストール | バイナリをインストール |
