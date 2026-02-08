# ナビゲーション・UIKit との統合

## ナビバー・タブバーの透過（最終的な正解）

```swift
// AppDelegate で UIAppearance を設定
class AppDelegate: NSObject, UIApplicationDelegate {
    func application(_ application: UIApplication,
                     didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil) -> Bool {
        // ナビゲーションバー
        let navAppearance = UINavigationBarAppearance()
        navAppearance.configureWithTransparentBackground()
        UINavigationBar.appearance().standardAppearance = navAppearance
        UINavigationBar.appearance().scrollEdgeAppearance = navAppearance

        // タブバー
        let tabAppearance = UITabBarAppearance()
        tabAppearance.configureWithTransparentBackground()
        UITabBar.appearance().standardAppearance = tabAppearance
        UITabBar.appearance().scrollEdgeAppearance = tabAppearance

        return true
    }
}
```

各画面で以下を設定:

```swift
.toolbarBackgroundVisibility(.hidden, for: .navigationBar)
.toolbarBackgroundVisibility(.hidden, for: .tabBar)
```

## .searchable の問題と代替

`.searchable` モディファイアは背景色のカスタマイズが困難。カスタム `SearchBar` を推奨:

```swift
struct SearchBar: View {
    @Binding var text: String
    @FocusState private var isFocused: Bool

    var body: some View {
        HStack {
            Image(systemName: "magnifyingglass")
            TextField("検索", text: $text)
                .focused($isFocused)
            if !text.isEmpty {
                Button { text = "" } label: {
                    Image(systemName: "xmark.circle.fill")
                }
            }
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.ultraThinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}
```

## 試行錯誤の記録

ナビバー透過は6回の試行が必要だった。SwiftUIだけでは制御不足で、UIAppearance（AppDelegate）でのグローバル設定 + `.toolbarBackgroundVisibility(.hidden)` の組み合わせが最終解。
