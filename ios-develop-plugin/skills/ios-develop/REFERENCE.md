# iOS Development Reference

詳細なリファレンス情報です。

## 1. Swift 5.9+ 新機能

### 条件式

```swift
let labelColor = if isError { Color.red } else { Color.primary }
```

### パラメータパック

SwiftUIで11個以上の子ビューを持つコンテナが直接記述可能。

## 2. ローカライズ詳細

### Localizable.strings

```
// Base.lproj/Localizable.strings
"welcome_message" = "Welcome!";

// ja.lproj/Localizable.strings
"welcome_message" = "ようこそ！";
```

### 複数形対応（.stringsdict）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>item_count_message</key>
    <dict>
        <key>NSStringLocalizedFormatKey</key>
        <string>%#@items@</string>
        <key>items</key>
        <dict>
            <key>NSStringFormatSpecTypeKey</key>
            <string>NSStringPluralRuleType</string>
            <key>NSStringFormatValueTypeKey</key>
            <string>d</string>
            <key>one</key>
            <string>%d item remaining</string>
            <key>other</key>
            <string>%d items remaining</string>
        </dict>
    </dict>
</dict>
</plist>
```

### 画像のローカライズ

Asset Catalogで画像セット選択→インスペクタの「Localization」で言語追加。

## 3. MVVMパターン

```swift
// Model
struct Task {
    let title: String
    let due: Date
}

// ViewModel (iOS 17+)
@Observable
class TaskViewModel {
    var tasks: [Task] = []
    func addTask(_ task: Task) { tasks.append(task) }
}

// View
struct TaskListView: View {
    @Bindable var viewModel: TaskViewModel
    var body: some View {
        List(viewModel.tasks) { task in
            Text(task.title)
        }
    }
}
```

## 4. Color Extension

```swift
extension Color {
    static let primaryText = Color("PrimaryText")
    static let backgroundPrimary = Color("BackgroundPrimary")
}

// 使用例
Text("Welcome").foregroundStyle(.primaryText)
```

## 5. AI生成コードチェックリスト

- [ ] Info.plistが存在し、正しい名前か
- [ ] @main属性を持つApp構造体があるか
- [ ] ファイルがターゲットメンバーシップに含まれているか
- [ ] 非推奨API（NavigationView等）を使用していないか

## 6. iOS 26 Liquid Glassデザイン

詳細は[LIQUID_GLASS.md](LIQUID_GLASS.md)を参照。

### ネイティブAPI（iOS 26+）

```swift
// 基本
Text("Hello")
    .glassEffect()

// 形状とティント指定
Button("Action") { }
    .glassEffect(.regular.tint(.blue), in: RoundedRectangle(cornerRadius: 16))

// インタラクティブ
Button("Submit") { }
    .glassEffect(.regular.interactive())
```

### モーフィング

```swift
@Namespace private var ns

GlassEffectContainer(spacing: 20) {
    Button { } label: { Image(systemName: "plus") }
        .glassEffect()
        .glassEffectID("main", in: ns)
}
```

### フォールバック実装（iOS 25以前）

```swift
struct CrystalGlassModifier: ViewModifier {
    var cornerRadius: CGFloat = 24.0
    var blurStyle: Material = .ultraThinMaterial

    func body(content: Content) -> some View {
        content
            .background {
                ZStack {
                    Rectangle()
                        .fill(blurStyle)
                        .environment(\.colorScheme, .light)
                        .opacity(0.6)
                    Color.white.opacity(0.1)
                        .blendMode(.overlay)
                }
                .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
                .shadow(color: Color.black.opacity(0.1), radius: 10, x: 0, y: 8)

                RoundedRectangle(cornerRadius: cornerRadius, style: .continuous)
                    .strokeBorder(
                        LinearGradient(
                            stops: [
                                .init(color: .white.opacity(0.6), location: 0.0),
                                .init(color: .white.opacity(0.2), location: 0.3),
                                .init(color: .white.opacity(0.05), location: 0.5),
                                .init(color: .white.opacity(0.3), location: 1.0)
                            ],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        ),
                        lineWidth: 1.0
                    )
                    .blendMode(.screen)
            }
    }
}

extension View {
    func liquidGlass(cornerRadius: CGFloat = 24) -> some View {
        self.modifier(CrystalGlassModifier(cornerRadius: cornerRadius))
    }
}
```

### アクセシビリティ

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion
// reduceMotion が true の場合は静的なすりガラス表示に切り替え
```
