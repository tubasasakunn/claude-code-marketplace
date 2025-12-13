---
name: skill-creator
description: Claude Code用のエージェントスキルを作成します。スキルの作成、SKILL.mdの書き方、スキル構造の設計について質問された場合に使用してください。
---

# スキル作成ガイド

## スキルとは

スキルはClaude Codeの機能を拡張するモジュール式機能です。`SKILL.md`ファイルとオプションのサポートファイルで構成されます。

## 保存場所

- **個人用**: `~/.claude/skills/skill-name/SKILL.md`
- **プロジェクト用**: `.claude/skills/skill-name/SKILL.md`

## SKILL.md構造

```yaml
---
name: skill-name
description: スキルが何をするか、いつ使用するかを説明（最大1024文字）
---

# スキル名

## Instructions
Claudeへの明確な指示

## Examples
具体的な使用例
```

## フィールド要件

**name**:
- 最大64文字
- 小文字、数字、ハイフンのみ
- 例: `pdf-processing`, `code-reviewer`

**description**:
- 何をするか + いつ使用するか を含める
- 三人称で記述
- 具体的なトリガー用語を含める

## ベストプラクティス

### 1. 簡潔に保つ

SKILL.mdボディは500行以下に。Claudeが既に知っていることは省略。

**良い例**:
```markdown
## PDF抽出
pdfplumberでテキスト抽出:
\`\`\`python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
\`\`\`
```

### 2. 段階的開示を活用

詳細は別ファイルに分離し、必要時のみ参照:

```
my-skill/
├── SKILL.md (メイン指示)
├── REFERENCE.md (詳細リファレンス)
├── EXAMPLES.md (追加例)
└── scripts/
    └── helper.py (ユーティリティ)
```

SKILL.mdから参照:
```markdown
詳細は[REFERENCE.md](REFERENCE.md)を参照。
```

### 3. 具体的な説明を書く

**悪い例**:
```yaml
description: ドキュメントを処理します
```

**良い例**:
```yaml
description: PDFファイルからテキストと表を抽出し、フォームに入力します。PDF、フォーム、ドキュメント抽出について言及された場合に使用してください。
```

### 4. ワークフローを明確に

複雑なタスクはステップに分解:

```markdown
## ワークフロー

1. 入力ファイルを分析
2. 処理計画を作成
3. 計画を検証
4. 処理を実行
5. 結果を確認
```

### 5. 一貫した用語を使用

スキル全体で同じ用語を使用。混在させない。

## 具体例

### シンプルなスキル

```yaml
---
name: commit-message-generator
description: git diffから明確なコミットメッセージを生成します。コミットメッセージの作成やステージされた変更のレビュー時に使用してください。
---

# コミットメッセージ生成

## 手順

1. `git diff --staged`で変更を確認
2. 以下の形式でメッセージを提案:
   - 50文字以下の要約
   - 詳細説明
   - 影響コンポーネント

## 形式

type(scope): 簡潔な説明

詳細説明（任意）

## 例

feat(auth): JWTベースの認証を実装

ログインエンドポイントとトークン検証ミドルウェアを追加
```

### ツール制限付きスキル

```yaml
---
name: code-reviewer
description: コードのベストプラクティスと問題をレビューします。コードレビュー、PR確認、コード品質分析時に使用してください。
allowed-tools: Read, Grep, Glob
---

# コードレビュー

## チェックリスト

1. コード構造と組織
2. エラー処理
3. パフォーマンス
4. セキュリティ
5. テストカバレッジ

## 手順

1. Readでファイル内容を確認
2. Grepでパターンを検索
3. Globで関連ファイルを発見
4. 詳細なフィードバックを提供
```

### マルチファイルスキル

```
data-analysis/
├── SKILL.md
├── SCHEMAS.md
└── scripts/
    └── validate.py
```

**SKILL.md**:
```yaml
---
name: data-analysis
description: データセットを分析してレポートを生成します。データ分析、統計、可視化について質問された場合に使用してください。
---

# データ分析

## クイックスタート

pandasでデータを読み込み:
\`\`\`python
import pandas as pd
df = pd.read_csv("data.csv")
\`\`\`

スキーマ定義は[SCHEMAS.md](SCHEMAS.md)を参照。

## 検証

データ検証:
\`\`\`bash
python scripts/validate.py data.csv
\`\`\`
```

## 避けるべきパターン

1. **冗長な説明**: Claudeが既に知っていることを説明しない
2. **時間に敏感な情報**: 「2025年8月以降は...」のような記述を避ける
3. **深いネスト**: 参照は1レベルまで
4. **Windowsパス**: 常に`/`を使用（`\`は使用しない）
5. **選択肢の過剰提示**: デフォルトを1つ提供し、代替案は必要時のみ

## スキル作成の流れ

1. **目的を明確化**: 何を解決するか
2. **ディレクトリ作成**: `mkdir -p .claude/skills/skill-name`
3. **SKILL.md作成**: 上記構造に従う
4. **テスト**: 実際のタスクで動作確認
5. **反復**: フィードバックに基づき改善

## チェックリスト

- [ ] nameは小文字、数字、ハイフンのみ
- [ ] descriptionは具体的で三人称
- [ ] SKILL.mdは500行以下
- [ ] 段階的開示を適切に使用
- [ ] 一貫した用語
- [ ] 具体的な例を含む
- [ ] Windowsパスなし
