# スキル作成の具体例集

## 目次

- 基本スキル
- フロントマター設定別の例
- テンプレート
- 高度な例 → [ADVANCED-EXAMPLES.md](ADVANCED-EXAMPLES.md)

---

## 基本スキル

### シンプルなリファレンススキル

```yaml
---
name: api-conventions
description: このコードベースのAPI設計パターン。API作成、エンドポイント設計時に使用。
---

# API規約

## エンドポイント設計

- RESTful命名規則を使用
- 一貫したエラー形式を返す
- リクエストバリデーションを含める

## レスポンス形式

```json
{
  "data": {},
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## エラー形式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力が無効です"
  }
}
```
```

### コミットメッセージ生成スキル

```yaml
---
name: commit-message
description: git diffから明確なコミットメッセージを生成。コミットメッセージ作成時に使用。
---

# コミットメッセージ生成

1. `git diff --staged`で変更確認
2. 以下の形式で提案:

## 形式

type(scope): 簡潔な説明

詳細説明（任意）

## タイプ

- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `docs`: ドキュメント
- `test`: テスト
- `chore`: その他

## 例

feat(auth): JWTベースの認証を実装

ログインエンドポイントとトークン検証ミドルウェアを追加
```

---

## フロントマター設定別の例

### disable-model-invocation: 手動呼び出しのみ

```yaml
---
name: deploy-production
description: 本番環境へのデプロイを実行
disable-model-invocation: true
argument-hint: [version]
---

# 本番デプロイ

バージョン $ARGUMENTS を本番環境にデプロイ:

進捗チェックリスト:
- [ ] テスト実行
- [ ] ビルド作成
- [ ] ステージングデプロイ
- [ ] 本番デプロイ
- [ ] 確認

## 1. テスト実行

```bash
npm run test
npm run lint
```

## 2. ビルド

```bash
npm run build
```

## 3. デプロイ

```bash
./scripts/deploy.sh production $ARGUMENTS
```
```

### user-invocable: false（バックグラウンド知識）

```yaml
---
name: legacy-db-context
description: レガシーデータベースの構造と制約。データベース操作時に参照。
user-invocable: false
---

# レガシーデータベースコンテキスト

## 注意事項

- `users`テーブルは`user_id`ではなく`id`を使用
- タイムスタンプはUTCで保存
- ソフトデリート（`deleted_at`カラム）を使用

## スキーマ

### users
- id (INT, PK)
- email (VARCHAR)
- created_at (TIMESTAMP)
- deleted_at (TIMESTAMP, nullable)

### orders
- order_id (INT, PK)
- user_id (INT, FK -> users.id)
- status (ENUM)
```

### context: fork（サブエージェント実行）

```yaml
---
name: architecture-review
description: コードベースのアーキテクチャをレビュー
context: fork
agent: Explore
---

# アーキテクチャレビュー

$ARGUMENTSについてアーキテクチャレビューを実行:

1. **プロジェクト構造を分析**
   - Globでディレクトリ構造を確認
   - 主要なエントリポイントを特定

2. **依存関係を調査**
   - package.json / requirements.txt を確認
   - 内部モジュール間の依存関係を分析

3. **パターンを特定**
   - デザインパターンの使用
   - コード構成の一貫性

4. **レポート作成**
   - 強み
   - 改善点
   - 推奨事項
```

### allowed-tools（ツール制限）

```yaml
---
name: code-explorer
description: コードベースを読み取り専用で探索
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
---

# コードエクスプローラー

$ARGUMENTSについてコードベースを探索:

1. Globで関連ファイルパターンを検索
2. Grepでキーワードを検索
3. Readで重要ファイルを分析
4. ファイル参照付きで要約

**ファイルの変更は行わない**
```

---

## テンプレート

### 基本スキルテンプレート

```yaml
---
name: [skill-name]
description: [何をするか]。[いつ使用するか]に使用。
---

# [スキル名]

## 概要

[1-2文で説明]

## 使い方

[基本的な使用方法]

## 手順

1. [ステップ1]
2. [ステップ2]
3. [ステップ3]

## 例

[具体的な使用例]

## 注意事項

- [重要な注意点1]
- [重要な注意点2]
```

### サブエージェントスキルテンプレート

```yaml
---
name: [skill-name]
description: [何をするか]。[いつ使用するか]に使用。
context: fork
agent: [Explore|Plan|general-purpose]
allowed-tools: [ツールリスト]
---

# [スキル名]

$ARGUMENTSについて実行:

1. [ステップ1]
2. [ステップ2]
3. [ステップ3]

## 出力形式

[期待される出力形式]
```

### Hooks付きスキルテンプレート

```yaml
---
name: [skill-name]
description: [何をするか]。[いつ使用するか]に使用。
hooks:
  PreToolUse:
    - matcher: "[ツールパターン]"
      hooks:
        - type: command
          command: "[コマンド]"
  PostToolUse:
    - matcher: "[ツールパターン]"
      hooks:
        - type: command
          command: "[コマンド]"
---

# [スキル名]

## 概要

[説明]

## 自動チェック

- PreToolUse: [何をチェックするか]
- PostToolUse: [何をチェックするか]
```

---

## 高度な例

コード付きスキル、ドメイン特化スキル、ワークフロースキル、Hooks付きスキルの詳細な例は[ADVANCED-EXAMPLES.md](ADVANCED-EXAMPLES.md)を参照。
