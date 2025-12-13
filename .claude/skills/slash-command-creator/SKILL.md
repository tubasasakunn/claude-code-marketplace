---
name: slash-command-creator
description: Claude Code用のカスタムスラッシュコマンドを作成します。スラッシュコマンドの作成、コマンドファイルの書き方、ベストプラクティスについて質問された場合に使用してください。
---

# カスタムスラッシュコマンド作成ガイド

## スラッシュコマンドとは

頻繁に使用するプロンプトをMarkdownファイルとして定義し、`/command-name`で呼び出せる機能です。

## 保存場所

- **プロジェクト用**: `.claude/commands/command-name.md`
- **個人用**: `~/.claude/commands/command-name.md`

## 基本構造

```markdown
---
allowed-tools: Bash(git:*), Read, Edit
argument-hint: [引数の説明]
description: コマンドの簡潔な説明
model: claude-sonnet-4-5-20250929
---

コマンドの本文（Claudeへの指示）
```

## フロントマター

| フィールド | 目的 | デフォルト |
|:---|:---|:---|
| `allowed-tools` | 使用可能なツール | 会話から継承 |
| `argument-hint` | 引数のヒント表示 | なし |
| `description` | コマンドの説明 | 本文の最初の行 |
| `model` | 使用するモデル | 会話から継承 |
| `disable-model-invocation` | SlashCommandツールからの呼び出しを禁止 | false |

## 引数の使い方

### 全引数を取得: `$ARGUMENTS`

```markdown
---
description: 課題を修正
---

課題 #$ARGUMENTS を修正してください。
```

使用: `/fix-issue 123 high-priority`
→ `$ARGUMENTS` = `123 high-priority`

### 位置引数: `$1`, `$2`, `$3`...

```markdown
---
argument-hint: [PR番号] [優先度] [担当者]
description: PRをレビュー
---

PR #$1 を優先度 $2 でレビューし、$3 に割り当ててください。
```

使用: `/review-pr 456 high alice`
→ `$1`=`456`, `$2`=`high`, `$3`=`alice`

## 特殊機能

### Bashコマンド実行: `!`プレフィックス

```markdown
---
allowed-tools: Bash(git:*)
description: gitコミットを作成
---

## コンテキスト

- 現在のステータス: !`git status`
- 差分: !`git diff HEAD`
- 最近のコミット: !`git log --oneline -5`

## タスク

上記の変更に基づいてコミットを作成してください。
```

### ファイル参照: `@`プレフィックス

```markdown
@src/utils/helpers.js の実装をレビューしてください。

@src/old.js と @src/new.js を比較してください。
```

### 拡張思考

本文に「think」「think hard」「think harder」などのキーワードを含めると拡張思考がトリガーされます。

## 名前空間

サブディレクトリで整理可能:

```
.claude/commands/
├── review.md         → /review (project)
├── frontend/
│   └── component.md  → /component (project:frontend)
└── backend/
    └── api.md        → /api (project:backend)
```

## ベストプラクティス

### 1. 具体的なdescriptionを書く

**悪い例**:
```yaml
description: コードを確認
```

**良い例**:
```yaml
description: セキュリティ、パフォーマンス、コードスタイルの観点からコードをレビュー
```

### 2. allowed-toolsを適切に制限

読み取り専用コマンドには書き込みツールを許可しない:

```yaml
allowed-tools: Read, Grep, Glob
```

### 3. argument-hintで使い方を明示

```yaml
argument-hint: [ファイルパス] [--verbose]
```

### 4. コンテキストを提供

Bashの`!`プレフィックスで動的情報を取得:

```markdown
## 現在の状態
- ブランチ: !`git branch --show-current`
- 変更ファイル: !`git status --short`
```

### 5. 明確なタスク指示

```markdown
## タスク

1. 変更内容を分析
2. 問題点を特定
3. 改善案を提案
```

## 具体例

### シンプルなコマンド

```markdown
---
description: コードのバグと改善点をレビュー
---

このコードをレビューして:
- バグ
- パフォーマンス問題
- コードスタイル違反

を指摘してください。
```

### Git操作コマンド

```markdown
---
allowed-tools: Bash(git add:*), Bash(git status:*), Bash(git commit:*)
argument-hint: [コミットメッセージ]
description: ステージされた変更をコミット
---

## コンテキスト

- ステータス: !`git status`
- 差分: !`git diff --staged`

## タスク

メッセージ「$ARGUMENTS」でコミットを作成してください。
メッセージが空の場合は、差分から適切なメッセージを提案してください。
```

### テスト実行コマンド

```markdown
---
allowed-tools: Bash(npm test:*), Bash(npx jest:*), Read
argument-hint: [テストファイルパス]
description: 指定したテストを実行し結果を分析
---

## タスク

1. $ARGUMENTS のテストを実行
2. 失敗したテストを分析
3. 修正案を提案

引数が空の場合は全テストを実行してください。
```

## スラッシュコマンド作成の流れ

1. **目的を明確化**: 何を自動化するか
2. **ディレクトリ確認**: `mkdir -p .claude/commands`
3. **ファイル作成**: `.claude/commands/command-name.md`
4. **テスト**: `/command-name` で動作確認
5. **改善**: フィードバックに基づき調整

## チェックリスト

- [ ] descriptionは具体的で簡潔
- [ ] allowed-toolsは必要最小限
- [ ] argument-hintで引数を説明
- [ ] `!`でコンテキスト情報を取得
- [ ] 明確なタスク指示を含む
- [ ] ファイル名は小文字とハイフン
