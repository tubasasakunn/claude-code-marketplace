---
name: plugin-guide
description: Claude Codeプラグインの作成、インストール、管理について説明します。プラグイン開発、マーケットプレイス設定、カスタムコマンド・エージェント・フック・スキル・MCPサーバー・LSPサーバーの統合について質問された場合に使用してください。
---

# プラグインガイド

> 最新のドキュメントインデックス: https://code.claude.com/docs/llms.txt

## 概要

プラグインはClaude Codeを拡張するモジュール式機能パッケージです。以下のコンポーネントを含めることができます：

- **スキル**: Claudeの機能を拡張するSKILL.md（自動またはユーザー呼び出し）
- **コマンド**: スラッシュコマンド（`/plugin-name:command`で呼び出し）
- **エージェント**: 特化したサブエージェント
- **フック**: イベントベースの自動化
- **MCPサーバー**: 外部ツール統合
- **LSPサーバー**: コードインテリジェンス

## プラグイン vs スタンドアロン構成

| アプローチ | スキル名 | 用途 |
|:-----------|:---------|:-----|
| **スタンドアロン**（`.claude/`） | `/hello` | 個人用、プロジェクト固有、実験用 |
| **プラグイン**（`.claude-plugin/plugin.json`） | `/plugin-name:hello` | チーム共有、コミュニティ配布、バージョン管理 |

## プラグイン構造

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      # プラグインメタデータ（必須）
├── skills/              # スキル（SKILL.md形式）
│   └── my-skill/
│       └── SKILL.md
├── commands/            # コマンド（レガシー、新規はskillsを推奨）
│   └── my-command.md
├── agents/              # サブエージェント定義
│   └── my-agent.md
├── hooks/               # イベントハンドラー
│   └── hooks.json
├── .mcp.json            # MCPサーバー設定
└── .lsp.json            # LSPサーバー設定
```

> **重要**: `commands/`、`agents/`、`skills/`、`hooks/`は**プラグインルート**に配置。`.claude-plugin/`内には`plugin.json`のみ。

## plugin.json（必須）

```json
{
  "name": "my-plugin",
  "description": "プラグインの説明（最大256文字）",
  "version": "1.0.0",
  "author": {
    "name": "作者名"
  }
}
```

## クイックスタート

### 1. プラグイン作成

```bash
mkdir -p my-plugin/.claude-plugin
mkdir -p my-plugin/skills/hello

# plugin.json作成
cat > my-plugin/.claude-plugin/plugin.json << 'EOF'
{
  "name": "my-plugin",
  "description": "My first plugin",
  "version": "1.0.0",
  "author": { "name": "Your Name" }
}
EOF

# スキル作成
cat > my-plugin/skills/hello/SKILL.md << 'EOF'
---
description: ユーザーに挨拶する
disable-model-invocation: true
---
ユーザーに親しみやすく挨拶してください。
EOF
```

### 2. テスト

```bash
claude --plugin-dir ./my-plugin
```

```shell
/my-plugin:hello
```

### 3. マーケットプレイス経由でインストール

```shell
/plugin marketplace add ./test-marketplace
/plugin install my-plugin@test-marketplace
# Claude Codeを再起動
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
| `/plugin marketplace update <name>` | マーケットプレイスを更新 |

## 詳細ドキュメント

- コンポーネント詳細: [REFERENCE.md](REFERENCE.md)
- 実践的な例: [EXAMPLES.md](EXAMPLES.md)
- 検証チェックリスト: [VALIDATION-CHECKLIST.md](VALIDATION-CHECKLIST.md)
- ベストプラクティス: [BEST-PRACTICES.md](BEST-PRACTICES.md)
- マーケットプレイス: [MARKETPLACE.md](MARKETPLACE.md)

## プラグイン作成の手順

### 1. ユーザー要件の確認

**プラグイン作成時は、必ずAskUserQuestionツールで以下を確認する**：

#### 基本情報
- プラグインの目的と主要な機能
- 対象ユーザー（個人用/チーム共有/コミュニティ配布）
- 含めるコンポーネント（スキル、エージェント、フック、MCP、LSP）

#### コンポーネント構成
- スキルの数と名前
- エージェントが必要か
- フックでの自動化が必要か
- 外部サービス連携（MCP）が必要か
- コードインテリジェンス（LSP）が必要か

### 2. 確認すべき質問リスト

```
1. 基本情報
   - プラグイン名は？（小文字、数字、ハイフンのみ）
   - 主な目的・機能は？
   - バージョンは？（デフォルト: 1.0.0）

2. コンポーネント構成
   - スキル: はい / いいえ
   - エージェント: はい / いいえ
   - フック: はい / いいえ
   - MCPサーバー: はい / いいえ
   - LSPサーバー: はい / いいえ

3. 配布方法
   - 配布先: 個人用 / チーム / コミュニティ
   - マーケットプレイス登録: はい / いいえ
```

## チーム配布

リポジトリの`.claude/settings.json`で自動インストールを設定：

```json
{
  "extraKnownMarketplaces": {
    "team-plugins": {
      "source": {
        "source": "github",
        "repo": "your-org/claude-plugins"
      }
    }
  },
  "enabledPlugins": {
    "formatter@team-plugins": true,
    "linter@team-plugins": true
  }
}
```

チームメンバーがリポジトリフォルダを信頼すると、プラグインが自動インストールされます。

## 環境変数

プラグイン内で使用可能な環境変数：

| 変数 | 説明 |
|:-----|:-----|
| `${CLAUDE_PLUGIN_ROOT}` | プラグインディレクトリの絶対パス |

フックやMCPサーバーでは必ずこの変数を使用：

```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
}
```
