---
name: ios-develop
description: iOS 17+/Swift 5.9+のベストプラクティスに基づいた実装を支援します。SwiftUI、@Observable、NavigationStack、ローカライズ、MVVM、Asset Catalog色管理、Liquid Glassデザインについて質問された場合に使用してください。
---

# iOS Development Skill

## 必須ルール

1. **@Observableを使用**（ObservableObject/@Publishedは非推奨）
2. **NavigationStackを使用**（NavigationViewは非推奨）
3. **色はAsset Catalogで一元管理**（ハードコード禁止）

## @Observable（iOS 17+）

```swift
@Observable
class UserSettings {
    var username: String = "Anonymous"
}

struct ProfileView: View {
    @Bindable var settings: UserSettings
    var body: some View {
        TextField("ユーザ名", text: $settings.username)
    }
}
```

## 色管理

```swift
// ✅ Asset Catalogから参照
Text("Welcome").foregroundStyle(Color("PrimaryText"))

// ❌ ハードコード禁止
Text("Welcome").foregroundStyle(.blue)
```

## フォルダ構成（機能別）

```
MyApp/
 ├── Features/
 │   ├── User/
 │   │   ├── Models/
 │   │   ├── Views/
 │   │   └── ViewModels/
 ├── Services/
 └── Resources/
```

## ローカライズ

```swift
let message = String(localized: "welcome_message", comment: "説明")
```

複数形は`.stringsdict`を使用。

## iOS 26 Liquid Glass（iOS 26+）

動的マテリアリティを持つ新しいUIパラダイム。

```swift
// 基本
Text("Hello").glassEffect()

// モーフィング
GlassEffectContainer(spacing: 20) {
    Button { }.glassEffect().glassEffectID("btn", in: ns)
}
```

**重要ポイント:**
- ネイティブAPI（`.glassEffect()`）を優先
- `GlassEffectContainer`で融合アニメーション
- レイヤーは2層まで

詳細は[LIQUID_GLASS.md](LIQUID_GLASS.md)を参照。

## Xcode以外での開発注意

- 新規ファイルはXcodeで追加（またはBuildable Folder使用）
- 定期的にXcodeでビルド確認

詳細は[REFERENCE.md](REFERENCE.md)を参照。
