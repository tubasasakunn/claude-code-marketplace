# iOS 26 Liquid Glass 技術リファレンス

iOS 26で導入された物理ベースの新しいマテリアルシステム。

## エグゼクティブサマリー

iOS 26の「Liquid Glass」は、過去10年で最も重要なHIGパラダイムシフト。iOS 7のフラットデザイン、Big Surの静的グラスモーフィズムを超え、**動的マテリアリティ（Dynamic Materiality）**を確立。

- **物理ベースレンダリング**: Metalパイプラインによるリアルタイム処理
- **リアルタイム光屈折**: レンズのように背景を歪ませる
- **流体相互作用**: メタボール技術による要素の融合・分離

---

## 第1章 哲学と物理的基盤

### 1.1 デザインの進化：静止画から流体へ

Liquid Glassは「Aqua」の光沢感とiOS 7以降の「機能的レイヤー構造」の統合。

- **スキューモーフィズム**: 静的なビットマップによる模倣
- **Liquid Glass**: センサーと演算能力を用いた「シミュレーション」

UI要素は高屈折率を持つ粘性流体として扱われ、ボタンはツールバーから分離（分化）し、不要になれば再び融合する。

### 1.2 光学特性：屈折、反射、レンズ効果

| 特性 | 説明 | 効果 |
|------|------|------|
| **リアルタイム屈折** | 背景を光学的に歪ませる（単純なブラーではない） | 物理的な厚みとボリューム感 |
| **スペキュラー反射** | ジャイロスコープ連動の反射ハイライト | 実在感と触れられる感覚 |
| **流動性（Fluidity）** | 表面張力による融合（メタボール技術） | 継ぎ目のない変形・合体 |

### 1.3 物理エンジンとSDF（符号付き距離場）

GlassEffectContainer内では、子ビューの形状が**符号付き距離場（SDF）**として解析される。

- 要素間距離が近づくとフィールドが干渉
- 自然な融合形状（フィレット）が動的に生成
- `spacing`プロパティ = 融合が起こる「近接閾値」

---

## 第2章 システム全体のデザイン言語

### 2.1 フローティング・ナビゲーション

画面端からUIが「剥離」し、浮遊する「島（Island）」として再定義。

| 要素 | iOS 18以前 | iOS 26 |
|------|-----------|--------|
| ボトムナビゲーション | 画面下端に固定 | 下端から浮いた角丸カプセル |
| ツールバー | 固定幅、静的配置 | コンテキストに応じて伸縮・分割 |
| プライマリアクション | ナビゲーション内 | 分離した独立ボタン |

### 2.2 プライマリアクションの分離

メッセージアプリの「新規作成」等は、ボトムナビゲーションから分離配置。

- スクロール・コンテキスト変化に応じて融合/変形
- 「現在の主要アクション」を直感的に伝達

### 2.3 アイコンと多層構造

ホーム画面アイコンは複数レイヤーで構成：
- 最前面：ガラス層
- 中間：グリフ（シンボル）層
- 背景層

デバイスを傾けると視差効果（パララックス）が発生。

---

## 第3章 レンダリングアーキテクチャ

### 3.1 Metalレンダリングパイプライン

1. **バックドロップサンプリング**: 背後コンテンツをキャプチャ・ダウンサンプリング
2. **SDF生成とモーフィング演算**: 統合距離場を計算、融合処理
3. **法線マップ生成**: SDFの勾配からレンズ効果の基礎を算出
4. **ライティングと屈折合成**: ピクセルシェーダーで最終合成

### 3.2 パフォーマンス最適化

- **Tile-Based Deferred Rendering**: 可視領域のみで高負荷シェーダー実行
- **キャッシング**: 静止状態ではSDF計算結果をキャッシュ
- **注意**: PhaseAnimatorで常時変化する場合は毎フレーム再計算

---

## 第4章 実装方針

### ネイティブAPI優先

**カスタム実装は避け、ネイティブAPIを使用すること。**

```swift
// ✅ 推奨：ネイティブAPI
Text("Hello")
    .glassEffect()

// ❌ 非推奨：カスタム実装
Text("Hello")
    .background(.ultraThinMaterial)
    .overlay(RoundedRectangle(...).stroke(...))
```

**理由:**
1. アクセシビリティ設定に自動対応
2. GPUレベルで最適化
3. OS全体のデザイン言語と調和
4. モーフィングはネイティブAPIでのみ実現可能

---

## 第5章 .glassEffect() 修飾子

### APIシグネチャ

```swift
func glassEffect(
    _ style: Glass = .regular,
    in shape: some Shape = .capsule,
    isEnabled: Bool = true
) -> some View
```

### スタイルバリアント

| バリアント | 説明 | 推奨ユースケース |
|-----------|------|-----------------|
| `.regular` | 標準。ライト/ダークに自動適応 | ツールバー、タブバー、FAB |
| `.clear` | 高透明。背景ディテールを保持 | 写真・地図上のオーバーレイ |
| `.identity` | 無効化。条件付きオン/オフに使用 | アクセシビリティ対応 |
| `.interactive()` | タッチ反応を有効化 | ボタン、トグル、リスト項目 |

### カラーティント

```swift
Image(systemName: "heart.fill")
    .glassEffect(.regular.tint(.red.opacity(0.4)).interactive(), in: .circle)
```

**注意**: 不透明度は0.3〜0.5程度を推奨。高すぎるとガラス質感が失われる。

### 推奨形状

| 形状 | 用途 |
|------|------|
| `Capsule` | ボタン、入力フィールド（デフォルト） |
| `Circle` | アイコンボタン、アバター |
| `RoundedRectangle` | カード、モーダル |
| `.rect(cornerRadius:.containerConcentric)` | ネストコンテナ |

---

## 第6章 GlassEffectContainer

### 基本的な融合

```swift
GlassEffectContainer(spacing: 20) {
    HStack(spacing: 15) {
        Image(systemName: "pencil").glassEffect()
        Image(systemName: "eraser").glassEffect()
    }
}
```

- **Container Spacing (20)**: 融合閾値
- **Layout Spacing (15)**: 実際のView間距離
- 距離(15) < 閾値(20) → 融合する

### glassEffectID によるモーフィング

```swift
@Namespace private var ns

if isExpanded {
    MenuView()
        .glassEffect()
        .glassEffectID("menu", in: ns)
} else {
    ButtonView()
        .glassEffect()
        .glassEffectID("menu", in: ns)
}
```

異なる形状・サイズ間でも滑らかに変形補間。

### glassEffectUnion

距離に関係なく同一のガラス形状として扱う：

```swift
.glassEffectUnion(id: "mediaPod", namespace: playerSpace)
```

---

## 第7章 高度なアニメーション

### 7.1 PhaseAnimatorによる有機的遷移

```swift
PhaseAnimator([false, true]) { morph in
    HStack(spacing: morph ? 50.0 : -15.0) {
        Circle().frame(width: 60, height: 60).glassEffect()
        Circle().frame(width: 60, height: 60).glassEffect()
    }
} animation: { _ in
    .easeInOut(duration: 1.5).repeatForever(autoreverses: true)
}
```

### 7.2 推奨アニメーションカーブ

| カーブ | 用途 |
|--------|------|
| `.bouncy` / `.spring` | 表面張力による揺らぎ |
| `.easeInOut` | 粘性の高い液体の動き |
| ❌ Linear | 機械的で不適切 |

---

## 第8章 実践的サンプルコード

### 8.1 モーフィング・アクションバー

```swift
import SwiftUI

struct LiquidActionBar: View {
    @State private var isExpanded = false
    @Namespace private var animationSpace

    var body: some View {
        ZStack(alignment: .bottom) {
            Image("NatureBackground")
                .resizable()
                .aspectRatio(contentMode: .fill)
                .edgesIgnoringSafeArea(.all)

            GlassEffectContainer(spacing: 15) {
                HStack(alignment: .center, spacing: 10) {
                    if isExpanded {
                        actionButton(icon: "square.and.arrow.up", id: "share")
                        actionButton(icon: "trash", id: "delete")
                        actionButton(icon: "checkmark", id: "save")
                    }

                    Button {
                        withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                            isExpanded.toggle()
                        }
                    } label: {
                        Image(systemName: isExpanded ? "xmark" : "pencil")
                            .font(.title2)
                            .fontWeight(.bold)
                            .frame(width: 60, height: 60)
                            .foregroundColor(.primary)
                    }
                    .glassEffect(.regular.interactive(), in: .circle)
                    .glassEffectID("mainButton", in: animationSpace)
                }
            }
            .padding(.bottom, 50)
        }
    }

    @ViewBuilder
    func actionButton(icon: String, id: String) -> some View {
        Button(action: { print("\(id) tapped") }) {
            Image(systemName: icon)
                .font(.headline)
                .frame(width: 50, height: 50)
                .foregroundColor(.primary)
        }
        .glassEffect(.regular.interactive(), in: .circle)
        .transition(.scale.combined(with: .opacity))
        .glassEffectID(id, in: animationSpace)
    }
}
```

### 8.2 呼吸するローダー

```swift
struct LiquidBreathingLoader: View {
    var body: some View {
        ZStack {
            Color.black.edgesIgnoringSafeArea(.all)

            GlassEffectContainer(spacing: 50) {
                PhaseAnimator([false, true]) { morph in
                    HStack(spacing: morph ? 50.0 : -15.0) {
                        Circle()
                            .frame(width: 60, height: 60)
                            .glassEffect(.regular.tint(.cyan), in: .circle)
                        Circle()
                            .frame(width: 60, height: 60)
                            .glassEffect(.regular.tint(.mint), in: .circle)
                    }
                } animation: { _ in
                    .easeInOut(duration: 1.5).repeatForever(autoreverses: true)
                }
            }
        }
    }
}
```

### 8.3 統合メディアコントロール

```swift
struct UnifiedMediaControl: View {
    @Namespace private var playerSpace

    var body: some View {
        ZStack {
            LinearGradient(colors: [.purple, .blue], startPoint: .top, endPoint: .bottom)
                .edgesIgnoringSafeArea(.all)

            GlassEffectContainer(spacing: 0) {
                HStack(spacing: 5) {
                    controlButton(icon: "backward.fill", id: "rewind")

                    Button(action: {}) {
                        Image(systemName: "play.fill")
                            .font(.system(size: 40))
                            .frame(width: 80, height: 80)
                    }
                    .glassEffect(.regular.interactive(), in: .circle)
                    .glassEffectUnion(id: "mediaPod", namespace: playerSpace)

                    controlButton(icon: "forward.fill", id: "forward")
                }
            }
        }
    }

    func controlButton(icon: String, id: String) -> some View {
        Button(action: {}) {
            Image(systemName: icon)
                .font(.title2)
                .frame(width: 60, height: 60)
        }
        .glassEffect(.regular.interactive(), in: .circle)
        .glassEffectUnion(id: "mediaPod", namespace: playerSpace)
    }
}
```

---

## 第9章 iOS 26.2の進化

### 9.1 不透明度調整の標準化

初期リリースの「視認性」批判に対応：

```swift
@Environment(\.glassOpacityPreference) var glassOpacity
```

**不透明度スライダー**: ユーザーが設定で調整可能
- 左スライド：クリアで読みやすい
- 右スライド：半透明で夢のような状態

### 9.2 可読性の向上

- テキストの下にLiquid Glassを敷く場合は**Vibrancy**エフェクトを併用
- ロック画面の時計は完全な透明度制御が可能に

### 9.3 ライブアクティビティへの影響

ウィジェット背景がLiquid Glassの場合、不透明度変化でもデザインが破綻しないようテストが必要。

---

## 第10章 UIKit統合

### UIGlassEffectの使用

```swift
let glassEffect = UIGlassEffect(style: .regular)
glassEffect.isInteractive = true

let visualEffectView = UIVisualEffectView(effect: glassEffect)
visualEffectView.frame = button.bounds
visualEffectView.layer.cornerRadius = 20
visualEffectView.layer.cornerCurve = .continuous
visualEffectView.clipsToBounds = true

button.insertSubview(visualEffectView, at: 0)
```

### 制約

- **UIKit**: 単体ビューへの効果のみ
- **モーフィング融合**: サポートなし → SwiftUIを埋め込み推奨

### UINavigationBarとの競合解消

```swift
if #available(iOS 26.0, *) {
    barButtonItem.hidesSharedBackground = true
}
```

---

## 第11章 タブバーの実装

### 標準的な実装

```swift
TabView {
    HomeView()
        .tabItem { Label("Home", systemImage: "house") }
    SettingsView()
        .tabItem { Label("Settings", systemImage: "gear") }
}
.tabBarMinimizeBehavior(.onScrollDown)
```

### 検索ロール

```swift
Tab("Search", systemImage: "magnifyingglass", role: .search) {
    SearchView()
}
```

- 他タブから視覚的に分離
- iPadでは独立した検索フィールドとして再配置

### タブバーアクセサリビュー

```swift
.tabViewBottomAccessory {
    Button("New Post") { }
        .buttonStyle(.glass)
}
```

---

## 第12章 検索モーフィング完全実装

```swift
struct LiquidSearchContainer: View {
    @Namespace private var ns
    @State private var isSearching = false
    @State private var searchText = ""

    var body: some View {
        ZStack(alignment: .bottom) {
            LinearGradient(colors: [.blue, .purple], startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            VStack {
                Spacer()
                GlassEffectContainer(spacing: 20) {
                    if isSearching {
                        HStack {
                            Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                            TextField("Search...", text: $searchText).textFieldStyle(.plain)
                            Button {
                                withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                                    isSearching = false
                                    searchText = ""
                                }
                            } label: {
                                Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                            }
                        }
                        .padding()
                        .frame(height: 60)
                        .frame(maxWidth: .infinity)
                        .glassEffect(.regular, in: .capsule)
                        .glassEffectID("search_interface", in: ns)
                        .padding(.horizontal)
                    } else {
                        HStack(spacing: 30) {
                            ForEach(0..<3) { idx in
                                Image(systemName: ["house", "heart", "person"][idx])
                                    .frame(width: 50, height: 50)
                                    .glassEffect(.regular.interactive(), in: .circle)
                            }
                            Button {
                                withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                                    isSearching = true
                                }
                            } label: {
                                Image(systemName: "magnifyingglass")
                                    .font(.title2)
                                    .frame(width: 60, height: 60)
                                    .foregroundStyle(.white)
                            }
                            .glassEffect(.regular.tint(.white.opacity(0.2)).interactive(), in: .circle)
                            .glassEffectID("search_interface", in: ns)
                        }
                        .padding(.bottom, 20)
                    }
                }
            }
        }
    }
}
```

---

## 第13章 ベストプラクティス

### 過剰使用の回避

**「Liquid Glassはスパイスであり、主食ではない」**

| 状況 | 推奨 |
|------|------|
| ❌ リストセル全てにLiquid Glass | GPU負荷増大、視覚的に「うるさい」 |
| ✅ 浮遊する作成ボタンやツールバーのみ | 階層構造が明確に |

### レイヤー数制限

- 画面上のLiquid Glassレイヤーは**2層まで**
- モーダル表示時は背面を`.identity`に

### 背景の設計

```swift
// ✅ グラデーション・画像
LinearGradient(colors: [.blue, .purple], startPoint: .top, endPoint: .bottom)

// ❌ 単色（ガラス効果が活きない）
Color.black
```

---

## 第14章 アクセシビリティ

### 透明度を下げる設定

Liquid Glassは自動でフロスティング強度を上げ、不透明度を増加。

### テキスト色

```swift
// ❌ 固定の白
.foregroundStyle(.white)

// ✅ セマンティックカラー
.foregroundStyle(.primary)
.foregroundStyle(.secondary)
```

### reduceMotion対応

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

if reduceMotion {
    // 静的なすりガラス表示
} else {
    // モーフィングアニメーション
}
```

---

## 第15章 Glass Card構築

### 基本実装

```swift
struct GlassCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Liquid Glass UI")
                .font(.headline)
                .foregroundStyle(.primary)
            Text("Refraction & Depth Simulation")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(20)
        .glassEffect(.regular, in: RoundedRectangle(cornerRadius: 24))
        .shadow(color: .black.opacity(0.15), radius: 10, x: 0, y: 5)
    }
}
```

### シャドウ設計

#### 色付きシャドウ（推奨）

```swift
// ✅ クリアな浮遊感
.shadow(color: Color.blue.opacity(0.3), radius: 20, x: 0, y: 10)
```

#### 二重シャドウ（高品質）

```swift
.shadow(color: .black.opacity(0.08), radius: 30, x: 0, y: 15)  // Ambient
.shadow(color: .black.opacity(0.15), radius: 8, x: 0, y: 4)    // Key
```

---

## 第16章 UI/UX設計フレームワーク

### Push vs Sheet

| 判定要素 | Push遷移 | Sheet遷移（Liquid Glass向き） |
|---------|---------|------------------------------|
| コンテキスト | 継続的（リスト→詳細） | 一時的（新規作成） |
| メンタルモデル | 「奥に進む」 | 「上に乗せる」 |

**Liquid GlassにはSheetが最適**: 背景が透けてコンテキストを維持。

### ボタン配置

| 位置 | 用途 |
|------|------|
| 画面下部 | プライマリアクション（新規作成、再生） |
| 画面右上 | セカンダリ/完了/破壊的操作 |

### タブ項目数

- iPhone: 3〜5個（最大5）
- iPad: サイドバーに変形

---

## 付録A：APIリファレンス早見表

### 修飾子

| 修飾子 | パラメータ | 説明 |
|--------|-----------|------|
| `.glassEffect` | `style: Glass` | マテリアル種類 |
| | `in: Shape` | 形状（デフォルト: .capsule） |
| | `isEnabled: Bool` | 条件付き無効化 |
| `GlassEffectContainer` | `spacing: CGFloat` | 融合閾値 |
| `.glassEffectID` | `id: Hashable` | モーフィング同一性追跡 |
| `.glassEffectUnion` | `id: Hashable` | 強制的な一体化レンダリング |
| `.interactive()` | なし | タッチ反応有効化 |

### デザインパターン比較

| 特徴 | iOS 18 | iOS 26 |
|------|--------|--------|
| 素材感 | 静的ぼかし | 動的屈折・反射 |
| ナビゲーション | 固定バー | 浮遊カプセル |
| アイコン | 平面グリフ | 多層構造・視差 |
| アニメーション | 線形・スプリング | 流体モーフィング |
| 物理挙動 | なし | ジャイロ反射・流体シミュレーション |

---

## 付録B：Figmaハンドオフ設定値

### Liquid Glass カード

| プロパティ | 値 |
|-----------|-----|
| Background Blur | 20〜40 |
| Fill | #FFFFFF 10〜20% |
| Inner Shadow (Top) | Y: +1, Blur: 0, White 50% |
| Inner Shadow (Bottom) | Y: -1, Blur: 0, White 10% |
| Drop Shadow | Blur: 30, Y: 15, Black 15% |
| Corner Radius | 16〜24 |

### グラデーションボーダー

```
Linear Gradient Stroke:
  - Start (Top-Left): White 60%
  - End (Bottom-Right): White 10%
  - Width: 1px
```

---

## 付録C：フォールバック実装（iOS 25以前）

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
