# プラグイン検証チェックリスト

プラグインを公開・共有する前に確認すべき項目。

---

## 必須チェック

### plugin.json

- [ ] `.claude-plugin/plugin.json`が存在する
- [ ] `name`フィールドが存在する
- [ ] JSON構文が正しい

### nameフィールド

- [ ] 64文字以下
- [ ] 小文字のみ使用
- [ ] 数字は使用可（ただし先頭は避ける）
- [ ] ハイフン(`-`)のみ使用（アンダースコア`_`は不可）
- [ ] スペースなし
- [ ] 予約語を含まない（`anthropic`, `claude`, `claude-code-marketplace`など）

### ディレクトリ構造

- [ ] `commands/`、`agents/`、`skills/`、`hooks/`がプラグインルートにある
- [ ] `.claude-plugin/`内には`plugin.json`のみ
- [ ] スキルは`skills/<name>/SKILL.md`形式

---

## コンポーネントチェック

### スキル（skills/）

- [ ] 各スキルディレクトリに`SKILL.md`が存在
- [ ] `description`フィールドが存在
- [ ] 何をするか＋いつ使用するかを説明
- [ ] 三人称で記述

### エージェント（agents/）

- [ ] `name`フィールドが存在
- [ ] `description`フィールドが存在
- [ ] トリガー条件を説明

### フック（hooks/）

- [ ] `hooks/hooks.json`形式が正しい
- [ ] スクリプトパスに`${CLAUDE_PLUGIN_ROOT}`を使用
- [ ] スクリプトに実行権限（`chmod +x`）

### MCPサーバー（.mcp.json）

- [ ] JSON構文が正しい
- [ ] パスに`${CLAUDE_PLUGIN_ROOT}`を使用
- [ ] 環境変数が適切に参照されている

### LSPサーバー（.lsp.json）

- [ ] `command`フィールドが存在
- [ ] `extensionToLanguage`フィールドが存在
- [ ] 言語サーバーバイナリのインストール手順を記載

---

## 品質チェック

### コンテンツ

- [ ] SKILL.mdボディが500行以下
- [ ] 時間に敏感な情報がない
- [ ] 用語が一貫している
- [ ] 具体的な例を含んでいる

### パス

- [ ] すべてのパスがフォワードスラッシュ（`/`）
- [ ] Windowsスタイルのパス（`\`）がない
- [ ] 相対パスを使用（`./`で開始）
- [ ] パストラバーサル（`..`）がない

### スクリプト

- [ ] shebang行がある（`#!/bin/bash`など）
- [ ] 実行権限がある
- [ ] エラーハンドリングが明示的
- [ ] 使用方法が明記されている

---

## セキュリティチェック

- [ ] 機密情報を含んでいない
- [ ] APIキー、パスワードがハードコードされていない
- [ ] 外部URLへの不要なアクセスがない
- [ ] ファイルアクセスが適切にスコープされている
- [ ] 破壊的な操作に警告がある

---

## 検証コマンド

### プラグイン検証

```bash
# 構文検証
claude plugin validate ./my-plugin

# または Claude Code 内で
/plugin validate ./my-plugin
```

### 構造確認

```bash
# プラグイン構造を確認
tree my-plugin/

# または
ls -laR my-plugin/
```

### JSON検証

```bash
# plugin.jsonの検証
cat my-plugin/.claude-plugin/plugin.json | jq .

# hooks.jsonの検証
cat my-plugin/hooks/hooks.json | jq .

# .mcp.jsonの検証
cat my-plugin/.mcp.json | jq .
```

### パス確認

```bash
# Windowsパスを検索
grep -r '\\' my-plugin/

# パストラバーサルを検索
grep -r '\.\.' my-plugin/
```

### スクリプト確認

```bash
# 実行権限を確認
ls -la my-plugin/scripts/

# shebangを確認
head -1 my-plugin/scripts/*.sh
```

---

## クイック検証スクリプト

```bash
#!/bin/bash
# validate-plugin.sh

PLUGIN_DIR=$1

if [ -z "$PLUGIN_DIR" ]; then
    echo "Usage: ./validate-plugin.sh <plugin-directory>"
    exit 1
fi

PLUGIN_JSON="$PLUGIN_DIR/.claude-plugin/plugin.json"

# plugin.jsonの存在確認
if [ ! -f "$PLUGIN_JSON" ]; then
    echo "ERROR: plugin.json not found at $PLUGIN_JSON"
    exit 1
fi

# JSON構文確認
if ! jq . "$PLUGIN_JSON" > /dev/null 2>&1; then
    echo "ERROR: Invalid JSON syntax in plugin.json"
    exit 1
fi

# nameフィールド確認
NAME=$(jq -r '.name' "$PLUGIN_JSON")
if [ "$NAME" == "null" ] || [ -z "$NAME" ]; then
    echo "ERROR: Missing name field"
    exit 1
fi

# name形式確認
if ! echo "$NAME" | grep -qE '^[a-z0-9][a-z0-9-]*$'; then
    echo "ERROR: Invalid name format (use lowercase, numbers, hyphens)"
    exit 1
fi

# Windowsパス確認
if grep -rq '\\' "$PLUGIN_DIR" 2>/dev/null; then
    echo "WARNING: Windows-style paths found"
fi

# スクリプト実行権限確認
for script in "$PLUGIN_DIR"/scripts/*.sh 2>/dev/null; do
    if [ -f "$script" ] && [ ! -x "$script" ]; then
        echo "WARNING: Script not executable: $script"
    fi
done

echo "Validation complete for: $NAME"
```

---

## 一般的なエラーメッセージ

### マニフェスト検証エラー

| エラー | 原因 | 解決策 |
|:-------|:-----|:-------|
| `Invalid JSON syntax` | JSON構文エラー | カンマ、クォートを確認 |
| `name: Required` | nameフィールドなし | nameを追加 |
| `Plugin directory not found` | パスが存在しない | ソースパスを確認 |

### プラグインロードエラー

| エラー | 原因 | 解決策 |
|:-------|:-----|:-------|
| `No commands found` | コマンドディレクトリが空 | .mdファイルを追加 |
| `Path traversal not allowed` | `..`を含むパス | 相対パスに修正 |

---

## トラブルシューティング

### プラグインがロードされない

1. `claude --debug`でロードログを確認
2. plugin.jsonの構文を確認
3. ディレクトリ構造を確認

### スキルがトリガーされない

1. descriptionが具体的か確認
2. トリガーワードが含まれているか確認
3. Claude Codeを再起動

### フックが動作しない

1. スクリプトの実行権限を確認
2. パスに`${CLAUDE_PLUGIN_ROOT}`を使用しているか確認
3. 環境変数が正しいか確認

### MCPサーバーが起動しない

1. コマンドが存在するか確認
2. パスに`${CLAUDE_PLUGIN_ROOT}`を使用しているか確認
3. 必要な環境変数が設定されているか確認
