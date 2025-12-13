---
name: plugin-guide
description: Claude Codeプラグインの作成、インストール、管理について説明します。プラグイン開発、マーケットプレイス設定、カスタムコマンド・エージェント・フック・スキル・MCPサーバーの統合について質問された場合に使用してください。
---

# プラグインガイド

## 概要

プラグインはClaude Codeを拡張するモジュール式機能パッケージです。以下のコンポーネントを含めることができます：

- **コマンド**: カスタムスラッシュコマンド
- **エージェント**: 特化したサブエージェント
- **スキル**: Claudeの機能を拡張するSKILL.md
- **フック**: イベントベースの自動化
- **MCPサーバー**: 外部ツール統合

## プラグイン構造

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      # プラグインメタデータ（必須）
├── commands/            # スラッシュコマンド
│   └── my-command.md
├── agents/              # サブエージェント定義
│   └── my-agent.md
├── skills/              # エージェントスキル
│   └── my-skill/
│       └── SKILL.md
├── hooks/               # イベントハンドラー
│   └── hooks.json
└── .mcp.json            # MCPサーバー設定
```

## plugin.json（必須）

```json
{
  "name": "my-plugin",
  "description": "プラグインの説明",
  "version": "1.0.0",
  "author": {
    "name": "作者名"
  }
}
```

## クイックスタート

### 1. プラグイン作成

```bash
mkdir my-plugin
cd my-plugin
mkdir .claude-plugin commands

# plugin.json作成
cat > .claude-plugin/plugin.json << 'EOF'
{
  "name": "my-plugin",
  "description": "My first plugin",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
EOF

# コマンド作成
cat > commands/hello.md << 'EOF'
---
description: ユーザーに挨拶する
---
ユーザーに親しみやすく挨拶してください。
EOF
```

### 2. テストマーケットプレイス作成

```bash
cd ..
mkdir test-marketplace
cd test-marketplace
mkdir .claude-plugin

cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "test-marketplace",
  "owner": { "name": "Test User" },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "../my-plugin",
      "description": "My test plugin"
    }
  ]
}
EOF
```

### 3. インストールとテスト

```shell
/plugin marketplace add ./test-marketplace
/plugin install my-plugin@test-marketplace
# Claude Codeを再起動
/hello  # コマンドをテスト
```

## プラグイン管理コマンド

| コマンド | 説明 |
|---------|------|
| `/plugin` | インタラクティブメニューを開く |
| `/plugin marketplace add <path>` | マーケットプレイスを追加 |
| `/plugin install <name>@<marketplace>` | プラグインをインストール |
| `/plugin uninstall <name>@<marketplace>` | プラグインを削除 |
| `/plugin enable <name>@<marketplace>` | プラグインを有効化 |
| `/plugin disable <name>@<marketplace>` | プラグインを無効化 |

## 詳細ドキュメント

- プラグインコンポーネントの詳細: [REFERENCE.md](REFERENCE.md)
- 実践的な例: [EXAMPLES.md](EXAMPLES.md)

## チーム配布

リポジトリの`.claude/settings.json`で自動インストールを設定：

```json
{
  "plugin_marketplaces": ["your-org/claude-plugins"],
  "plugins": ["formatter@your-org", "linter@your-org"]
}
```

チームメンバーがリポジトリフォルダを信頼すると、プラグインが自動インストールされます。
