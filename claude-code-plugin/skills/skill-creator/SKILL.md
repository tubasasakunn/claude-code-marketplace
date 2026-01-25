---
name: skill-creator
description: Claude Code用のエージェントスキルを作成します。スキルの作成、SKILL.mdの書き方、スキル構造の設計、フロントマター設定（context、hooks、allowed-toolsなど）について質問された場合に使用してください。
---

# スキル作成ガイド

> 最新のドキュメントインデックス: https://code.claude.com/docs/llms.txt

## スキルとは

スキルはClaude Codeの機能を拡張するモジュールです。`SKILL.md`ファイルに指示を記述すると、Claudeがツールキットに追加します。関連する場合に自動的に使用されるか、`/skill-name`で直接呼び出せます。

## 保存場所

| 場所 | パス | 適用対象 |
|:-----|:-----|:---------|
| 個人用 | `~/.claude/skills/<skill-name>/SKILL.md` | 全プロジェクト |
| プロジェクト用 | `.claude/skills/<skill-name>/SKILL.md` | このプロジェクトのみ |
| プラグイン | `<plugin>/skills/<skill-name>/SKILL.md` | プラグイン有効時 |

プロジェクトスキルは同名の個人スキルをオーバーライドします。

## SKILL.md基本構造

```yaml
---
name: skill-name
description: 何をするか。いつ使用するかを説明。
---

# スキル名

## 指示
Claudeへの明確な指示

## 例
具体的な使用例
```

## スキル作成の手順

### 1. ユーザー要件の確認

**スキル作成時は、必ずAskUserQuestionツールで以下を確認する**：

#### 基本情報
- スキルの目的と主要な機能
- 対象ユーザー（個人用/プロジェクト共有）
- 想定される使用シナリオ

#### フロントマター設定
- `context: fork`が必要か（サブエージェントで実行するか）
- `disable-model-invocation: true`が必要か（手動呼び出しのみか）
- `allowed-tools`で制限するツールがあるか
- `argument-hint`で引数のヒントが必要か
- `hooks`でライフサイクルフックが必要か

#### コンテンツ範囲
- スクリプトを含むか（コード付きスキル）
- 別ファイルへの分離が必要か（500行を超えそうか）
- テンプレートや出力形式の指定があるか

### 2. フロントマター設定の決定

詳細は[FRONTMATTER.md](FRONTMATTER.md)を参照。

**主要フィールド**:

| フィールド | 必須 | 説明 |
|:-----------|:-----|:-----|
| `name` | 推奨 | 小文字、数字、ハイフンのみ（最大64文字） |
| `description` | 推奨 | 何をするか＋いつ使用するか |
| `argument-hint` | 任意 | 引数ヒント（例：`[filename]`） |
| `disable-model-invocation` | 任意 | `true`でClaude自動呼び出しを無効化 |
| `user-invocable` | 任意 | `false`で`/`メニューから非表示 |
| `allowed-tools` | 任意 | 使用可能なツールを制限 |
| `context` | 任意 | `fork`でサブエージェント実行 |
| `agent` | 任意 | `context: fork`時のエージェントタイプ |
| `hooks` | 任意 | ライフサイクルフック設定 |

### 3. コンテンツタイプの選択

**リファレンスコンテンツ**（知識を追加）:
```yaml
---
name: api-conventions
description: このコードベースのAPI設計パターン
---

APIエンドポイント作成時:
- RESTful命名規則を使用
- 一貫したエラー形式を返す
- リクエストバリデーションを含める
```

**タスクコンテンツ**（アクションを実行）:
```yaml
---
name: deploy
description: アプリケーションを本番環境にデプロイ
context: fork
disable-model-invocation: true
---

デプロイ手順:
1. テストスイートを実行
2. アプリケーションをビルド
3. デプロイターゲットにプッシュ
```

### 4. ディレクトリ作成

```bash
# 個人用
mkdir -p ~/.claude/skills/skill-name

# プロジェクト用
mkdir -p .claude/skills/skill-name
```

### 5. SKILL.md作成

**簡潔さを保つ**: 500行以下に。Claudeが既に知っていることは省略。

**段階的開示を活用**: 詳細は別ファイルに分離。
```markdown
詳細は[REFERENCE.md](REFERENCE.md)を参照。
```

### 6. テストと反復

1. 実際のタスクでスキルをテスト
2. 使用予定のモデル（Haiku/Sonnet/Opus）で確認
3. フィードバックに基づき改善

## 確認すべき質問リスト

スキル作成時にAskUserQuestionで確認：

```
1. 基本情報
   - スキルの名前は？（小文字、数字、ハイフンのみ）
   - 主な目的・機能は？
   - いつ使用されるべき？（トリガー条件）

2. 呼び出し制御
   - Claude自動呼び出し: 許可 / 手動のみ
   - /メニュー表示: 表示 / 非表示

3. 実行環境
   - 実行方式: インライン / サブエージェント（fork）
   - サブエージェントの場合: Explore / Plan / general-purpose / カスタム

4. ツール制限
   - 使用ツール: 全て / 制限あり
   - 制限する場合: どのツールを許可？

5. 引数
   - 引数を受け取る: はい / いいえ
   - 引数ヒント: 例）[filename] [format]

6. Hooks
   - ライフサイクルフック: 不要 / 必要
   - 必要な場合: PreToolUse / PostToolUse / Stop

7. コンテンツ
   - スクリプトを含む: はい / いいえ
   - 別ファイル分離: 必要 / 不要
```

## 参照ドキュメント

- [FRONTMATTER.md](FRONTMATTER.md) - フロントマター詳細リファレンス
- [ADVANCED-PATTERNS.md](ADVANCED-PATTERNS.md) - 高度なパターン（動的コンテキスト、サブエージェント）
- [HOOKS-REFERENCE.md](HOOKS-REFERENCE.md) - Hooksリファレンス
- [BEST-PRACTICES.md](BEST-PRACTICES.md) - ベストプラクティス
- [EXAMPLES.md](EXAMPLES.md) - 具体例集
- [DIRECTORY-PATTERNS.md](DIRECTORY-PATTERNS.md) - ディレクトリ構造パターン
- [VALIDATION-CHECKLIST.md](VALIDATION-CHECKLIST.md) - 検証チェックリスト

## クイックスタート例

### シンプルなスキル

```yaml
---
name: commit-message
description: git diffから明確なコミットメッセージを生成。コミットメッセージ作成時に使用。
---

# コミットメッセージ生成

1. `git diff --staged`で変更確認
2. 以下の形式で提案:

type(scope): 簡潔な説明

詳細説明（任意）

## 例
feat(auth): JWTベースの認証を実装
```

### 手動呼び出しスキル

```yaml
---
name: deploy
description: 本番環境にデプロイ
disable-model-invocation: true
argument-hint: [environment]
---

# デプロイ

$ARGUMENTS環境にデプロイ:
1. テスト実行
2. ビルド
3. デプロイ
4. 確認
```

### サブエージェント実行スキル

```yaml
---
name: deep-research
description: トピックを徹底的にリサーチ
context: fork
agent: Explore
---

# リサーチ

$ARGUMENTSを徹底調査:
1. Glob/Grepで関連ファイル検索
2. コードを分析
3. ファイル参照付きで要約
```

## 避けるべきパターン

1. **冗長な説明**: Claudeが既に知っていることを説明しない
2. **時間依存情報**: 「2025年8月以降は...」を避ける
3. **深いネスト**: 参照は1レベルまで
4. **Windowsパス**: 常に`/`を使用
5. **過剰な選択肢**: デフォルトを1つ提供
