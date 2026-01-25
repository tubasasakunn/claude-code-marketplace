# スキル作成の具体例集

## 目次

- 基本スキル
- フロントマター設定別の例
- コード付きスキル
- ドメイン特化スキル
- ワークフロースキル
- Hooks付きスキル
- テンプレート

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

## 出力形式

## アーキテクチャレビューレポート

### 概要
[1-2文の概要]

### 構造
[ディレクトリ構造の説明]

### 強み
- ポイント1
- ポイント2

### 改善点
1. [具体的な改善案]
2. [具体的な改善案]
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

## コード付きスキル

### APIテストスキル

```
api-tester/
├── SKILL.md
├── SCHEMAS.md
└── scripts/
    ├── test_endpoint.py
    └── validate_response.py
```

**SKILL.md**:
```yaml
---
name: api-tester
description: REST APIエンドポイントをテスト。APIテスト、レスポンス検証時に使用。
---

# APIテスト

## クイックスタート

エンドポイントテスト:
```bash
python scripts/test_endpoint.py GET https://api.example.com/users
```

レスポンス検証:
```bash
python scripts/validate_response.py response.json schema.json
```

## ワークフロー

1. エンドポイント情報を収集
2. テストリクエストを実行
3. レスポンスを検証
4. 結果をレポート

スキーマ定義は[SCHEMAS.md](SCHEMAS.md)を参照。
```

**scripts/test_endpoint.py**:
```python
#!/usr/bin/env python3
"""APIエンドポイントテストスクリプト"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

def test_endpoint(method, url, data=None, headers=None):
    """エンドポイントをテストして結果を返す"""
    headers = headers or {"Content-Type": "application/json"}
    start_time = datetime.now()

    try:
        if data:
            data = json.dumps(data).encode('utf-8')

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        with urllib.request.urlopen(req, timeout=30) as response:
            elapsed = (datetime.now() - start_time).total_seconds()
            body = response.read().decode('utf-8')

            result = {
                "success": True,
                "status_code": response.status,
                "headers": dict(response.headers),
                "body": json.loads(body) if body else None,
                "elapsed_seconds": elapsed
            }

    except urllib.error.HTTPError as e:
        elapsed = (datetime.now() - start_time).total_seconds()
        result = {
            "success": False,
            "status_code": e.code,
            "error": str(e),
            "elapsed_seconds": elapsed
        }
    except Exception as e:
        result = {
            "success": False,
            "error": str(e)
        }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python test_endpoint.py METHOD URL [DATA_JSON]")
        sys.exit(1)

    method = sys.argv[1].upper()
    url = sys.argv[2]
    data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None

    test_endpoint(method, url, data)
```

---

## ドメイン特化スキル

### SQLクエリヘルパー

```yaml
---
name: sql-query-helper
description: SQLクエリの作成と最適化を支援。SQL作成、クエリ最適化時に使用。
---

# SQLクエリヘルパー

## クエリ作成ガイドライン

### SELECT
- 必要なカラムのみ指定（`*`は避ける）
- 適切なインデックスを活用
- JOINは必要最小限に

### INSERT/UPDATE/DELETE
- トランザクションを使用
- WHERE句を必ず確認
- 影響行数を事前に確認

## 最適化チェックリスト

- [ ] インデックスが適切に使用されているか
- [ ] N+1問題がないか
- [ ] 不要なサブクエリがないか
- [ ] LIMIT/OFFSETの使用が適切か

## よくあるパターン

### ページネーション

```sql
SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 40;
```

### 集計

```sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as count
FROM orders
GROUP BY DATE(created_at)
ORDER BY date DESC;
```
```

---

## ワークフロースキル

### PRレビューワークフロー

```yaml
---
name: pr-review
description: PRの包括的なレビューを実行
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash(gh:*)
---

# PRレビュー

## コンテキスト

- PR diff: !`gh pr diff`
- PRコメント: !`gh pr view --comments`
- 変更ファイル: !`gh pr diff --name-only`

## レビュー手順

1. **変更の概要を把握**
   - 変更ファイル一覧を確認
   - 変更の目的を理解

2. **コード品質をチェック**
   - 命名規則
   - エラー処理
   - テストカバレッジ

3. **潜在的な問題を特定**
   - パフォーマンス影響
   - セキュリティリスク
   - 後方互換性

4. **フィードバックを作成**

## 出力形式

## PRレビュー結果

### 概要
[変更の要約]

### 良い点
- ポイント1
- ポイント2

### 懸念事項
1. [具体的な懸念と提案]
2. [具体的な懸念と提案]

### 推奨事項
- [ ] 修正すべき項目
```

---

## Hooks付きスキル

### セキュリティチェック付き操作

```yaml
---
name: secure-file-ops
description: セキュリティチェック付きでファイル操作を実行
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: "./scripts/security-check.sh"
          timeout: 10
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: "./scripts/lint-check.sh"
---

# セキュアファイル操作

ファイル操作時は自動的にセキュリティチェックが実行されます。

## セキュリティポリシー

- 機密ファイル（.env, credentials等）への書き込みは禁止
- sudoコマンドは禁止
- rm -rfは禁止

## 編集後の自動チェック

- 構文エラーチェック
- リントチェック
- フォーマット確認
```

**scripts/security-check.sh**:
```bash
#!/bin/bash
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

if [ -z "$command" ]; then
    exit 0
fi

# 危険なコマンドをチェック
if echo "$command" | grep -qE '(rm -rf|sudo|chmod 777)'; then
    echo "危険なコマンドが検出されました: $command" >&2
    exit 2
fi

# 機密ファイルへのアクセスをチェック
if echo "$command" | grep -qE '\.(env|key|pem|credentials)'; then
    echo "機密ファイルへのアクセスは許可されていません" >&2
    exit 2
fi

exit 0
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
