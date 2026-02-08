# アーキテクチャパターン

## MVVM + @Observable

```swift
// ViewModel
@Observable
final class HomeViewModel {
    var selectedMovie: Movie?
}

// View
struct HomeView: View {
    @State private var viewModel = HomeViewModel()
    @Query(sort: \Movie.addedAt, order: .reverse) private var movies: [Movie]
}
```

## Singleton サービス

```swift
@Observable
final class ThemeManager: @unchecked Sendable {
    static let shared = ThemeManager()
    private init() { /* UserDefaults から復元 */ }
}
```

## Fire-and-Forget 同期

```swift
// UI をブロックしない非同期 API 同期
Task.detached {
    try? await MovieSyncService.shared.syncUpsert(movie)
}
```

**設計思想:** SwiftData が source of truth、API は非同期バックアップ。

## Endpoint プロトコル

```swift
protocol Endpoint {
    var baseURL: String { get }
    var path: String { get }
    var method: HTTPMethod { get }
    var queryItems: [URLQueryItem]? { get }
    var body: Data? { get }
    func makeRequest() -> URLRequest
}
```
