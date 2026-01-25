---
name: ios-coding-rules
description: mylibrary iOSアプリのコーディング規約を提供します。ファイル配置、命名規則、SwiftUI、SwiftData、API連携のルールを含みます。iOS実装、コードレビュー、新規ファイル作成時に使用してください。
context: fork
agent: general-purpose
argument-hint: <task|code|file>
allowed-tools:
  - Read
  - Edit
  - Write
  - Glob
  - Grep
  - Bash
  - Task
---

# iOS Coding Rules

mylibraryプロジェクトのコーディング規約リファレンス。

## ワークフロー

```
入力を受け取る
    │
    ├─「実装」「作成」「追加」→ 実装モード
    │   1. REFERENCE.md確認 → 2. 既存パターン参照 → 3. 実装 → 4. CHECKLIST.mdでチェック
    │
    └─「レビュー」「チェック」→ レビューモード
        1. コード取得 → 2. CHECKLIST.mdでチェック → 3. 違反箇所と修正案を出力
```

## クイックリファレンス

### 絶対に守る項目

| 項目 | NG | OK |
|------|----|----|
| Spacing | `spacing: 16` | `DesignTokens.Spacing.lg` |
| Color | `Color.white` | `Color.textPrimary` |
| ツールバー | ZStackオーバーレイ | `.toolbar { ToolbarItem }` |
| データ保存 | API優先 | ローカルファースト |

### ファイル配置

```
Core/Models/         → @Model
Core/Network/        → API通信
Core/Repositories/   → データアクセス
Features/{Name}/     → View, ViewModel
DesignSystem/        → 共通UI, Theme
Services/            → ビジネスロジック
```

### プロパティ順序（View）

```swift
@Bindable var viewModel   // 1. ViewModel
@Binding var isPresented  // 2. バインディング
let initialValue          // 3. 外部プロパティ
@State private var ...    // 4. ローカル状態
@Environment(...) var ... // 5. 環境値
@Query private var ...    // 6. SwiftDataクエリ
```

### DesignTokens早見表

| カテゴリ | 値 |
|---------|-----|
| Spacing | `.xxs`(2), `.xs`(4), `.sm`(8), `.md`(12), `.lg`(16), `.xl`(20), `.xxl`(24) |
| CornerRadius | `.minimal`(4), `.small`(8), `.inputField`(12), `.tile`(16), `.card`(24) |
| Color | `textPrimary`, `textSecondary`, `backgroundPrimary`, `backgroundSecondary` |

## 詳細ドキュメント

| ドキュメント | 内容 |
|:-------------|:-----|
| [ARCHITECTURE.md](ARCHITECTURE.md) | ディレクトリ構成、ファイル配置、レイヤー設計 |
| [NAMING-STYLE.md](NAMING-STYLE.md) | 命名規則、コードスタイル、ドキュメンテーション |
| [SWIFTUI.md](SWIFTUI.md) | View構成、モディファイア、ナビゲーション |
| [SWIFTDATA-API.md](SWIFTDATA-API.md) | SwiftData、ローカルファースト、API連携 |
| [VIEWMODEL.md](VIEWMODEL.md) | ViewModel、依存性注入、非同期処理 |
| [CHECKLIST.md](CHECKLIST.md) | 実装・レビュー時のチェックリスト |
| [REFERENCE.md](REFERENCE.md) | 全規約の一覧（参照用） |

## 出力フォーマット

### 実装完了時

```markdown
## 実装完了

### 作成/編集ファイル
- `path/to/File.swift` - 説明

### 自己チェック
- [x] ファイル配置: OK
- [x] 命名規則: OK
- [x] DesignTokens: OK
```

### レビュー結果

```markdown
## レビュー結果

### 要約
- 規約違反: X件
- 警告: Y件

### 詳細

#### 1. [重大] ハードコード値
**箇所**: L15 `VStack(spacing: 16)`
**修正**: `VStack(spacing: DesignTokens.Spacing.lg)`
```

## 終了条件

- [ ] 実装コードがCHECKLIST.mdの該当項目をパス
- [ ] 出力フォーマットに従った報告を提示
