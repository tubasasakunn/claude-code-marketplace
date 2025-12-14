# Claude Code Marketplace

Claude Code プラグインのマーケットプレイスです。

## インストール方法

### 1. マーケットプレイスを追加

```bash
/plugin marketplace add tubasasakunn/claude-code-marketplace
```

### 2. プラグインをインストール

```bash
/plugin install <plugin-name>@claude-code-marketplace
```

### 3. Claude Code を再起動

インストール後、Claude Code を再起動してプラグインを有効化します。

---

## プラグイン一覧

| プラグイン | 説明 |
|-----------|------|
| [claude-code-plugin](#claude-code-plugin) | Claude Code の機能拡張スキル集 |
| [ios-develop-plugin](#ios-develop-plugin) | iOS/Swift 開発支援プラグイン |
| [design-plugin](#design-plugin) | デザインレビュープラグイン |
| [common-plugin](#common-plugin) | 汎用的な開発支援プラグイン |

---

## claude-code-plugin

Claude Code 自体の機能を拡張するためのスキル集です。

### インストール

```bash
/plugin install claude-code-plugin@claude-code-marketplace
```

### 含まれるスキル

| スキル | 説明 | 使い方 |
|--------|------|--------|
| `claude-code-guide` | Claude Code の仕様・設定・機能のガイド | `Skill: claude-code-guide` |
| `slash-command-creator` | カスタムスラッシュコマンドの作成支援 | `Skill: slash-command-creator` |
| `subagent-creator` | カスタムサブエージェントの作成支援 | `Skill: subagent-creator` |
| `skill-creator` | カスタムスキルの作成支援 | `Skill: skill-creator` |
| `plugin-guide` | プラグインの作成・管理ガイド | `Skill: plugin-guide` |
| `hooks-guide` | フック（イベントハンドラー）の作成支援 | `Skill: hooks-guide` |

### 使用例

```
Claude Code でスラッシュコマンドを作りたい
→ Skill: slash-command-creator が自動的に呼び出されます
```

---

## ios-develop-plugin

iOS 17+ / Swift 5.9+ のベストプラクティスに基づいた開発支援プラグインです。

### インストール

```bash
/plugin install ios-develop-plugin@claude-code-marketplace
```

### 含まれるスキル

| スキル | 説明 | 使い方 |
|--------|------|--------|
| `ios-develop` | SwiftUI、@Observable、NavigationStack、ローカライズ、MVVM、Asset Catalog、Liquid Glass デザインなどのベストプラクティス | `Skill: ios-develop-plugin:ios-develop` |

### 含まれるエージェント

| エージェント | 説明 |
|-------------|------|
| `ios-implementer` | iOS/Swift 実装の専門エージェント。全体最適化を重視し、コードの整合性・一貫性を保ちながら実装 |
| `ios-reviewer` | iOS/Swift コードレビューの専門エージェント。ベストプラクティスに即しているかを検証 |
| `ios-screenshot` | iOS アプリの起動とスクリーンショット取得の専門エージェント。シミュレーターで Maestro を使って操作・撮影 |

### 使用例

```
SwiftUI で新しい画面を作りたい
→ ios-implementer エージェントが自動的に実装を行います

コードレビューをして
→ ios-reviewer エージェントがレビューを行います

アプリのスクリーンショットを撮って
→ ios-screenshot エージェントがシミュレーターを操作して撮影します
```

---

## design-plugin

モバイルアプリの UI/UX デザインレビューを支援するプラグインです。

### インストール

```bash
/plugin install design-plugin@claude-code-marketplace
```

### 含まれるスキル

| スキル | 説明 | 使い方 |
|--------|------|--------|
| `mobile-ui-design` | モバイルアプリ UI/UX デザインの包括的原則と品質基準 | `Skill: design-plugin:mobile-ui-design` |
| `ui-critique` | UI デザインの「ダサさ」「違和感」を言語化し、修正可能な指摘に変換 | `Skill: design-plugin:ui-critique` |

### 含まれるエージェント

| エージェント | 説明 |
|-------------|------|
| `design-reviewer` | モバイルアプリ UI デザインの画像をレビューし、問題点を指摘して点数評価 |

### 使用例

```
この UI がなんとなくダサいんだけど、何が問題？
→ ui-critique スキルが具体的な問題点を言語化します

スクリーンショットをレビューして
→ design-reviewer エージェントがデザインを評価します
```

---

## common-plugin

言語やフレームワークに依存しない、汎用的な開発支援プラグインです。

### インストール

```bash
/plugin install common-plugin@claude-code-marketplace
```

### 含まれるスキル

| スキル | 説明 | 使い方 |
|--------|------|--------|
| `troubleshooting-capture` | トラブルシューティング時の情報収集支援 | `Skill: common-plugin:troubleshooting-capture` |

### 含まれるエージェント

| エージェント | 説明 |
|-------------|------|
| `investigator` | バグの原因調査や実装方法の調査を行う専門家。問題点やエラーの報告を受けた時、実装方法がわからない時に使用 |
| `slack-notifier` | Slack へのメッセージ送信・画像アップロードを行う専門家。作業完了通知、スクリーンショット共有、レポート送信時に使用（環境変数 `SLACK_TOKEN` と `SLACK_CHANNEL_ID` が必要） |

### 含まれるコマンド

| コマンド | 説明 | 使い方 |
|---------|------|--------|
| `/implement` | 機能実装を要件に基づいて実装・レビューを反復して完成させる | `/common-plugin:implement [要件]` |
| `/ui-implement` | UI 実装を要件に基づいて実装・レビュー・評価を反復して完成させる | `/common-plugin:ui-implement [要件]` |
| `/refactor` | 現在の差分を確認し、コード全体を見てリファクタリング | `/common-plugin:refactor [方針]` |
| `/fix-issues` | 指摘事項を修正する | `/common-plugin:fix-issues` |

### 使用例

```
/common-plugin:implement ユーザー認証機能を追加
→ 実装とレビューを繰り返して完成させます

このエラーの原因を調べて
→ investigator エージェントが調査します

作業が終わったら Slack に通知して
→ slack-notifier エージェントが通知を送信します
```

---

## よく使うコマンド

| 操作 | コマンド |
|------|---------|
| マーケットプレイス一覧 | `/plugin marketplace list` |
| マーケットプレイス追加 | `/plugin marketplace add <owner/repo>` |
| マーケットプレイス削除 | `/plugin marketplace remove <name>` |
| プラグインインストール | `/plugin install <name>@<marketplace>` |
| プラグインアンインストール | `/plugin uninstall <name>@<marketplace>` |
| 対話メニュー | `/plugin` |

---

## ライセンス

MIT License
