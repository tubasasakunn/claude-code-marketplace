---
name: ios-app-guide
description: SwiftUI + SwiftDataを使ったiOSアプリの開発手順・アーキテクチャ・注意点のガイドラインを提供します。iOSアプリの新規開発、プロジェクト構成、開発フェーズの進め方について質問された場合に使用してください。
context: fork
agent: general-purpose
argument-hint: <質問 または 開発フェーズ>
allowed-tools:
  - Read
  - Glob
  - Grep
---

# iOS アプリ開発ガイド

SwiftUI + SwiftData + Cloudflare Workers によるiOSアプリ開発の手順・パターン・注意点。
Filmi (mymovie) の30コミット・8フェーズの開発プロセスから抽出した再利用可能なガイドライン。

## ユーザーの質問に回答する

`$ARGUMENTS` の内容に基づいて、以下の参照ドキュメントから適切な情報を選択し回答する。

## 開発の順序（鉄則）

```
1. プロジェクト作成 + .gitignore + CLAUDE.md
2. Core 層（Models, Network, Services）
3. 基本画面（Home, Add, Detail, Edit）
4. デザインシステム（DesignTokens, Color+Theme）
5. テーマシステム
6. バックエンド API + 同期サービス
7. オンボーディング
8. ユーザーシステム + ソーシャル機能
9. デザイン統一（セマンティックカラー適用）
10. ナビバー・検索バーのポリッシュ
11. ブランディング（アイコン、表示名、法的リンク）
12. 最終 UI 微調整
```

**鉄則:** 機能を先に作り、デザインの微調整は最後にまとめて行う。

## プロジェクト初期設定チェックリスト

```
[ ] .gitignore 作成（node_modules, DerivedData, .DS_Store, *.xcuserstate）
[ ] Bundle ID / Development Team / Deployment Target 設定
[ ] CLAUDE.md / README.md 作成
[ ] DesignTokens.swift 作成（スペーシング・角丸・グリッド定数）
[ ] Color+Theme.swift 作成（セマンティックカラー）
[ ] APIClient.swift 作成（singleton + Sendable）
[ ] Endpoint プロトコル作成
[ ] SwiftData モデル作成（@Attribute(.unique)）
```

## クイックリファレンス: よくあるミス

| ミス | 対処法 |
|------|--------|
| `.gitignore` 未設定 | プロジェクト作成直後に設定 |
| SwiftData フィールドにデフォルト値なし | 新フィールドには必ずデフォルト値 |
| `import SwiftData` 忘れ | 使う全ファイルに追加 |
| ナビバー背景が消えない | UIAppearance + toolbarBackgroundVisibility |
| .searchable の背景色 | カスタム SearchBar コンポーネント |
| UI が固まる | `Task.detached` で fire-and-forget |

## 詳細ドキュメント

| ドキュメント | 内容 |
|:-------------|:-----|
| [PHASES.md](PHASES.md) | 8フェーズの開発手順と教訓 |
| [ARCHITECTURE.md](ARCHITECTURE.md) | MVVM + @Observable、Endpoint、同期パターン |
| [SWIFTUI-SWIFTDATA.md](SWIFTUI-SWIFTDATA.md) | SwiftUI / SwiftData の注意点とパターン |
| [DESIGN-SYSTEM.md](DESIGN-SYSTEM.md) | DesignTokens、セマンティックカラー、テーマ |
| [NAVIGATION-UIKIT.md](NAVIGATION-UIKIT.md) | ナビバー透過、カスタムSearchBar |
| [API-SYNC.md](API-SYNC.md) | Hono + Workers、iOS同期、Zodバリデーション |
| [TESTING.md](TESTING.md) | Maestro自動化、スクリーンショット撮影 |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | UI・API・同期のよくある問題と解決策 |
| [DIRECTORY.md](DIRECTORY.md) | 推奨ディレクトリ構成 |
