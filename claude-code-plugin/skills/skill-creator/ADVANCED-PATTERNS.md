# 高度なパターン

スキルの高度な機能と実装パターンを説明します。

---

## 目次

- 動的コンテキスト注入
- サブエージェント実行
- スキル呼び出し制御
- ビジュアル出力生成
- 検証可能な中間出力

---

## 動的コンテキスト注入

`!`command`` 構文でシェルコマンドを実行し、結果をスキルコンテンツに注入できます。

### 基本構文

```yaml
---
name: pr-summary
description: PRの変更を要約
context: fork
agent: Explore
allowed-tools: Bash(gh:*)
---

## PRコンテキスト
- PR diff: !`gh pr diff`
- PRコメント: !`gh pr view --comments`
- 変更ファイル: !`gh pr diff --name-only`

## タスク
このPRを要約...
```

### 動作

1. 各 `!`command`` が**即座に実行**される（Claudeが見る前に）
2. 出力がプレースホルダーを置き換える
3. Claudeは完全にレンダリングされたプロンプトを受け取る

**重要**: これはプリプロセッシングであり、Claudeが実行するものではありません。

### 使用例

**現在の日時を注入**:
```markdown
現在時刻: !`date +"%Y-%m-%d %H:%M"`
```

**Git情報を注入**:
```markdown
現在のブランチ: !`git branch --show-current`
最新コミット: !`git log -1 --oneline`
```

**環境変数を注入**:
```markdown
プロジェクトルート: !`echo $CLAUDE_PROJECT_DIR`
```

---

## サブエージェント実行

`context: fork`でスキルをサブエージェントとして実行します。

### 基本設定

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
3. ファイル参照付きで要約
```

### スキルとサブエージェントの連携

| アプローチ | システムプロンプト | タスク | 追加読み込み |
|:-----------|:-------------------|:-------|:-------------|
| `context: fork`のスキル | エージェントタイプから | SKILL.mdコンテンツ | CLAUDE.md |
| `skills`フィールドのサブエージェント | サブエージェントのマークダウン本体 | Claudeの委任メッセージ | プリロードスキル + CLAUDE.md |

### 利用可能なエージェントタイプ

**組み込みエージェント**:

| エージェント | 用途 | ツール |
|:-------------|:-----|:-------|
| `Explore` | コードベース探索 | 読み取り専用（Read, Grep, Glob） |
| `Plan` | 実装計画設計 | 読み取り専用 |
| `general-purpose` | 汎用（デフォルト） | すべて |

**カスタムエージェント**:
`.claude/agents/`に定義したカスタムサブエージェントも指定可能。

### 使用上の注意

**適切な使用**:
- 明示的なタスク指示を含むスキル
- 会話履歴が不要な独立タスク
- 長時間実行されるリサーチ

**不適切な使用**:
- ガイドラインのみのスキル（タスクなし）
- 会話コンテキストが必要なスキル

### 例: Exploreエージェントでのリサーチ

```yaml
---
name: architecture-review
description: コードベースのアーキテクチャをレビュー
context: fork
agent: Explore
---

アーキテクチャレビューを実行:

1. プロジェクト構造を分析
   - Globでディレクトリ構造を確認
   - 主要なエントリポイントを特定

2. 依存関係を調査
   - package.json / requirements.txt を確認
   - 内部モジュール間の依存関係を分析

3. パターンを特定
   - デザインパターンの使用
   - コード構成の一貫性

4. レポート作成
   - 強み
   - 改善点
   - 推奨事項
```

---

## スキル呼び出し制御

### 呼び出しパターン

| フロントマター | ユーザー | Claude | 用途 |
|:---------------|:---------|:-------|:-----|
| デフォルト | ○ | ○ | 通常のスキル |
| `disable-model-invocation: true` | ○ | × | 副作用のあるワークフロー |
| `user-invocable: false` | × | ○ | バックグラウンド知識 |

### 権限ルールでの制限

`/permissions`で特定のスキルを許可/拒否:

```
# 特定のスキルのみ許可
Skill(commit)
Skill(review-pr:*)

# 特定のスキルを拒否
Skill(deploy:*)
```

### 引数の渡し方

スキル呼び出し時の引数は`$ARGUMENTS`で利用可能:

```yaml
---
name: fix-issue
description: GitHub issueを修正
disable-model-invocation: true
argument-hint: [issue-number]
---

GitHub issue $ARGUMENTS を修正:
1. issueの説明を読む
2. 要件を理解
3. 修正を実装
4. テストを作成
5. コミットを作成
```

`/fix-issue 123`を実行すると、Claudeは「GitHub issue 123 を修正:...」を受け取ります。

---

## ビジュアル出力生成

スクリプトをバンドルしてビジュアル出力を生成できます。

### 構造

```
codebase-visualizer/
├── SKILL.md
└── scripts/
    └── visualize.py
```

### SKILL.md例

````yaml
---
name: codebase-visualizer
description: コードベースのインタラクティブなツリービューを生成。プロジェクト構造の探索、理解、大きなファイルの特定時に使用。
allowed-tools: Bash(python:*)
---

# コードベースビジュアライザー

プロジェクトルートから可視化スクリプトを実行:

```bash
python ~/.claude/skills/codebase-visualizer/scripts/visualize.py .
```

これにより`codebase-map.html`が生成され、ブラウザで開きます。

## 表示内容

- **折りたたみ可能なディレクトリ**: クリックで展開/折りたたみ
- **ファイルサイズ**: 各ファイルの横に表示
- **色分け**: ファイルタイプ別に色分け
- **ディレクトリ合計**: 各フォルダの合計サイズ
````

### 活用例

- 依存関係グラフ
- テストカバレッジレポート
- APIドキュメント
- データベーススキーマ可視化

---

## 検証可能な中間出力

複雑なタスクでは「計画-検証-実行」パターンを使用。

### パターン

```
分析 → 計画ファイル作成 → 計画検証 → 実行 → 確認
```

### 例: フォーム入力ワークフロー

````yaml
---
name: pdf-form-filler
description: PDFフォームに自動入力
allowed-tools: Bash(python:*)
---

# PDFフォーム入力

進捗チェックリスト:
```
- [ ] ステップ1: フォーム分析
- [ ] ステップ2: フィールドマッピング作成
- [ ] ステップ3: マッピング検証
- [ ] ステップ4: フォーム入力
- [ ] ステップ5: 出力確認
```

## ステップ1: フォーム分析

```bash
python scripts/analyze_form.py input.pdf > fields.json
```

## ステップ2: フィールドマッピング作成

`fields.json`を編集して各フィールドの値を設定。

## ステップ3: マッピング検証

```bash
python scripts/validate_fields.py fields.json
```

**検証が成功したときのみ続行**

## ステップ4: フォーム入力

```bash
python scripts/fill_form.py input.pdf fields.json output.pdf
```

## ステップ5: 出力確認

```bash
python scripts/verify_output.py output.pdf
```

検証が失敗した場合、ステップ2に戻る。
````

### このパターンの利点

- **早期エラー検出**: 変更前に問題を発見
- **機械検証可能**: スクリプトで客観的な検証
- **可逆的な計画**: 元ファイルに触れずに反復
- **明確なデバッグ**: 具体的なエラーメッセージ

---

## 拡張思考の有効化

スキルで拡張思考（extended thinking）を有効にするには、スキルコンテンツのどこかに「ultrathink」という単語を含めます。

```yaml
---
name: complex-analysis
description: 複雑な分析を実行
---

# 複雑な分析

この分析には深い推論が必要です。ultrathinkモードで実行してください。

...
```

---

## MCPツール参照

MCPツールを使用するスキルでは、完全修飾ツール名を使用:

**形式**: `ServerName:tool_name`

```markdown
BigQuery:bigquery_schemaツールを使用してテーブルスキーマを取得します。
GitHub:create_issueツールを使用してissueを作成します。
```

サーバープレフィックスがないと、ツールの場所を特定できない可能性があります。
