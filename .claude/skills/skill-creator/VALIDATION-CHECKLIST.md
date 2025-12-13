# スキル検証チェックリスト

スキルを公開・共有する前に確認すべき項目。

---

## 必須チェック

### YAMLフロントマター

- [ ] `---`で開始している
- [ ] `---`で終了している
- [ ] `name`フィールドが存在する
- [ ] `description`フィールドが存在する

### nameフィールド

- [ ] 64文字以下
- [ ] 小文字のみ使用
- [ ] 数字は使用可（ただし先頭は避ける）
- [ ] ハイフン(`-`)のみ使用（アンダースコア`_`は不可）
- [ ] スペースなし
- [ ] 予約語を含まない（`anthropic`, `claude`）
- [ ] XMLタグを含まない

### descriptionフィールド

- [ ] 1024文字以下
- [ ] 空でない
- [ ] XMLタグを含まない
- [ ] 何をするかを説明している
- [ ] いつ使用するかを説明している
- [ ] 三人称で記述している

---

## 品質チェック

### コンテンツ

- [ ] SKILL.mdボディが500行以下
- [ ] Claudeが既に知っていることを説明していない
- [ ] 時間に敏感な情報がない
- [ ] 用語が一貫している
- [ ] 具体的な例を含んでいる

### 構造

- [ ] 段階的開示を適切に使用
- [ ] 参照は1レベルの深さまで
- [ ] ファイル名が説明的
- [ ] ディレクトリ構造が論理的

### パス

- [ ] すべてのパスがフォワードスラッシュ（`/`）
- [ ] Windowsスタイルのパス（`\`）がない
- [ ] 相対パスを使用

---

## スクリプトチェック（該当する場合）

### コード品質

- [ ] エラーハンドリングが明示的
- [ ] マジックナンバーがない（値が説明されている）
- [ ] 必要なパッケージがドキュメントに記載

### 実行可能性

- [ ] スクリプトが実行可能（`chmod +x`）
- [ ] shebang行がある（`#!/usr/bin/env python3`）
- [ ] 使用方法が明記されている

---

## テストチェック

### 基本テスト

- [ ] スキルが正しくトリガーされる
- [ ] 指示が明確で従いやすい
- [ ] 例が実際に動作する

### モデルテスト

- [ ] Haikuで動作確認（使用予定の場合）
- [ ] Sonnetで動作確認
- [ ] Opusで動作確認（使用予定の場合）

### エッジケース

- [ ] 異常な入力でも適切に対応
- [ ] エラー時のガイダンスがある

---

## セキュリティチェック

- [ ] 機密情報を含んでいない
- [ ] 外部URLへの不要なアクセスがない
- [ ] ファイルアクセスが適切にスコープされている
- [ ] 破壊的な操作に警告がある

---

## 検証コマンド

### YAMLの検証

```bash
# フロントマターを確認
head -20 SKILL.md

# YAML構文チェック（yq使用）
yq eval '.' SKILL.md 2>&1 | head -5
```

### ファイル構造の確認

```bash
# スキルディレクトリの構造を表示
tree .claude/skills/skill-name/

# または
find .claude/skills/skill-name/ -type f
```

### パスの確認

```bash
# Windowsパスを検索
grep -r '\\' .claude/skills/skill-name/
```

---

## クイック検証スクリプト

```bash
#!/bin/bash
# validate-skill.sh

SKILL_DIR=$1

if [ -z "$SKILL_DIR" ]; then
    echo "Usage: ./validate-skill.sh <skill-directory>"
    exit 1
fi

SKILL_FILE="$SKILL_DIR/SKILL.md"

# SKILL.mdの存在確認
if [ ! -f "$SKILL_FILE" ]; then
    echo "ERROR: SKILL.md not found"
    exit 1
fi

# フロントマター確認
if ! head -1 "$SKILL_FILE" | grep -q "^---$"; then
    echo "ERROR: Missing opening ---"
    exit 1
fi

# nameフィールド確認
if ! grep -q "^name:" "$SKILL_FILE"; then
    echo "ERROR: Missing name field"
    exit 1
fi

# descriptionフィールド確認
if ! grep -q "^description:" "$SKILL_FILE"; then
    echo "ERROR: Missing description field"
    exit 1
fi

# 行数確認
LINES=$(wc -l < "$SKILL_FILE")
if [ "$LINES" -gt 500 ]; then
    echo "WARNING: SKILL.md has $LINES lines (recommended: <500)"
fi

# Windowsパス確認
if grep -r '\\' "$SKILL_DIR" > /dev/null 2>&1; then
    echo "WARNING: Windows-style paths found"
fi

echo "Validation complete!"
```

---

## 問題解決

### スキルがトリガーされない

1. descriptionが具体的か確認
2. トリガーワードが含まれているか確認
3. Claude Codeを再起動

### YAMLエラー

1. タブではなくスペースを使用
2. 特殊文字はクォートで囲む
3. `---`の位置を確認

### スクリプトが動作しない

1. 実行権限を確認
2. 依存パッケージを確認
3. パスを確認
