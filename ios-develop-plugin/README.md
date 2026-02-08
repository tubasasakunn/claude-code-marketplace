# ios-develop-plugin

iOS/Swift開発を支援するClaude Codeプラグイン。

## インストール

```bash
/plugin install ios-develop-plugin@tubasasakunn-marketplace
```

## スキル一覧

| スキル | 説明 | 呼び出し方 |
|--------|------|------------|
| [ios-coding-rules](skills/ios-coding-rules/) | mylibraryプロジェクトのコーディング規約 | `/ios-coding-rules <タスク>` |
| [ios-design](skills/ios-design/) | iOS/SwiftUIデザインレビュー | `/ios-design <画像/コード>` |
| [ios-testing](skills/ios-testing/) | MaestroによるUIテスト・スクリーンショット | `/ios-testing <要件>` |
| [ios-app-guide](skills/ios-app-guide/) | iOSアプリ開発手順・アーキテクチャガイド | `/ios-app-guide <質問>` |

## 使用例

### コーディング規約

```
/ios-coding-rules 新しいViewModelを作成
/ios-coding-rules このViewをレビュー
```

### デザインレビュー

```
/ios-design screenshots/home.png
/ios-design Features/Home/HomeView.swift
```

### UIテスト

```
/ios-testing ログイン画面のスクリーンショットを撮影
/ios-testing 設定画面への遷移をテスト
```

### アプリ開発ガイド

```
/ios-app-guide 新しいiOSアプリの開発手順を教えて
/ios-app-guide SwiftDataのマイグレーション注意点
/ios-app-guide ナビバーの透過設定方法
```

## 機能詳細

### ios-coding-rules

- ファイル配置ルール（Core/, Features/, DesignSystem/）
- 命名規則とコードスタイル
- SwiftUI/SwiftData/API連携のベストプラクティス
- 実装モード・レビューモード

### ios-design

- HIG（Human Interface Guidelines）準拠チェック
- アクセシビリティ評価
- iOS 26 Liquid Glass実装レビュー

### ios-testing

- Maestro MCPツール統合
- テストフロー自動生成
- スクリーンショット撮影
- 最大5回リトライによる自動修正

### ios-app-guide

- 8フェーズの開発手順と教訓（Filmi実績ベース）
- MVVM + @Observable アーキテクチャパターン
- SwiftUI / SwiftData の注意点（マイグレーション、@Query等）
- デザインシステム構築（DesignTokens、セマンティックカラー、テーマ）
- ナビバー・タブバー透過の正解パターン
- Hono + Cloudflare Workers でのAPI連携
- Maestroテスト自動化

## MCPサーバー

このプラグインには以下のMCPサーバーが含まれます：

- **Maestro MCP** - iOSシミュレータのUI自動化
- **Context7 MCP** - ドキュメント検索

## バージョン

- v1.4.0
