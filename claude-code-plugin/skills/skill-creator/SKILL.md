---
name: skill-creator
description: Claude Code用のスキルを作成・修正します。スキルの作成、SKILL.mdの書き方、スキル構造の設計、フロントマター設定について質問された場合に使用してください。
---

# スキル作成ガイド

スキルはClaude Codeの機能を拡張するモジュールです。`SKILL.md`ファイルに指示を記述し、Claudeのツールキットに追加します。

---

## ワークフロー概要

スキル作成は4フェーズで進行します。詳細は[WORKFLOW.md](WORKFLOW.md)を参照。

| Phase | 目的 | 完了条件 |
|:------|:-----|:---------|
| 1. 要件確定 | ユーザー要件を固める | スキルの目的・タイプ・実行方式が決定 |
| 2. 情報構造化 | ファイル構成を設計 | SKILL.mdがインデックスとして機能する設計 |
| 3. 構成設計 | 参照ドキュメントを確認し設計 | フロントマター・セクション構成が決定 |
| 4. スキル作成 | ファイルを作成・検証 | VALIDATION-CHECKLISTをパス |

---

## クイックリファレンス

### descriptionの書き方（最重要）

**「何をするか」+「いつ使うか」を三人称で記述**

```yaml
# 良い例
description: PDFファイルからテキストを抽出します。PDF、ドキュメント抽出について言及された場合に使用してください。

# 悪い例
description: ドキュメントを処理します
```

### descriptionテンプレート

```yaml
# リファレンス型
description: [対象]の[ガイドライン/規約]を提供します。[トリガー条件]について質問された場合に使用してください。

# タスク実行型
description: [タスク]を実行します。[トリガー条件]の場合に使用してください。

# 分析・レビュー型
description: [対象]を分析/レビューします。[トリガー条件]について質問された場合に使用してください。
```

### フロントマター決定フロー

```
副作用がある？ → disable-model-invocation: true
会話履歴不要？ → context: fork
読み取りのみ？ → allowed-tools: Read, Grep, Glob
ユーザー呼び出し不要？ → user-invocable: false
```

### ファイル構成パターン

```
〜200行 → SKILL.mdのみ
〜400行 → SKILL.md + REFERENCE.md
400行〜 → SKILL.md + 複数ファイル
```

---

## SKILL.md構成テンプレート

```markdown
---
name: skill-name
description: [何をするか]。[いつ使うか]について質問された場合に使用してください。
---

# スキル名

## 概要
1-2文で目的を説明

## ワークフロー
ステップの概要

## クイックリファレンス
よく使う情報の要約

## 詳細ドキュメント
- [WORKFLOW.md](WORKFLOW.md)
- [REFERENCE.md](REFERENCE.md)

## 終了条件
- [ ] 条件1
- [ ] 条件2
```

---

## 終了条件

スキル作成が完了したと判断する条件：

- [ ] Phase 1-4がすべて完了
- [ ] SKILL.mdがインデックスとして機能
- [ ] エージェント型の場合、反復可能なワークフローを含む
- [ ] 終了条件がSKILL.md内に明記
- [ ] VALIDATION-CHECKLISTの必須項目をパス
- [ ] 実際のタスクでテストし動作確認

---

## 参照ドキュメント

| ドキュメント | 内容 |
|:-------------|:-----|
| [WORKFLOW.md](WORKFLOW.md) | 4フェーズの詳細ワークフロー |
| [FRONTMATTER.md](FRONTMATTER.md) | フロントマター詳細リファレンス |
| [BEST-PRACTICES.md](BEST-PRACTICES.md) | ベストプラクティス |
| [EXAMPLES.md](EXAMPLES.md) | 基本例・テンプレート |
| [ADVANCED-EXAMPLES.md](ADVANCED-EXAMPLES.md) | 高度な例（コード付き、Hooks付き等） |
| [VALIDATION-CHECKLIST.md](VALIDATION-CHECKLIST.md) | 検証チェックリスト |
| [ADVANCED-PATTERNS.md](ADVANCED-PATTERNS.md) | 高度なパターン |
| [HOOKS-REFERENCE.md](HOOKS-REFERENCE.md) | Hooksリファレンス |
| [DIRECTORY-PATTERNS.md](DIRECTORY-PATTERNS.md) | ディレクトリ構造パターン |

---

## 避けるべきパターン

1. **冗長な説明** - Claudeが既に知っていることを書かない
2. **曖昧なdescription** - 「何を」+「いつ」を必ず含める
3. **深いネスト** - 参照は1レベルまで
4. **500行超過** - 詳細は別ファイルに分離
5. **終了条件の欠落** - エージェント型では必須
