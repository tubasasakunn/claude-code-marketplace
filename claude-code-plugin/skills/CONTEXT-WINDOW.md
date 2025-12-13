# Claude Code コンテキストウィンドウ

## 基本概念

コンテキストウィンドウは、モデルが参照できるテキスト量と生成テキストの合計。モデルの「ワーキングメモリ」。

---

## サイズ

| モデル | 標準 | 拡張 |
|--------|------|------|
| Sonnet 4/4.5 | 200K | 1M（ベータ） |
| Opus 4.5 | 200K | - |
| Haiku | 200K | - |

---

## 拡張思考（Extended Thinking）

### 動作

1. 思考トークンは`max_tokens`のサブセット
2. 出力トークンとして課金
3. **前のターンの思考ブロックは自動削除**

### トークン計算

```
context_window = (input_tokens - previous_thinking_tokens) + current_turn_tokens
```

### ツール使用時の注意

**重要**: ツール結果を返す際、その思考ブロックを含める**必要あり**。

```
ターン1: 入力 + 思考 + テキスト + ツール呼び出し
ターン2: 前の全ブロック + tool_result（思考含む）→ テキスト応答
ターン3: 思考ブロック削除可能 + 新しいユーザー入力 → 新しい思考
```

### インターリーブ思考

Claude 4モデル: ツール呼び出し間で思考可能（Sonnet 3.7は非対応）

---

## 100万トークンコンテキスト

### 要件

- 使用層4以上
- Claude Sonnet 4/4.5のみ
- ベータヘッダー必要

### 有効化

```python
response = client.beta.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1024,
    messages=[...],
    betas=["context-1m-2025-08-07"]
)
```

### 価格

200Kトークン超過分:
- 入力: 2倍
- 出力: 1.5倍

---

## コンテキスト認識（Claude 4.5）

Claude Sonnet 4.5とHaiku 4.5は残りコンテキストを自動追跡。

### 動作

**開始時**:
```xml
<budget:token_budget>200000</budget:token_budget>
```

**ツール呼び出し後**:
```xml
<system_warning>Token usage: 35000/200000; 165000 remaining</system_warning>
```

### メリット

- 長時間エージェントセッションで効果的
- マルチコンテキストウィンドウワークフロー
- 慎重なトークン管理が必要なタスク

---

## コンテキスト管理

### 新モデル（Sonnet 3.7以降）

プロンプト + 出力がコンテキストウィンドウを超える場合:
- 静かな切り詰め**なし**
- **検証エラーを返す**

### トークンカウントAPI

送信前にトークン数を推定:

```python
from anthropic import Anthropic
client = Anthropic()

# トークン数を推定
count = client.messages.count_tokens(
    model="claude-sonnet-4-5",
    messages=[{"role": "user", "content": "..."}]
)
```

---

## ベストプラクティス

1. **長いコンテキストは計画的に**: 必要な情報のみ含める
2. **トークンカウント活用**: 送信前に確認
3. **拡張思考の理解**: 思考トークンの課金と削除を理解
4. **ツール使用時の注意**: 思考ブロックの扱いに注意
