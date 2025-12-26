---
name: ios-design
description: iOS 26のLiquid Glassデザインシステムの実装を支援します。glassEffect、GlassEffectContainer、モーフィングアニメーション、HIG準拠について質問された場合に使用してください。
---

# iOS Design - Liquid Glass デザインシステム

iOS 26で導入されたLiquid Glassデザインシステムの実装ガイドです。

## 重要: 実装前の確認事項

**コードを書く前に必ず以下を確認してください:**

1. **Swiftバージョンの確認**
   ```bash
   swift --version
   ```

2. **Context7で最新情報を取得**
   - Liquid GlassのAPIは進化中のため、実装前にContext7（MCP）で最新のSwiftUI APIを確認
   - 特に `glassEffect`、`GlassEffectContainer` の最新シグネチャを検証

3. **Xcodeバージョン**
   - Xcode 26以降が必要
   - iOS 26 SDKでビルド

---

## 概要

**Liquid Glass**は、iOS 7以来最大のUI刷新であり、visionOSの3D表現を2D画面に翻訳したデザイン言語です。

### 特徴

| 従来のデザイン | Liquid Glass |
|--------------|--------------|
| すりガラス（光を散乱） | レンズ効果（光を屈折） |
| 静的なシェイプ | 流体的な変形（モーフィング） |
| ドロップシャドウで深度表現 | 光学的深度で階層表現 |
| 固定の角丸 | デバイスと調和する同心円 |

---

## デザインの三原則

### 1. Hierarchy（階層性）
光学的深度でレイヤーを表現。ナビゲーションバーやタブバーはコンテンツの上に「浮かぶガラス」として描画される。

### 2. Harmony（調和）
UI要素の角丸はデバイスのディスプレイ角丸と数学的に調和。`GlassEffectContainer`が自動計算。

### 3. Consistency（一貫性）
流体としての振る舞い。近接した要素は表面張力のように融合（モーフィング）する。

---

## 基本実装

### .glassEffect() モディファイア

```swift
func glassEffect(
    _ style: Glass = .regular,
    in shape: some Shape = DefaultGlassEffectShape()
) -> some View
```

### マテリアルバリアント

| バリアント | 用途 |
|-----------|------|
| `.regular` | 標準。タブバー、ナビゲーションバー、ボタン |
| `.clear` | 透明度高。写真や地図の上に配置する場合 |
| `.identity` | エフェクトなし。条件付き無効化用 |

### 基本的なガラスボタン

```swift
Button(action: { /* action */ }) {
    Label("Explore", systemImage: "globe")
        .padding()
}
.glassEffect(.regular, in: Capsule())
```

### インタラクティブなガラスボタン

```swift
Button(action: { /* action */ }) {
    Label("Save", systemImage: "checkmark")
        .padding()
}
.glassEffect(
    .regular
        .tint(.blue)      // ガラスに色味を追加
        .interactive(),   // タッチフィードバック有効
    in: Capsule()
)
```

---

## 融合（モーフィング）

### GlassEffectContainer

複数のガラス要素を融合させるコンテナ。

```swift
GlassEffectContainer(spacing: 20) {
    // spacing より近い要素は融合する
    Button("Action 1") { }
        .glassEffect(.regular, in: Capsule())

    Button("Action 2") { }
        .glassEffect(.regular, in: Capsule())
}
```

### .glassEffectID でアニメーション追跡

状態変化時に「同じガラスが変形した」と認識させる。

```swift
struct MorphingMenu: View {
    @Namespace private var animation
    @State private var isExpanded = false

    var body: some View {
        GlassEffectContainer(spacing: 15) {
            VStack {
                Button {
                    withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                        isExpanded.toggle()
                    }
                } label: {
                    Image(systemName: isExpanded ? "xmark" : "plus")
                        .padding()
                }
                .glassEffect(.regular.interactive(), in: Circle())
                .glassEffectID("mainButton", in: animation)

                if isExpanded {
                    ForEach(["camera", "photo", "mic"], id: \.self) { icon in
                        Button { } label: {
                            Image(systemName: icon)
                                .padding()
                        }
                        .glassEffect(.regular.interactive(), in: Circle())
                        .glassEffectID(icon, in: animation)
                        .transition(.scale.combined(with: .opacity))
                    }
                }
            }
        }
    }
}
```

---

## ボタンスタイル

```swift
// 二次的アクション向け（透過度高）
Button("Cancel") { }
    .buttonStyle(.glass)

// プライマリアクション向け（不透明度高）
Button("Save") { }
    .buttonStyle(.glassProminent)
```

---

## HIG準拠ルール

### 適用すべき場所

- ナビゲーションバー
- タブバー
- サイドバー
- モーダルシート
- フローティングコントロール

### 禁止事項

- リストセルやカードの背景への適用（Blur Pile問題）
- カスタム背景色との併用（システムのガラス素材に任せる）

### タイポグラフィ

```swift
// Good: セマンティックカラーを使用
Text("Title")
    .foregroundStyle(.primary)

// Bad: 固定色（ガラス越しの視認性が保証されない）
Text("Title")
    .foregroundStyle(Color.white)
```

---

## アクセシビリティ対応

| 設定 | 効果 | 開発者対応 |
|------|------|-----------|
| 透明度を下げる | ガラス→ソリッドカラー | `.identity`フォールバックの確認 |
| 視差効果を減らす | モーフィング停止 | 瞬時切り替えでも機能するUI設計 |
| コントラストを上げる | ボーダー追加 | 余白の余裕を持たせる |

---

## クイックリファレンス

| 機能 | 従来 (〜iOS 25) | iOS 26 Liquid Glass |
|------|-----------------|---------------------|
| 素材適用 | `.background(.ultraThinMaterial)` | `.glassEffect(.regular)` |
| グループ化 | `HStack`, `ZStack` | `GlassEffectContainer(spacing:)` |
| アニメーション | `.matchedGeometryEffect` | `.glassEffectID(...)` |
| インタラクション | ボタンスタイル変更 | `.glassEffect(.interactive())` |
| アイコン | PNG/SVG画像 | Icon Composer（3層構造） |

---

## 詳細リファレンス

詳細なレンダリング仕様、アイコン設計、移行戦略は[REFERENCE.md](REFERENCE.md)を参照。
