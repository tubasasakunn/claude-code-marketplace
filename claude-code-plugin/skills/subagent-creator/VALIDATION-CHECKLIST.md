# サブエージェント検証チェックリスト

サブエージェントを公開・共有する前に確認すべき項目。

---

## 必須チェック

### YAMLフロントマター

- [ ] `---`で開始している
- [ ] `---`で終了している
- [ ] `name`フィールドが存在する
- [ ] `description`フィールドが存在する

### nameフィールド

- [ ] 小文字のみ使用
- [ ] ハイフン(`-`)で単語を区切り
- [ ] スペースなし
- [ ] 一意の識別子

**良い例**:
- `code-reviewer`
- `test-runner`
- `security-auditor`

**悪い例**:
- `Code_Reviewer`
- `test runner`
- `myAgent`

### descriptionフィールド

- [ ] 目的が明確
- [ ] いつ使用するかが記述されている
- [ ] 積極的使用のトリガーが含まれている（推奨）

**良い例**:
```yaml
description: Expert code reviewer. Use PROACTIVELY after code changes.
```

**悪い例**:
```yaml
description: Reviews code
```

---

## ツール設定チェック

### toolsフィールド

- [ ] 必要なツールのみ許可
- [ ] ツール名が正確（大文字小文字区別）
- [ ] カンマとスペースで区切り

**形式**:
```yaml
tools: Read, Grep, Glob
```

### モデル設定

- [ ] 有効な値を使用: `sonnet`, `opus`, `haiku`, `inherit`
- [ ] 用途に適したモデルを選択

| モデル | 用途 |
|--------|------|
| `inherit` | メイン会話と一貫性を保つ |
| `sonnet` | バランスの取れた性能 |
| `opus` | 高精度が必要な場合 |
| `haiku` | 高速・低コスト |

---

## システムプロンプトチェック

### 構造

- [ ] 役割が明確に定義されている
- [ ] 実行手順が記載されている
- [ ] 出力形式が指定されている（必要な場合）

### 内容

- [ ] 具体的で実行可能な指示
- [ ] 曖昧な表現を避けている
- [ ] 例やテンプレートを含む（複雑な場合）

### ベストプラクティス

- [ ] 「When invoked:」セクションがある
- [ ] チェックリストや手順が番号付き
- [ ] 出力形式が明示されている

---

## ファイル配置チェック

### プロジェクトサブエージェント

- [ ] `.claude/agents/`に配置
- [ ] ファイル拡張子は`.md`

```bash
# 確認コマンド
ls -la .claude/agents/
```

### ユーザーサブエージェント

- [ ] `~/.claude/agents/`に配置
- [ ] ファイル拡張子は`.md`

```bash
# 確認コマンド
ls -la ~/.claude/agents/
```

---

## セキュリティチェック

### ツール権限

- [ ] 最小権限の原則に従っている
- [ ] 不要な`Bash`アクセスがない
- [ ] 分析系は読み取り専用ツールのみ

### システムプロンプト

- [ ] 機密情報を含んでいない
- [ ] 危険なコマンド実行を指示していない
- [ ] 適切な制約が記載されている

---

## 動作テストチェック

### 基本テスト

- [ ] サブエージェントが認識される
- [ ] 明示的呼び出しで動作する
- [ ] 期待通りの出力を返す

### 自動委譲テスト

- [ ] descriptionに基づいて自動選択される
- [ ] 適切なタイミングでトリガーされる

### エッジケース

- [ ] エラー時に適切に対応
- [ ] 大きな入力でも動作する

---

## クイック検証スクリプト

```bash
#!/bin/bash
# validate-agent.sh

AGENT_FILE=$1

if [ -z "$AGENT_FILE" ]; then
    echo "Usage: ./validate-agent.sh <agent-file.md>"
    exit 1
fi

# ファイル存在確認
if [ ! -f "$AGENT_FILE" ]; then
    echo "ERROR: File not found: $AGENT_FILE"
    exit 1
fi

# フロントマター確認
if ! head -1 "$AGENT_FILE" | grep -q "^---$"; then
    echo "ERROR: Missing opening ---"
    exit 1
fi

# nameフィールド確認
if ! grep -q "^name:" "$AGENT_FILE"; then
    echo "ERROR: Missing name field"
    exit 1
fi

# descriptionフィールド確認
if ! grep -q "^description:" "$AGENT_FILE"; then
    echo "ERROR: Missing description field"
    exit 1
fi

# name形式確認
NAME=$(grep "^name:" "$AGENT_FILE" | sed 's/name: *//')
if echo "$NAME" | grep -qE '[A-Z]|_| '; then
    echo "WARNING: name should use lowercase and hyphens only: $NAME"
fi

# toolsフィールド確認（存在する場合）
if grep -q "^tools:" "$AGENT_FILE"; then
    TOOLS=$(grep "^tools:" "$AGENT_FILE" | sed 's/tools: *//')
    echo "INFO: Tools configured: $TOOLS"
else
    echo "INFO: No tools specified (will inherit all)"
fi

# modelフィールド確認（存在する場合）
if grep -q "^model:" "$AGENT_FILE"; then
    MODEL=$(grep "^model:" "$AGENT_FILE" | sed 's/model: *//')
    if ! echo "$MODEL" | grep -qE '^(sonnet|opus|haiku|inherit)$'; then
        echo "WARNING: Invalid model value: $MODEL"
    fi
fi

echo "Validation complete for: $AGENT_FILE"
```

---

## /agentsコマンドでの確認

最も簡単な確認方法:

```
/agents
```

このコマンドで:
- すべてのサブエージェントを一覧表示
- 設定内容を確認
- ツール権限を確認
- 編集・削除が可能

---

## トラブルシューティング

### サブエージェントが認識されない

1. ファイルパスを確認
2. ファイル拡張子が`.md`か確認
3. YAMLフロントマターの形式を確認
4. Claude Codeを再起動

### ツールが動作しない

1. ツール名のスペルを確認
2. 大文字小文字を確認
3. メインスレッドでそのツールが利用可能か確認

### 自動委譲されない

1. descriptionが具体的か確認
2. 「Use PROACTIVELY」などのトリガーを追加
3. タスクとdescriptionの一致を確認

### エラーが発生する

1. システムプロンプトの指示を確認
2. ツール権限が十分か確認
3. 入力データの形式を確認
