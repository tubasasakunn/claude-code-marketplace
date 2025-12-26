---
name: ios-coding-rules
description: mylibrary iOSアプリのコーディング規約を提供します。ファイル配置、命名規則、SwiftUI、SwiftData、API連携のルールを含みます。iOS実装、コードレビュー、新規ファイル作成時に使用してください。
---

# iOS Coding Rules - mylibrary

mylibraryプロジェクトのコーディング規約です。

## クイックリファレンス

### ディレクトリ構成

```
mylibrary/
├── App/                     # アプリエントリーポイント
├── Core/                    # データ層・インフラ
│   ├── Models/              # SwiftDataモデル
│   ├── Network/             # API通信基盤
│   ├── Repositories/        # データアクセス層
│   └── Sync/                # 同期処理
├── Features/                # 機能別モジュール
│   └── {FeatureName}/
│       ├── Components/      # 機能固有のコンポーネント
│       ├── {FeatureName}View.swift
│       └── {FeatureName}ViewModel.swift
├── DesignSystem/            # UIコンポーネント・スタイル
│   ├── Theme/               # 色、フォント、アニメーション
│   ├── Components/          # 再利用可能なUIコンポーネント
│   └── Extensions/          # View拡張
├── Services/                # ドメインサービス
└── Resources/               # アセット
```

### ファイル配置判断フロー

| 新規ファイルの種類 | 配置先 |
|------------------|--------|
| SwiftDataの@Model | `Core/Models/` |
| API通信関連 | `Core/Network/` |
| データ取得・保存の抽象化 | `Core/Repositories/` |
| 特定画面専用のView | `Features/{機能名}/` |
| 複数画面で使うUI | `DesignSystem/Components/` |
| ViewModel | `Features/{機能名}/` |
| View拡張・モディファイア | `DesignSystem/Extensions/` |
| 色・フォント・定数 | `DesignSystem/Theme/` |
| ビジネスロジック | `Services/` |

### 禁止事項

- `Features/` 直下にファイルを置かない
- `Core/` に UI 関連のコードを置かない
- `DesignSystem/` にビジネスロジックを含めない
- ルートディレクトリにSwiftファイルを置かない

## 基本原則

### 1. ファイルサイズ制限

| ファイル種別 | 推奨上限 | 絶対上限 |
|-------------|---------|---------|
| View | 200行 | 300行 |
| ViewModel | 250行 | 400行 |
| Model | 100行 | 150行 |
| 関数 | 30行 | 50行 |

### 2. 命名規則

```swift
// ファイル名
{機能名}View.swift          // View
{機能名}ViewModel.swift     // ViewModel
{名詞}.swift                // Model
{型名}+{機能}.swift         // Extension

// 変数名
let bookTitle: String       // キャメルケース
var isLoading: Bool         // Bool は is/has/can/should で始める
private let apiClient       // private は明示
```

### 3. ViewModel のルール

```swift
@Observable
@MainActor
final class BookDetailViewModel {
    // プロパティは自動的に監視される
    var book: Book?
    var isLoading = false

    // 依存性注入
    private let repository: BookRepositoryProtocol

    init(repository: BookRepositoryProtocol = BookRepository.shared) {
        self.repository = repository
    }
}
```

### 4. DesignTokensの使用（ハードコード禁止）

```swift
// Bad
VStack(spacing: 16) { }
.padding(24)
.cornerRadius(12)

// Good
VStack(spacing: DesignTokens.Spacing.lg) { }
.padding(DesignTokens.Spacing.xxl)
.clipShape(RoundedRectangle(cornerRadius: DesignTokens.CornerRadius.inputField))
```

| カテゴリ | 値 |
|---------|-----|
| Spacing | `.xxs`(2), `.xs`(4), `.sm`(8), `.md`(12), `.lg`(16), `.xl`(20), `.xxl`(24) |
| CornerRadius | `.minimal`(4), `.small`(8), `.inputField`(12), `.tile`(16), `.card`(24) |

### 5. セマンティックカラーの使用（直接色指定禁止）

```swift
// Bad
Color.white
Color.black
.foregroundStyle(.white)

// Good
Color.textPrimary
Color.backgroundPrimary
.foregroundStyle(Color.cameraText)
```

### 6. ツールバー実装（ZStackオーバーレイ禁止）

```swift
// Bad: ZStackでカスタムツールバー（fullScreenCover dismiss後にバグ）
NavigationStack {
    ZStack(alignment: .topTrailing) {
        content
        HStack { Button("Settings") { } }
    }
}

// Good: 標準の.toolbarモディファイア
NavigationStack {
    content
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Settings") { }
            }
        }
        .toolbarBackground(.visible, for: .navigationBar)
}
```

### 7. ローカルファースト戦略

```swift
@MainActor
func saveBook(_ book: Book, modelContext: ModelContext) async {
    // 1. ローカルに即座に保存
    modelContext.insert(book)
    try? modelContext.save()

    // 2. APIに非同期で同期
    do {
        try await apiClient.request(endpoint)
    } catch {
        // 3. 失敗時は PendingOperation として保存
        let pending = PendingOperationFactory.upsertBook(...)
        modelContext.insert(pending)
    }
}
```

### 8. SwiftDataの@Query

```swift
// 常にソート順序を明示
@Query(sort: \Book.addedAt, order: .reverse)
private var books: [Book]
```

## 詳細リファレンス

詳細なルールは以下を参照:
- [REFERENCE.md](REFERENCE.md) - 完全なコーディング規約
- [CHECKLIST.md](CHECKLIST.md) - シーン別チェックリスト

## View構成の標準順序

```swift
struct FeatureView: View {
    // 1. @Bindable ViewModel
    @Bindable var viewModel: FeatureViewModel

    // 2. @Binding 親からのバインディング
    @Binding var isPresented: Bool

    // 3. let/var 外部プロパティ
    let initialValue: String

    // 4. @State ローカル状態
    @State private var isLoading = false

    // 5. @Environment 環境値
    @Environment(\.dismiss) private var dismiss

    // 6. @Query SwiftDataクエリ
    @Query private var items: [Item]

    // 7. Body
    var body: some View { }
}
```

## MARKセクション順序

```swift
// MARK: - Properties
// MARK: - State
// MARK: - Environment
// MARK: - Initializer
// MARK: - Body
// MARK: - Subviews
// MARK: - Private Methods
// MARK: - Preview
```

## エラーハンドリング

```swift
do {
    result = try await apiClient.request(endpoint)
} catch let error as APIError {
    switch error {
    case .conflict:
        // 409: 既存データとして成功扱い
        return
    case .notFound:
        errorMessage = "データが見つかりませんでした"
    default:
        savePendingOperation(...)
    }
} catch {
    savePendingOperation(...)
}
```

## ログ出力形式

```swift
print("[クラス名] メッセージ: \(詳細)")
// 例
print("[BookRepository] Book saved: isbn=\(isbn)")
print("[SyncManager] Failed to sync: \(error.localizedDescription)")
```
