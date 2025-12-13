---
name: hooks-guide
description: Claude Codeのフック（Hooks）を作成・設定します。フックの作成、hooks.json の書き方、イベントハンドラーの実装について質問された場合に使用してください。
---

# Claude Code Hooks ガイド

## フックとは

フックはClaude Codeのライフサイクルの特定ポイントで実行されるシェルコマンドです。LLMの判断に依存せず、決定論的に特定のアクションを実行できます。

## 設定ファイルの場所

- **ユーザー設定**: `~/.claude/settings.json`
- **プロジェクト設定**: `.claude/settings.json`
- **ローカル設定**: `.claude/settings.local.json`（コミットしない）
- **プラグイン**: `hooks/hooks.json`

## 基本構造

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          {
            "type": "command",
            "command": "your-command-here",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

## フィールド

| フィールド | 説明 |
|---------|------|
| `matcher` | ツール名パターン（正規表現可）。`*`で全ツール |
| `type` | `"command"`（bash）または`"prompt"`（LLM評価） |
| `command` | 実行するbashコマンド |
| `timeout` | タイムアウト秒数（デフォルト60秒） |

## イベント一覧

| イベント | タイミング | matcher使用 |
|--------|----------|-------------|
| `PreToolUse` | ツール実行前（ブロック可） | ○ |
| `PostToolUse` | ツール実行後 | ○ |
| `UserPromptSubmit` | プロンプト送信時 | × |
| `Notification` | 通知送信時 | × |
| `Stop` | エージェント停止時 | × |
| `SubagentStop` | サブエージェント停止時 | × |
| `PreCompact` | コンパクト操作前 | △（manual/auto） |
| `SessionStart` | セッション開始時 | △（startup/resume/clear/compact） |
| `SessionEnd` | セッション終了時 | × |

## 終了コード

| コード | 動作 |
|-------|------|
| 0 | 成功。stdoutはトランスクリプトに表示 |
| 2 | ブロック。stderrがClaudeにフィードバック |
| その他 | エラー表示のみ、実行は継続 |

## 環境変数

| 変数 | 説明 |
|-----|------|
| `CLAUDE_PROJECT_DIR` | プロジェクトルートの絶対パス |
| `CLAUDE_ENV_FILE` | 環境変数永続化ファイル（SessionStartのみ） |
| `CLAUDE_PLUGIN_ROOT` | プラグインディレクトリ（プラグインのみ） |

## クイックスタート

### 1. `/hooks`コマンドで設定

```
/hooks → イベント選択 → マッチャー追加 → コマンド追加
```

### 2. 設定ファイルを直接編集

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "npx prettier --write \"$(jq -r '.tool_input.file_path')\""
          }
        ]
      }
    ]
  }
}
```

## よく使うパターン

### ファイル編集後のフォーマット

```json
{
  "matcher": "Edit|Write",
  "hooks": [{
    "type": "command",
    "command": "jq -r '.tool_input.file_path' | xargs -I {} sh -c 'echo {} | grep -q \"\\.ts$\" && npx prettier --write {}'"
  }]
}
```

### 機密ファイル保護

```json
{
  "matcher": "Edit|Write",
  "hooks": [{
    "type": "command",
    "command": "python3 -c \"import json,sys; p=json.load(sys.stdin).get('tool_input',{}).get('file_path',''); sys.exit(2 if any(x in p for x in ['.env','.git/']) else 0)\""
  }]
}
```

### Bashコマンドログ

```json
{
  "matcher": "Bash",
  "hooks": [{
    "type": "command",
    "command": "jq -r '.tool_input.command' >> ~/.claude/bash-log.txt"
  }]
}
```

詳細な例は[EXAMPLES.md](EXAMPLES.md)、入出力スキーマは[REFERENCE.md](REFERENCE.md)を参照。

## フック作成の流れ

1. **目的を決める**: 何を自動化/制御したいか
2. **イベントを選ぶ**: どのタイミングで実行するか
3. **マッチャーを設定**: どのツールを対象にするか
4. **コマンドを書く**: stdin JSONを処理するスクリプト
5. **テスト**: 手動でコマンドを実行して確認
6. **登録**: `/hooks`または設定ファイルで登録

## チェックリスト

- [ ] 適切なイベントを選択したか
- [ ] マッチャーパターンは正しいか（大文字小文字区別）
- [ ] スクリプトは実行可能か（`chmod +x`）
- [ ] 入力JSONを正しく処理しているか
- [ ] 終了コードは適切か（0=成功、2=ブロック）
- [ ] タイムアウトは十分か
- [ ] セキュリティリスクを確認したか
