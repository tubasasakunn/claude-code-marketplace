# iOS Coding Rules - 完全リファレンス

mylibraryプロジェクトの完全なコーディング規約です。

---

## 1. ディレクトリ構成

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
│   ├── GlassEffect/         # エフェクト関連
│   └── Extensions/          # View拡張
├── Services/                # ドメインサービス
└── Resources/               # アセット
```

### 各ディレクトリの責務

| ディレクトリ | 責務 | 配置するもの |
|-------------|------|-------------|
| `App/` | アプリ起動・設定 | `@main` App, ContentView, AppDelegate |
| `Core/Models/` | データ定義 | SwiftDataモデル、DTO、Enum |
| `Core/Network/` | 通信基盤 | APIClient、Endpoint定義、エラー型 |
| `Core/Repositories/` | データアクセス抽象化 | Repository実装、Protocol |
| `Core/Sync/` | 同期処理 | SyncManager、PendingOperation処理 |
| `Features/{Name}/` | 機能実装 | View、ViewModel、機能固有コンポーネント |
| `DesignSystem/Theme/` | デザイントークン | 色定義、フォント、アニメーション定数 |
| `DesignSystem/Components/` | 共通UI | 2つ以上の機能で使われるUIコンポーネント |
| `Services/` | ドメインロジック | ビジネスロジック、外部API連携 |
| `Resources/` | 静的リソース | Assets、MLモデル、フォント |

---

## 2. ファイル配置ルール

### 新規ファイルの配置判断フロー

```
新しいファイルを作成する
    │
    ├─ SwiftDataの@Modelか？ → Core/Models/
    │
    ├─ API通信関連か？ → Core/Network/
    │
    ├─ データの取得・保存を抽象化するか？ → Core/Repositories/
    │
    ├─ 特定の画面のViewか？
    │   └─ その画面専用か？ → Features/{機能名}/
    │   └─ 複数画面で使うか？ → DesignSystem/Components/
    │
    ├─ ViewModelか？ → Features/{機能名}/
    │
    ├─ View拡張・モディファイアか？ → DesignSystem/Extensions/
    │
    ├─ 色・フォント・定数か？ → DesignSystem/Theme/
    │
    └─ ビジネスロジック・外部連携か？ → Services/
```

### コンポーネントの配置基準

| 使用箇所 | 配置先 |
|---------|--------|
| 1つの機能でのみ使用 | `Features/{機能名}/Components/` |
| 2つ以上の機能で使用 | `DesignSystem/Components/` |
| アプリ全体で使用（TabBar等） | `DesignSystem/Components/` |

### 禁止事項

- `Features/` 直下にファイルを置かない（必ず機能フォルダを作成）
- `Core/` に UI 関連のコードを置かない
- `DesignSystem/` にビジネスロジックを含めない
- ルートディレクトリにSwiftファイルを置かない

---

## 3. ファイルサイズ制限

### 行数制限

| ファイル種別 | 推奨上限 | 絶対上限 | 超過時の対応 |
|-------------|---------|---------|-------------|
| View | 200行 | 300行 | コンポーネント分割 |
| ViewModel | 250行 | 400行 | ヘルパークラス抽出 |
| Model | 100行 | 150行 | Extension分割 |
| Service | 200行 | 350行 | 責務分割 |
| Repository | 200行 | 300行 | 操作別に分割 |
| Extension | 100行 | 150行 | 機能別に分割 |

### 関数サイズ制限

| 項目 | 推奨上限 | 絶対上限 |
|-----|---------|---------|
| 関数の行数 | 30行 | 50行 |
| 関数の引数 | 4個 | 6個 |
| ネストの深さ | 3レベル | 4レベル |
| 1ファイル内の型定義 | 1個 | 3個（関連する場合のみ） |

### 分割の指針

**Viewが大きくなった場合:**
```swift
// Bad: 1つのViewに全て記述
struct BookDetailView: View {
    var body: some View {
        VStack {
            // 200行のUI...
        }
    }
}

// Good: サブビューに分割
struct BookDetailView: View {
    var body: some View {
        VStack {
            HeaderSection(book: book)
            ContentSection(book: book)
            ActionSection(onSave: saveBook)
        }
    }
}
```

**ViewModelが大きくなった場合:**
```swift
// Good: ヘルパーやExtensionに分割
// BookDetailViewModel.swift
@Observable
final class BookDetailViewModel {
    // 主要なプロパティとメソッド
}

// BookDetailViewModel+Quotes.swift (同じフォルダ内)
extension BookDetailViewModel {
    // 引用関連のメソッド
}
```

---

## 4. 命名規則

### ファイル名

| 種別 | 命名パターン | 例 |
|-----|-------------|-----|
| View | `{機能名}View.swift` | `HomeView.swift` |
| ViewModel | `{機能名}ViewModel.swift` | `HomeViewModel.swift` |
| Model | `{名詞}.swift` | `Book.swift` |
| Service | `{機能}Service.swift` | `ISBNService.swift` |
| Repository | `{対象}Repository.swift` | `BookRepository.swift` |
| Extension | `{型名}+{機能}.swift` | `View+GlassEffect.swift` |
| Protocol | `{名前}Protocol.swift` または型と同じファイル | `APIClientProtocol` |

### 型名

```swift
// Good
struct Book { }                    // Model: 名詞
class BookRepository { }           // Repository: 対象+Repository
class ISBNService { }              // Service: 機能+Service
struct HomeView: View { }          // View: 機能+View
class HomeViewModel { }            // ViewModel: 機能+ViewModel
protocol APIClientProtocol { }     // Protocol: 名前+Protocol
enum ReadingStatus { }             // Enum: 名詞（状態を表す）
struct BookDTO { }                 // DTO: 名前+DTO

// Bad
struct BookData { }                // 曖昧
class BookManager { }              // Manager は避ける
struct HomeScreen { }              // Screen ではなく View
```

### 変数・定数名

```swift
// Good
let bookTitle: String              // キャメルケース
var isLoading: Bool                // Bool は is/has/can/should で始める
let maxRetryCount = 3              // 定数は意味のある名前
private let apiClient: APIClient   // private は明示

// Bad
let title: String                  // 曖昧（何のtitleか）
var loading: Bool                  // is がない
let MAX_RETRY = 3                  // SCREAMING_CASE は使わない
let cnt = 3                        // 略語は避ける
```

### 関数名

```swift
// Good
func fetchBookInfo(isbn: String) async throws -> BookInfo
func saveBook(_ book: Book, to shelf: Shelf)
func deleteBook(_ book: Book)
func updateReadingStatus(to status: ReadingStatus)

// Bad
func getBook(isbn: String)         // get より fetch/load
func save(book: Book, shelf: Shelf) // 引数ラベルが不明確
func delete()                      // 何を削除するか不明
```

---

## 5. コードスタイル

### インポート順序

```swift
// 1. Foundation/標準ライブラリ
import Foundation
import SwiftUI
import SwiftData

// 2. Apple フレームワーク（アルファベット順）
import AVFoundation
import CoreML
import Network
import PhotosUI
import Vision

// 3. サードパーティ（使用する場合）
// import Alamofire
```

### ファイル構造

```swift
/// ファイルヘッダーコメント
/// {ファイル名}
/// {簡潔な説明}
///
/// 責務:
/// - {責務1}
/// - {責務2}
///
/// 依存:
/// - {依存1}
/// - {依存2}

import SwiftUI

// MARK: - {型名}

/// 型のドキュメンテーション
struct SomeView: View {

    // MARK: - Environment

    @Environment(\.dismiss) private var dismiss

    // MARK: - Properties

    let inputProperty: String

    // MARK: - State

    @State private var localState: Bool = false

    // MARK: - Body

    var body: some View {
        // ...
    }

    // MARK: - Subviews

    private var headerView: some View {
        // ...
    }

    // MARK: - Private Methods

    private func handleAction() {
        // ...
    }
}

// MARK: - Preview

#Preview {
    SomeView(inputProperty: "Test")
}
```

### MARK コメントの使用

```swift
// MARK: - Section Name        // セクション区切り
// MARK: Section Name          // サブセクション
// TODO: 後で実装              // 未実装
// FIXME: バグがある           // 既知のバグ
// NOTE: 重要な注意点          // 注意事項
```

### スペース・改行

```swift
// Good
func someFunction(
    parameter1: String,
    parameter2: Int,
    parameter3: Bool
) -> Result {
    // 処理
}

// コロンの後にスペース
let value: String = "test"

// カンマの後にスペース
let array = [1, 2, 3]

// 演算子の前後にスペース
let sum = 1 + 2

// Bad
func someFunction(parameter1:String,parameter2:Int)->Result{
    // 処理
}
```

---

## 6. アーキテクチャ

### レイヤー構成

```
┌─────────────────────────────────────────┐
│              Features (UI)               │
│         View ←→ ViewModel                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│              Services                    │
│      ドメインロジック・外部連携          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           Core/Repositories              │
│         データアクセス抽象化             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Core/Network + Models            │
│          API通信・データ定義             │
└─────────────────────────────────────────┘
```

### 依存関係のルール

```
許可される依存:
View → ViewModel → Repository → Network/Models
View → DesignSystem
ViewModel → Services
Services → Repositories

禁止される依存:
Models → View（逆方向）
Network → ViewModel（逆方向）
DesignSystem → Features（逆方向）
Repository → View（逆方向）
```

### ViewModel のルール

```swift
// Good: @Observable + @MainActor
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

// Bad: ObservableObject（iOS 17未満の互換性が不要な場合）
class BookDetailViewModel: ObservableObject {
    @Published var book: Book?
}
```

### Repository のルール

```swift
// Good: プロトコルを定義してテスト可能に
protocol BookRepositoryProtocol: Sendable {
    func fetchBook(isbn: String) async throws -> BookDTO
    func saveBook(_ book: Book, modelContext: ModelContext) async
}

final class BookRepository: BookRepositoryProtocol {
    static let shared = BookRepository()

    private let apiClient: APIClientProtocol

    init(apiClient: APIClientProtocol = APIClient.shared) {
        self.apiClient = apiClient
    }
}
```

---

## 7. SwiftUI

### View の構成

```swift
struct FeatureView: View {
    // 1. Environment
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext

    // 2. Query（SwiftData）
    @Query private var items: [Item]

    // 3. 外部から渡されるプロパティ
    let inputData: String
    var onComplete: (() -> Void)?

    // 4. State（ローカル状態）
    @State private var isLoading = false
    @State private var showAlert = false

    // 5. StateObject/ObservedObject（ViewModel）
    @State private var viewModel: FeatureViewModel

    // 6. Body
    var body: some View {
        // ...
    }

    // 7. Computed Subviews（private var xxx: some View）

    // 8. Private Methods
}
```

### Viewの分割基準

```swift
// Good: 意味のある単位で分割
var body: some View {
    ScrollView {
        VStack(spacing: 16) {
            headerSection      // 10-20行程度のサブビュー
            contentSection     // 10-20行程度のサブビュー
            actionSection      // 10-20行程度のサブビュー
        }
    }
}

private var headerSection: some View {
    // ヘッダーのUI
}

// Bad: 分割しすぎ
var body: some View {
    titleText          // 1行のためのサブビュー
    subtitleText       // 1行のためのサブビュー
    iconImage          // 1行のためのサブビュー
}
```

### モディファイア

```swift
// Good: 1行に1モディファイア
Button("Save") { save() }
    .font(.headline)
    .foregroundStyle(.white)
    .padding(.horizontal, 16)
    .padding(.vertical, 8)
    .background(Color.accentColor)
    .clipShape(RoundedRectangle(cornerRadius: 8))

// Bad: 複数モディファイアを1行に
Button("Save") { save() }.font(.headline).foregroundStyle(.white)
```

### Previewの書き方

```swift
// Good: 複数のプレビューを用意
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

### ナビゲーションとツールバーの実装

**ツールバーは必ず標準の `.toolbar` モディファイアを使用する。ZStackでカスタムツールバーをオーバーレイしない。**

```swift
// Bad: ZStackでカスタムツールバーをオーバーレイ
// fullScreenCover dismiss後にツールバーが消えるバグの原因になる
NavigationStack {
    ZStack(alignment: .topTrailing) {
        scrollableContent

        // カスタムツールバー（これが問題）
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

**理由**: `fullScreenCover` がdismissされると、NavigationStackが再構築されます。このとき、ZStack内のカスタムツールバーは正しく再描画されない場合があります（SwiftUIの既知のバグ）。標準の `.toolbar` モディファイアはNavigationStackのライフサイクルと連動して管理されるため、この問題を回避できます。

**必須ルール:**
1. ツールバーは `.toolbar { ToolbarItem(...) { } }` で実装
2. `.toolbarBackground` を必ず設定（`.visible` または `.hidden`）
3. ナビゲーションバー内のボタンは `ToolbarItem(placement:)` で配置

```swift
// Good: 完全な実装例
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

## 8. SwiftData

### Model 定義

```swift
/// モデルのドキュメント
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

### クエリの書き方

```swift
// Good: @Query は View で使用
struct BookListView: View {
    @Query(
        filter: #Predicate<Book> { $0.readingStatus == .reading },
        sort: \Book.createdAt,
        order: .reverse
    )
    private var books: [Book]
}

// ViewModel では FetchDescriptor を使用
@MainActor
func fetchBooks(modelContext: ModelContext) -> [Book] {
    let descriptor = FetchDescriptor<Book>(
        predicate: #Predicate { $0.readingStatus == .reading },
        sortBy: [SortDescriptor(\.createdAt, order: .reverse)]
    )
    return (try? modelContext.fetch(descriptor)) ?? []
}
```

### 保存のルール

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

## 9. API連携

### Endpoint 定義

```swift
/// エンドポイント定義
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

### ローカルファースト戦略

```swift
/// ローカルファースト: 常にローカルを優先
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
        try? modelContext.save()
    }
}
```

### リトライ機構

```swift
// PendingOperation で失敗した操作を永続化
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

## 10. エラーハンドリング

### エラー型の定義

```swift
/// API エラー型
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
        case .invalidURL:
            return "無効なURLです"
        case .networkError(let error):
            return "ネットワークエラー: \(error.localizedDescription)"
        // ...
        }
    }
}
```

### エラー処理パターン

```swift
// Good: 適切なエラーハンドリング
func fetchBook(isbn: String) async {
    do {
        book = try await repository.fetchBook(isbn: isbn)
    } catch let error as APIError {
        switch error {
        case .notFound:
            // 見つからない場合は手動入力モードへ
            isManualInputMode = true
        case .networkError:
            // ネットワークエラーはユーザーに通知
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

### ログ出力

```swift
// 統一されたログフォーマット
print("[クラス名] メッセージ: \(詳細)")

// 例
print("[BookRepository] Book registered to API: isbn=\(isbn)")
print("[SyncManager] Failed to sync: \(error.localizedDescription)")
```

---

## 11. 非同期処理

### async/await の使用

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

### MainActor

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

### Task の使用

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

## 12. ドキュメンテーション

### ファイルヘッダー

すべての Swift ファイルに以下のヘッダーを含める:

```swift
/// {ファイル名}
/// {1行の説明}
///
/// 責務:
/// - {責務1}
/// - {責務2}
///
/// 依存:
/// - {依存クラス/モジュール1}
/// - {依存クラス/モジュール2}
///
/// 使用場所:
/// - {使用される場所1}
/// - {使用される場所2}
```

### 型・関数のドキュメント

```swift
/// 書籍情報を管理するリポジトリ
///
/// ローカル（SwiftData）とリモート（API）の両方を扱う。
/// API 失敗時は PendingOperation として保存し、後でリトライする。
final class BookRepository {

    /// 書籍を保存する
    ///
    /// 1. ローカルに即座に保存
    /// 2. API に登録を試行
    /// 3. 失敗時は PendingOperation として保存
    ///
    /// - Parameters:
    ///   - book: 保存する書籍
    ///   - modelContext: SwiftData のモデルコンテキスト
    @MainActor
    func saveBook(_ book: Book, modelContext: ModelContext) async {
        // ...
    }
}
```

### コメントのルール

```swift
// Good: なぜそうするかを説明
// 409 (Conflict) は既に登録済みなので成功として扱う
if case .conflict = error { return }

// Good: 複雑なロジックの説明
// タグの差分を計算: 追加されたものと削除されたものを特定
let addedShelves = newShelves.filter { !oldIds.contains($0.id) }
let removedShelves = oldShelves.filter { !newIds.contains($0.id) }

// Bad: コードを読めばわかることを書く
// カウントをインクリメント
count += 1

// Bad: 古くなったコメント
// TODO: 後で実装（3年前のコメント）
```

---

## 13. テスト

### テストファイルの配置

```
mylibraryTests/
├── Core/
│   ├── Models/
│   │   └── BookTests.swift
│   ├── Network/
│   │   └── APIClientTests.swift
│   └── Repositories/
│       └── BookRepositoryTests.swift
├── Features/
│   └── Home/
│       └── HomeViewModelTests.swift
└── Services/
    └── ISBNServiceTests.swift
```

### テスト命名規則

```swift
// 命名: test_{テスト対象}_{条件}_{期待結果}
func test_fetchBook_withValidISBN_returnsBook() async throws {
    // ...
}

func test_fetchBook_withInvalidISBN_throwsError() async throws {
    // ...
}

func test_saveBook_whenOffline_createsPendingOperation() async {
    // ...
}
```

### モックの使用

```swift
// プロトコルを使ってモック可能に
protocol APIClientProtocol {
    func request<T: Decodable>(_ endpoint: Endpoint) async throws -> T
}

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

---

## 14. Git運用

### ブランチ命名

```
feature/{機能名}      # 新機能
fix/{バグ内容}        # バグ修正
refactor/{対象}       # リファクタリング
docs/{内容}           # ドキュメント
```

### コミットメッセージ

```
{type}: {簡潔な説明}

{詳細な説明（必要な場合）}

Generated with Claude Code
```

**type の種類:**
- `feat`: 新機能
- `fix`: バグ修正
- `refactor`: リファクタリング
- `docs`: ドキュメント
- `style`: コードスタイル（動作に影響なし）
- `test`: テスト追加・修正
- `chore`: ビルド・設定変更

### コミット単位

- 1つのコミットは1つの論理的な変更
- 動作する状態でコミット（ビルドが通る）
- 関連するファイル変更はまとめてコミット

---

## 15. DesignTokens・スタイル定義

### ハードコード値の禁止

**すべてのUI値は `DesignTokens` を使用する。**

```swift
// Bad: ハードコードされた値
VStack(spacing: 16) { }
.padding(24)
.cornerRadius(12)

// Good: DesignTokensを使用
VStack(spacing: DesignTokens.Spacing.lg) { }
.padding(DesignTokens.Spacing.xxl)
.clipShape(RoundedRectangle(cornerRadius: DesignTokens.CornerRadius.inputField))
```

### DesignTokensの種類

| カテゴリ | 使用例 | 定義場所 |
|---------|--------|----------|
| Spacing | `.xxs`(2), `.xs`(4), `.sm`(8), `.md`(12), `.lg`(16), `.xl`(20), `.xxl`(24), `.xxxl`(32) | `DesignTokens.Spacing` |
| CornerRadius | `.minimal`(4), `.small`(8), `.inputField`(12), `.tile`(16), `.glass`(20), `.card`(24) | `DesignTokens.CornerRadius` |
| Typography | `.captionSize`(13), `.subheadlineSize`(15), `.bodySize`(17), `.titleSize`(20), `.headlineSize`(22), `.largeTitleSize`(28) | `DesignTokens.Typography` |
| IconSize | `.sm`(12), `.md`(16), `.lg`(20), `.xl`(24), `.xxl`(32), `.stateIcon`(48) | `DesignTokens.IconSize` |
| TouchTarget | `.minimum`(44), `.recommended`(48) | `DesignTokens.TouchTarget` |

### セマンティックカラーの使用

**直接的な色指定（Color.white, Color.black）は禁止。セマンティックカラーを使用する。**

```swift
// Bad: 直接的な色指定
Color.white
Color.black
Color.black.opacity(0.5)
.foregroundStyle(.white)

// Good: セマンティックカラー
Color.textPrimary
Color.backgroundPrimary
Color.overlayBackground
.foregroundStyle(Color.cameraText)
```

### セマンティックカラー一覧

| 用途 | カラー名 |
|------|----------|
| テキスト | `textPrimary`, `textSecondary`, `textTertiary` |
| 背景 | `backgroundPrimary`, `backgroundSecondary`, `backgroundTertiary` |
| アクセント | `accent`, `accentSecondary` |
| ステータス | `statusReading`, `statusFinished`, `statusWantToRead`, `statusUnread` |
| カメラUI | `cameraBackground`, `cameraText`, `cameraFrame`, `cameraFrameSubtle`, `cameraOverlayLight`, `cameraOverlayDark` |
| オーバーレイ | `overlayBackground` |
| 検索 | `searchHighlight` |

### 新しいトークンの追加

新しい値が必要な場合は、既存のトークンで代替できないか確認した上で、`DesignTokens.swift` または `Color+Theme.swift` に追加する。

---

## 16. コンポーネント設計原則

### コンポーネントレイヤーの分離

**Features層にprivate structで定義されたUIコンポーネントは、再利用可能な場合 `DesignSystem/Components/` に移動する。**

```swift
// Bad: Features層にprivate structとして定義
// Features/Quote/QuoteCard.swift
struct QuoteCard: View {
    // ...

    private struct MemoModalView: View {  // ← ここに定義
        // ...
    }
}

// Good: DesignSystem/Componentsに分離
// DesignSystem/Components/TextContentModal.swift
struct TextContentModal: View {
    let title: String
    let content: String
    // ...
}

// Features/Quote/QuoteCard.swift
struct QuoteCard: View {
    // TextContentModalを使用
}
```

### 依存性逆転の原則

**コンポーネントは具象のViewModelに依存せず、クロージャやプロトコルで依存を注入する。**

```swift
// Bad: ViewModelに依存
struct EmptyShelvesView: View {
    let viewModel: ShelfListViewModel  // 具象に依存

    var body: some View {
        Button("追加") {
            viewModel.showAddShelf()
        }
    }
}

// Good: クロージャで依存を注入
struct EmptyActionView: View {
    let icon: String
    let message: String
    let actionTitle: String
    let action: () -> Void  // クロージャで依存を注入

    var body: some View {
        Button(actionTitle, action: action)
    }
}
```

### ジェネリック・再利用可能なコンポーネント

**類似のコンポーネントはジェネリック化して統合する。**

```swift
// Bad: 類似のコンポーネントが複数存在
struct SegmentButton: View { }    // 引用選択用
struct BookHitCell: View { }      // 検索結果用

// Good: 汎用コンポーネントに統合
struct SelectableListItem: View {
    let text: String
    let isSelected: Bool
    let onTap: () -> Void
}

struct BookListCell: View {
    let book: Book
    var searchQuery: String? = nil  // オプショナルパラメータで機能拡張
}
```

### コンポーネント配置の判断基準

| 条件 | 配置先 |
|------|--------|
| 2つ以上のFeatureで使用される | `DesignSystem/Components/` |
| 汎用的なUI要素（ボタン、カード、リスト項目） | `DesignSystem/Components/` |
| 1つのFeature専用で複雑 | `Features/{Feature}/Components/` |
| 1つのFeature専用で単純（10行以下） | View内のprivate computed property |

---

## 17. コード重複の排除

### 重複関数の検出と統合

**同じロジックが複数箇所に存在する場合、Extensionに統合する。**

```swift
// Bad: 複数ファイルに同じ関数
// BookListCell.swift
private func highlightText(_ text: String, query: String) -> AttributedString { ... }

// SearchResultsList.swift
private func highlightText(_ text: String, query: String) -> AttributedString { ... }

// Good: Extensionに統合
// DesignSystem/Extensions/AttributedString+Highlight.swift
extension AttributedString {
    static func highlighted(
        _ text: String,
        query: String,
        highlightColor: Color = .searchHighlight
    ) -> AttributedString {
        // 共通ロジック
    }
}
```

### Extension配置ルール

| Extension種別 | 配置先 |
|--------------|--------|
| View拡張（モディファイア） | `DesignSystem/Extensions/View+{機能}.swift` |
| 型拡張（ユーティリティ） | `DesignSystem/Extensions/{型}+{機能}.swift` |
| Model拡張 | `Core/Models/{Model}+{機能}.swift` |

### 共通パターンの抽出

**繰り返されるUIパターンはコンポーネント化する。**

```swift
// Bad: 繰り返されるパターン
// SettingsView.swift
VStack(alignment: .leading, spacing: 4) {
    Text("タイトル").font(.headline)
    Text("説明").font(.subheadline).foregroundStyle(.secondary)
}

// OtherView.swift
VStack(alignment: .leading, spacing: 4) {
    Text("別タイトル").font(.headline)
    Text("別説明").font(.subheadline).foregroundStyle(.secondary)
}

// Good: コンポーネント化
struct TitleDescriptionStack: View {
    let title: String
    let description: String

    var body: some View {
        VStack(alignment: .leading, spacing: DesignTokens.Spacing.xxs) {
            Text(title).font(.headline)
            Text(description).font(.subheadline).foregroundStyle(.secondary)
        }
    }
}
```

---

## 18. 暗黙的なコーディングパターン

### ViewModelのプロパティ定義順序

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

### Viewのプロパティ定義順序

```swift
struct SomeView: View {

    // MARK: - Properties

    /// ViewModel（@Bindable）
    @Bindable var viewModel: SomeViewModel

    /// 親から渡されるバインディング
    @Binding var isPresented: Bool

    /// 外部から渡される値
    let initialValue: String

    // MARK: - State

    @State private var showSheet = false
    @State private var selectedItem: Item?

    // MARK: - Environment

    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext

    // MARK: - SwiftData Queries

    @Query(sort: \Book.addedAt, order: .reverse)
    private var books: [Book]
}
```

**順序ルール:**
1. `@Bindable` ViewModel
2. `@Binding` 親からのバインディング
3. `let` / `var` 外部プロパティ
4. `@State` ローカル状態
5. `@Environment` 環境値
6. `@Query` SwiftDataクエリ

### MARKセクションの標準順序

```swift
// MARK: - Properties

// MARK: - State

// MARK: - Environment

// MARK: - SwiftData Queries

// MARK: - Initializer

// MARK: - Computed Properties

// MARK: - Body

// MARK: - Subviews

// MARK: - Public Methods

// MARK: - Private Methods

// MARK: - Preview
```

### ログ出力の統一形式

```swift
// フォーマット: [クラス名] メッセージ: 詳細
print("[BookRepository] Book saved: isbn=\(isbn)")
print("[SyncManager] Retry failed: \(error.localizedDescription)")
print("[SearchViewModel] ModelContext is not set. Call setModelContext() first.")

// 成功時
print("[UserBookTagRepository] Tag registered: tagId=\(tagId)")

// 失敗時
print("[BookRepository] Failed to save book locally: \(error)")
```

### @Query のソート指定

**常にソート順序を明示的に指定する:**

```swift
// Good: ソート順序を明示
@Query(sort: \Book.addedAt, order: .reverse)
private var books: [Book]

@Query(sort: \Shelf.createdAt, order: .reverse)
private var shelves: [Shelf]

@Query(sort: \Quote.createdAt, order: .reverse)
private var quotes: [Quote]

// Bad: ソート順序が不明確
@Query private var books: [Book]
```

### ナビゲーション状態管理

**NavigationPath での明示的管理:**

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
        // 連続タップ防止
        guard !isNavigationDisabled else { return }
        // 既にナビゲーション中でないことを確認
        guard navigationPath.isEmpty else { return }

        navigationPath.append(shelf.persistentModelID)
    }

    /// ナビゲーションを戻る
    func popFromNavigationPath() {
        guard !navigationPath.isEmpty else { return }

        isNavigationDisabled = true
        navigationPath.removeLast()

        // 戻り完了後に再有効化
        Task { @MainActor in
            try? await Task.sleep(for: .milliseconds(500))
            self.isNavigationDisabled = false
        }
    }
}
```

### エラーハンドリングの階層パターン

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
        print("[Repository] API error, saving as pending: \(error)")
        savePendingOperation(...)
    }
} catch {
    // ネットワークエラー等: PendingOperationに保存
    print("[Repository] Network error, saving as pending: \(error)")
    savePendingOperation(...)
}
```

### Previewの提供パターン

```swift
#if DEBUG
extension SomeViewModel {

    /// 標準プレビュー
    static var preview: SomeViewModel {
        let vm = SomeViewModel()
        vm.items = [.sample1, .sample2]
        vm.isLoading = false
        return vm
    }

    /// ローディング状態プレビュー
    static var loadingPreview: SomeViewModel {
        let vm = SomeViewModel()
        vm.isLoading = true
        return vm
    }

    /// エラー状態プレビュー
    static var errorPreview: SomeViewModel {
        let vm = SomeViewModel()
        vm.errorMessage = "エラーが発生しました"
        return vm
    }

    /// 空状態プレビュー
    static var emptyPreview: SomeViewModel {
        SomeViewModel()
    }
}
#endif

// Viewでの使用
#Preview("Default") {
    SomeView(viewModel: .preview)
}

#Preview("Loading") {
    SomeView(viewModel: .loadingPreview)
}

#Preview("Error") {
    SomeView(viewModel: .errorPreview)
}
```

### モディファイアの適用順序

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

### サブビュー分割の基準

| 行数 | 対応 |
|------|------|
| 10行以下 | インラインで記述 |
| 10〜50行 | `private var` で分割 |
| 50行超 | 別ファイルに分離 |
| 再利用性あり | `DesignSystem/Components/` に配置 |

```swift
// 10行以下: インライン
var body: some View {
    VStack {
        Text(title).font(.headline)
        Text(subtitle).font(.subheadline)
    }
}

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

// 50行超: 別ファイル（Components/HeaderSection.swift）
```

### 依存注入の統一パターン

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

### ローカルファースト戦略

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
