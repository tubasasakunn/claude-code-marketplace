# iOS 26 Liquid Glass 技術リファレンス

iOS 26で導入された物理ベースの新しいマテリアルシステム。

## 設計思想

Liquid Glassは単なる視覚効果（VFX）ではなく、UIコンポーネントの「状態」と「関係性」を物理的に表現するための**機能的マテリアル**。

### 3つの柱

| 柱 | 概要 |
|----|------|
| Crystal Clarity | 水晶のように透き通った質感。背景コンテンツを透過・屈折させてUIの存在を示す |
| Fluidity | 液体のように融合・分離するUI。要素同士が近づくと水滴のように結合 |
| Refraction | レンズのように光を曲げる。厚みと深度を表現 |

### 従来デザインからの脱却

- グラデーションなどの人工的な装飾を排除
- 光学的なリアリティと流体的なモーションで構成
- 背景コンテンツを透過・屈折させてUIの存在を示す

---

## 実装方針：ネイティブAPI優先

**カスタム実装は避け、ネイティブAPIを使用すること。**

```swift
// ✅ 推奨：ネイティブAPI
Text("Hello")
    .glassEffect()

// ❌ 非推奨：カスタム実装
Text("Hello")
    .background(.ultraThinMaterial)
    .overlay(RoundedRectangle(...).stroke(...))
    .shadow(...)
```

### 理由

1. **システム統合**: アクセシビリティ設定（透明度を下げる等）に自動対応
2. **パフォーマンス**: GPUレベルで最適化されたレンダリング
3. **一貫性**: OS全体のデザイン言語と調和
4. **将来互換性**: OSアップデート時に自動的に改善される
5. **モーフィング**: `GlassEffectContainer`による融合アニメーションはネイティブAPIでのみ実現可能

### カスタム実装が許容されるケース

- iOS 25以前をサポートする必要がある場合のフォールバック
- ネイティブAPIでは実現できない特殊な視覚効果が必要な場合

---

## 1. 概要：従来のすりガラスとの違い

| 特性 | 従来のすりガラス (Blur) | Liquid Glass (Lensing) |
|------|------------------------|------------------------|
| 処理ロジック | ピクセルの平均化 (Low Pass Filter) | ピクセル座標の変位 (Displacement Mapping) |
| 視覚効果 | 平面的、均一な曇り | 3次元的、エッジでの光の屈折、厚みの表現 |
| 動的挙動 | 静的 (Static) | 動的 (Dynamic) - 要素の移動に合わせて歪みが変化 |
| 計算リソース | CPU/GPU (定数コスト) | GPU (フラグメントシェーダーによるピクセル毎計算) |

Liquid Glassは「Lensing（レンズ効果）」と「Fluidity（流動性）」を持ち、UI要素同士が接近した際に水滴のように融合し、離れる際には有機的に分離する。

### 背景ブラーの自動適用

**重要**: `.glassEffect()`を適用するだけで、背景のブラー＋屈折効果が自動的に付与される。

```swift
// ✅ これだけで背景ブラー効果が付く
Text("Content")
    .padding()
    .glassEffect()

// ❌ 不要：別途Material/Blurを追加する必要はない
Text("Content")
    .padding()
    .background(.ultraThinMaterial)  // 不要
    .glassEffect()
```

### 光学的4特性

Liquid Glassは以下の4つの光学特性をシミュレートする：

| 特性 | 物理的役割 | ネイティブAPIでの実現 |
|------|-----------|---------------------|
| 屈折 (Refraction) | 背景の光を曲げ、オブジェクトの厚みを示唆 | `.glassEffect()`に含まれる |
| 拡散 (Diffusion) | 背景をぼかし、前景の可読性を確保 | `.glassEffect()`に含まれる |
| 鏡面反射 (Specular) | 光源からの光がエッジに反射し表面張力を表現 | `.glassEffect()`に含まれる |
| 投影 (Cast Shadow) | オブジェクトの浮遊感（エレベーション）を定義 | `.shadow()`で追加 |

**ネイティブAPIを使えば、屈折・拡散・鏡面反射は自動処理される。** 開発者が追加で対応するのは影（Shadow）のみ。

## 2. マテリアルバリアント

### .regular（標準）

タブバー、ツールバー、ナビゲーションバー、標準ボタンに使用。

```swift
Text("Hello")
    .padding()
    .glassEffect(.regular, in: RoundedRectangle(cornerRadius: 16))
```

### .clear（クリア）

写真や地図の上に配置される小さなフローティングコントロール向け。

```swift
Button(action: {}) {
    Image(systemName: "location")
}
.glassEffect(.clear, in: .circle)
```

### .identity（アイデンティティ）

視覚効果を無効化するパススルー状態。

```swift
.glassEffect(isEnabled ? .regular : .identity)
```

## 3. 基本実装：.glassEffect()

### 基本構文

```swift
// デフォルト：.regular バリアント, .capsule 形状
Text("Hello, Liquid Glass!")
    .padding()
    .glassEffect()
```

### 形状とティントを指定

```swift
Button(action: { }) {
    Label("Home", systemImage: "house")
        .padding()
}
.glassEffect(
    .regular.tint(.blue.opacity(0.8)),
    in: RoundedRectangle(cornerRadius: 16)
)
```

### 推奨形状

| 形状 | 推奨される用途 | 特記事項 |
|------|---------------|---------|
| Capsule | ボタン、入力フィールド、トグル | デフォルト形状。最も流体的な変形に適している |
| Circle | アイコンのみのボタン、アバター | `frame(width:height:)`で正方形を確保 |
| RoundedRectangle | カード、モーダル、リスト項目 | 角丸の半径は一貫性が重要 |
| .rect(cornerRadius:.containerConcentric) | ネストされたコンテナ | 親コンテナの角丸と視覚的に調和 |

### インタラクティブ効果

```swift
Button("Submit") {
    submitAction()
}
.glassEffect(.regular.interactive())
```

`.interactive()`を適用すると：
- **スケーリング**: 押下時にわずかに縮小
- **イルミネーション**: タッチ位置から光の波紋
- **シマー**: 表面を斜めに走るスペキュラハイライト

## 4. Glass Card の構築

### 基本実装

```swift
struct GlassCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Liquid Glass UI")
                .font(.headline)
                .foregroundStyle(.primary)  // セマンティックカラー推奨
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

**ポイント**: `.glassEffect()`だけで背景ブラー＋屈折＋リムライト（エッジの光沢）が自動適用される。追加で必要なのは影のみ。

### シャドウ設計ガイドライン

#### 色付きシャドウ（推奨）

黒ではなく、背景色やボタン色を含んだ暗色を使用すると、濁りのないクリアな浮遊感が生まれる。

```swift
// ❌ 純粋な黒（濁って見える）
.shadow(color: .black.opacity(0.3), radius: 20, x: 0, y: 10)

// ✅ 色付きシャドウ（クリアな浮遊感）
.shadow(color: Color.blue.opacity(0.3), radius: 20, x: 0, y: 10)
```

#### 二重シャドウ（高品質）

1つのシャドウで全てを表現せず、2つを組み合わせると自然な浮遊感が得られる。

```swift
.shadow(color: .black.opacity(0.08), radius: 30, x: 0, y: 15)  // Ambient: 広範囲の薄い影
.shadow(color: .black.opacity(0.15), radius: 8, x: 0, y: 4)    // Key: 直下の濃く狭い影
```

#### 推奨値

| パラメータ | 推奨値 | 備考 |
|-----------|--------|------|
| Radius | 10〜20pt | 大きく柔らかく |
| Y Offset | 5〜10pt | 光源を上部に想定 |
| Opacity | 明るい背景: 15%、暗い背景: 30% | 背景に応じて調整 |

### リムライト（エッジの光沢）

ネイティブAPIでは自動適用されるが、カスタム実装が必要な場合：

```swift
// iOS 25以前のフォールバック用
.overlay(
    RoundedRectangle(cornerRadius: 24, style: .continuous)
        .stroke(
            LinearGradient(
                colors: [
                    .white.opacity(0.6),  // 上部左：ハイライト
                    .white.opacity(0.1)   // 下部右：シェードへフェード
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            ),
            lineWidth: 1
        )
)
```

**注意**: 背景にはリッチなグラデーションや写真を配置すること。単色背景ではLiquid Glassの効果が活きない。

## 5. GlassEffectContainer とモーフィング

複数のガラス要素が融合・分離するアニメーションを実現。

### 基本的な融合

```swift
GlassEffectContainer(spacing: 20) {
    HStack(spacing: 15) {
        Image(systemName: "pencil")
            .glassEffect()

        Image(systemName: "eraser")
            .glassEffect()
    }
}
```

- **Container Spacing (20)**: 融合の閾値。この距離以下で融合開始
- **Layout Spacing (15)**: 実際のView間距離

上記例では実際の距離（15）が閾値（20）より小さいため、2つのアイコンは融合する。

### glassEffectID によるモーフィング

```swift
struct MorphingMenu: View {
    @Namespace private var namespace
    @State private var isExpanded = false

    var body: some View {
        GlassEffectContainer(spacing: 30) {
            VStack {
                Button {
                    withAnimation(.bouncy) { isExpanded.toggle() }
                } label: {
                    Image(systemName: isExpanded ? "xmark" : "plus")
                        .padding()
                }
                .glassEffect()
                .glassEffectID("mainButton", in: namespace)

                if isExpanded {
                    Button(action: {}) { Image(systemName: "doc") }
                        .glassEffect()
                        .glassEffectID("action1", in: namespace)

                    Button(action: {}) { Image(systemName: "mic") }
                        .glassEffect()
                        .glassEffectID("action2", in: namespace)
                }
            }
        }
    }
}
```

### glassEffectUnion

複数のViewを距離に関係なく一つのガラス形状として扱う場合に使用。

```swift
.glassEffectUnion(id: "control", namespace: namespace)
```

## 6. タブバーの実装

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

`.search`ロールが適用されると：
- 他のタブから視覚的に分離配置
- より目立つガラススタイルが自動適用
- iPadでは独立した検索フィールドとして再配置

### カスタムフローティングボタン

```swift
ZStack(alignment: .bottom) {
    TabView { /* ... */ }

    Button(action: { showAddSheet = true }) {
        Image(systemName: "plus")
            .font(.title2)
            .padding()
            .foregroundStyle(.white)
    }
    .glassEffect(.regular.tint(.blue).interactive(), in: .circle)
    .padding(.bottom, 10)
}
```

### タブバーアクセサリビュー

```swift
.tabViewBottomAccessory {
    Button("New Post") { /* ... */ }
        .buttonStyle(.glass)
}
```

## 7. 検索モーフィングの完全実装

```swift
import SwiftUI

struct LiquidSearchContainer: View {
    @Namespace private var ns
    @State private var isSearching = false
    @State private var searchText = ""

    var body: some View {
        ZStack(alignment: .bottom) {
            // 背景：ガラス効果を際立たせるグラデーション
            LinearGradient(colors: [.blue, .purple], startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            VStack {
                Spacer()

                GlassEffectContainer(spacing: 20) {
                    if isSearching {
                        // 展開された検索バー
                        HStack {
                            Image(systemName: "magnifyingglass")
                                .foregroundStyle(.secondary)
                            TextField("Search...", text: $searchText)
                                .textFieldStyle(.plain)
                            Button {
                                withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                                    isSearching = false
                                    searchText = ""
                                }
                            } label: {
                                Image(systemName: "xmark.circle.fill")
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding()
                        .frame(height: 60)
                        .frame(maxWidth: .infinity)
                        .glassEffect(.regular, in: .capsule)
                        .glassEffectID("search_interface", in: ns)
                        .padding(.horizontal)
                        .transition(.scale(scale: 1.0))
                    } else {
                        // タブバーとフローティング検索ボタン
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

## 8. UIKit統合

### UINavigationBar との競合解消

```swift
let hostingController = UIHostingController(rootView: MySwiftUIView())
let barButtonItem = UIBarButtonItem(customView: hostingController.view)

if #available(iOS 26.0, *) {
    barButtonItem.hidesSharedBackground = true
}
```

## 9. パフォーマンス最適化

### オーバードローの回避

- 画面上のLiquid Glassレイヤーは原則2層まで
- モーダル表示時は背面のガラス効果を `.identity` にする
- `GlassEffectContainer` を使用してドローコールを削減

### GlassEffectContainer によるバッチ処理

コンテナ内の子要素を一つのメッシュとして計算。10個のボタンを個別に描画するよりも効率的。

## 10. アクセシビリティ

### 透明度を下げる設定への対応

Liquid Glassマテリアルは自動的にフロスティングの強度を上げ、不透明度を増す。

### テキスト色の推奨

```swift
// ❌ 固定の白
.foregroundStyle(.white)

// ✅ セマンティックカラー
.foregroundStyle(.label)
.foregroundStyle(.secondary)
```

### reduceMotion への対応

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion

// reduceMotion が true の場合は静的表示に切り替え
if reduceMotion {
    // 静的なすりガラス表示
} else {
    // モーフィングアニメーション
}
```

## 11. システム設定への適応

- **透明度を下げる**: 自動的に不透明度を増加
- **着色モード (iOS 26.1+)**: 背景色を彩度低下させ、ユーザーのティントカラーを乗算合成

---

## 12. UI/UX設計の意思決定フレームワーク

Liquid Glassを効果的に活用するための設計判断基準。

### 12.1 画面遷移：Push vs Sheet

| 判定要素 | Push遷移 (NavigationStack) | Sheet遷移 (Liquid Glass向き) |
|---------|---------------------------|------------------------------|
| コンテキスト | 継続的（リスト→詳細） | 一時的・独立的（新規作成、設定変更） |
| フローの性質 | 線形（ステップ1→2→3） | 分岐・中断（サブタスク） |
| メンタルモデル | 「奥に進む」 | 「上に乗せる」 |
| 画面占有率 | 原則全画面 | ハーフモーダル〜全画面（可変） |
| データ操作 | 自動保存・閲覧が主 | 明示的な「保存」「キャンセル」 |

**Liquid GlassにはSheetが最適**: 背景が透けて見えるため、ユーザーは元のコンテキストを見失わない。

```swift
// Sheetの高さ（Detents）設定
.sheet(isPresented: $showSheet) {
    ContentView()
        .presentationDetents([.medium, .large])
}
```

- **Medium**: 背景を参照しながら入力する場合
- **Large**: コンテンツ量が多い、没入が必要な場合

### 12.2 ボタン配置

#### 画面下部（プライマリアクション）

```swift
// ✅ 推奨：ネイティブのタブバーアクセサリ
.tabViewBottomAccessory {
    Button("New Post") { }
        .buttonStyle(.glass)
}
```

適用ケース：
- 最も頻繁に行うアクション（新規作成、再生、カートに追加）
- 片手操作（親指で届く範囲）

#### 画面右上（セカンダリアクション）

```swift
.toolbar {
    ToolbarItem(placement: .topBarTrailing) {
        Button("Done") { }
    }
}
```

適用ケース：
- 頻度は低いが重要な操作（編集、共有、フィルタ）
- 完了・キャンセル操作
- 破壊的操作（誤タップ防止）

### 12.3 タブバー項目数

| デバイス | 推奨 | 最大 |
|---------|------|------|
| iPhone | 3〜5個 | 5個（6個以上は「その他」に集約され、UX低下） |
| iPad | サイドバーに変形 | 制限なし |

```swift
TabView {
    // 最大5つまで
}
.tabViewStyle(.sidebarAdaptable) // iPad対応
```

### 12.4 情報密度とコンポーネント数

#### Miller's Law（7±2の法則）

1画面の主要要素は **5〜7個以内** に抑える。

#### プログレッシブ・ディスクロージャー

最初から全情報を表示せず、段階的に開示。

```swift
// SheetのDetentsで段階的に情報を開示
.presentationDetents([.medium, .large])
```

### 12.5 タイポグラフィ

#### フォントウェイト

```swift
// ❌ 背景が複雑な場合、細いフォントは避ける
.fontWeight(.ultraLight)
.fontWeight(.thin)

// ✅ 可読性を確保
.fontWeight(.regular)
.fontWeight(.medium)
.fontWeight(.semibold)
```

#### 色の指定

```swift
// ❌ 固定色（背景変化に対応できない）
.foregroundColor(Color(red: 0, green: 0, blue: 0))

// ✅ セマンティックカラー（自動でコントラスト調整）
.foregroundStyle(.primary)
.foregroundStyle(.secondary)
.foregroundStyle(.label)
```

#### 行間

フォントサイズの **120〜145%** を確保。

```swift
Text("Long text content")
    .lineSpacing(8)
```

### 12.6 判定基準チェックリスト

| 検討項目 | 判定基準 | 推奨設定 |
|---------|---------|---------|
| 画面遷移 vs Sheet | コンテキスト維持の必要性 | 一時的タスク→Sheet、フロー切り替え→Push |
| Sheetの高さ | コンテンツ量と参照性 | 入力中→Medium、閲覧中→Large |
| ボタン配置 | 頻度と指の届きやすさ | プライマリ→下部、完了/破壊的→右上 |
| タブ項目数 | 画面幅と重要度 | 3〜5個。それ以上はサイドバー検討 |
| コンポーネント数 | 認知的負荷 | 1画面あたり主要要素5〜7個以内 |
| 文字色 | 背景可変性への耐性 | セマンティックカラー使用 |

---

## 13. 背景の設計

Liquid Glassの視覚的魅力は背景に依存する。

### 推奨される背景

```swift
// ✅ グラデーション
LinearGradient(colors: [.blue, .purple], startPoint: .top, endPoint: .bottom)

// ✅ MeshGradient（iOS 18+）
MeshGradient(...)

// ✅ 写真・画像
Image("background")
    .resizable()
    .scaledToFill()
```

### 避けるべき背景

```swift
// ❌ 単色（ガラス効果が活きない）
Color.black
Color.white
Color.gray
```

### 背景とガラスの層構造

```
[最背面] グラデーション/画像
    ↓
[中間層] スクロールコンテンツ
    ↓
[前面層] Liquid Glass カード/タブバー（最大2層まで）
```

**重要**: ガラスの重ね合わせは2層までに抑える（GPU負荷軽減）

---

## 14. スクロールエッジ効果の制御

コンテンツが最上部/最下部にあるときのバーの透明度変化を制御。

### 効果を有効化（コンテンツを裏に透かす）

```swift
.toolbar {
    ToolbarItem(placement: .bottomBar) {
        // バーの下までコンテンツが伸びる
    }
}
```

### 効果を無効化（コンテンツを避ける）

```swift
.safeAreaInset(edge: .bottom) {
    // コンテンツの余白を確保し、バーの裏に入り込まない
}
```

---

## 15. Figmaでのハンドオフ設定値

デザイナーからエンジニアへの指示用。

### Liquid Glass カードの設定

| プロパティ | 値 |
|-----------|-----|
| Background Blur | 20〜40 |
| Fill | Solid White (#FFFFFF), Opacity 10〜20% |
| Inner Shadow (Top) | Y: +1, Blur: 0, Color: White 50%（上端の光） |
| Inner Shadow (Bottom) | Y: -1, Blur: 0, Color: White 10%（下端の反射） |
| Drop Shadow | Blur: 30, Y: 15, Color: Black (または背景の暗色) 15% |
| Corner Radius | 16〜24（用途に応じて） |

### グラデーションボーダー（リムライト）

```
Linear Gradient Stroke:
  - Start (Top-Left): White 60%
  - End (Bottom-Right): White 10%
  - Width: 1px
```

### 色付きシャドウの指定方法

```
Drop Shadow:
  - Color: 背景のメインカラーを暗くしたもの（例：青背景なら濃紺）
  - Blur: 20-30
  - Y: 10-15
  - Opacity: 15-25%
```
