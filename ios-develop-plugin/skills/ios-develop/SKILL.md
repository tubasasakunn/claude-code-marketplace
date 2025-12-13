# iOS Development Skill

iOS/Swift開発のベストプラクティスに基づいた実装を支援するスキルです。

## 対象

- iOS 17以降 / Swift 5.9以降のアプリ開発
- SwiftUIを中心としたモダンなUI実装
- Xcode以外のエディタ（Cursor、VSCodeなど）での開発

---

## 1. 最新のSwiftとSwiftUIの記法（iOS 17 / Swift 5.9以降）

### 条件式の簡潔化

`if`や`switch`が式として使え、値を直接返せる：

```swift
let labelColor = if isError {
    Color.red
} else if isWarning {
    Color.yellow
} else {
    Color.primary
}
```

### パラメータパック

ジェネリクスの拡張により、SwiftUIで11個以上の子ビューを持つコンテナが直接記述可能になった。

### マクロ機能

`@Observable`マクロにより状態管理が簡潔に：

```swift
import SwiftUI

@Observable
class UserSettings {
    var username: String = "Anonymous"
    // 従来必要だった ObservableObject や @Published の記述が不要
}

struct ProfileView: View {
    @Bindable var settings: UserSettings
    var body: some View {
        TextField("ユーザ名", text: $settings.username)
            .padding()
    }
}
```

従来の書き方（iOS 16以前）：

```swift
class UserSettings: ObservableObject {
    @Published var username: String = "Anonymous"
}

struct ProfileView: View {
    @ObservedObject var settings = UserSettings()
    var body: some View {
        TextField("ユーザ名", text: $settings.username)
    }
}
```

### NavigationStack

iOS 16以降は`NavigationView`ではなく`NavigationStack`/`NavigationSplitView`を使用する。

---

## 2. 多言語化（ローカライズ）

### Localizable.stringsと.stringsdict

基本的な文字列：

```
// Base.lproj/Localizable.strings
"welcome_message" = "Welcome!";
"item_count_message" = "%d items remaining";

// ja.lproj/Localizable.strings
"welcome_message" = "ようこそ！";
"item_count_message" = "%d 個のアイテムが残っています";
```

複数形対応（.stringsdict）：

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

### String(localized:) API

```swift
let message = String(localized: "welcome_message", comment: "ホーム画面挨拶文")
```

### 画像のローカライズ

Asset Catalog内で画像セットを選択し、インスペクタの「Localization」で言語を追加。コードは`Image("Hello")`のまま、言語設定に応じて自動で切り替わる。

---

## 3. アーキテクチャ（MVVM、ファイル構成、モジュール分割）

### MVVMパターン

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

    func addTask(_ task: Task) {
        tasks.append(task)
    }
}

// View
struct TaskListView: View {
    @Bindable var viewModel: TaskViewModel
    var body: some View {
        List(viewModel.tasks) { task in
            Text(task.title)
        }
        .toolbar {
            Button("Add Sample") {
                viewModel.addTask(Task(title: "Sample", due: Date()))
            }
        }
    }
}
```

### フォルダ構成

**小規模プロジェクト：**

```
MyApp/
 ├── MyAppApp.swift
 ├── Models/
 │   └── User.swift
 ├── Views/
 │   ├── ContentView.swift
 │   └── UserDetailView.swift
 ├── ViewModels/
 │   └── UserViewModel.swift
 └── Resources/
     └── Assets.xcassets
```

**中規模プロジェクト（機能別構成）：**

```
MyApp/
 ├── MyAppApp.swift
 ├── Features/
 │   ├── User/
 │   │   ├── Models/
 │   │   ├── Views/
 │   │   └── ViewModels/
 │   ├── Post/
 │   │   ├── Models/
 │   │   ├── Views/
 │   │   └── ViewModels/
 │   └── Comment/
 ├── Services/
 │   ├── NetworkService.swift
 │   └── DatabaseService.swift
 └── Resources/
     ├── Assets.xcassets
     └── Localizable.strings
```

### モジュール分割

大規模プロジェクトではSwift Package Managerでモジュールを分割：
- ビルド時間の短縮
- チーム開発の分離
- コードの再利用性向上

---

## 4. Xcode以外のエディタでの開発注意点

### プロジェクトファイル管理

- 新規ファイル作成時は**Xcodeでファイルを追加する**か、**Xcode 16+のBuildable Folder機能**を使用
- VSCodeで直接ファイルを作成しても.xcodeprojに反映されない

### 依存管理

- CocoaPods使用時は.xcworkspace経由で作業
- **可能な限りSwift Package Managerへ移行推奨**

### Info.plist

- ファイル名は厳密に`Info.plist`（大文字小文字含む）
- 外部エディタで編集時はXML構文ミスに注意

### 定期的な確認

- Xcodeで定期的にビルド＆実行テストを行う
- 参照切れファイルがないか確認

---

## 5. AI生成コードのXcode互換性

### チェックリスト

- [ ] Info.plistが存在し、正しい名前か
- [ ] @main属性を持つApp構造体があるか（SwiftUIアプリの場合）
- [ ] ファイルがターゲットメンバーシップに含まれているか
- [ ] 非推奨API（NavigationViewなど）を使用していないか
- [ ] リソースパスが正しいか（Asset Catalog vs バンドル直下）

### 注意点

- AIが古いSwift構文を生成する可能性あり
- 必ずコンパイルしてDeprecation警告を確認
- ユニットテスト・実機テストで動作確認

---

## 6. 色とスタイルの一元管理

### Asset Catalogでの色管理（必須）

1. Assets.xcassetsを開く
2. 「+」→「Color Set」を選択
3. 役割ベースの命名：`PrimaryText`, `BackgroundPrimary`, `AccentButton`など
4. Light/Dark Appearanceそれぞれの色を設定

### コードでの使用

```swift
// ✅ 正しい書き方 - Asset Catalogから参照
Text("Welcome")
    .foregroundStyle(Color("PrimaryText"))
    .background(Color("BackgroundPrimary"))

Button("Submit") {
    // action
}
.foregroundStyle(Color("AccentColor"))
.background(Color("ButtonBackground"))
```

```swift
// ❌ 絶対に避ける - ハードコード
Text("Welcome")
    .foregroundStyle(.blue)
    .background(.white)

// ❌ RGB値の直接指定
Color(red: 0.2, green: 0.5, blue: 0.8)
```

### Color Extension（オプション）

```swift
extension Color {
    static let primaryText = Color("PrimaryText")
    static let backgroundPrimary = Color("BackgroundPrimary")
    static let accentButton = Color("AccentButton")
}

// 使用例
Text("Welcome")
    .foregroundStyle(.primaryText)
```

---

## 7. iOS 26 Liquid Glassデザイン

### 設計思想

- グラデーションなどの人工的な装飾を排除
- 光学的なリアリティと流体的なモーションで構成
- 背景コンテンツを透過・屈折させてUIの存在を示す

### 3つの柱

| 柱 | 概要 | 実装キーワード |
|---|---|---|
| Crystal Clarity | 水晶のように透き通った質感 | `blendMode(.overlay)`, low blur radius |
| Fluidity | 液体のように融合・分離するUI | `Canvas`, `alphaThreshold`, Metaballs |
| Refraction | レンズのように光を曲げる | Metal Shader, `distortionEffect` |

### CrystalGlassModifier実装

```swift
import SwiftUI

struct CrystalGlassModifier: ViewModifier {
    var cornerRadius: CGFloat = 24.0
    var blurStyle: Material = .ultraThinMaterial
    var whiteOpacity: Double = 0.1

    func body(content: Content) -> some View {
        content
            .background {
                ZStack {
                    // 屈折レイヤー
                    Rectangle()
                        .fill(blurStyle)
                        .environment(\.colorScheme, .light)
                        .opacity(0.6)

                    // 質感レイヤー
                    Color.white.opacity(whiteOpacity)
                        .blendMode(.overlay)
                }
                .clipShape(RoundedRectangle(cornerRadius: cornerRadius, style: .continuous))
                .shadow(color: Color.black.opacity(0.1), radius: 10, x: 0, y: 8)

                // エッジライト
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

### Liquid Tab Bar（Metaballs）

```swift
import SwiftUI

struct LiquidTabBar: View {
    @State var selectedTab: Int = 0
    let icons = ["house.fill", "magnifyingglass", "bell.fill", "person.fill"]

    var body: some View {
        ZStack(alignment: .bottom) {
            Color.black.ignoresSafeArea()

            Canvas { context, size in
                context.addFilter(.alphaThreshold(min: 0.5, color: .white))
                context.addFilter(.blur(radius: 15))

                context.drawLayer { ctx in
                    let barHeight: CGFloat = 80
                    let barRect = CGRect(x: 0, y: size.height - barHeight, width: size.width, height: barHeight)
                    ctx.fill(Path(roundedRect: barRect, cornerRadius: 30), with: .color(.white))

                    let tabWidth = size.width / CGFloat(icons.count)
                    let xPosition = tabWidth * CGFloat(selectedTab) + (tabWidth / 2)
                    let circleSize: CGFloat = 60
                    let indicatorCenter = CGPoint(x: xPosition, y: size.height - barHeight + 10)

                    ctx.fill(
                        Circle().path(in: CGRect(
                            x: indicatorCenter.x - circleSize/2,
                            y: indicatorCenter.y - circleSize/2,
                            width: circleSize,
                            height: circleSize
                        )),
                        with: .color(.white)
                    )
                }
            }
            .frame(height: 120)
            .opacity(0.8)
            .blendMode(.hardLight)

            HStack(spacing: 0) {
                ForEach(0..<icons.count, id: \.self) { index in
                    Button(action: {
                        withAnimation(.spring(response: 0.5, dampingFraction: 0.7)) {
                            selectedTab = index
                        }
                    }) {
                        Image(systemName: icons[index])
                            .font(.system(size: 24, weight: .bold))
                            .foregroundColor(selectedTab == index ? .black : .gray)
                            .frame(maxWidth: .infinity)
                            .frame(height: 80)
                            .offset(y: selectedTab == index ? -10 : 0)
                    }
                }
            }
            .frame(height: 80)
        }
    }
}
```

### Metal Shader（屈折効果）

**LiquidGlass.metal:**

```cpp
#include <metal_stdlib>
#include <SwiftUI/SwiftUI_Metal.h>
using namespace metal;

[[ stitchable ]] half4 refractiveGlass(
    float2 position,
    SwiftUI::Layer layer,
    float2 size,
    float time,
    float strength
) {
    float2 uv = position / size;

    // 液体の揺らぎ
    float flowX = sin(uv.y * 10.0 + time) * 0.005;
    float flowY = cos(uv.x * 12.0 + time * 1.2) * 0.005;

    // レンズ歪み
    float2 center = size / 2.0;
    float2 toCenter = position - center;
    float dist = length(toCenter);
    float lensDistortion = (dist / length(center)) * strength * 20.0;

    float2 distortedPosition = position + float2(flowX * size.x, flowY * size.y) - (toCenter * lensDistortion * 0.01);

    half4 color = layer.sample(distortedPosition);

    // スペキュラー
    float gloss = smoothstep(0.8, 0.95, uv.y + flowX * 2.0);
    color += half4(gloss * 0.15);

    return color;
}
```

**SwiftUIからの呼び出し:**

```swift
import SwiftUI

struct RefractiveView: View {
    var body: some View {
        TimelineView(.animation) { context in
            let time = context.date.timeIntervalSinceReferenceDate

            ZStack {
                Image("colorful_background")
                    .resizable()
                    .aspectRatio(contentMode: .fill)
                    .ignoresSafeArea()

                RoundedRectangle(cornerRadius: 30, style: .continuous)
                    .fill(.white.opacity(0.1))
                    .frame(width: 300, height: 200)
                    .layerEffect(
                        ShaderLibrary.refractiveGlass(
                            .float2(CGSize(width: 300, height: 200)),
                            .float(time),
                            .float(0.5)
                        ),
                        maxSampleOffset: .zero
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 30, style: .continuous)
                            .stroke(.white.opacity(0.3), lineWidth: 1)
                    )
            }
        }
    }
}
```

### アクセシビリティ対応

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

// reduceMotion が true の場合は静的なすりガラス表示に切り替え
```

---

## ベストプラクティスまとめ

1. **Swift 5.9+の新機能を活用**（@Observable、if式、パラメータパック）
2. **NavigationStackを使用**（NavigationViewは非推奨）
3. **色はAsset Catalogで一元管理**（ハードコード禁止）
4. **MVVMアーキテクチャを採用**
5. **機能別フォルダ構成**で整理
6. **Xcode以外で開発時は定期的にXcodeでビルド確認**
7. **Liquid Glassデザインはグラデーション排除、光学効果で表現**
