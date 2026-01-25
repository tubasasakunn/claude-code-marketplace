# iOS Coding Rules - 命名規則 & コードスタイル

ファイル名、型名、変数名、関数名、コードフォーマットのルール。

---

## 1. ファイル名

| 種別 | 命名パターン | 例 |
|-----|-------------|-----|
| View | `{機能名}View.swift` | `HomeView.swift` |
| ViewModel | `{機能名}ViewModel.swift` | `HomeViewModel.swift` |
| Model | `{名詞}.swift` | `Book.swift` |
| Service | `{機能}Service.swift` | `ISBNService.swift` |
| Repository | `{対象}Repository.swift` | `BookRepository.swift` |
| Extension | `{型名}+{機能}.swift` | `View+GlassEffect.swift` |
| Protocol | `{名前}Protocol.swift` または型と同じファイル | `APIClientProtocol` |

---

## 2. 型名

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

---

## 3. 変数・定数名

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

---

## 4. 関数名

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

## 5. インポート順序

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

---

## 6. ファイル構造

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

import SwiftUI

// MARK: - {型名}

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

---

## 7. MARK コメント

```swift
// MARK: - Section Name        // セクション区切り
// MARK: Section Name          // サブセクション
// TODO: 後で実装              // 未実装
// FIXME: バグがある           // 既知のバグ
// NOTE: 重要な注意点          // 注意事項
```

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

---

## 8. スペース・改行

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

## 9. ログ出力の統一形式

```swift
// フォーマット: [クラス名] メッセージ: 詳細
print("[BookRepository] Book saved: isbn=\(isbn)")
print("[SyncManager] Retry failed: \(error.localizedDescription)")
print("[SearchViewModel] ModelContext is not set. Call setModelContext() first.")
```

---

## 10. ドキュメンテーション

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
///
/// 使用場所:
/// - {使用される場所1}
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

// Bad: コードを読めばわかることを書く
// カウントをインクリメント
count += 1
```
