# ベストプラクティス

効果的なプラグインを作成するための実践的なガイドラインです。

---

## 目次

- コア原則
- プラグイン設計
- コンポーネント設計
- セキュリティ
- バージョン管理
- チーム配布
- 避けるべきアンチパターン
- チェックリスト

---

## コア原則

### 1. シンプルに保つ

**最小限のコンポーネントで始める**:
- まず雛形（plugin.jsonのみ）を作成
- 必要なコンポーネントを1つずつ追加
- 動作確認してから次へ

**各コンポーネントの責務を明確に**:
- 1つのスキル = 1つの機能
- エージェントは特定の領域に特化
- フックは単一のイベントに対応

### 2. 名前空間を意識

プラグインのスキルは自動的に名前空間化されます：

| プラグイン名 | スキル名 | 呼び出し |
|:-------------|:---------|:---------|
| `my-plugin` | `hello` | `/my-plugin:hello` |
| `code-tools` | `review` | `/code-tools:review` |

**命名のベストプラクティス**:
- プラグイン名は機能を表す（`deployment-tools`）
- スキル名は動作を表す（`deploy`、`rollback`）
- 一貫した命名規則を使用

### 3. 環境変数を活用

プラグイン内のパスには必ず`${CLAUDE_PLUGIN_ROOT}`を使用：

```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check.sh"
}
```

**理由**: プラグインはキャッシュディレクトリにコピーされるため、相対パスは動作しない。

---

## プラグイン設計

### ディレクトリ構造

**良い例**:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json      # ここにのみ配置
├── skills/              # プラグインルート
├── agents/              # プラグインルート
└── hooks/               # プラグインルート
```

**悪い例**:
```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json
│   ├── skills/          # NG: .claude-plugin内
│   └── hooks/           # NG: .claude-plugin内
```

### スキル vs コマンド

| コンポーネント | 形式 | 用途 |
|:---------------|:-----|:-----|
| スキル（推奨） | `skills/<name>/SKILL.md` | 複雑な指示、参照ファイル、スクリプト |
| コマンド | `commands/<name>.md` | シンプルな単一ファイル指示（レガシー） |

**推奨**: 新規作成は`skills/`を使用。`commands/`はレガシー互換。

### 段階的開示

大きなプラグインは参照ファイルで分割：

```
skills/complex-skill/
├── SKILL.md           # 概要とナビゲーション（500行以下）
├── REFERENCE.md       # 詳細リファレンス
├── PATTERNS.md        # パターン集
└── scripts/           # ユーティリティ
```

**SKILL.mdでの参照**:
```markdown
詳細は[REFERENCE.md](REFERENCE.md)を参照。
```

---

## コンポーネント設計

### スキル設計

**description は具体的に**:

良い例:
```yaml
description: PDFファイルからテキストと表を抽出し、フォームに入力します。PDF、フォーム、ドキュメント抽出について言及された場合に使用してください。
```

悪い例:
```yaml
description: ドキュメントを処理します
```

**呼び出し制御を適切に設定**:

| ユースケース | 設定 |
|:-------------|:-----|
| 通常のスキル | デフォルト |
| 副作用のある操作（デプロイ等） | `disable-model-invocation: true` |
| バックグラウンド知識 | `user-invocable: false` |

### エージェント設計

**特定の領域に特化**:
- `migration-planner`: DBマイグレーション
- `security-reviewer`: セキュリティ分析
- `architect`: アーキテクチャ設計

**能力を明示**:
```yaml
capabilities: ["schema-analysis", "migration-planning", "rollback-design"]
```

### フック設計

**`${CLAUDE_PLUGIN_ROOT}`を必ず使用**:

良い例:
```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/lint.sh $CLAUDE_FILE_PATH"
}
```

悪い例:
```json
{
  "command": "./scripts/lint.sh $CLAUDE_FILE_PATH"
}
```

**スクリプトは実行可能に**:
```bash
chmod +x scripts/*.sh
```

---

## セキュリティ

### 機密情報の扱い

- APIキー、パスワードをハードコードしない
- 環境変数参照を使用：`${API_KEY}`
- `.gitignore`に機密ファイルを追加

### ファイルアクセス

- `allowed-tools`でツールを制限
- 読み取り専用操作は`Read, Grep, Glob`のみ許可
- 破壊的な操作には警告を含める

### 外部通信

- 不要な外部URLアクセスを避ける
- MCPサーバーの信頼性を確認
- 環境変数でURLを設定可能に

---

## バージョン管理

### セマンティックバージョニング

```
MAJOR.MINOR.PATCH
```

- **MAJOR**: 破壊的変更（互換性なし）
- **MINOR**: 新機能追加（後方互換）
- **PATCH**: バグ修正（後方互換）

### バージョン更新タイミング

| 変更 | バージョン |
|:-----|:-----------|
| スキル追加 | MINOR |
| バグ修正 | PATCH |
| スキル名変更 | MAJOR |
| 必須引数追加 | MAJOR |

### CHANGELOG

変更履歴を`CHANGELOG.md`で管理：

```markdown
# Changelog

## [2.0.0] - 2026-01-25
### Breaking Changes
- スキル名を`review`から`code-review`に変更

### Added
- 新しいスキル`security-scan`

### Fixed
- フックのパス解決問題を修正
```

---

## チーム配布

### リポジトリ設定

`.claude/settings.json`でチーム標準を設定：

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

### プライベートリポジトリ

認証トークンを環境変数で設定：

| プロバイダー | 環境変数 |
|:-------------|:---------|
| GitHub | `GITHUB_TOKEN` または `GH_TOKEN` |
| GitLab | `GITLAB_TOKEN` または `GL_TOKEN` |
| Bitbucket | `BITBUCKET_TOKEN` |

### マーケットプレイス制限

管理者は`strictKnownMarketplaces`で許可リストを設定可能：

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

---

## 避けるべきアンチパターン

### 1. .claude-plugin内にコンポーネント配置

❌ 悪い例:
```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json
│   └── skills/        # NG
```

✅ 良い例:
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json
└── skills/            # OK
```

### 2. 絶対パスの使用

❌ 悪い例:
```json
{
  "command": "/Users/dev/plugins/my-plugin/scripts/check.sh"
}
```

✅ 良い例:
```json
{
  "command": "${CLAUDE_PLUGIN_ROOT}/scripts/check.sh"
}
```

### 3. パストラバーサル

❌ 悪い例:
```json
{
  "source": "../shared-utils"
}
```

✅ 良い例:
```
# シンボリックリンクを使用
ln -s /path/to/shared-utils ./shared-utils
```

### 4. 機密情報のハードコード

❌ 悪い例:
```json
{
  "env": {
    "API_KEY": "sk-1234567890abcdef"
  }
}
```

✅ 良い例:
```json
{
  "env": {
    "API_KEY": "${API_KEY}"
  }
}
```

### 5. 過度に複雑なプラグイン

❌ 悪い例:
- 1つのプラグインに20個のスキル
- すべての機能を1つにまとめる

✅ 良い例:
- 機能ごとにプラグインを分割
- 各プラグインは3-5個のスキル

---

## 効果的なプラグインのチェックリスト

### 構造
- [ ] `.claude-plugin/plugin.json`のみがマニフェストディレクトリ内
- [ ] コンポーネントはプラグインルートに配置
- [ ] 相対パスを使用（`./`で開始）
- [ ] `${CLAUDE_PLUGIN_ROOT}`をスクリプトパスに使用

### 品質
- [ ] スキルのdescriptionが具体的
- [ ] 三人称で記述
- [ ] SKILL.mdが500行以下
- [ ] 参照は1レベルの深さまで

### セキュリティ
- [ ] 機密情報がハードコードされていない
- [ ] 環境変数参照を使用
- [ ] `allowed-tools`で適切に制限

### 配布
- [ ] セマンティックバージョニング
- [ ] CHANGELOGを維持
- [ ] READMEにインストール手順
