# iOS Coding Rules - SwiftData & API連携

SwiftData Model、クエリ、ローカルファースト戦略、API連携のルール。

---

## 1. SwiftData Model 定義

```swift
@Model
final class Book {
    // MARK: - Properties

    /// 必須プロパティ
    var title: String
    var author: String
    var createdAt: Date

    /// オプショナルプロパティ
    var isbn: String?
    var coverImageData: Data?

    /// リレーション（inverse を明示）
    @Relationship(deleteRule: .nullify, inverse: \Shelf.books)
    var shelves: [Shelf] = []

    @Relationship(deleteRule: .cascade, inverse: \Quote.book)
    var quotes: [Quote] = []

    // MARK: - Initializer

    init(title: String, author: String) {
        self.title = title
        self.author = author
        self.createdAt = Date()
    }
}
```

---

## 2. クエリの書き方

### @Query（Viewで使用）

```swift
struct BookListView: View {
    @Query(
        filter: #Predicate<Book> { $0.readingStatus == .reading },
        sort: \Book.createdAt,
        order: .reverse
    )
    private var books: [Book]
}
```

**常にソート順序を明示的に指定する:**

```swift
// Good: ソート順序を明示
@Query(sort: \Book.addedAt, order: .reverse)
private var books: [Book]

// Bad: ソート順序が不明確
@Query private var books: [Book]
```

### FetchDescriptor（ViewModelで使用）

```swift
@MainActor
func fetchBooks(modelContext: ModelContext) -> [Book] {
    let descriptor = FetchDescriptor<Book>(
        predicate: #Predicate { $0.readingStatus == .reading },
        sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
    )
    return (try? modelContext.fetch(descriptor)) ?? []
}
```

---

## 3. 保存のルール

```swift
// Good: 明示的に save() を呼ぶ
func saveBook(_ book: Book, modelContext: ModelContext) {
    modelContext.insert(book)
    do {
        try modelContext.save()
    } catch {
        print("[BookRepository] Failed to save: \(error)")
    }
}

// Bad: 自動保存に依存
func saveBook(_ book: Book, modelContext: ModelContext) {
    modelContext.insert(book)
    // save() を呼ばない → タイミングが不定
}
```

---

## 4. API Endpoint 定義

```swift
enum BooksEndpoint: Endpoint {
    case getBook(isbn: String)
    case upsertBook(isbn: String, title: String, author: String, imageUrl: String?)

    var path: String {
        switch self {
        case .getBook(let isbn):
            return "/books/\(isbn)"
        case .upsertBook(let isbn, _, _, _):
            return "/books/\(isbn)"
        }
    }

    var method: HTTPMethod {
        switch self {
        case .getBook: return .get
        case .upsertBook: return .put
        }
    }

    var body: Data? {
        switch self {
        case .getBook:
            return nil
        case .upsertBook(_, let title, let author, let imageUrl):
            let payload = ["title": title, "author": author, "imageUrl": imageUrl]
            return try? JSONEncoder().encode(payload)
        }
    }
}
```

---

## 5. ローカルファースト戦略

**すべてのデータ操作で以下の順序を守る:**

```swift
@MainActor
func saveBook(_ book: Book, modelContext: ModelContext) async {
    // 1. ローカル（SwiftData）に即座に保存
    modelContext.insert(book)
    do {
        try modelContext.save()
    } catch {
        print("[BookRepository] Failed to save locally: \(error)")
        return
    }

    // 2. API呼び出しを非同期で試行
    do {
        _ = try await apiClient.request(endpoint)
        print("[BookRepository] Synced to API: isbn=\(isbn)")
    } catch {
        // 3. 失敗時はPendingOperationとして保存
        print("[BookRepository] API failed, saving pending: \(error)")
        let pendingOp = PendingOperationFactory.upsertBook(...)
        modelContext.insert(pendingOp)
        try? modelContext.save()
    }
}
```

---

## 6. リトライ機構

```swift
@Model
final class PendingOperation {
    var operationTypeRaw: String
    var parametersJSON: String
    var retryCount: Int
    var maxRetryCount: Int = 3

    var canRetry: Bool {
        retryCount < maxRetryCount
    }
}

// SyncManager で起動時にリトライ
func startSync(modelContext: ModelContext) async {
    let pendingOps = fetchPendingOperations(modelContext: modelContext)
    for op in pendingOps {
        await retryOperation(op, modelContext: modelContext)
    }
}
```

---

## 7. Repository のルール

```swift
// プロトコルを定義してテスト可能に
protocol BookRepositoryProtocol: Sendable {
    func fetchBook(isbn: String) async throws -> BookDTO
    func saveBook(_ book: Book, modelContext: ModelContext) async
}

final class BookRepository: BookRepositoryProtocol, @unchecked Sendable {
    static let shared = BookRepository()

    private let apiClient: APIClientProtocol

    // デフォルト引数でシングルトンを指定（テスト時はモック注入可能）
    init(apiClient: APIClientProtocol = APIClient.shared) {
        self.apiClient = apiClient
    }
}
```

---

## 8. エラーハンドリング

### エラー型の定義

```swift
enum APIError: LocalizedError {
    case invalidURL
    case invalidResponse
    case networkError(Error)
    case decodingError(Error)
    case unauthorized
    case notFound
    case conflict
    case serverError(Int)

    var errorDescription: String? {
        switch self {
        case .invalidURL: return "無効なURLです"
        case .networkError(let error): return "ネットワークエラー: \(error.localizedDescription)"
        // ...
        }
    }
}
```

### エラー処理パターン

```swift
do {
    result = try await apiClient.request(endpoint)
    print("[Repository] Success: \(result)")
} catch let error as APIError {
    switch error {
    case .conflict:
        // 409: 既存データとして成功扱い
        print("[Repository] Already exists, treating as success")
        return
    case .notFound:
        // 404: 見つからない場合の特別処理
        errorMessage = "データが見つかりませんでした"
    default:
        // その他のAPIエラー: PendingOperationに保存
        savePendingOperation(...)
    }
} catch {
    // ネットワークエラー等: PendingOperationに保存
    savePendingOperation(...)
}
```
