# iOS Coding Rules - SwiftUI

View構成、モディファイア、ナビゲーション、Previewのルール。

---

## 1. View の構成

```swift
struct FeatureView: View {
    // 1. ViewModel（@Bindable）
    @Bindable var viewModel: FeatureViewModel

    // 2. 親からのバインディング
    @Binding var isPresented: Bool

    // 3. 外部から渡されるプロパティ
    let inputData: String
    var onComplete: (() -> Void)?

    // 4. State（ローカル状態）
    @State private var isLoading = false
    @State private var showAlert = false

    // 5. Environment
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext

    // 6. Query（SwiftData）
    @Query private var items: [Item]

    // 7. Body
    var body: some View {
        // ...
    }

    // 8. Computed Subviews（private var xxx: some View）

    // 9. Private Methods
}
```

---

## 2. モディファイアの適用順序

```swift
Text("Title")
    // 1. テキスト属性
    .font(.headline)
    .foregroundStyle(Color.textPrimary)

    // 2. 余白
    .padding(.vertical, DesignTokens.Spacing.md)
    .padding(.horizontal, DesignTokens.Spacing.lg)

    // 3. サイズ
    .frame(maxWidth: .infinity)
    .frame(height: DesignTokens.TouchTarget.minimum)

    // 4. 背景・装飾
    .background(Color.backgroundSecondary)
    .clipShape(RoundedRectangle(cornerRadius: DesignTokens.CornerRadius.inputField))
    .shadow(color: .black.opacity(0.1), radius: 4, y: 2)

    // 5. 透明度・表示制御
    .opacity(isVisible ? 1 : 0)

    // 6. アニメーション
    .animation(.easeOut(duration: 0.3), value: isVisible)

    // 7. インタラクション
    .contentShape(Rectangle())
    .onTapGesture { handleTap() }
```

---

## 3. ナビゲーションとツールバー

**ツールバーは必ず標準の `.toolbar` モディファイアを使用する。ZStackでカスタムツールバーをオーバーレイしない。**

```swift
// Bad: ZStackでカスタムツールバーをオーバーレイ
NavigationStack {
    ZStack(alignment: .topTrailing) {
        scrollableContent
        HStack {
            Button("Settings") { ... }
        }
        .padding()
    }
}

// Good: 標準の.toolbarモディファイアを使用
NavigationStack {
    scrollableContent
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Settings") { ... }
            }
        }
        .toolbarBackground(.visible, for: .navigationBar)
}
```

**理由**: `fullScreenCover` がdismissされると、NavigationStackが再構築されます。ZStack内のカスタムツールバーは正しく再描画されない場合があります。

**完全な実装例:**

```swift
NavigationStack {
    contentView
        .navigationTitle("タイトル")
        .navigationBarTitleDisplayMode(.inline)
        .toolbarBackground(.visible, for: .navigationBar)
        .toolbar {
            ToolbarItem(placement: .cancellationAction) {
                Button("閉じる") { dismiss() }
            }
            ToolbarItem(placement: .confirmationAction) {
                Button("保存") { save() }
            }
        }
}
```

---

## 4. Viewの分割基準

| 行数 | 対応 |
|------|------|
| 10行以下 | インラインで記述 |
| 10〜50行 | `private var` で分割 |
| 50行超 | 別ファイルに分離 |
| 再利用性あり | `DesignSystem/Components/` に配置 |

```swift
// 10〜50行: private var
var body: some View {
    VStack {
        headerSection
        contentSection
    }
}

private var headerSection: some View {
    VStack(spacing: DesignTokens.Spacing.sm) {
        // 20行程度のUI
    }
}
```

---

## 5. Previewの書き方

```swift
#Preview("Default") {
    BookDetailView(book: .preview)
}

#Preview("Loading") {
    BookDetailView(book: .preview)
        .environment(\.isLoading, true)
}

#Preview("Empty") {
    BookDetailView(book: nil)
}
```

### ViewModelのPreviewパターン

```swift
#if DEBUG
extension SomeViewModel {
    static var preview: SomeViewModel {
        let vm = SomeViewModel()
        vm.items = [.sample1, .sample2]
        return vm
    }

    static var loadingPreview: SomeViewModel {
        let vm = SomeViewModel()
        vm.isLoading = true
        return vm
    }

    static var emptyPreview: SomeViewModel {
        SomeViewModel()
    }
}
#endif
```

---

## 6. コンポーネント設計原則

### 依存性逆転の原則

**コンポーネントは具象のViewModelに依存せず、クロージャやプロトコルで依存を注入する。**

```swift
// Bad: ViewModelに依存
struct EmptyShelvesView: View {
    let viewModel: ShelfListViewModel  // 具象に依存
}

// Good: クロージャで依存を注入
struct EmptyActionView: View {
    let icon: String
    let message: String
    let actionTitle: String
    let action: () -> Void  // クロージャで依存を注入
}
```

### コンポーネント配置の判断基準

| 条件 | 配置先 |
|------|--------|
| 2つ以上のFeatureで使用される | `DesignSystem/Components/` |
| 汎用的なUI要素（ボタン、カード、リスト項目） | `DesignSystem/Components/` |
| 1つのFeature専用で複雑 | `Features/{Feature}/Components/` |
| 1つのFeature専用で単純（10行以下） | View内のprivate computed property |
