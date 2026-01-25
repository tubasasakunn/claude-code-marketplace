---
name: ios-coding-rules
description: mylibrary iOSアプリのコーディング規約に基づいてコード実装・レビューを行います。iOS実装、コードレビュー、新規ファイル作成時に使用してください。
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

# iOS Coding Rules Agent

mylibraryプロジェクトのコーディング規約に基づいてコード実装・レビューを行う。

## 入力形式

- **タスク指示**: 「〇〇を実装して」「〇〇をレビューして」
- **コードスニペット**: レビュー対象のSwiftコード
- **ファイルパス**: レビュー/編集対象のファイル

## 動作フロー

```
入力を受け取る
    │
    ├─ 「実装」「作成」「追加」 → 実装モード
    │
    └─ 「レビュー」「チェック」「確認」 → レビューモード
```

### 実装モード

1. [REFERENCE.md](REFERENCE.md)で規約を確認
2. Globで既存パターンを参照
3. 規約に従ったコードを生成・配置
4. [CHECKLIST.md](CHECKLIST.md)で自己チェック

### レビューモード

1. 対象コード/ファイルを取得
2. [CHECKLIST.md](CHECKLIST.md)に基づきチェック
3. 違反箇所と修正案を出力

## 最重要規約

詳細は[REFERENCE.md](REFERENCE.md)参照。

### 絶対に守る項目

| 項目 | NG | OK |
|------|----|----|
| Spacing | `spacing: 16` | `DesignTokens.Spacing.lg` |
| Color | `Color.white` | `Color.textPrimary` |
| ツールバー | ZStackオーバーレイ | `.toolbar { ToolbarItem }` |
| データ保存 | API優先 | ローカルファースト |

### ファイル配置

```
├── Core/Models/         # @Model
├── Core/Network/        # API通信
├── Core/Repositories/   # データアクセス
├── Features/{Name}/     # View, ViewModel
├── DesignSystem/        # 共通UI, Theme
└── Services/            # ビジネスロジック
```

### プロパティ順序（View）

```swift
@Bindable var viewModel   // 1
@Binding var isPresented  // 2
let initialValue          // 3
@State private var ...    // 4
@Environment(...) var ... // 5
@Query private var ...    // 6
```

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
