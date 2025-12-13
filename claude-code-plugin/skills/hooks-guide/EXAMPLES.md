# フック実装例

## PreToolUse フック

### Bashコマンドバリデーター

危険なコマンドをブロック:

```python
#!/usr/bin/env python3
import json
import re
import sys

DANGEROUS_PATTERNS = [
    (r"\brm\s+-rf\s+/", "ルートディレクトリの削除は禁止"),
    (r"\bsudo\b", "sudoコマンドは禁止"),
    (r">\s*/dev/", "デバイスファイルへの書き込みは禁止"),
]

input_data = json.load(sys.stdin)
command = input_data.get("tool_input", {}).get("command", "")

for pattern, message in DANGEROUS_PATTERNS:
    if re.search(pattern, command):
        print(f"ブロック: {message}", file=sys.stderr)
        sys.exit(2)

sys.exit(0)
```

設定:
```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "python3 \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/bash_validator.py"
      }]
    }]
  }
}
```

### ファイル保護（JSON出力）

機密ファイルへのアクセスを制御:

```python
#!/usr/bin/env python3
import json
import sys

PROTECTED = [".env", "secrets/", ".git/config", "credentials"]

input_data = json.load(sys.stdin)
file_path = input_data.get("tool_input", {}).get("file_path", "")

for pattern in PROTECTED:
    if pattern in file_path:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": f"保護されたファイル: {pattern}"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

# ドキュメントファイルは自動承認
if file_path.endswith((".md", ".txt", ".json")):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "ドキュメントファイル自動承認"
        },
        "suppressOutput": True
    }
    print(json.dumps(output))
    sys.exit(0)

sys.exit(0)
```

## PostToolUse フック

### TypeScript自動フォーマット

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "jq -r '.tool_input.file_path' | { read f; [[ \"$f\" == *.ts ]] && npx prettier --write \"$f\"; } || true"
      }]
    }]
  }
}
```

### Markdown言語タグ修正

````python
#!/usr/bin/env python3
import json
import sys
import re
import os

def detect_language(code):
    s = code.strip()
    if re.search(r'^\s*[{\[]', s):
        try:
            json.loads(s)
            return 'json'
        except: pass
    if re.search(r'^\s*(def|import|from)\s+', s, re.M):
        return 'python'
    if re.search(r'\b(function|const|=>)\b', s):
        return 'javascript'
    if re.search(r'^#!.*\b(bash|sh)\b', s, re.M):
        return 'bash'
    return 'text'

def format_markdown(content):
    def add_lang(match):
        indent, info, body, closing = match.groups()
        if not info.strip():
            lang = detect_language(body)
            return f"{indent}```{lang}\n{body}{closing}\n"
        return match.group(0)

    pattern = r'(?ms)^([ \t]{0,3})```([^\n]*)\n(.*?)(\n\1```)\s*$'
    return re.sub(pattern, add_lang, content)

input_data = json.load(sys.stdin)
file_path = input_data.get('tool_input', {}).get('file_path', '')

if file_path.endswith(('.md', '.mdx')) and os.path.exists(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    formatted = format_markdown(content)
    if formatted != content:
        with open(file_path, 'w') as f:
            f.write(formatted)
        print(f"✓ {file_path} をフォーマットしました")
````

### フィードバック付きPostToolUse

```python
#!/usr/bin/env python3
import json
import sys
import subprocess

input_data = json.load(sys.stdin)
file_path = input_data.get('tool_input', {}).get('file_path', '')

if file_path.endswith('.py'):
    result = subprocess.run(['ruff', 'check', file_path], capture_output=True, text=True)
    if result.returncode != 0:
        output = {
            "decision": "block",
            "reason": f"Lintエラー:\n{result.stdout}",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "ruffで問題が検出されました。修正してください。"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

sys.exit(0)
```

## UserPromptSubmit フック

### プロンプト検証とコンテキスト追加

```python
#!/usr/bin/env python3
import json
import sys
import re
from datetime import datetime

input_data = json.load(sys.stdin)
prompt = input_data.get("prompt", "")

# 機密情報チェック
if re.search(r'(?i)(password|secret|api.?key)\s*[:=]\s*\S+', prompt):
    output = {
        "decision": "block",
        "reason": "プロンプトに機密情報が含まれている可能性があります"
    }
    print(json.dumps(output))
    sys.exit(0)

# コンテキスト追加（stdoutに出力するだけでOK）
print(f"現在時刻: {datetime.now().isoformat()}")
sys.exit(0)
```

## Notification フック

### デスクトップ通知

macOS:
```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "jq -r '.message' | xargs -I {} osascript -e 'display notification \"{}\" with title \"Claude Code\"'"
      }]
    }]
  }
}
```

Linux:
```json
{
  "hooks": {
    "Notification": [{
      "hooks": [{
        "type": "command",
        "command": "jq -r '.message' | xargs notify-send 'Claude Code'"
      }]
    }]
  }
}
```

## Stop / SubagentStop フック

### インテリジェント停止判定（プロンプトベース）

```json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "prompt",
        "prompt": "Claudeが停止すべきか評価してください。コンテキスト: $ARGUMENTS\n\n確認事項:\n1. 全タスクが完了したか\n2. エラーが残っていないか\n3. フォローアップが必要か\n\n{\"decision\": \"approve\" or \"block\", \"reason\": \"説明\"} で応答",
        "timeout": 30
      }]
    }]
  }
}
```

### 継続判定スクリプト

```python
#!/usr/bin/env python3
import json
import sys

input_data = json.load(sys.stdin)

# 無限ループ防止
if input_data.get("stop_hook_active"):
    sys.exit(0)

# トランスクリプトを分析して未完了タスクをチェック
# （実際の実装ではtranscript_pathを読んで分析）

output = {
    "decision": "block",
    "reason": "テストの実行が完了していません。`npm test`を実行してください。"
}
print(json.dumps(output))
sys.exit(0)
```

## SessionStart フック

### 環境変数の永続化

```bash
#!/bin/bash

# Node.jsバージョン設定
source ~/.nvm/nvm.sh
nvm use 20

# 環境変数を永続化
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"
  echo 'export DEBUG=true' >> "$CLAUDE_ENV_FILE"
fi

exit 0
```

### 開発コンテキストのロード

```python
#!/usr/bin/env python3
import json
import subprocess
import sys

# 最近のgitコミットを取得
result = subprocess.run(
    ['git', 'log', '--oneline', '-5'],
    capture_output=True, text=True
)

context = f"""
## 最近のコミット
{result.stdout}

## 現在のブランチ
{subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True).stdout.strip()}
"""

# JSON出力でコンテキスト追加
output = {
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": context
    }
}
print(json.dumps(output))
```

## MCPツール用フック

### メモリ操作のログ

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "mcp__memory__.*",
      "hooks": [{
        "type": "command",
        "command": "jq -r '.tool_name' >> ~/.claude/mcp-memory-log.txt"
      }]
    }]
  }
}
```

### 書き込み操作の検証

```json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "mcp__.*__write.*",
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/validate-mcp-write.py"
      }]
    }]
  }
}
```

## プラグインフック

`hooks/hooks.json`:
```json
{
  "description": "自動コードフォーマット",
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
        "timeout": 30
      }]
    }]
  }
}
```
