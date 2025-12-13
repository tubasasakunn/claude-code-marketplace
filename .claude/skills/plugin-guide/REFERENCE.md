# プラグインリファレンス

## plugin.json スキーマ

```json
{
  "name": "plugin-name",
  "description": "プラグインの説明（最大256文字）",
  "version": "1.0.0",
  "author": {
    "name": "作者名",
    "email": "optional@example.com",
    "url": "https://optional-url.com"
  },
  "repository": "https://github.com/user/repo",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

### フィールド要件

| フィールド | 必須 | 説明 |
|-----------|-----|------|
| name | ✓ | 小文字、数字、ハイフンのみ。最大64文字 |
| description | ✓ | プラグインの説明。最大256文字 |
| version | ✓ | セマンティックバージョニング（例: 1.0.0） |
| author.name | ✓ | 作者名 |
| author.email | | 連絡先メール |
| author.url | | 作者のウェブサイト |
| repository | | ソースコードリポジトリURL |
| license | | ライセンス識別子 |
| keywords | | 検索用キーワード配列 |

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

### フロントマター

| フィールド | 必須 | 説明 |
|-----------|-----|------|
| description | ✓ | コマンドの説明（/helpに表示） |
| allowed-tools | | 許可するツールのカンマ区切りリスト |

### 引数の受け取り

コマンドは引数を受け取れます。`$ARGUMENTS`プレースホルダーを使用：

```markdown
---
description: 指定されたファイルをレビュー
---

以下のファイルをレビューしてください: $ARGUMENTS
```

使用例: `/review src/main.ts`

---

## エージェント（agents/）

### ファイル形式

```markdown
---
name: agent-name
description: エージェントが何をするか、いつ使用するか
allowed-tools: Read, Grep, Glob, Bash
---

# エージェント名

## 目的

このエージェントの目的を説明

## 手順

1. ステップ1
2. ステップ2
3. ステップ3

## 出力形式

結果の報告形式を定義
```

### フロントマター

| フィールド | 必須 | 説明 |
|-----------|-----|------|
| name | ✓ | エージェント識別子 |
| description | ✓ | エージェントの説明とトリガー条件 |
| allowed-tools | | 許可するツール |

---

## スキル（skills/）

### ディレクトリ構造

```
skills/
└── my-skill/
    ├── SKILL.md      # メイン定義（必須）
    ├── REFERENCE.md  # 詳細リファレンス
    └── scripts/      # ユーティリティスクリプト
```

### SKILL.md形式

```markdown
---
name: skill-name
description: スキルの説明（最大1024文字）
allowed-tools: Read, Write, Bash
---

# スキル名

## Instructions

Claudeへの指示

## Examples

使用例
```

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
            "command": "echo 'Bash tool is about to run'"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/lint.sh $CLAUDE_FILE_PATH"
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
            "command": "notify-send 'Claude Code' '$CLAUDE_NOTIFICATION'"
          }
        ]
      }
    ]
  }
}
```

### フックイベント

| イベント | タイミング | 用途 |
|---------|-----------|------|
| PreToolUse | ツール実行前 | 検証、確認 |
| PostToolUse | ツール実行後 | 後処理、通知 |
| Notification | 通知発生時 | カスタム通知 |
| Stop | 停止時 | クリーンアップ |

### 環境変数

フックで使用可能な環境変数：

| 変数 | 説明 |
|-----|------|
| CLAUDE_FILE_PATH | 対象ファイルパス |
| CLAUDE_FILE_CONTENT | ファイル内容 |
| CLAUDE_NOTIFICATION | 通知メッセージ |
| CLAUDE_TOOL_NAME | ツール名 |
| CLAUDE_TOOL_INPUT | ツール入力（JSON） |
| CLAUDE_TOOL_OUTPUT | ツール出力（JSON） |

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
    }
  }
}
```

### フィールド

| フィールド | 必須 | 説明 |
|-----------|-----|------|
| command | ✓ | 実行コマンド |
| args | | コマンド引数配列 |
| env | | 環境変数マッピング |

---

## マーケットプレイス

### marketplace.json形式

```json
{
  "name": "marketplace-name",
  "owner": {
    "name": "オーナー名"
  },
  "description": "マーケットプレイスの説明",
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "プラグインの説明",
      "version": "1.0.0"
    }
  ]
}
```

### プラグインソース形式

| 形式 | 例 |
|-----|-----|
| 相対パス | `./plugins/my-plugin` |
| 絶対パス | `/path/to/plugin` |
| Git URL | `https://github.com/user/plugin.git` |
| Git + パス | `https://github.com/user/repo.git#plugins/my-plugin` |

---

## デバッグ

### 構造確認

```bash
# プラグイン構造を確認
ls -la my-plugin/
ls -la my-plugin/.claude-plugin/
cat my-plugin/.claude-plugin/plugin.json
```

### 一般的な問題

| 問題 | 解決策 |
|-----|-------|
| コマンドが表示されない | commands/がプラグインルートにあるか確認 |
| プラグインがインストールできない | plugin.jsonの構文を確認 |
| フックが動作しない | hooks.jsonの形式とパスを確認 |
| 再起動後に反映されない | Claude Codeを完全に再起動 |

### 開発サイクル

```shell
# 変更をテストする際の流れ
/plugin uninstall my-plugin@test-marketplace
# プラグインファイルを編集
/plugin install my-plugin@test-marketplace
# Claude Codeを再起動してテスト
```
