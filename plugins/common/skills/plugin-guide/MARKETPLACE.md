# マーケットプレイスガイド

プラグインマーケットプレイスの作成、配布、管理について説明します。

---

## 概要

マーケットプレイスはプラグインのカタログです。ユーザーは：
1. マーケットプレイスを追加
2. 個別のプラグインをインストール

という2ステップでプラグインを利用できます。

---

## marketplace.json スキーマ

### 必須フィールド

| フィールド | 型 | 説明 | 例 |
|:-----------|:---|:-----|:---|
| `name` | string | マーケットプレイス識別子（kebab-case） | `"acme-tools"` |
| `owner` | object | メンテナー情報 | |
| `plugins` | array | プラグインリスト | |

### 完全なスキーマ

```json
{
  "name": "my-marketplace",
  "owner": {
    "name": "Your Name",
    "email": "optional@example.com"
  },
  "metadata": {
    "description": "マーケットプレイスの説明",
    "version": "1.0.0",
    "pluginRoot": "./plugins"
  },
  "plugins": [
    {
      "name": "plugin-name",
      "source": "./plugins/plugin-name",
      "description": "プラグインの説明",
      "version": "1.0.0",
      "author": {
        "name": "Author Name"
      },
      "homepage": "https://docs.example.com",
      "repository": "https://github.com/user/repo",
      "license": "MIT",
      "keywords": ["keyword1", "keyword2"],
      "category": "productivity",
      "tags": ["tag1", "tag2"],
      "strict": true
    }
  ]
}
```

### 予約名

以下のマーケットプレイス名は予約済み：
- `claude-code-marketplace`
- `claude-code-plugins`
- `claude-plugins-official`
- `anthropic-marketplace`
- `anthropic-plugins`
- `agent-skills`
- `life-sciences`

---

## プラグインソース形式

### 相対パス

```json
{
  "name": "my-plugin",
  "source": "./plugins/my-plugin"
}
```

> **注意**: 相対パスはGitベースのマーケットプレイスでのみ動作。URLベースでは使用不可。

### GitHub

```json
{
  "name": "github-plugin",
  "source": {
    "source": "github",
    "repo": "owner/repo"
  }
}
```

ブランチ/タグ/コミット指定：

```json
{
  "name": "github-plugin",
  "source": {
    "source": "github",
    "repo": "owner/repo",
    "ref": "v2.0.0",
    "sha": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
  }
}
```

### Git URL

```json
{
  "name": "git-plugin",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git"
  }
}
```

ブランチ/タグ指定：

```json
{
  "name": "git-plugin",
  "source": {
    "source": "url",
    "url": "https://gitlab.com/team/plugin.git",
    "ref": "main",
    "sha": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0"
  }
}
```

---

## マーケットプレイス作成

### 1. ディレクトリ構造作成

```bash
mkdir -p my-marketplace/.claude-plugin
mkdir -p my-marketplace/plugins/my-plugin/.claude-plugin
mkdir -p my-marketplace/plugins/my-plugin/skills/hello
```

### 2. marketplace.json作成

```bash
cat > my-marketplace/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "my-marketplace",
  "owner": {
    "name": "Your Name"
  },
  "plugins": [
    {
      "name": "my-plugin",
      "source": "./plugins/my-plugin",
      "description": "My plugin description"
    }
  ]
}
EOF
```

### 3. プラグイン作成

```bash
# plugin.json
cat > my-marketplace/plugins/my-plugin/.claude-plugin/plugin.json << 'EOF'
{
  "name": "my-plugin",
  "description": "My plugin",
  "version": "1.0.0"
}
EOF

# スキル
cat > my-marketplace/plugins/my-plugin/skills/hello/SKILL.md << 'EOF'
---
description: Say hello
disable-model-invocation: true
---
Say hello to the user.
EOF
```

### 4. テスト

```shell
/plugin marketplace add ./my-marketplace
/plugin install my-plugin@my-marketplace
```

---

## 配布方法

### GitHub（推奨）

1. リポジトリを作成
2. `.claude-plugin/marketplace.json`を配置
3. ユーザーは以下で追加：

```shell
/plugin marketplace add owner/repo
```

### GitLab/Bitbucket/自己ホスト

```shell
/plugin marketplace add https://gitlab.com/company/plugins.git
```

### ローカルパス

```shell
/plugin marketplace add ./my-marketplace
```

### リモートURL

```shell
/plugin marketplace add https://example.com/marketplace.json
```

> **制限**: URLベースでは相対パスソースが動作しない。

---

## プライベートリポジトリ

認証トークンを環境変数で設定：

```bash
# GitHub
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# GitLab
export GITLAB_TOKEN=glpat-xxxxxxxxxxxx

# Bitbucket
export BITBUCKET_TOKEN=xxxxxxxxxxxx
```

---

## チーム配布

### リポジトリ設定

`.claude/settings.json`に追加：

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
    "linter@team-plugins": true,
    "formatter@team-plugins": true
  }
}
```

### 自動更新

マーケットプレイスごとに自動更新を設定可能：
1. `/plugin`を実行
2. **Marketplaces**タブを選択
3. マーケットプレイスを選択
4. **Enable auto-update** / **Disable auto-update**を選択

---

## 管理者制限

### strictKnownMarketplaces

管理者は`managed-settings.json`で許可リストを設定：

```json
{
  "strictKnownMarketplaces": [
    {
      "source": "github",
      "repo": "company/approved-plugins"
    }
  ]
}
```

| 値 | 動作 |
|:---|:-----|
| 未定義 | 制限なし |
| 空配列 `[]` | 新規追加を完全禁止 |
| ソースリスト | 許可リストのみ追加可能 |

---

## プラグインエントリの詳細設定

### strict フラグ

| 値 | 動作 |
|:---|:-----|
| `true`（デフォルト） | プラグインにplugin.jsonが必要。マーケットプレイスエントリはマージ。 |
| `false` | plugin.json不要。マーケットプレイスエントリで全て定義。 |

シンプルなプラグインは`strict: false`で完全にmarketplace.jsonで定義可能：

```json
{
  "name": "simple-plugin",
  "source": "./plugins/simple",
  "description": "A simple plugin",
  "version": "1.0.0",
  "skills": ["./plugins/simple/skills/"],
  "strict": false
}
```

### コンポーネントパス指定

```json
{
  "name": "complex-plugin",
  "source": "./plugins/complex",
  "commands": [
    "./plugins/complex/commands/core/",
    "./plugins/complex/commands/advanced/"
  ],
  "agents": [
    "./plugins/complex/agents/reviewer.md"
  ],
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/validate.sh"
          }
        ]
      }
    ]
  },
  "strict": false
}
```

---

## トラブルシューティング

### マーケットプレイスがロードされない

1. URLがアクセス可能か確認
2. `.claude-plugin/marketplace.json`が存在するか確認
3. JSON構文を確認

### プラグインインストール失敗

1. プラグインソースURLがアクセス可能か確認
2. プライベートリポジトリの場合、認証トークンを確認
3. plugin.json構文を確認

### 相対パスが動作しない

URLベースのマーケットプレイスでは相対パスが動作しない。解決策：
1. Gitベースのマーケットプレイスを使用
2. GitHub/GitLab/git URLソースを使用

### ファイルが見つからない

プラグインはキャッシュにコピーされるため、外部参照（`../`）は動作しない。解決策：
1. シンボリックリンクを使用（コピー時に追従）
2. マーケットプレイスのソースパスを親ディレクトリに設定

---

## 検証

### 構文検証

```bash
claude plugin validate ./my-marketplace
```

または：

```shell
/plugin validate ./my-marketplace
```

### 一般的なエラー

| エラー | 原因 | 解決策 |
|:-------|:-----|:-------|
| `File not found` | marketplace.jsonなし | ファイルを作成 |
| `Invalid JSON syntax` | JSON構文エラー | カンマ、クォートを確認 |
| `Duplicate plugin name` | 同名プラグイン | 一意な名前に変更 |
| `Path traversal not allowed` | `..`を含むパス | 相対パスに修正 |
