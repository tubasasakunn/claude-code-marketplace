# Claude Code ステータスライン

## 概要

カスタムステータスラインでClaude Codeをパーソナライズ。ターミナルのPS1プロンプトに類似。

---

## 設定方法

### 対話的設定

```
/statusline
```

Claudeがターミナルプロンプトを再現。追加指示も可能:
```
/statusline show the model name in orange
```

### 手動設定

`.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 0
  }
}
```

---

## 動作

- 会話メッセージ更新時に更新
- 最大300ms間隔
- stdoutの最初の行が表示
- ANSIカラーコード対応

---

## 入力JSON構造

```json
{
  "hook_event_name": "Status",
  "session_id": "abc123...",
  "transcript_path": "/path/to/transcript.json",
  "cwd": "/current/working/directory",
  "model": {
    "id": "claude-opus-4-1",
    "display_name": "Opus"
  },
  "workspace": {
    "current_dir": "/current/working/directory",
    "project_dir": "/original/project/directory"
  },
  "version": "1.0.80",
  "output_style": {
    "name": "default"
  },
  "cost": {
    "total_cost_usd": 0.01234,
    "total_duration_ms": 45000,
    "total_api_duration_ms": 2300,
    "total_lines_added": 156,
    "total_lines_removed": 23
  },
  "context_window": {
    "total_input_tokens": 15234,
    "total_output_tokens": 4521,
    "context_window_size": 200000
  }
}
```

---

## スクリプト例

### シンプル（Bash）

```bash
#!/bin/bash
input=$(cat)

MODEL_DISPLAY=$(echo "$input" | jq -r '.model.display_name')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir')

echo "[$MODEL_DISPLAY] 📁 ${CURRENT_DIR##*/}"
```

### Git対応

```bash
#!/bin/bash
input=$(cat)

MODEL_DISPLAY=$(echo "$input" | jq -r '.model.display_name')
CURRENT_DIR=$(echo "$input" | jq -r '.workspace.current_dir')

GIT_BRANCH=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null)
    if [ -n "$BRANCH" ]; then
        GIT_BRANCH=" | 🌿 $BRANCH"
    fi
fi

echo "[$MODEL_DISPLAY] 📁 ${CURRENT_DIR##*/}$GIT_BRANCH"
```

### コンテキスト使用量

```bash
#!/bin/bash
input=$(cat)

INPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_input_tokens')
OUTPUT_TOKENS=$(echo "$input" | jq -r '.context_window.total_output_tokens')
CONTEXT_SIZE=$(echo "$input" | jq -r '.context_window.context_window_size')
MODEL=$(echo "$input" | jq -r '.model.display_name')

TOTAL_TOKENS=$((INPUT_TOKENS + OUTPUT_TOKENS))
PERCENT_USED=$((TOTAL_TOKENS * 100 / CONTEXT_SIZE))

echo "[$MODEL] Context: ${PERCENT_USED}%"
```

### Python

```python
#!/usr/bin/env python3
import json
import sys
import os

data = json.load(sys.stdin)

model = data['model']['display_name']
current_dir = os.path.basename(data['workspace']['current_dir'])

git_branch = ""
if os.path.exists('.git'):
    try:
        with open('.git/HEAD', 'r') as f:
            ref = f.read().strip()
            if ref.startswith('ref: refs/heads/'):
                git_branch = f" | 🌿 {ref.replace('ref: refs/heads/', '')}"
    except:
        pass

print(f"[{model}] 📁 {current_dir}{git_branch}")
```

### Node.js

```javascript
#!/usr/bin/env node
const fs = require('fs');
const path = require('path');

let input = '';
process.stdin.on('data', chunk => input += chunk);
process.stdin.on('end', () => {
    const data = JSON.parse(input);

    const model = data.model.display_name;
    const currentDir = path.basename(data.workspace.current_dir);

    let gitBranch = '';
    try {
        const headContent = fs.readFileSync('.git/HEAD', 'utf8').trim();
        if (headContent.startsWith('ref: refs/heads/')) {
            gitBranch = ` | 🌿 ${headContent.replace('ref: refs/heads/', '')}`;
        }
    } catch (e) {}

    console.log(`[${model}] 📁 ${currentDir}${gitBranch}`);
});
```

---

## ヘルパー関数パターン

```bash
#!/bin/bash
input=$(cat)

get_model_name() { echo "$input" | jq -r '.model.display_name'; }
get_current_dir() { echo "$input" | jq -r '.workspace.current_dir'; }
get_cost() { echo "$input" | jq -r '.cost.total_cost_usd'; }
get_input_tokens() { echo "$input" | jq -r '.context_window.total_input_tokens'; }

MODEL=$(get_model_name)
DIR=$(get_current_dir)
echo "[$MODEL] 📁 ${DIR##*/}"
```

---

## Tips

- 簡潔に（1行に収まるように）
- 絵文字とカラーで視認性向上
- jqでJSON解析
- テスト: `echo '{"model":{"display_name":"Test"}}' | ./statusline.sh`

---

## トラブルシューティング

**表示されない**:
1. 実行権限確認（`chmod +x`）
2. stdoutに出力しているか確認

**エラー**:
1. jqがインストールされているか確認
2. JSONの形式を確認
