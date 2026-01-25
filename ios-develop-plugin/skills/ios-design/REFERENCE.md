# iOS Design - Liquid Glass 技術リファレンス

iOS 26 Liquid Glassの実装に必要な技術仕様。

---

## 重要: 実装前の確認

Liquid GlassのAPIは進化中。実装前に必ず確認:
1. Swiftバージョン: `swift --version`
2. Context7で最新API取得（`glassEffect`, `GlassEffectContainer`）
3. Apple HIG最新版

---

## SwiftUI API

### .glassEffect()

```swift
func glassEffect(
    _ style: Glass = .regular,
    in shape: some Shape = DefaultGlassEffectShape()
) -> some View

// メソッドチェーン
.glassEffect(
    .regular
        .tint(Color)       // 色味付加
        .interactive(),    // タッチ操作への物理挙動
    in: Capsule()          // 形状指定
)
```

### GlassEffectContainer

```swift
GlassEffectContainer(spacing: CGFloat) {
    // glassEffectを持つ複数のビュー
}
```

**spacingの挙動**:
- 要素間距離 < spacing → 境界が液状化し結合
- 要素間距離 > spacing → 分離

### .glassEffectID

`matchedGeometryEffect`のLiquid Glass専用拡張:

```swift
@Namespace private var animation
.glassEffectID("identifier", in: animation)
```

### ボタンスタイル

```swift
.buttonStyle(.glass)           // 二次的アクション
.buttonStyle(.glassProminent)  // プライマリアクション
```

---

## マテリアルバリアント

| バリアント | 特徴 | 用途 |
|-----------|------|------|
| Regular | 適度なぼかしと屈折 | TabBar, NavigationBar, ボタン |
| Clear | 透明度高、ぼかし最小 | 写真・地図の上 |
| Identity | エフェクトなし | 条件付き無効化時 |

---

## HIG要点

### 適用ルール

**適用場所（最上位レイヤーのみ）**:
- NavigationBar, TabBar, Sidebar
- Modal, FloatingControl

**禁止**:
- リストセル・カード背景（Blur Pile発生）
- カスタム背景色との併用
- 不透明背景（Color.white等）

### タイポグラフィ

```swift
// Good: システムがVibrancyフィルター適用
Text("Title").foregroundStyle(.primary)

// Bad: コントラスト不足リスク
Text("Title").foregroundStyle(Color.white)
```

- フォントウェイトは**Medium以上**

---

## アクセシビリティ

| 設定 | 効果 | 確認項目 |
|------|------|---------|
| 透明度を下げる | ソリッドカラー化 | `.identity`フォールバック |
| 視差効果を減らす | モーフィング停止 | 瞬時切り替えの動作 |
| コントラストを上げる | ボーダー追加 | レイアウト崩れ |

**必ずアクセシビリティ設定ONでテスト**

---

## 移行例

```swift
// Before (iOS 25以前)
Button("Save") { }
    .background(Color.blue)
    .cornerRadius(8)
.toolbarBackground(Color.white, for: .navigationBar)

// After (iOS 26)
Button("Save") { }
    .glassEffect(.regular.tint(.blue).interactive(), in: Capsule())
.toolbarBackground(.visible, for: .navigationBar)
```

---

## クイックリファレンス

| 機能 | 従来 (〜iOS 25) | iOS 26 Liquid Glass |
|------|-----------------|---------------------|
| 素材適用 | `.background(.ultraThinMaterial)` | `.glassEffect(.regular)` |
| グループ化 | `HStack`, `ZStack` | `GlassEffectContainer(spacing:)` |
| アニメーション | `.matchedGeometryEffect` | `.glassEffectID(...)` |
| 背景 | `Color.white` | システムのガラス素材に委譲 |
