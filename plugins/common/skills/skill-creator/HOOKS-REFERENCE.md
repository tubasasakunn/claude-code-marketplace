# Hooksリファレンス

スキル、エージェント、スラッシュコマンドで使用できるHooksの詳細リファレンスです。

---

## 目次

- 基本構造
- サポートイベント
- Hook入力
- Hook出力
- 設定例
- プロンプトベースHooks

---

## 基本構造

### スキル/エージェント/スラッシュコマンドでのHooks

フロントマターで定義:

```yaml
---
name: secure-operations
description: セキュリティチェック付き操作
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/run-linter.sh"
---
```

### 設定ファイルでのHooks

`settings.json`で定義:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/format.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

---

## サポートイベント

スキル、エージェント、スラッシュコマンドでサポートされるイベント:

| イベント | 説明 |
|:---------|:-----|
| `PreToolUse` | ツール呼び出し処理前 |
| `PostToolUse` | ツール完了直後 |
| `Stop` | エージェント応答終了時 |

### 設定ファイルでの追加イベント

| イベント | 説明 |
|:---------|:-----|
| `PermissionRequest` | 許可ダイアログ表示時 |
| `Notification` | 通知送信時 |
| `UserPromptSubmit` | プロンプト送信時 |
| `SubagentStop` | サブエージェント終了時 |
| `PreCompact` | コンパクト操作前 |
| `SessionStart` | セッション開始時 |
| `SessionEnd` | セッション終了時 |

---

## 一般的なマッチャー

### ツール名

- `Bash` - シェルコマンド
- `Read` - ファイル読み取り
- `Edit` - ファイル編集
- `Write` - ファイル書き込み
- `Glob` - ファイルパターンマッチング
- `Grep` - コンテンツ検索
- `Task` - サブエージェントタスク
- `WebFetch`、`WebSearch` - Web操作

### パターンマッチング

- 単純文字列: `Write`（完全一致）
- 正規表現: `Edit|Write`、`Notebook.*`
- すべて: `*`または空文字列

---

## Hook入力

Hooksはstdinを介してJSONデータを受け取ります。

### 共通フィールド

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/directory",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse"
}
```

### PreToolUse入力

```json
{
  "session_id": "abc123",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

### PostToolUse入力

```json
{
  "session_id": "abc123",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

### Stop入力

```json
{
  "session_id": "abc123",
  "hook_event_name": "Stop",
  "stop_hook_active": false
}
```

---

## Hook出力

### 終了コードによる制御

| 終了コード | 動作 |
|:-----------|:-----|
| 0 | 成功。stdoutは詳細モードで表示 |
| 2 | ブロッキングエラー。stderrをClaudeにフィードバック |
| その他 | 非ブロッキングエラー。stderrを詳細モードで表示 |

### 終了コード2の動作

| イベント | 動作 |
|:---------|:-----|
| `PreToolUse` | ツール呼び出しをブロック |
| `PostToolUse` | stderrをClaudeに表示（ツールは既に実行済み） |
| `Stop` | 停止をブロック、stderrをClaudeに表示 |

### JSON出力による高度な制御

終了コード0でstdoutにJSONを出力:

#### PreToolUse決定制御

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "自動承認理由",
    "updatedInput": {
      "field_to_modify": "new value"
    }
  }
}
```

**permissionDecision**:
- `"allow"` - 許可システムをバイパス
- `"deny"` - ツール呼び出しを拒否
- `"ask"` - ユーザーに確認を求める

#### PostToolUse決定制御

```json
{
  "decision": "block",
  "reason": "リント違反が検出されました",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "追加コンテキスト情報"
  }
}
```

#### Stop決定制御

```json
{
  "decision": "block",
  "reason": "テストが失敗しています。修正してください。"
}
```

---

## 設定例

### セキュリティチェック（PreToolUse）

```yaml
---
name: secure-bash
description: Bashコマンドにセキュリティチェックを適用
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
          timeout: 10
---
```

**scripts/security-check.sh**:
```bash
#!/bin/bash
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command')

# 危険なコマンドをチェック
if echo "$command" | grep -qE '(rm -rf|sudo|chmod 777)'; then
    echo "危険なコマンドが検出されました" >&2
    exit 2
fi

exit 0
```

### コードフォーマット（PostToolUse）

```yaml
---
name: auto-format
description: ファイル編集後に自動フォーマット
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/format.sh"
---
```

**scripts/format.sh**:
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path')

# ファイル拡張子に基づいてフォーマット
case "$file_path" in
    *.py)
        black "$file_path" 2>/dev/null
        ;;
    *.js|*.ts)
        prettier --write "$file_path" 2>/dev/null
        ;;
esac

exit 0
```

### 完了確認（Stop）

```yaml
---
name: completion-check
description: タスク完了を確認
hooks:
  Stop:
    - hooks:
        - type: command
          command: "./scripts/check-completion.sh"
---
```

---

## プロンプトベースHooks

LLMを使用してアクションを評価:

```yaml
hooks:
  Stop:
    - hooks:
        - type: prompt
          prompt: |
            タスクの完了状況を評価してください。
            コンテキスト: $ARGUMENTS

            以下を確認:
            1. すべての要求タスクが完了しているか
            2. エラーが解決されているか
            3. フォローアップが必要か

            JSON形式で応答: {"ok": true} または {"ok": false, "reason": "理由"}
          timeout: 30
```

### レスポンス形式

```json
{
  "ok": true
}
```

または

```json
{
  "ok": false,
  "reason": "テストが失敗しています"
}
```

---

## 環境変数

Hookコマンド実行時に利用可能:

| 変数 | 説明 |
|:-----|:-----|
| `CLAUDE_PROJECT_DIR` | プロジェクトルートディレクトリ |
| `CLAUDE_PLUGIN_ROOT` | プラグインディレクトリ（プラグインhookのみ） |
| `CLAUDE_CODE_REMOTE` | リモート環境では`"true"` |

---

## 追加オプション

### once（スキル/スラッシュコマンドのみ）

`once: true`でセッションごとに1回だけ実行:

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/one-time-setup.sh"
          once: true
```

---

## セキュリティに関する考慮事項

### ベストプラクティス

1. **入力を検証**: 入力データを盲目的に信頼しない
2. **変数をクォート**: `$VAR`ではなく`"$VAR"`
3. **パストラバーサルをブロック**: ファイルパスで`..`をチェック
4. **絶対パスを使用**: スクリプトの完全なパスを指定
5. **機密ファイルをスキップ**: `.env`、`.git/`、キーを避ける

### 入力検証例

```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path')

# パストラバーサルをチェック
if echo "$file_path" | grep -q '\.\.'; then
    echo "不正なパスが検出されました" >&2
    exit 2
fi

# 機密ファイルをチェック
if echo "$file_path" | grep -qE '\.(env|key|pem)$'; then
    echo "機密ファイルへのアクセスは許可されていません" >&2
    exit 2
fi

exit 0
```

---

## デバッグ

### 基本的なトラブルシューティング

1. `/hooks`でhook登録を確認
2. JSON構文を検証
3. コマンドを手動でテスト
4. スクリプトの実行権限を確認
5. `claude --debug`でhook実行詳細を確認

### デバッグ出力例

```
[DEBUG] Executing hooks for PostToolUse:Write
[DEBUG] Found 1 hook commands to execute
[DEBUG] Hook command completed with status 0
```
