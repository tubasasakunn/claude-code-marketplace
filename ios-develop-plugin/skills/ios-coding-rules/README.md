# ios-coding-rules

mylibraryプロジェクト向けiOSアプリのコーディング規約スキル。

## 概要

iOS/SwiftUIアプリ開発のためのコーディング規約を提供します。ファイル配置、命名規則、SwiftUI、SwiftData、API連携のルールを網羅的にカバーします。

## 使用方法

`/ios-coding-rules <タスク|コード|ファイル>`

```
/ios-coding-rules 新しいViewModelを作成
/ios-coding-rules このコードをレビュー
```

## モード

### 実装モード
「実装」「作成」「追加」キーワードで起動
1. REFERENCE.md確認
2. 既存パターン参照
3. 実装
4. CHECKLIST.mdでチェック

### レビューモード
「レビュー」「チェック」キーワードで起動
1. コード取得
2. CHECKLIST.mdでチェック
3. 違反箇所と修正案を出力

## 主要ルール

| 項目 | NG | OK |
|------|----|----|
| Spacing | `spacing: 16` | `DesignTokens.Spacing.lg` |
| Color | `Color.white` | `Color.textPrimary` |
| ツールバー | ZStackオーバーレイ | `.toolbar { ToolbarItem }` |
| データ保存 | API優先 | ローカルファースト |

## 関連ドキュメント

| ファイル | 内容 |
|----------|------|
| SKILL.md | スキル本体 |
| ARCHITECTURE.md | ディレクトリ構成、レイヤー設計 |
| NAMING-STYLE.md | 命名規則、コードスタイル |
| SWIFTUI.md | View構成、モディファイア |
| SWIFTDATA-API.md | SwiftData、API連携 |
| VIEWMODEL.md | ViewModel、依存性注入 |
| CHECKLIST.md | 実装・レビューチェックリスト |
| REFERENCE.md | 全規約一覧 |
