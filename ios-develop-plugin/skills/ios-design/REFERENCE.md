# iOS Design - Liquid Glass 詳細リファレンス

iOS 26 Liquid Glassの詳細な技術仕様、レンダリングエンジン、移行戦略を解説します。

---

## 重要: 実装前の確認

**Liquid GlassのAPIは進化中です。実装前に必ず以下を確認してください:**

1. **Swiftバージョン確認**: `swift --version`
2. **Context7で最新API取得**: 特に `glassEffect`、`GlassEffectContainer` のシグネチャ
3. **Apple公式ドキュメント**: Human Interface Guidelines (HIG) の最新版

---

## 1. 起源とデザイン哲学

### 1.1 コードネーム「Solarium」

Liquid Glassの開発プロジェクトは内部で「Solarium（日光浴室）」と呼ばれていた。ガラス張りの空間が光を透過させて内部と外部を繋ぐように、デジタルインターフェースにおける「光」と「透過性」を再定義する。

### 1.2 visionOSからの継承

直接的なインスピレーション源はvisionOS。UI要素が物理空間に浮かび、環境光を反射・屈折させる3次元的な物理特性を、2次元スクリーンに翻訳している。

### 1.3 フラットデザインとの違い

| 特性 | フラットデザイン / すりガラス | Liquid Glass |
|------|------------------------------|--------------|
| 光の扱い | 散乱（ぼかし） | 屈折（レンズ効果） |
| 深度表現 | ドロップシャドウ | 光学的深度 |
| 形状 | 固定 | 流体的変形 |
| ハードウェア連携 | なし | 同心円性（Concentricity） |

---

## 2. デザインの三原則 詳細

### 2.1 Hierarchy（階層性）：光による深度

従来はサイズ、色、シャドウで階層を表現。Liquid Glassでは「光学的深度」が決定する。

- ナビゲーションバー、タブバー = 「流体ガラス」としてコンテンツの上に浮遊
- 背景コンテンツはガラス越しに屈折
- 影なしで明確な分離（Separation）を実現

### 2.2 Harmony（調和）：同心円性

「Concentricity（同心円性）」がキーワード。

- UI要素の角丸はデバイスのディスプレイ角丸と数学的に調和
- `GlassEffectContainer` が位置とベゼル形状から最適ラジアスを自動計算
- ソフトウェアがハードウェアと一体化した感覚を生成

### 2.3 Consistency（一貫性）：流体としての振る舞い

静的素材ではなく「流体」として振る舞う。

- 近接したボタンは表面張力のように融合（モーフィング）
- 操作に応じて形状変化
- デジタル空間の「手触り」を提供

---

## 3. レンダリングエンジン

### 3.1 リアルタイム処理

Appleシリコン（A/Mシリーズ）のNeural EngineとGPUを活用したシェーダーエフェクト。

| 処理フェーズ | 技術詳細 |
|-------------|---------|
| 1. 背景サンプリング | ビュー背後のコンテンツ（画像、テキスト、動画）をリアルタイム取得 |
| 2. 屈折マッピング | UI要素形状からディスプレイスメントマップ生成、光の屈折シミュレート |
| 3. 鏡面反射 | ジャイロスコープ・加速度センサーで仮想光源からの反射光計算 |
| 4. 環境適応 | 背景の輝度・色相を分析し透明度とぼかしを自動調整（Adaptive Tinting） |

### 3.2 マテリアルバリアント詳細

#### Regular（標準）
- 最も一般的
- 適度なぼかしと屈折
- Light/Darkモードで輝度自動調整
- 用途: タブバー、ナビゲーションバー、ボタン

#### Clear（クリア）
- 透明度高、ぼかし最小
- 背景の細部を隠すべきでない環境向け
- 用途: 写真、地図の上
- 注意: ディミングレイヤー等で可読性確保が必要

#### Identity（アイデンティティ）
- エフェクトなし
- 条件付きロジックでグラスエフェクト無効化時に使用

---

## 4. SwiftUI API 詳細

### 4.1 .glassEffect() 完全仕様

```swift
func glassEffect(
    _ style: Glass = .regular,
    in shape: some Shape = DefaultGlassEffectShape()
) -> some View
```

#### Glassスタイルのメソッドチェーン

```swift
.glassEffect(
    .regular
        .tint(Color)       // ガラス素材自体に色味
        .interactive(),    // タッチ操作への物理挙動
    in: Shape
)
```

#### シェイプオプション

```swift
// カプセル（デフォルト）
.glassEffect(.regular, in: Capsule())

// 角丸四角形
.glassEffect(.regular, in: RoundedRectangle(cornerRadius: 16))

// 円
.glassEffect(.regular, in: Circle())
```

### 4.2 GlassEffectContainer 詳細

```swift
GlassEffectContainer(spacing: CGFloat) {
    // glassEffectを持つ複数のビュー
}
```

#### spacingパラメータの物理学

- 視覚的余白だけでなく「融合の閾値」として機能
- 要素間距離 < spacing → 境界線が液状化し結合（Union）
- 要素間距離 > spacing → 表面張力が切れるように分離
- 動的に要素が増減するメニューで有機的アニメーション自動生成

### 4.3 .glassEffectID 詳細

`matchedGeometryEffect`のLiquid Glass専用拡張。

```swift
@Namespace private var animation

// ビューに付与
.glassEffectID("identifier", in: animation)
```

ステート変化時に「同じガラスの塊が変形した」と認識させる。

---

## 5. ボタンスタイル

### 5.1 標準スタイル

```swift
// 二次的アクション向け（透過度高）
.buttonStyle(.glass)

// プライマリアクション向け（不透明度高、視覚的重み）
.buttonStyle(.glassProminent)
```

### 5.2 UIKit統合

UIKitの `UINavigationBar`、`UITabBar` はSDKリンク時に自動適応。カスタムビューでの詳細制御は制限あり。

完全な効果には `UIHostingController` 経由でSwiftUIビュー埋め込みを推奨。

---

## 6. Human Interface Guidelines (HIG)

### 6.1 適用レイヤーの原則

**最上位レイヤー（Topmost Layer）にのみ適用:**
- ナビゲーションバー
- タブバー
- サイドバー
- モーダルシート
- フローティングコントロール

### 6.2 禁止事項

| 禁止行為 | 理由 |
|---------|------|
| リストセル・カードの背景への適用 | 物理メタファー崩壊、Blur Pile発生 |
| カスタム背景色との併用 | OS全体の照明効果と不整合 |
| 不透明背景（Color.white等） | スクロール時挙動と不整合 |

### 6.3 アイコン設計：3層構造

iOS 26のアプリアイコンは以下の3層構造:

| 層 | 内容 |
|----|------|
| Background Layer | 抽象的なグラデーション、テクスチャ |
| Middle Layer | 補助的シェイプ、影 |
| Foreground Layer | 主要グリフ、ロゴ |

**Icon Composer（Xcode付属）で合成。**

システムがジャイロスコープデータでパララックス効果と動的ハイライトを付与。

#### 自動適応モード
- Dark（ダーク）
- Tinted（色付き）
- Clear（透明）

### 6.4 タイポグラフィとバイブランシー

#### セマンティックスタイルの使用（必須）

```swift
// Good: システムが自動でVibrancyフィルター適用
Text("Title")
    .foregroundStyle(.primary)

Text("Subtitle")
    .foregroundStyle(.secondary)

// Bad: 背景によってはコントラスト不足
Text("Title")
    .foregroundStyle(Color.white)
```

#### ウェイトの推奨

シンボル（SF Symbols）やテキストには**Medium以上**の太いウェイトを使用。屈折効果に埋もれないようにする。

---

## 7. アクセシビリティ

### 7.1 システムオーバーライド

| 設定 | 効果 | 開発者対応 |
|------|------|-----------|
| 透明度を下げる | Liquid Glass→不透明ソリッドカラー | `.identity`やフォールバック背景の動作確認 |
| 視差効果を減らす | スペキュラーハイライト移動・モーフィング停止 | 瞬時切り替えでも違和感ないUI設計 |
| コントラストを上げる | ガラス周囲にボーダー追加 | ボーダー追加でレイアウト崩れないよう余白設計 |

### 7.2 批判と対応

初期ベータで「視認性低い」「目が疲れる」との批判あり。

- 複雑な背景でWCAGコントラスト基準を下回るリスク
- 揺らめく反射・モーフィングが「視覚的乗り物酔い」を誘発

**必ずアクセシビリティ設定ONでテストすること。**

---

## 8. 移行戦略

### 8.1 既存アプリのリファクタリング手順

1. **SDKの更新**
   - Xcode 26でビルド
   - 標準コンポーネントの自動適応を確認

2. **背景色の撤去**
   - Toolbar、TabBarのカスタム背景色を削除
   - `.tint`モディファイアでブランドカラーをアクセントとして適用

3. **レイアウト調整**
   - `GlassEffectContainer`導入
   - 散在ボタンをグループ化して融合
   - 画面上の要素数を視覚的に削減

### 8.2 コードマイグレーション例

```swift
// Before (iOS 25以前)
NavigationStack {
    content
        .toolbar {
            ToolbarItem {
                Button("Save") { }
                    .background(Color.blue)
                    .cornerRadius(8)
            }
        }
        .toolbarBackground(Color.white, for: .navigationBar)
}

// After (iOS 26)
NavigationStack {
    content
        .toolbar {
            ToolbarItem {
                Button("Save") { }
                    .glassEffect(.regular.tint(.blue).interactive(), in: Capsule())
            }
        }
        // 背景色を削除し、システムのガラス素材に任せる
        .toolbarBackground(.visible, for: .navigationBar)
}
```

---

## 9. Apple Intelligenceとの統合

Liquid Glassのレンダリングは「Apple Intelligence」と深く結合。

- AIが画面コンテンツをセマンティック理解
- ガラス背後が「テキスト」か「画像」か判別
- ぼかし強度・ティントを局所的に最適化
- 手動調整なしで可読性をある程度担保

---

## 10. 実装チェックリスト

### 新規実装時

- [ ] Context7で最新のglassEffect APIを確認
- [ ] Swiftバージョンを確認（`swift --version`）
- [ ] 最上位レイヤーにのみglassEffect適用
- [ ] GlassEffectContainerで関連要素をグループ化
- [ ] セマンティックカラー（.primary, .secondary）を使用
- [ ] Medium以上のフォントウェイトを使用

### 移行時

- [ ] カスタム背景色を削除
- [ ] .tintでブランドカラー適用
- [ ] アクセシビリティ設定ONでテスト
- [ ] 「透明度を下げる」有効時の表示確認
- [ ] 「視差効果を減らす」有効時のアニメーション確認

### レビュー時

- [ ] リストセル・カード背景にglassEffect使用していないか
- [ ] 固定色（Color.white/black）を使用していないか
- [ ] コントラスト比がWCAG基準を満たすか

---

## 11. クイックリファレンス

| 機能 | 従来 (〜iOS 25) | iOS 26 Liquid Glass |
|------|-----------------|---------------------|
| 素材適用 | `.background(.ultraThinMaterial)` | `.glassEffect(.regular)` |
| グループ化 | `HStack`, `ZStack` | `GlassEffectContainer(spacing:)` |
| アニメーション | `.matchedGeometryEffect` | `.glassEffectID(...)` |
| インタラクション | ボタンスタイル変更 | `.glassEffect(.interactive())` |
| アイコン | PNG/SVG画像 | Icon Composer（3層構造） |
| 背景 | `Color.white` | システムのガラス素材に委譲 |

---

## 参考リンク

- [Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [SwiftUI Documentation](https://developer.apple.com/documentation/swiftui/)
- [WWDC 2025 Sessions](https://developer.apple.com/wwdc/)
