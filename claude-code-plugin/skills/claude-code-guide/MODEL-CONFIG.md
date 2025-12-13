# Claude Code モデル設定

## モデルエイリアス

| エイリアス | 動作 |
|-----------|------|
| `default` | アカウントタイプに応じた推奨モデル |
| `sonnet` | 最新Sonnet（現在4.5）- 日常コーディング |
| `opus` | Opus（現在4.5）- 複雑な推論 |
| `haiku` | 高速・低コスト・シンプルタスク |
| `sonnet[1m]` | 100万トークンコンテキスト |
| `opusplan` | プラン時opus → 実行時sonnet |

---

## モデルの設定方法

### 優先度順

1. **セッション中**: `/model <alias|name>`
2. **起動時**: `claude --model <alias|name>`
3. **環境変数**: `ANTHROPIC_MODEL=<alias|name>`
4. **設定ファイル**: settings.jsonの`model`フィールド

### 使用例

```bash
# Opusで起動
claude --model opus

# セッション中にSonnetへ切り替え
/model sonnet
```

### settings.json

```json
{
  "permissions": {},
  "model": "opus"
}
```

---

## 特殊なモデル動作

### defaultモデル

アカウントタイプに依存。Maxユーザーの場合、Opusの使用量閾値に達するとSonnetにフォールバック。

### opusplanモデル

ハイブリッドアプローチ:
- **プランモード**: 複雑な推論にopus使用
- **実行モード**: コード生成にsonnet自動切り替え

### [1m]サフィックス

Console/APIユーザー向け。100万トークンコンテキストを有効化。

```bash
/model anthropic.claude-sonnet-4-5-20250929-v1:0[1m]
```

**注意**: 拡張コンテキストは異なる価格体系。

---

## 現在のモデル確認

1. ステータスライン（設定時）
2. `/status` コマンド

---

## 環境変数

| 変数 | 説明 |
|------|------|
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | opusエイリアスのモデル名 |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | sonnetエイリアスのモデル名 |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | haikuエイリアスのモデル名 |
| `CLAUDE_CODE_SUBAGENT_MODEL` | サブエージェント用モデル |

---

## プロンプトキャッシュ設定

自動的にプロンプトキャッシュを使用してパフォーマンス最適化。

| 変数 | 説明 |
|------|------|
| `DISABLE_PROMPT_CACHING` | 全モデルでキャッシュ無効 |
| `DISABLE_PROMPT_CACHING_HAIKU` | Haikuのみ無効 |
| `DISABLE_PROMPT_CACHING_SONNET` | Sonnetのみ無効 |
| `DISABLE_PROMPT_CACHING_OPUS` | Opusのみ無効 |

---

## APIプロバイダー別

### Anthropic API
- 完全なモデル名を使用
- 例: `claude-sonnet-4-5-20250929`

### Amazon Bedrock
- 推論プロファイルARNを使用

### Google Vertex AI
- バージョン名を使用

### Microsoft Foundry
- デプロイメント名を使用
