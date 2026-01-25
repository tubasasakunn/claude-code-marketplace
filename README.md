# Claude Code Marketplace

Claude Code プラグインのマーケットプレイスです。

## インストール方法

### 1. マーケットプレイスを追加

```bash
/plugin marketplace add tubasasakunn/claude-code-marketplace
```

### 2. プラグインをインストール

```bash
/plugin install <plugin-name>@tubasasakunn-marketplace
```

### 3. Claude Code を再起動

インストール後、Claude Code を再起動してプラグインを有効化します。

---

## プラグイン一覧

| プラグイン | 説明 | スキル数 |
|-----------|------|----------|
| [claude-code-plugin](claude-code-plugin/) | Claude Code の機能拡張スキル集 | 2 |
| [ios-develop-plugin](ios-develop-plugin/) | iOS/Swift 開発支援プラグイン | 3 |
| [design-plugin](design-plugin/) | デザインレビュープラグイン | 4 |
| [common-plugin](common-plugin/) | 汎用的な開発支援プラグイン | 2 |

---

## スキル一覧

### claude-code-plugin

| スキル | 説明 |
|--------|------|
| [plugin-guide](claude-code-plugin/skills/plugin-guide/) | プラグイン作成・インストール・管理ガイド |
| [skill-creator](claude-code-plugin/skills/skill-creator/) | スキル（SKILL.md）作成ガイド |

### ios-develop-plugin

| スキル | 説明 |
|--------|------|
| [ios-coding-rules](ios-develop-plugin/skills/ios-coding-rules/) | iOSアプリのコーディング規約 |
| [ios-design](ios-develop-plugin/skills/ios-design/) | iOS/SwiftUIデザインレビュー |
| [ios-testing](ios-develop-plugin/skills/ios-testing/) | Maestro UIテスト・スクリーンショット |

### design-plugin

| スキル | 説明 |
|--------|------|
| [mobile-ui-design](design-plugin/skills/mobile-ui-design/) | モバイルUI 6カテゴリ評価 |
| [ui-critique](design-plugin/skills/ui-critique/) | UI批評 7項目100点評価 |
| [ui-ux-pro-max](design-plugin/skills/ui-ux-pro-max/) | UI/UX 10カテゴリ包括評価 |
| [ux-psychology](design-plugin/skills/ux-psychology/) | 心理学的UX 8カテゴリ評価 |

### common-plugin

| スキル | 説明 |
|--------|------|
| [commit](common-plugin/skills/commit/) | 日本語Conventional Commitsでコミット |
| [push](common-plugin/skills/push/) | リモートに安全にpush |

---

## クイックスタート

### iOS開発

```bash
/plugin install ios-develop-plugin@tubasasakunn-marketplace
```

```
/ios-coding-rules 新しいViewModelを作成
/ios-design screenshots/home.png
/ios-testing ログイン画面のスクリーンショット
```

### デザインレビュー

```bash
/plugin install design-plugin@tubasasakunn-marketplace
```

```
/ui-critique screenshots/profile.png
/ux-psychology screenshots/checkout.png
```

### Git操作

```bash
/plugin install common-plugin@tubasasakunn-marketplace
```

```
/commit
/push
```

---

## プラグイン開発

新しいプラグインを作成する場合は、claude-code-pluginをインストールして`plugin-guide`と`skill-creator`スキルを活用してください。

```bash
/plugin install claude-code-plugin@tubasasakunn-marketplace
```

```
プラグインを作成したい
スキルの書き方を教えて
```

---

## よく使うコマンド

| 操作 | コマンド |
|------|---------|
| マーケットプレイス追加 | `/plugin marketplace add <path>` |
| マーケットプレイス削除 | `/plugin marketplace remove <name>` |
| プラグインインストール | `/plugin install <name>@<marketplace>` |
| プラグインアンインストール | `/plugin uninstall <name>@<marketplace>` |
| 対話メニュー | `/plugin` |

---

## ライセンス

MIT
