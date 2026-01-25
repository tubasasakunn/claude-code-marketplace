# iOS Coding Rules - ViewModel & 非同期処理

ViewModel構成、依存性注入、async/await、MainActorのルール。

---

## 1. ViewModelの構成

```swift
@MainActor
@Observable
final class SomeViewModel {

    // MARK: - Properties（公開状態）

    var items: [Item] = []
    var isLoading = false
    var errorMessage: String?

    // MARK: - Computed Properties

    var isEmpty: Bool { items.isEmpty }
    var hasError: Bool { errorMessage != nil }

    // MARK: - Private Properties

    private let repository: RepositoryProtocol
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initializer

    init(repository: RepositoryProtocol = SomeRepository.shared) {
        self.repository = repository
    }
}
```

**順序ルール:**
1. 公開状態プロパティ（UIバインディング用）
2. Computed Properties（派生値）
3. Private Properties（依存・内部状態）
4. Initializer

---

## 2. @Observable vs ObservableObject

```swift
// Good: @Observable + @MainActor（iOS 17+）
@Observable
@MainActor
final class BookDetailViewModel {
    var book: Book?
    var isLoading = false

    private let repository: BookRepositoryProtocol

    init(repository: BookRepositoryProtocol = BookRepository.shared) {
        self.repository = repository
    }
}

// Bad: ObservableObject（iOS 17未満の互換性が不要な場合）
class BookDetailViewModel: ObservableObject {
    @Published var book: Book?
}
```

---

## 3. 依存性注入パターン

```swift
// Protocol定義
protocol BookRepositoryProtocol: Sendable {
    func fetchBook(isbn: String) async throws -> BookDTO
}

// 実装（シングルトン + DI対応）
final class BookRepository: BookRepositoryProtocol, @unchecked Sendable {
    static let shared = BookRepository()

    private let apiClient: APIClientProtocol

    // デフォルト引数でシングルトンを指定（テスト時はモック注入可能）
    init(apiClient: APIClientProtocol = APIClient.shared) {
        self.apiClient = apiClient
    }
}

// ViewModelでの使用
@MainActor
@Observable
final class BookViewModel {
    private let repository: BookRepositoryProtocol

    init(repository: BookRepositoryProtocol = BookRepository.shared) {
        self.repository = repository
    }
}
```

---

## 4. async/await の使用

```swift
// Good: async/await を使用
func fetchData() async throws -> Data {
    try await apiClient.request(endpoint)
}

// Bad: completion handler（レガシー）
func fetchData(completion: @escaping (Result<Data, Error>) -> Void) {
    // ...
}
```

---

## 5. MainActor

```swift
// Good: UI更新は @MainActor
@MainActor
func updateUI() {
    isLoading = false
    errorMessage = nil
}

// ViewModel 全体を MainActor に
@Observable
@MainActor
final class FeatureViewModel {
    var isLoading = false
}
```

---

## 6. Task の使用

```swift
// Good: Task で非同期処理をラップ
Button("Save") {
    Task {
        await viewModel.save()
    }
}

// .task モディファイア
.task {
    await viewModel.loadData()
}

// Bad: Task の結果を待たずに dismiss
func save() {
    Task {
        await repository.save(item)
    }
    dismiss()  // 保存完了前に閉じる可能性
}
```

---

## 7. ナビゲーション状態管理

```swift
@MainActor
@Observable
final class HomeViewModel {

    /// NavigationStackのパス
    var navigationPath = NavigationPath()

    /// 連続タップ防止フラグ
    private var isNavigationDisabled = false

    /// 本棚を選択してナビゲーション
    func selectShelf(_ shelf: Shelf) {
        guard !isNavigationDisabled else { return }
        guard navigationPath.isEmpty else { return }

        navigationPath.append(shelf.persistentModelID)
    }

    /// ナビゲーションを戻る
    func popFromNavigationPath() {
        guard !navigationPath.isEmpty else { return }

        isNavigationDisabled = true
        navigationPath.removeLast()

        Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(500))
            self.isNavigationDisabled = false
        }
    }
}
```

---

## 8. エラーハンドリング

```swift
// Good: 適切なエラーハンドリング
func fetchBook(isbn: String) async {
    do {
        book = try await repository.fetchBook(isbn: isbn)
    } catch let error as APIError {
        switch error {
        case .notFound:
            isManualInputMode = true
        case .networkError:
            errorMessage = error.localizedDescription
        default:
            errorMessage = "予期せぬエラーが発生しました"
        }
    } catch {
        errorMessage = error.localizedDescription
    }
}

// Bad: エラーを握りつぶす
func fetchBook(isbn: String) async {
    book = try? await repository.fetchBook(isbn: isbn)
}
```

---

## 9. テスト

### テスト命名規則

```swift
// 命名: test_{テスト対象}_{条件}_{期待結果}
func test_fetchBook_withValidISBN_returnsBook() async throws {
    // ...
}

func test_fetchBook_withInvalidISBN_throwsError() async throws {
    // ...
}
```

### モックの使用

```swift
// テスト用モック
final class MockAPIClient: APIClientProtocol {
    var mockResponse: Any?
    var mockError: Error?

    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T {
        if let error = mockError { throw error }
        return mockResponse as! T
    }
}

// テストでの使用
func test_fetchBook_success() async throws {
    let mockClient = MockAPIClient()
    mockClient.mockResponse = BookDTO(isbn: "123", title: "Test", author: "Author")

    let repository = BookRepository(apiClient: mockClient)
    let result = try await repository.fetchBook(isbn: "123")

    XCTAssertEqual(result.title, "Test")
}
```
