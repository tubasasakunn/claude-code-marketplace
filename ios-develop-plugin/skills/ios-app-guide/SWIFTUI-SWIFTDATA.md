# SwiftUI / SwiftData の注意点

## 必須: import SwiftData

`.modelContainer()` や `modelContext.delete()` 等を使う**全ファイル**で `import SwiftData` が必要。忘れるとビルドエラーになる。

## Lightweight Migration

新フィールド追加時は**必ずデフォルト値**を設定する:

```swift
// OK: デフォルト値あり → マイグレーション成功
var rating: Int = 0

// NG: デフォルト値なし → クラッシュの可能性
var rating: Int  // 既存データが壊れる
```

## @Attribute(.unique)

```swift
@Model
final class Movie {
    @Attribute(.unique) var tmdbId: Int  // 重複防止
}
```

## @Query でのソート

```swift
@Query(sort: \Movie.addedAt, order: .reverse) private var movies: [Movie]
```
