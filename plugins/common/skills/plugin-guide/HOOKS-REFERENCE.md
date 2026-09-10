# Hooks リファレンス

Hooksは、Claude Codeのイベントに応じて自動的にコマンドやプロンプトを実行する仕組みです。

---

## クイックスタート

### 1. ディレクトリ作成

```bash
mkdir -p my-plugin/hooks
mkdir -p my-plugin/scripts
```

### 2. hooks.json作成

```bash
cat > my-plugin/hooks/hooks.json << 'EOF'
{
  "hooks": {
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
EOF
```

### 3. スクリプト作成

```bash
cat > my-plugin/scripts/lint.sh << 'EOF'
#!/bin/bash
FILE="$1"

case "$FILE" in
  *.ts|*.tsx)
    npx eslint "$FILE" --fix
    ;;
  *.py)
    ruff check "$FILE" --fix
    ;;
esac
EOF

chmod +x my-plugin/scripts/lint.sh
```

---

## hooks.json スキーマ

### 基本構造

```json
{
  "description": "フックの説明（任意）",
  "hooks": {
    "イベント名": [
      {
        "matcher": "ツールパターン",
        "hooks": [
          {
            "type": "command",
            "command": "実行コマンド",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### フィールド

| フィールド | 必須 | 説明 |
|:-----------|:-----|:-----|
| `matcher` | ✓ | ツール名パターン（正規表現対応） |
| `hooks` | ✓ | 実行するフック配列 |
| `type` | ✓ | `command`または`prompt` |
| `command` | ※ | 実行するシェルコマンド（type: commandの場合） |
| `prompt` | ※ | LLMに送るプロンプト（type: promptの場合） |
| `timeout` | - | タイムアウト秒数（デフォルト: 60） |

---

## フックイベント一覧

### ツール関連

| イベント | タイミング | 主な用途 |
|:---------|:-----------|:---------|
| `PreToolUse` | ツール実行前 | 検証、ブロック、入力修正 |
| `PostToolUse` | ツール成功後 | lint、フォーマット、ログ |
| `PostToolUseFailure` | ツール失敗後 | エラーハンドリング |
| `PermissionRequest` | 許可ダイアログ表示時 | カスタム確認、自動承認 |

### セッション関連

| イベント | タイミング | 主な用途 |
|:---------|:-----------|:---------|
| `SessionStart` | セッション開始時 | 環境変数設定、初期化 |
| `SessionEnd` | セッション終了時 | クリーンアップ |
| `UserPromptSubmit` | ユーザー入力時 | 入力検証、コンテキスト追加 |
| `Stop` | Claude応答完了時 | 終了処理 |

### サブエージェント関連

| イベント | タイミング | 主な用途 |
|:---------|:-----------|:---------|
| `SubagentStart` | サブエージェント開始時 | 初期化 |
| `SubagentStop` | サブエージェント終了時 | 終了処理 |

### その他

| イベント | タイミング | 主な用途 |
|:---------|:-----------|:---------|
| `Notification` | 通知発生時 | ログ、外部通知 |
| `PreCompact` | 履歴圧縮前 | データ保存 |
| `Setup` | `--init`等のフラグ使用時 | セットアップ処理 |

---

## マッチャーの書き方

```json
// 単一ツール
"matcher": "Bash"

// 複数ツール（正規表現）
"matcher": "Write|Edit"

// 全ツール
"matcher": "*"
"matcher": ""

// MCPツール
"matcher": "mcp__memory__.*"
"matcher": "mcp__.*__write.*"
```

### イベント別マッチャー

#### PreToolUse / PostToolUse / PermissionRequest

- `Bash` - シェルコマンド
- `Read` - ファイル読み取り
- `Write` - ファイル書き込み
- `Edit` - ファイル編集
- `Glob` - ファイルパターンマッチング
- `Grep` - コンテンツ検索
- `Task` - サブエージェントタスク
- `WebFetch`, `WebSearch` - Web操作

#### Notification

- `permission_prompt` - 許可リクエスト
- `idle_prompt` - ユーザー入力待ち（60秒以上）
- `auth_success` - 認証成功通知
- `elicitation_dialog` - MCPツール入力要求

#### PreCompact

- `manual` - `/compact`から呼び出し
- `auto` - 自動コンパクト

#### SessionStart

- `startup` - 起動時
- `resume` - `--resume`、`--continue`、`/resume`から
- `clear` - `/clear`から
- `compact` - コンパクト後

#### Setup

- `init` - `--init`または`--init-only`から
- `maintenance` - `--maintenance`から

---

## フックタイプ

### command（シェルコマンド）

```json
{
  "type": "command",
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint.sh $CLAUDE_FILE_PATH",
  "timeout": 30
}
```

### prompt（LLM評価）

高速LLM（Haiku）でプロンプトを評価します。

```json
{
  "type": "prompt",
  "prompt": "タスクが完了したか評価: $ARGUMENTS。すべてのタスクが完了しているか確認してください。",
  "timeout": 30
}
```

**特徴:**
- `$ARGUMENTS`プレースホルダーでフック入力JSONを参照
- 応答スキーマ: `{"ok": true|false, "reason": "説明"}`
- `Stop`や`SubagentStop`での完了確認に有用

---

## 環境変数

### 全フック共通

| 変数 | 説明 |
|:-----|:-----|
| `CLAUDE_PROJECT_DIR` | プロジェクトルートの絶対パス |
| `CLAUDE_PLUGIN_ROOT` | プラグインディレクトリの絶対パス |
| `CLAUDE_CODE_REMOTE` | リモート環境では`"true"` |

### ツール関連フック

| 変数 | 説明 |
|:-----|:-----|
| `CLAUDE_TOOL_NAME` | ツール名 |
| `CLAUDE_TOOL_INPUT` | ツール入力（JSON） |
| `CLAUDE_TOOL_OUTPUT` | ツール出力（JSON）※PostToolUseのみ |
| `CLAUDE_FILE_PATH` | 対象ファイルパス |
| `CLAUDE_FILE_CONTENT` | ファイル内容 |

### その他

| 変数 | 説明 |
|:-----|:-----|
| `CLAUDE_NOTIFICATION` | 通知メッセージ |
| `CLAUDE_ENV_FILE` | 環境変数永続化ファイルパス |

---

## 戻り値（Exit Code）

| Exit Code | 意味 | 動作 |
|:----------|:-----|:-----|
| `0` | 成功 | stdoutがverboseモードで表示 |
| `2` | ブロッキングエラー | 処理をブロック、stderrがClaudeにフィードバック |
| その他 | 非ブロッキングエラー | stderrがverboseで表示、実行継続 |

### Exit Code 2のイベント別動作

| イベント | 動作 |
|:---------|:-----|
| `PreToolUse` | ツール呼び出しをブロック |
| `PermissionRequest` | 許可を拒否 |
| `PostToolUse` | stderrをClaudeに表示（既に実行済み） |
| `UserPromptSubmit` | プロンプト処理をブロック |
| `Stop` | 停止をブロック |
| `SubagentStop` | 停止をブロック |

---

## JSON出力（高度な制御）

stdoutにJSONを出力することで、より細かい制御が可能です。

### 共通フィールド

```json
{
  "continue": true,
  "stopReason": "停止理由",
  "suppressOutput": true,
  "systemMessage": "システムメッセージ"
}
```

### PreToolUse 制御

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "理由",
    "updatedInput": { "field": "new value" },
    "additionalContext": "追加コンテキスト"
  }
}
```

**permissionDecision:**
- `allow` - 自動承認
- `deny` - 拒否
- `ask` - ユーザーに確認

### PermissionRequest 制御

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow",
      "updatedInput": { "command": "npm run lint" },
      "message": "拒否理由",
      "interrupt": true
    }
  }
}
```

### PostToolUse 制御

```json
{
  "decision": "block",
  "reason": "説明",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "追加情報"
  }
}
```

---

## フック入力データ構造

フックはstdinでJSON形式のデータを受け取ります。

### 共通フィールド

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/Users/...",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse"
}
```

### ツール別入力

**Bash:**
```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test",
    "description": "Run tests",
    "timeout": 120000
  }
}
```

**Write:**
```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  }
}
```

**Edit:**
```json
{
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "old_string": "original",
    "new_string": "replacement"
  }
}
```

---

## 実践例

### 例1: ファイル保存後に自動lint

```json
{
  "hooks": {
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

**scripts/lint.sh:**
```bash
#!/bin/bash
FILE="$1"

case "$FILE" in
  *.ts|*.tsx|*.js|*.jsx)
    npx eslint "$FILE" --fix 2>&1
    ;;
  *.py)
    ruff check "$FILE" --fix 2>&1
    ;;
  *)
    exit 0
    ;;
esac
```

### 例2: 危険なBashコマンドをブロック

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate-bash.py"
          }
        ]
      }
    ]
  }
}
```

**scripts/validate-bash.py:**
```python
#!/usr/bin/env python3
import json
import re
import sys

DANGEROUS_PATTERNS = [
    (r'rm\s+-rf\s+/', "rm -rf / is not allowed"),
    (r'>\s*/dev/sd', "Writing to block devices is not allowed"),
]

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Invalid JSON: {e}", file=sys.stderr)
    sys.exit(1)

command = input_data.get("tool_input", {}).get("command", "")

for pattern, message in DANGEROUS_PATTERNS:
    if re.search(pattern, command):
        print(message, file=sys.stderr)
        sys.exit(2)

sys.exit(0)
```

### 例3: 通知をログに記録

```json
{
  "hooks": {
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

### 例4: セッション開始時に環境変数設定

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/init-env.sh"
          }
        ]
      }
    ]
  }
}
```

**scripts/init-env.sh:**
```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"
  echo 'export DEBUG=true' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

### 例5: ドキュメントファイルの自動承認

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/auto-approve-docs.py"
          }
        ]
      }
    ]
  }
}
```

**scripts/auto-approve-docs.py:**
```python
#!/usr/bin/env python3
import json
import sys

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(1)

file_path = input_data.get("tool_input", {}).get("file_path", "")

if file_path.endswith((".md", ".mdx", ".txt", ".json")):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Documentation file auto-approved"
        },
        "suppressOutput": True
    }
    print(json.dumps(output))

sys.exit(0)
```

### 例6: タスク完了確認（prompt型）

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "prompt",
            "prompt": "以下のコンテキストを確認し、すべてのタスクが完了しているか評価してください: $ARGUMENTS"
          }
        ]
      }
    ]
  }
}
```

---

## スキル内でのフック定義

スキルのフロントマターでもフックを定義できます。

```yaml
---
name: secure-operations
description: セキュリティチェック付きで操作を実行
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
          once: true
---
```

**追加オプション:**
- `once`: `true`でセッション中一度だけ実行

---

## デバッグ

```bash
claude --debug
```

**デバッグ出力例:**
```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Getting matching hook commands for PostToolUse with query: Write
[DEBUG] Found 1 hook matchers in settings
[DEBUG] Matched 1 hooks for query "Write"
[DEBUG] Found 1 hook commands to execute
[DEBUG] Executing hook command: <command> with timeout 60000ms
[DEBUG] Hook command completed with status 0: <stdout>
```

---

## トラブルシューティング

| 問題 | 原因 | 解決策 |
|:-----|:-----|:-------|
| フックが動作しない | 実行権限なし | `chmod +x script.sh` |
| パスが見つからない | 絶対パス使用 | `${CLAUDE_PLUGIN_ROOT}`を使用 |
| JSONパースエラー | stdin読み取り失敗 | `json.load(sys.stdin)`で読み取り |
| ブロックされない | exit code != 2 | `exit 2`でブロック |
| 環境変数が空 | 変数名の誤り | 正しい変数名を確認 |

---

## セキュリティベストプラクティス

1. **入力を検証** - stdinのJSONを盲目的に信頼しない
2. **シェル変数をクォート** - `$VAR`ではなく`"$VAR"`
3. **パストラバーサルをブロック** - `..`をチェック
4. **絶対パスを使用** - スクリプトにはフルパスを指定
5. **機密ファイルをスキップ** - `.env`、キーファイルを避ける
