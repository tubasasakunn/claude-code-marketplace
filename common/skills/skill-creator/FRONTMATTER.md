# フロントマターリファレンス

SKILL.mdの上部にある`---`マーカー間のYAMLフロントマターで、スキルの動作を設定します。

---

## 全フィールド一覧

```yaml
---
name: my-skill
description: スキルの説明
argument-hint: [引数ヒント]
disable-model-invocation: true
user-invocable: false
allowed-tools: Read, Grep, Glob
model: sonnet
context: fork
agent: Explore
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/check.sh"
---
```

すべてのフィールドは任意ですが、`description`は推奨です。

---

## 各フィールドの詳細

### name

スキルの表示名。省略時はディレクトリ名を使用。

**要件**:
- 最大64文字
- 小文字、数字、ハイフンのみ
- XMLタグ不可
- 予約語不可（`anthropic`、`claude`）

**良い例**:
- `pdf-processing`
- `code-reviewer`
- `api-tester`

**悪い例**:
- `PDF_Processing`（大文字、アンダースコア）
- `claude-helper`（予約語）
- `my skill`（スペース）

### description

スキルが何をするか、いつ使用するかを説明。Claudeがスキルを適用するかどうかの判断に使用。

**要件**:
- 最大1024文字
- 空でないこと
- XMLタグ不可
- 三人称で記述

**良い例**:
```yaml
description: PDFファイルからテキストと表を抽出し、フォームに入力します。PDF、フォーム、ドキュメント抽出について言及された場合に使用してください。
```

**悪い例**:
```yaml
description: ドキュメントを処理します
```

### argument-hint

オートコンプリート時に表示される引数ヒント。

**例**:
```yaml
argument-hint: [issue-number]
argument-hint: [filename] [format]
```

ユーザーが`/fix-issue`と入力すると、`[issue-number]`がヒントとして表示されます。

### disable-model-invocation

`true`に設定すると、Claudeが自動的にスキルをロードするのを防ぎます。`/name`での手動呼び出しのみ。

**使用例**:
- デプロイメント
- データ削除
- 外部API呼び出し
- 副作用のあるワークフロー

```yaml
---
name: deploy
description: 本番環境にデプロイ
disable-model-invocation: true
---
```

### user-invocable

`false`に設定すると、`/`メニューから非表示になります。Claudeのみが呼び出し可能。

**使用例**:
- バックグラウンド知識
- 他のスキルからの参照用
- ユーザーが直接呼び出す必要がない情報

```yaml
---
name: legacy-system-context
description: レガシーシステムの仕組みを説明
user-invocable: false
---
```

### allowed-tools

スキルがアクティブな場合に使用可能なツールを制限。

**使用例**:
```yaml
# 読み取り専用モード
allowed-tools: Read, Grep, Glob

# 特定のBashコマンドのみ
allowed-tools: Bash(npm:*)

# 複数指定
allowed-tools: Read, Grep, Glob, Bash(git:*)
```

### model

スキルがアクティブな場合に使用するモデル。

**オプション**:
- `sonnet`（バランス）
- `opus`（高性能推論）
- `haiku`（高速、経済的）

```yaml
---
name: complex-analysis
description: 複雑な分析を実行
model: opus
---
```

### context

`fork`に設定すると、サブエージェントコンテキストで実行。スキルコンテンツがサブエージェントのプロンプトになります。

**重要**: 明示的なタスク指示を含むスキルでのみ使用。ガイドラインのみのスキルでは使用しない。

```yaml
---
name: deep-research
description: トピックを徹底調査
context: fork
agent: Explore
---

$ARGUMENTSを調査:
1. 関連ファイルを検索
2. コードを分析
3. 要約を作成
```

### agent

`context: fork`設定時に使用するサブエージェントタイプ。

**組み込みエージェント**:
- `Explore` - コードベース探索に最適化（読み取り専用）
- `Plan` - 実装計画設計
- `general-purpose` - 汎用（デフォルト）

**カスタムエージェント**:
`.claude/agents/`からのカスタムサブエージェントも指定可能。

### hooks

スキルのライフサイクルにスコープされたフック。

**サポートイベント**: `PreToolUse`、`PostToolUse`、`Stop`

```yaml
---
name: secure-ops
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
          command: "./scripts/lint.sh"
---
```

詳細は[HOOKS-REFERENCE.md](HOOKS-REFERENCE.md)を参照。

---

## 呼び出し制御の組み合わせ

| フロントマター | ユーザー呼び出し | Claude呼び出し | 用途 |
|:---------------|:-----------------|:---------------|:-----|
| （デフォルト） | ○ | ○ | 通常のスキル |
| `disable-model-invocation: true` | ○ | × | 副作用のあるワークフロー |
| `user-invocable: false` | × | ○ | バックグラウンド知識 |

---

## 文字列置換

スキルコンテンツ内で使用可能な動的変数：

| 変数 | 説明 |
|:-----|:-----|
| `$ARGUMENTS` | スキル呼び出し時に渡された引数 |
| `${CLAUDE_SESSION_ID}` | 現在のセッションID |

**例**:
```yaml
---
name: session-logger
description: セッションアクティビティをログ
---

以下をlogs/${CLAUDE_SESSION_ID}.logに記録:

$ARGUMENTS
```

---

## 決定フローチャート

### disable-model-invocationを使うべき？

```
スキルに副作用がある？
  ├─ はい → disable-model-invocation: true
  └─ いいえ → デフォルトのまま
```

### context: forkを使うべき？

```
スキルに明示的なタスク指示がある？
  ├─ いいえ → 使用しない
  └─ はい
      ├─ 会話履歴が不要？ → context: fork
      └─ 会話履歴が必要？ → インライン実行
```

### user-invocable: falseを使うべき？

```
ユーザーが直接呼び出す意味がある？
  ├─ はい → デフォルトのまま
  └─ いいえ（バックグラウンド知識のみ） → user-invocable: false
```

---

## 完全な例

### 読み取り専用リサーチスキル

```yaml
---
name: code-explorer
description: コードベースを探索して構造を理解。コードベースの構造、アーキテクチャ、ファイル配置について質問された場合に使用。
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

$ARGUMENTSについてコードベースを探索:

1. Globで関連ファイルパターンを検索
2. Grepでキーワードを検索
3. Readで重要ファイルを分析
4. ファイル参照付きで要約

ファイルの変更は行わない。
```

### 手動デプロイスキル

```yaml
---
name: deploy-production
description: 本番環境へのデプロイを実行
disable-model-invocation: true
argument-hint: [version]
allowed-tools: Bash(npm:*), Bash(git:*)
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/deploy-check.sh"
---

バージョン $ARGUMENTS を本番環境にデプロイ:

進捗チェックリスト:
- [ ] テスト実行
- [ ] ビルド作成
- [ ] ステージングデプロイ
- [ ] 本番デプロイ
- [ ] 確認
```
