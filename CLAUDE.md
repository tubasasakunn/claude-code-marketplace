# Claude Code Marketplace

Claude Code プラグインのマーケットプレイスです。

## プラグイン一覧

- `claude-code-plugin` - Claude Codeの機能拡張スキル集
- `ios-develop-plugin` - iOS/Swift開発支援プラグイン
- `design-plugin` - デザインレビュープラグイン
- `common-plugin` - 汎用的な開発支援プラグイン

---

## プラグインのインストール方法

### 1. マーケットプレイスを追加

```
/plugin marketplace add ~/workspace/claude-code-marketplace
```

### 2. プラグインをインストール

```
/plugin install <plugin-name>@claude-code-marketplace
```

例：
```
/plugin install ios-develop-plugin@claude-code-marketplace
/plugin install common-plugin@claude-code-marketplace
```

### 3. Claude Codeを再起動

インストール後、Claude Codeを再起動してプラグインを読み込む

### よく使うコマンド

| 操作 | コマンド |
|------|---------|
| マーケットプレイス追加 | `/plugin marketplace add <path>` |
| マーケットプレイス削除 | `/plugin marketplace remove <name>` |
| プラグインインストール | `/plugin install <name>@<marketplace>` |
| プラグインアンインストール | `/plugin uninstall <name>@<marketplace>` |
| 対話メニュー | `/plugin` |

---

## プラグイン作成手順

### 1. 雛形の作成

**必ず`plugin-guide`スキルを使用する：**

```
Skill: plugin-guide
```

スキルの指示に従い、以下の最小構成を作成：

```
<plugin-name>/
└── .claude-plugin/
    └── plugin.json
```

> **重要**: 最初は雛形のみ作成し、中身（skills, agents, commands等）は後から追加する

### 1.5. marketplace.jsonへの登録

**プラグイン作成後、必ず`.claude-plugin/marketplace.json`の`plugins`配列に追加する：**

```json
{
  "plugins": [
    // 既存のプラグイン...
    {
      "name": "<plugin-name>",
      "source": "./<plugin-name>",
      "description": "プラグインの説明"
    }
  ]
}
```

> **重要**: この登録を忘れると`/plugin install`でプラグインが見つからないエラーになる

---

### 2. コンポーネントの追加

各コンポーネントを追加する際は、**対応するスキルを必ず使用する**：

| 追加するもの | 使用するスキル | 保存先 |
|---|---|---|
| スキル | `skill-creator` | `skills/<name>/SKILL.md` |
| サブエージェント | `subagent-creator` | `agents/<name>.md` |
| スラッシュコマンド | `slash-command-creator` | `commands/<name>.md` |
| フック | `hooks-guide` | `hooks/hooks.json` |
| MCPサーバー | - | `.mcp.json` |

#### スキルの作成

```
Skill: skill-creator
```

→ 知識ベースとなるSKILL.mdを作成

#### サブエージェントの作成

```
Skill: subagent-creator
```

→ 特化したタスクを実行するエージェントを定義

#### スラッシュコマンドの作成

```
Skill: slash-command-creator
```

→ `/command-name`で呼び出せるコマンドを作成

#### フックの作成

```
Skill: hooks-guide
```

→ イベントベースの自動化を設定

---

### 3. 完成したプラグイン構成例

```
<plugin-name>/
├── .claude-plugin/
│   └── plugin.json           # 必須：プラグインメタデータ
├── .mcp.json                 # 任意：MCPサーバー設定
├── agents/                   # 任意：サブエージェント
│   └── <agent-name>.md
├── commands/                 # 任意：スラッシュコマンド
│   └── <command-name>.md
├── skills/                   # 任意：スキル
│   └── <skill-name>/
│       └── SKILL.md
└── hooks/                    # 任意：フック
    └── hooks.json
```

---

## 作成時の原則

1. **スキルファーストで作成する**
   - 必ず対応するスキルを読み込んでから作成
   - スキルなしで手動作成しない

2. **雛形から始める**
   - 最初は最小構成（plugin.jsonのみ）
   - 必要なコンポーネントを順次追加

3. **一度に一つずつ追加**
   - 複数のコンポーネントを同時に作らない
   - 各コンポーネントを作成後、動作確認

4. **スキル間の連携を意識**
   - サブエージェントからスキルを読み込む設計
   - 例：`ios-implementer`エージェントが`ios-develop`スキルを読み込む

5. **プラグイン更新後は必ずバージョンをアップデート**
   - `plugin.json`の`version`フィールドを更新する
   - セマンティックバージョニング（major.minor.patch）に従う
   - 破壊的変更: major、機能追加: minor、バグ修正: patch
