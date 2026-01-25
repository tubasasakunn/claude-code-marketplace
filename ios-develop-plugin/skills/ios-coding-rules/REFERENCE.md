# iOS Coding Rules - 完全リファレンス

mylibraryプロジェクトの全コーディング規約の一覧です。詳細は各ドキュメントを参照してください。

---

## 関連ドキュメント

| ドキュメント | 内容 |
|:-------------|:-----|
| [ARCHITECTURE.md](ARCHITECTURE.md) | ディレクトリ構成、ファイル配置、レイヤー設計 |
| [NAMING-STYLE.md](NAMING-STYLE.md) | 命名規則、コードスタイル、ドキュメンテーション |
| [SWIFTUI.md](SWIFTUI.md) | View構成、モディファイア、ナビゲーション |
| [SWIFTDATA-API.md](SWIFTDATA-API.md) | SwiftData、ローカルファースト、API連携 |
| [VIEWMODEL.md](VIEWMODEL.md) | ViewModel、依存性注入、非同期処理 |
| [CHECKLIST.md](CHECKLIST.md) | 実装・レビュー時のチェックリスト |

---

## 1. ディレクトリ構成

→ 詳細: [ARCHITECTURE.md](ARCHITECTURE.md)

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
├── DesignSystem/            # UIコンポーネント・スタイル
├── Services/                # ドメインサービス
└── Resources/               # アセット
```

---

## 2. ファイルサイズ制限

→ 詳細: [ARCHITECTURE.md](ARCHITECTURE.md)

| ファイル種別 | 推奨上限 | 絶対上限 |
|-------------|---------|---------|
| View | 200行 | 300行 |
| ViewModel | 250行 | 400行 |
| Model | 100行 | 150行 |
| 関数 | 30行 | 50行 |

---

## 3. 命名規則

→ 詳細: [NAMING-STYLE.md](NAMING-STYLE.md)

| 種別 | パターン | 例 |
|-----|---------|-----|
| View | `{機能名}View.swift` | `HomeView.swift` |
| ViewModel | `{機能名}ViewModel.swift` | `HomeViewModel.swift` |
| Model | `{名詞}.swift` | `Book.swift` |
| Extension | `{型名}+{機能}.swift` | `View+GlassEffect.swift` |

---

## 4. コードスタイル

→ 詳細: [NAMING-STYLE.md](NAMING-STYLE.md)

### インポート順序

```swift
import Foundation
import SwiftUI
import SwiftData
// Apple フレームワーク（アルファベット順）
// サードパーティ
```

### MARKセクション

```swift
// MARK: - Properties
// MARK: - State
// MARK: - Environment
// MARK: - Body
// MARK: - Subviews
// MARK: - Private Methods
```

---

## 5. レイヤー構成

→ 詳細: [ARCHITECTURE.md](ARCHITECTURE.md)

```
Features (UI) → Services → Repositories → Network/Models
Features (UI) → DesignSystem
```

---

## 6. SwiftUI

→ 詳細: [SWIFTUI.md](SWIFTUI.md)

### Viewプロパティ順序

1. `@Bindable` ViewModel
2. `@Binding`
3. `let/var` 外部プロパティ
4. `@State`
5. `@Environment`
6. `@Query`

### モディファイア順序

1. テキスト属性 → 2. 余白 → 3. サイズ → 4. 背景 → 5. 透明度 → 6. アニメーション → 7. インタラクション

### ツールバー

```swift
// Good: .toolbarを使用
.toolbar {
    ToolbarItem(placement: .topBarTrailing) {
        Button("Settings") { ... }
    }
}
.toolbarBackground(.visible, for: .navigationBar)

// Bad: ZStackオーバーレイ
```

---

## 7. ViewModel

→ 詳細: [VIEWMODEL.md](VIEWMODEL.md)

```swift
@MainActor
@Observable
final class SomeViewModel {
    // 公開状態プロパティ
    var items: [Item] = []
    var isLoading = false

    // Private Properties
    private let repository: RepositoryProtocol

    // Initializer（DI対応）
    init(repository: RepositoryProtocol = SomeRepository.shared) {
        self.repository = repository
    }
}
```

---

## 8. SwiftData

→ 詳細: [SWIFTDATA-API.md](SWIFTDATA-API.md)

```swift
@Model
final class Book {
    var title: String
    var author: String

    @Relationship(deleteRule: .cascade, inverse: \Quote.book)
    var quotes: [Quote] = []
}
```

### @Query（常にソートを明示）

```swift
@Query(sort: \Book.addedAt, order: .reverse)
private var books: [Book]
```

---

## 9. ローカルファースト戦略

→ 詳細: [SWIFTDATA-API.md](SWIFTDATA-API.md)

1. ローカル（SwiftData）に即座に保存
2. APIに非同期で同期
3. 失敗時はPendingOperationに保存

---

## 10. DesignTokens

→ 詳細: [SWIFTUI.md](SWIFTUI.md)

```swift
// Bad
VStack(spacing: 16) { }
Color.white

// Good
VStack(spacing: DesignTokens.Spacing.lg) { }
Color.textPrimary
```

| カテゴリ | 値 |
|---------|-----|
| Spacing | `.xxs`(2), `.xs`(4), `.sm`(8), `.md`(12), `.lg`(16), `.xl`(20), `.xxl`(24) |
| CornerRadius | `.minimal`(4), `.small`(8), `.inputField`(12), `.tile`(16), `.card`(24) |
| Color | `textPrimary`, `textSecondary`, `backgroundPrimary`, `backgroundSecondary` |

---

## 11. エラーハンドリング

→ 詳細: [VIEWMODEL.md](VIEWMODEL.md)

```swift
do {
    result = try await apiClient.request(endpoint)
} catch let error as APIError {
    switch error {
    case .conflict: return  // 成功扱い
    case .notFound: errorMessage = "見つかりません"
    default: savePendingOperation(...)
    }
} catch {
    savePendingOperation(...)
}
```

---

## 12. ログ出力

→ 詳細: [NAMING-STYLE.md](NAMING-STYLE.md)

```swift
print("[BookRepository] Book saved: isbn=\(isbn)")
print("[SyncManager] Retry failed: \(error.localizedDescription)")
```

---

## 13. テスト

→ 詳細: [VIEWMODEL.md](VIEWMODEL.md)

### 命名規則

```swift
func test_{テスト対象}_{条件}_{期待結果}() async throws
```

### テストファイル配置

```
mylibraryTests/
├── Core/
│   ├── Models/
│   ├── Network/
│   └── Repositories/
├── Features/
└── Services/
```

---

## 14. Git運用

### ブランチ命名

```
feature/{機能名}
fix/{バグ内容}
refactor/{対象}
docs/{内容}
```

### コミットメッセージ

```
{type}: {簡潔な説明}

Generated with Claude Code
```

type: `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`
