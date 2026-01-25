---
name: commit
description: 現在の変更を確認し、全てステージングして日本語のConventional Commitsでコミット。/commitで呼び出し。
disable-model-invocation: true
allowed-tools:
  - Bash(git *)
  - Read
---

# Git Commit スキル

現在の変更を確認し、適切な日本語コミットメッセージで即座にコミットする。

## 実行手順

### 1. 変更の確認

並列で以下を実行:
- `git status` - 変更ファイル一覧
- `git diff` - 未ステージの変更内容
- `git diff --staged` - ステージ済みの変更内容
- `git log --oneline -5` - 直近のコミットスタイル確認

### 2. ステージング

すべての変更をステージング:
```bash
git add -A
```

### 3. コミットメッセージ作成

Conventional Commits形式（日本語）で作成:

```
<type>(<scope>): <日本語の説明>

<詳細説明（任意）>

Co-Authored-By: Claude <noreply@anthropic.com>
```

#### Type一覧
| Type | 用途 |
|------|------|
| feat | 新機能追加 |
| fix | バグ修正 |
| docs | ドキュメントのみの変更 |
| style | コードの意味に影響しない変更（空白、フォーマット等） |
| refactor | バグ修正でも機能追加でもないコード変更 |
| test | テストの追加・修正 |
| chore | ビルドプロセスやツールの変更 |

#### Scope
変更の影響範囲を示す（任意）。例: `auth`, `api`, `ui`

### 4. コミット実行

HEREDOCを使用してコミット:
```bash
git commit -m "$(cat <<'EOF'
<type>(<scope>): <説明>

<詳細>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### 5. 結果確認

```bash
git log --oneline -1
```

## 例

### 機能追加
```
feat(skill): commitスキルを追加

日本語でConventional Commitsを生成するスキル

Co-Authored-By: Claude <noreply@anthropic.com>
```

### バグ修正
```
fix(api): 認証トークンの有効期限チェックを修正

Co-Authored-By: Claude <noreply@anthropic.com>
```

### ドキュメント更新
```
docs: READMEにインストール手順を追加

Co-Authored-By: Claude <noreply@anthropic.com>
```

## 注意事項

- 変更がない場合はコミットしない
- `.env`や認証情報などの機密ファイルがあれば警告
- pre-commit hookが失敗した場合は修正後に新規コミット（`--amend`は使わない）
