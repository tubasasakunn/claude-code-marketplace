# フックリファレンス

## 入力スキーマ

全フックはstdinでJSONを受け取る。共通フィールド:

```typescript
{
  session_id: string
  transcript_path: string  // 会話JSONへのパス
  cwd: string              // 現在の作業ディレクトリ
  permission_mode: string  // "default" | "plan" | "acceptEdits" | "bypassPermissions"
  hook_event_name: string
}
```

### PreToolUse

```json
{
  "session_id": "abc123",
  "transcript_path": "~/.claude/projects/.../xxx.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "default",
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  }
}
```

### PostToolUse

```json
{
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.txt",
    "content": "file content"
  },
  "tool_response": {
    "filePath": "/path/to/file.txt",
    "success": true
  }
}
```

### UserPromptSubmit

```json
{
  "hook_event_name": "UserPromptSubmit",
  "prompt": "ユーザーが入力したプロンプト"
}
```

### Notification

```json
{
  "hook_event_name": "Notification",
  "message": "通知メッセージ"
}
```

### Stop / SubagentStop

```json
{
  "hook_event_name": "Stop",
  "stop_hook_active": true  // 既にstopフックで継続中の場合true
}
```

### PreCompact

```json
{
  "hook_event_name": "PreCompact",
  "trigger": "manual",  // "manual" | "auto"
  "custom_instructions": "/compactに渡された指示"
}
```

### SessionStart

```json
{
  "hook_event_name": "SessionStart",
  "source": "startup"  // "startup" | "resume" | "clear" | "compact"
}
```

### SessionEnd

```json
{
  "hook_event_name": "SessionEnd",
  "reason": "exit"  // "clear" | "logout" | "prompt_input_exit" | "other"
}
```

## 出力スキーマ

### シンプル出力（終了コード）

| 終了コード | stdout | stderr | 動作 |
|----------|--------|--------|------|
| 0 | トランスクリプトに表示 | - | 成功 |
| 2 | - | Claudeにフィードバック | ブロック |
| その他 | - | ユーザーに表示 | エラー（継続） |

### JSON出力

#### 共通フィールド

```json
{
  "continue": true,           // false=Claude全体を停止
  "stopReason": "停止理由",    // continueがfalseの場合
  "suppressOutput": false,    // trueでトランスクリプト非表示
  "systemMessage": "警告"      // ユーザーへの追加メッセージ
}
```

#### PreToolUse

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",  // "allow" | "deny" | "ask"
    "permissionDecisionReason": "理由",
    "updatedInput": {               // ツール入力の変更（オプション）
      "field_to_modify": "new value"
    }
  }
}
```

| permissionDecision | 動作 |
|-------------------|------|
| `allow` | 権限システムをバイパスして許可 |
| `deny` | ツール呼び出しをブロック |
| `ask` | ユーザーに確認を求める |

#### PostToolUse

```json
{
  "decision": "block",
  "reason": "Claudeへのフィードバック",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "追加コンテキスト"
  }
}
```

#### UserPromptSubmit

```json
{
  "decision": "block",
  "reason": "ユーザーへの説明",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "コンテキストに追加"
  }
}
```

#### Stop / SubagentStop

```json
{
  "decision": "block",
  "reason": "Claudeへの継続指示（必須）"
}
```

#### SessionStart

```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "セッション開始時のコンテキスト"
  }
}
```

## マッチャーパターン

| パターン | マッチ対象 |
|---------|----------|
| `Bash` | Bashツールのみ |
| `Edit\|Write` | EditまたはWrite |
| `Notebook.*` | Notebookで始まるツール |
| `mcp__memory__.*` | memoryサーバーの全ツール |
| `mcp__.*__write.*` | 全MCPサーバーのwrite系ツール |
| `*` または `""` | 全ツール |

## 主要ツール名

| ツール名 | 説明 |
|---------|------|
| `Bash` | シェルコマンド |
| `Read` | ファイル読み取り |
| `Write` | ファイル作成 |
| `Edit` | ファイル編集 |
| `Glob` | ファイルパターン検索 |
| `Grep` | コンテンツ検索 |
| `Task` | サブエージェント |
| `WebFetch` | Web取得 |
| `WebSearch` | Web検索 |
| `mcp__<server>__<tool>` | MCPツール |

## プロンプトベースのフック

`type: "prompt"`で LLM評価を使用:

```json
{
  "type": "prompt",
  "prompt": "評価内容: $ARGUMENTS",
  "timeout": 30
}
```

LLMは以下のJSONで応答:

```json
{
  "decision": "approve",  // "approve" | "block"
  "reason": "説明",
  "continue": false,      // オプション
  "stopReason": "メッセージ",
  "systemMessage": "警告"
}
```

## セキュリティ

### 必須事項

- シェル変数は常にクォート: `"$VAR"`
- 入力は検証・サニタイズ
- パストラバーサル（`..`）をチェック
- 絶対パスまたは`$CLAUDE_PROJECT_DIR`を使用
- 機密ファイル（`.env`, `.git/`）をスキップ

### 設定の安全性

- 設定変更は即座に反映されない
- スタートアップ時のスナップショットを使用
- 外部変更は警告表示
- `/hooks`でレビュー後に適用

## デバッグ

```bash
# デバッグモードで実行
claude --debug

# 手動テスト
echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' | python3 hook.py
```

## 実行仕様

| 項目 | 値 |
|-----|-----|
| デフォルトタイムアウト | 60秒 |
| 実行 | マッチする全フックが並列実行 |
| 重複排除 | 同一コマンドは自動重複排除 |
| 環境 | Claude Codeの環境で実行 |
