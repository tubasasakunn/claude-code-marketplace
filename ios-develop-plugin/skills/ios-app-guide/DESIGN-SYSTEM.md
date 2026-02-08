# デザインシステムの構築

## DesignTokens（定数の一元管理）

```swift
enum DesignTokens {
    enum Spacing {
        static let xs: CGFloat = 4
        static let sm: CGFloat = 8
        static let md: CGFloat = 16
        static let lg: CGFloat = 24
        static let xl: CGFloat = 32
    }
    enum CornerRadius {
        static let sm: CGFloat = 8
        static let md: CGFloat = 12
        static let lg: CGFloat = 16
    }
    enum Grid {
        static let columns = 3
        static let edgePadding: CGFloat = 1
    }
}
```

## セマンティックカラー

```swift
extension Color {
    static var backgroundPrimary: Color { /* テーマに応じた背景色 */ }
    static var backgroundSecondary: Color { /* テーマに応じたセカンダリ背景色 */ }
    static var textPrimary: Color { /* テーマに応じたテキスト色 */ }
    static var textSecondary: Color { /* テーマに応じたサブテキスト色 */ }
    static var themeAccent: Color { ThemeManager.shared.accentColor }
}
```

## テーマシステムの設計

各テーマに必要なもの:
- `accentColor` - アクセントカラー
- `backgroundColor` - ライト用背景
- `darkBackgroundColor` - ダーク用背景
- `iconName` - SF Symbols アイコン名
- `displayName` - 表示名

テーマ例:
- ライト: blue, purple, pink, red, orange, green（6色）
- ダーク: teal, indigo, brown, navy, wine, charcoal（6色）

**Tips:**
- `Color.mix` で背景にアクセントカラーをティントすると統一感が出る
- テーマカラーはライトモード・ダークモードの**両方**で背景色を用意する
