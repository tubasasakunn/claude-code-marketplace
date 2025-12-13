# スキル作成の具体例集

## 目次

- コードなしスキル（指示のみ）
- コード付きスキル（スクリプト含む）
- ドメイン特化スキル
- ワークフロースキル

---

## コードなしスキル

### 1. ドキュメントレビュースキル

```yaml
---
name: doc-reviewer
description: 技術ドキュメントの品質をレビューします。ドキュメントのレビュー、改善提案、スタイルチェック時に使用してください。
---

# ドキュメントレビュー

## レビュー観点

1. **明確さ**: 対象読者が理解できるか
2. **完全性**: 必要な情報がすべて含まれているか
3. **正確性**: 技術的に正しいか
4. **構造**: 論理的に整理されているか
5. **一貫性**: 用語とスタイルが統一されているか

## チェックリスト

- [ ] タイトルが内容を正確に反映
- [ ] 目的が冒頭で明示
- [ ] ステップが順序立てて説明
- [ ] コード例が動作確認済み
- [ ] リンクが有効

## フィードバック形式

## 総評
[全体的な印象と主要な改善点]

## 良い点
- ポイント1
- ポイント2

## 改善提案
1. [具体的な改善案と理由]
2. [具体的な改善案と理由]
```

### 2. コミュニケーションスキル

```yaml
---
name: meeting-summarizer
description: 会議メモから構造化された要約を作成します。会議の要約、議事録作成、アクションアイテム抽出時に使用してください。
---

# 会議要約

## 出力形式

# [会議タイトル] - [日付]

## 参加者
- 名前1（役割）
- 名前2（役割）

## 決定事項
1. [決定内容]
2. [決定内容]

## アクションアイテム
| 担当者 | タスク | 期限 |
|--------|--------|------|
| 名前   | 内容   | 日付 |

## 議論のポイント
- トピック1: [要約]
- トピック2: [要約]

## 次回予定
- 日時:
- 議題:

## ガイドライン

- 決定事項は明確に記述
- アクションアイテムには必ず担当者と期限を含める
- 議論は要点のみ、詳細は省略
```

---

## コード付きスキル

### 1. API テストスキル

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
description: REST APIエンドポイントをテストし、レスポンスを検証します。API テスト、エンドポイント検証、レスポンス確認時に使用してください。
---

# APIテスト

## クイックスタート

エンドポイントテスト:
\`\`\`bash
python scripts/test_endpoint.py GET https://api.example.com/users
\`\`\`

レスポンス検証:
\`\`\`bash
python scripts/validate_response.py response.json schema.json
\`\`\`

## ワークフロー

1. エンドポイント情報を収集
2. テストリクエストを実行
3. レスポンスを検証
4. 結果をレポート

スキーマ定義は[SCHEMAS.md](SCHEMAS.md)を参照。

## 検証項目

- ステータスコード
- レスポンス形式（JSON/XML）
- 必須フィールドの存在
- データ型の一致
- レスポンス時間
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

### 2. ログ分析スキル

```
log-analyzer/
├── SKILL.md
└── scripts/
    ├── parse_logs.py
    └── find_patterns.py
```

**SKILL.md**:
```yaml
---
name: log-analyzer
description: ログファイルを分析してエラーパターンや異常を検出します。ログ分析、エラー調査、パターン検出時に使用してください。
---

# ログ分析

## 基本分析

ログ解析:
\`\`\`bash
python scripts/parse_logs.py app.log
\`\`\`

パターン検索:
\`\`\`bash
python scripts/find_patterns.py app.log "ERROR|WARN"
\`\`\`

## 分析ステップ

1. ログファイルを読み込み
2. タイムスタンプとレベルを抽出
3. エラーパターンを特定
4. 時系列で集計
5. レポートを生成

## 出力形式

## ログ分析レポート

### サマリー
- 総行数: X
- エラー数: X
- 警告数: X
- 期間: YYYY-MM-DD HH:MM ~ YYYY-MM-DD HH:MM

### エラー頻度
| 時間帯 | エラー数 |
|--------|----------|
| 00:00  | X        |

### 主要エラー
1. [エラーメッセージ] - X回
2. [エラーメッセージ] - X回
```

---

## ドメイン特化スキル

### データベーススキル

```yaml
---
name: sql-query-helper
description: SQLクエリの作成と最適化を支援します。SQL作成、クエリ最適化、データベース操作時に使用してください。
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
\`\`\`sql
SELECT * FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 40;
\`\`\`

### 集計
\`\`\`sql
SELECT
    DATE(created_at) as date,
    COUNT(*) as count
FROM orders
GROUP BY DATE(created_at)
ORDER BY date DESC;
\`\`\`
```

---

## ワークフロースキル

### デプロイメントスキル

```yaml
---
name: deployment-workflow
description: アプリケーションのデプロイメントプロセスをガイドします。デプロイ、リリース、本番環境への反映時に使用してください。
---

# デプロイメントワークフロー

## プロセス

進捗チェックリスト:
\`\`\`
デプロイ進捗:
- [ ] 1. プリフライトチェック
- [ ] 2. テスト実行
- [ ] 3. ビルド作成
- [ ] 4. ステージングデプロイ
- [ ] 5. ステージング確認
- [ ] 6. 本番デプロイ
- [ ] 7. 本番確認
- [ ] 8. ロールバック準備確認
\`\`\`

## 1. プリフライトチェック

- [ ] 全テストがパス
- [ ] コードレビュー完了
- [ ] CHANGELOGを更新
- [ ] バージョン番号を更新

## 2. テスト実行

\`\`\`bash
npm run test
npm run lint
npm run build
\`\`\`

## 3. ステージングデプロイ

\`\`\`bash
./scripts/deploy.sh staging
\`\`\`

確認項目:
- [ ] アプリケーションが起動
- [ ] 主要機能が動作
- [ ] エラーログなし

## 4. 本番デプロイ

\`\`\`bash
./scripts/deploy.sh production
\`\`\`

## 5. ロールバック手順

問題発生時:
\`\`\`bash
./scripts/rollback.sh production
\`\`\`
```

---

## テンプレート

新しいスキル作成時のテンプレート:

```yaml
---
name: [skill-name]
description: [何をするか]。[いつ使用するか]に使用してください。
---

# [スキル名]

## 概要

[スキルの目的を1-2文で説明]

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
