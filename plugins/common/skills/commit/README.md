# commit

現在の変更を日本語のConventional Commitsでコミットするスキル。

## 概要

変更を確認し、すべてステージングして適切なコミットメッセージで即座にコミットします。

## 使用方法

```
/commit
```

手動呼び出し専用（`disable-model-invocation: true`）

## 実行手順

1. **変更の確認** - `git status`, `git diff`を並列実行
2. **ステージング** - `git add -A`で全変更をステージ
3. **コミットメッセージ作成** - Conventional Commits形式（日本語）
4. **コミット実行** - HEREDOCでメッセージを渡してコミット
5. **結果確認** - `git log --oneline -1`

## コミットメッセージ形式

```
<type>(<scope>): <日本語の説明>

<詳細説明（任意）>

Co-Authored-By: Claude <noreply@anthropic.com>
```

### Type一覧

| Type | 用途 |
|------|------|
| feat | 新機能追加 |
| fix | バグ修正 |
| docs | ドキュメントのみの変更 |
| style | コードの意味に影響しない変更 |
| refactor | リファクタリング |
| test | テストの追加・修正 |
| chore | ビルドプロセスやツールの変更 |

## 注意事項

- 変更がない場合はコミットしない
- `.env`などの機密ファイルがあれば警告
- pre-commit hook失敗時は修正後に新規コミット
