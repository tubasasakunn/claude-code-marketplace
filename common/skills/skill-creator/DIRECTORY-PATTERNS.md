# スキルディレクトリ構造パターン

## 基本構造

### シンプルスキル（単一ファイル）

```
skill-name/
└── SKILL.md
```

最もシンプルな構成。指示のみで完結する場合に使用。

**適用例**: コミットメッセージ生成、コードレビューガイド

### 参照付きスキル

```
skill-name/
├── SKILL.md
├── REFERENCE.md
└── EXAMPLES.md
```

詳細なリファレンスや追加例が必要な場合。

**適用例**: APIドキュメント参照、スタイルガイド

### スクリプト付きスキル

```
skill-name/
├── SKILL.md
└── scripts/
    ├── main.py
    ├── validate.py
    └── utils.py
```

自動化スクリプトを含む場合。

**適用例**: データ処理、ファイル変換、検証タスク

### フルスキル

```
skill-name/
├── SKILL.md
├── REFERENCE.md
├── EXAMPLES.md
├── scripts/
│   ├── process.py
│   └── validate.py
└── templates/
    └── output.md
```

すべての要素を含む完全な構成。

**適用例**: 複雑なワークフロー、エンタープライズ向け

---

## ドメイン別パターン

### ドキュメント処理

```
doc-processor/
├── SKILL.md
├── FORMATS.md          # 対応形式の説明
├── scripts/
│   ├── convert.py      # 形式変換
│   ├── extract.py      # テキスト抽出
│   └── validate.py     # 形式検証
└── templates/
    └── report.md       # 出力テンプレート
```

### データ分析

```
data-analyzer/
├── SKILL.md
├── SCHEMAS.md          # データスキーマ定義
├── QUERIES.md          # よく使うクエリ
└── scripts/
    ├── analyze.py      # 分析スクリプト
    ├── visualize.py    # 可視化
    └── export.py       # エクスポート
```

### 開発ワークフロー

```
dev-workflow/
├── SKILL.md
├── CHECKLIST.md        # チェックリスト
├── TROUBLESHOOTING.md  # トラブルシューティング
└── scripts/
    ├── setup.sh        # 環境セットアップ
    ├── test.sh         # テスト実行
    └── deploy.sh       # デプロイ
```

### API統合

```
api-integration/
├── SKILL.md
├── ENDPOINTS.md        # エンドポイント一覧
├── AUTH.md             # 認証方法
└── scripts/
    ├── request.py      # リクエスト送信
    └── parse.py        # レスポンス解析
```

---

## ファイル命名規則

### SKILL.md内の参照ファイル

| ファイル名 | 用途 |
|-----------|------|
| REFERENCE.md | 詳細なリファレンス |
| EXAMPLES.md | 追加の使用例 |
| SCHEMAS.md | データスキーマ定義 |
| FORMATS.md | 形式・フォーマット説明 |
| CHECKLIST.md | チェックリスト |
| TROUBLESHOOTING.md | トラブルシューティング |
| AUTH.md | 認証・認可関連 |
| ENDPOINTS.md | APIエンドポイント |

### スクリプトファイル

| ファイル名 | 用途 |
|-----------|------|
| main.py / index.py | メイン処理 |
| validate.py | 検証処理 |
| process.py | データ処理 |
| convert.py | 形式変換 |
| extract.py | 抽出処理 |
| analyze.py | 分析処理 |
| export.py | エクスポート |
| utils.py | ユーティリティ |

---

## ディレクトリ配置

### 個人用スキル

```
~/.claude/skills/
├── my-workflow/
│   └── SKILL.md
├── code-helper/
│   ├── SKILL.md
│   └── scripts/
└── doc-generator/
    ├── SKILL.md
    └── templates/
```

全プロジェクトで使用可能。

### プロジェクトスキル

```
project-root/
├── .claude/
│   └── skills/
│       ├── project-workflow/
│       │   └── SKILL.md
│       └── api-client/
│           ├── SKILL.md
│           └── ENDPOINTS.md
├── src/
└── package.json
```

プロジェクト固有。gitでチーム共有可能。

---

## 段階的開示の実装

### レベル1: メタデータのみ

```yaml
---
name: my-skill
description: 説明文（これだけが常にロードされる）
---
```

### レベル2: メイン指示

SKILL.mdのボディ（トリガー時にロード）

### レベル3以上: 参照ファイル

```markdown
詳細は[REFERENCE.md](REFERENCE.md)を参照。
```

必要時のみClaudeがファイルを読む。

---

## ベストプラクティス

### DO

- ファイル名は説明的に
- 階層は浅く（最大2レベル）
- 参照は1レベル深さまで
- フォワードスラッシュを使用

### DON'T

- 深いネスト（`a/b/c/d/file.md`）
- 曖昧な名前（`doc1.md`, `file.md`）
- Windowsパス（`scripts\main.py`）
- 巨大な単一ファイル

---

## クイックスタート

新規スキル作成:

```bash
# 個人用
mkdir -p ~/.claude/skills/my-skill
touch ~/.claude/skills/my-skill/SKILL.md

# プロジェクト用
mkdir -p .claude/skills/my-skill
touch .claude/skills/my-skill/SKILL.md
```
