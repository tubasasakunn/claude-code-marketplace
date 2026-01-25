# ios-design

iOS/SwiftUIのデザインレビューを実行するスキル。

## 概要

スクリーンショットやSwiftUIコードを入力として受け取り、以下の観点からレビューします：

- HIG（Human Interface Guidelines）準拠
- アクセシビリティ
- iOS 26 Liquid Glass実装

## 使用方法

`/ios-design <画像パス または ファイルパス>`

```
/ios-design screenshots/home.png
/ios-design Features/Home/HomeView.swift
```

## レビュー項目

### Liquid Glass適用ルール

| 適用すべき場所 | 禁止 |
|---------------|------|
| NavigationBar, TabBar, Sidebar | リストセル・カード背景 |
| Modal, FloatingControl | カスタム背景色との併用 |

### API対応表

| 確認項目 | Good | Bad |
|---------|------|-----|
| 素材 | `.glassEffect(.regular)` | `.background(.ultraThinMaterial)` |
| グループ | `GlassEffectContainer` | `HStack`/`ZStack` |
| アニメーション | `.glassEffectID()` | `.matchedGeometryEffect()` |
| 色 | `.primary`, `.secondary` | `Color.white`, `Color.black` |

## 出力形式

```markdown
## iOS Design Review

### HIG準拠 ✅/⚠️/❌
### アクセシビリティ ✅/⚠️/❌
### 実装品質 ✅/⚠️/❌

### 改善提案
1. [優先度高] ...
2. [優先度中] ...
```

## 関連ドキュメント

| ファイル | 内容 |
|----------|------|
| SKILL.md | スキル本体 |
| CHECKLIST.md | レビューチェックリスト |
| REFERENCE.md | Liquid Glass詳細 |
