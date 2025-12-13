---
name: subagent-creator
description: Claude Code用のカスタムサブエージェントを作成します。サブエージェントの作成、エージェント設定、特化したAIアシスタントの設計について質問された場合に使用してください。
---

# サブエージェント作成ガイド

## サブエージェントとは

サブエージェントは、Claude Codeがタスクを委譲できる特化したAIアシスタントです。各サブエージェント：

- 特定の目的と専門分野を持つ
- 独立したコンテキストウィンドウで動作
- 許可されたツールを設定可能
- カスタムシステムプロンプトを含む

## 保存場所

| タイプ | 場所 | スコープ | 優先度 |
|--------|------|----------|--------|
| プロジェクト | `.claude/agents/` | 現在のプロジェクト | 最高 |
| ユーザー | `~/.claude/agents/` | 全プロジェクト | 低い |

## ファイル形式

```markdown
---
name: agent-name
description: エージェントの目的といつ使用すべきかの説明
tools: tool1, tool2, tool3  # 省略時は全ツール継承
model: sonnet  # sonnet, opus, haiku, inherit
---

システムプロンプトをここに記述。
エージェントの役割、能力、問題解決アプローチを明確に定義。
```

## 設定フィールド

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `name` | はい | 小文字とハイフンの一意識別子 |
| `description` | はい | 目的の自然言語説明 |
| `tools` | いいえ | ツールのカンマ区切りリスト |
| `model` | いいえ | `sonnet`, `opus`, `haiku`, `inherit` |

## 利用可能なツール

主要なツール：
- `Read` - ファイル読み取り
- `Write` - ファイル書き込み
- `Edit` - ファイル編集
- `Bash` - コマンド実行
- `Grep` - パターン検索
- `Glob` - ファイルパターンマッチング
- `WebFetch` - Web取得
- `WebSearch` - Web検索

ツールの完全リストは`/agents`コマンドで確認可能。

## ベストプラクティス

### 1. Claudeで生成してカスタマイズ

`/agents`コマンドでClaudeに生成させ、その後カスタマイズ。

### 2. 焦点を絞った設計

1つのサブエージェントに1つの明確な責任。

**良い例**:
- `code-reviewer` - コードレビュー専門
- `test-runner` - テスト実行専門
- `debugger` - デバッグ専門

**悪い例**:
- `do-everything` - すべてをこなす

### 3. 詳細なプロンプト

具体的な指示、例、制約を含める。

### 4. ツールアクセスを制限

必要なツールのみを許可：
```yaml
tools: Read, Grep, Glob  # 読み取り専用
```

### 5. 積極的な使用を促す

descriptionに明示：
```yaml
description: Use PROACTIVELY after code changes
```

## 具体例

### コードレビュアー

```markdown
---
name: code-reviewer
description: Expert code review specialist. Use PROACTIVELY after writing or modifying code.
tools: Read, Grep, Glob, Bash
model: inherit
---

You are a senior code reviewer ensuring high standards.

When invoked:
1. Run git diff to see recent changes
2. Focus on modified files
3. Begin review immediately

Review checklist:
- Code is simple and readable
- Functions and variables are well-named
- No duplicated code
- Proper error handling
- No exposed secrets
- Input validation implemented
- Good test coverage

Provide feedback by priority:
- Critical (must fix)
- Warnings (should fix)
- Suggestions (consider)

Include specific examples of how to fix issues.
```

### デバッガー

```markdown
---
name: debugger
description: Debugging specialist for errors and test failures. Use PROACTIVELY when encountering issues.
tools: Read, Edit, Bash, Grep, Glob
---

You are an expert debugger specializing in root cause analysis.

When invoked:
1. Capture error message and stack trace
2. Identify reproduction steps
3. Isolate the failure location
4. Implement minimal fix
5. Verify solution works

For each issue, provide:
- Root cause explanation
- Evidence supporting diagnosis
- Specific code fix
- Testing approach
- Prevention recommendations

Focus on fixing the underlying issue, not symptoms.
```

### テストランナー

```markdown
---
name: test-runner
description: Test automation expert. Use PROACTIVELY to run tests and fix failures.
---

You are a test automation expert.

When you see code changes:
1. Run the appropriate tests
2. If tests fail, analyze failures
3. Fix issues while preserving test intent

Key practices:
- Run relevant tests only
- Provide clear failure summaries
- Suggest fixes with explanations
```

詳細な例は[EXAMPLES.md](EXAMPLES.md)を参照。

## 作成手順

### /agentsコマンド（推奨）

```
/agents
```

対話的メニューで：
1. 「新しいエージェントを作成」を選択
2. プロジェクト/ユーザーレベルを選択
3. Claudeで生成またはカスタム作成
4. ツールを選択
5. 保存

### 手動作成

```bash
# プロジェクトサブエージェント
mkdir -p .claude/agents
cat > .claude/agents/my-agent.md << 'EOF'
---
name: my-agent
description: Description here
tools: Read, Bash
---

System prompt here.
EOF

# ユーザーサブエージェント
mkdir -p ~/.claude/agents
# 同様にファイル作成
```

### CLIフラグ

```bash
claude --agents '{
  "my-agent": {
    "description": "Description",
    "prompt": "System prompt",
    "tools": ["Read", "Bash"],
    "model": "sonnet"
  }
}'
```

## 使用方法

### 自動委譲

Claude Codeはタスクに基づいて自動的に適切なサブエージェントを選択。

### 明示的呼び出し

```
Use the code-reviewer subagent to check my changes
Have the debugger subagent investigate this error
```

### サブエージェントのチェーン

```
First use the code-analyzer to find issues, then use the optimizer to fix them
```

### 再開

以前のエージェントを再開して続行：
```
Resume agent abc123 and continue the analysis
```

## チェックリスト

- [ ] nameは小文字とハイフンのみ
- [ ] descriptionが具体的で明確
- [ ] 必要なツールのみを許可
- [ ] システムプロンプトに具体的な指示
- [ ] 積極的使用のトリガーを含む
- [ ] プロジェクト用は`.claude/agents/`に配置
