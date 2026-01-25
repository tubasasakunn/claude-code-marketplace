# 高度なスキル例

コード付きスキル、ドメイン特化スキル、ワークフロースキル、Hooks付きスキルの詳細な例です。

基本的な例は[EXAMPLES.md](EXAMPLES.md)を参照。

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
