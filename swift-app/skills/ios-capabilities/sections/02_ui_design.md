# iOS 26 UI/デザイン系新機能 サードパーティ開発者向け調査報告

対象: iOS 26（2025年6月 WWDC25発表、2025年9月正式リリース）と、前世代 iOS 18（2024年 WWDC24）。iOS 26 は Apple がバージョン番号をカレンダー年ベースに統一した結果、旧命名では「iOS 19」にあたる。

---

## 1. Liquid Glass デザイン

### 1.1 何が変わったか

iOS 7 以来最大規模のデザイン刷新。`Liquid Glass` という新素材が、コントロール・ナビゲーション・アプリアイコン・ウィジェットなど全面に適用された。特徴は「ぼかし（blur）」ではなく「レンズ効果（lensing）」— 背後のコンテンツを屈折・反射させ、デバイスの動きに反応してスペキュラハイライトが動く。iOS 26 / iPadOS 26 / macOS Tahoe 26 / watchOS 26 / tvOS 26 / visionOS 26 の全プラットフォーム共通言語。

- 最低OS: **iOS 26.0+**（`glassEffect` 系APIはこれより前には遡って使えない）
- 既存アプリは Xcode 26 でビルドし直すと**自動的に**新しい見た目（タブバー、ナビゲーションバー、ツールバー、シート等）を継承する。明示的な `.glassEffect()` を書かなくてもシステム標準コントロールは切り替わる

### 1.2 SwiftUI の新API

```swift
// 単体
view.glassEffect(.regular, in: .capsule)
view.glassEffect(.clear.tint(.blue).interactive())

// 複数要素をひとつのガラス塊として振る舞わせる
GlassEffectContainer(spacing: 20) {
    HStack {
        Button1().glassEffect(in: .circle)
        Button2().glassEffect(in: .circle)
    }
}
```

| API | できること | 制約 |
|---|---|---|
| `.glassEffect(_:in:)` | ビューにガラス質感を付与。`Glass.regular`（適応型・既定）／`Glass.clear`（高透過）／`Glass.identity`（無効化）の3variant | シェイプ指定必須（`.capsule`など）。過剰使用は非推奨（Appleは「コントロール・ナビゲーション要素にのみ」推奨） |
| `.tint(_:)`（Glassに連結） | ガラスに色味を付ける | — |
| `.interactive()` | タップ/ポインタでスケール・バウンス・シマーが発生し「触れる」質感になる | ボタン等インタラクティブ要素向け |
| `GlassEffectContainer` | 複数の `.glassEffect()` ビューを1つの塊として、重なり部分のブレンド・レイアウト変化時のモーフィング（`glassEffectID`で紐付け）を実現 | パフォーマンス上、近接する複数ガラス要素は必ずコンテナでまとめる |

UIKit側にも `UIGlassEffect` / `UIVisualEffectView` 経由での対応、`UIBarButtonItem` の自動ガラス化などが用意されている。

### 1.3 既存アプリの移行・オプトアウト

- Info.plist に `UIDesignRequiresCompatibility` を `YES` で追加すると、旧デザイン（iOS 18以前の見た目）のまま据え置ける。**ただしAppleは「デバッグ・移行期間中の一時措置」と明言しており、次期メジャーXcodeで廃止予定**。恒久対応にはしない
- アイコン単体だけ旧デザインを維持したい場合、Xcode 26 のアセットカタログに「レガシーアイコン維持」フラグがある（Firefox iOS等の事例で報告あり）

### 1.4 アプリアイコン（Icon Composer）

- **Icon Composer**: Xcode 26 に同梱される無償ツール（単体でも配布、macOS 15.3+で動作）。ひとつのレイヤー構成から iPhone/iPad/Mac/Apple Watch 用アイコンを一括生成
- レイヤードアイコン: 複数レイヤーそれぞれが Liquid Glass 素材として振る舞い、下の背景を反射する「小さなガラス板の積層」に見える
- **6つの見た目モード**を1デザインから自動生成: `Default` / `Dark` / `Clear Light` / `Clear Dark`（透明・色を抜いて反射のみ）/ `Tinted Light` / `Tinted Dark`
- 調整可能パラメータ: スペキュラハイライト、屈折率、透過度、影 — シンボルがClearモードで白飛びしたりDarkモードでコントラスト不足になりがちなので個別調整が要る
- ファイル実体: `.icon` バンドル（JSON構成 + PNGレイヤー）。GUIなしでスクリプト生成も可能（このリポジトリの `icon-crafting` スキルで実装済み）
- 提出仕様: マスターは **1024×1024、アルファなし、sRGB/Display P3、PNG**。Xcode 26のアセットカタログはこの単一サイズのみで残り全サイズを自動生成（角丸マスクもシステムが自動適用するため角丸加工済み画像を渡さないこと）

**アプリアイデアへの示唆**: 既存アプリ群（Nagasu/Bide/Kasaneru等）は `design-crafting`→`icon-crafting` の流れで既にIcon Composer運用済み。新規アプリでも同フローを継続すればよい。Clearモードでの視認性確認（薄い背景でのシンボル可読性）を審査前チェックに含める価値がある。

---

## 2. SwiftUI の新機能

### 2.1 iOS 26（WWDC25）

| 機能 | 概要 | 最低OS |
|---|---|---|
| `WebView` / `WebPage` | SwiftUI純正のWeb表示。`WebView(url:)`一行で埋め込み可能。`WebPage`はJS実行・進捗取得・履歴操作など高機能版 | iOS 26.0+ |
| `TextEditor` + `AttributedString` | リッチテキスト編集がネイティブ対応。太字/斜体/下線/取り消し線/フォント/色/カーニング/段落スタイル/Genmojiまで。`AttributedTextSelection`で選択範囲の属性取得・`typingAttributes`操作も可能 | iOS 26.0+ |
| `@Animatable` マクロ | カスタムView/Shapeの `animatableData` を手書きせず、プロパティに付けるだけでアニメーション可能に。`VectorArithmetic`準拠型が対象。除外は `@AnimatableIgnored` | iOS 26.0+ |
| `Chart3D` / `SurfacePlot` | Swift Charts の3D化。ドラッグで回転可能、`PointMark`/`RuleMark`/`RectangleMark`のZ軸対応3D初期化子、`chart3DCameraProjection`（正投影/透視投影切替） | iOS 26.0+ / macOS 26 / visionOS 26 |
| Reorderable containers | `List`・`LazyVGrid`に加えwatchOSでも初めてドラッグ並べ替え対応。任意ビューへのスワイプアクション拡張も | iOS 26.0+ |
| `tabViewBottomAccessory` | タブバー上に浮かぶフローティングCTAボタン領域 | iOS 26.0+ |
| `tabBarMinimizeBehavior` | スクロールに応じてタブバーを最小化（`.automatic`/`.never`/`.onScrollDown`） | iOS 26.0+ |
| `searchToolbarBehavior()` | 検索フィールドをツールバーボタンに折りたたむ制御 | iOS 26.0+ |
| `AsyncImage` HTTPキャッシュ標準対応 | カスタム`URLRequest`/`URLSession`設定も可能に | iOS 26.0+ |
| `@State` のマクロ化 | クラス初期化が遅延化され無駄な確保を防止 | iOS 26.0+ |
| `DocumentCreationSource` | カスタム新規ドキュメント作成フロー、`FileDocument`/`ReferenceFileDocument`のURL直接アクセス対応 | iOS 26.0+ |

### 2.2 iOS 18（WWDC24、前世代の到達点）

- **`@Entry` マクロ**: `EnvironmentValues`/`FocusedValues`等のカスタムキーを大幅省力化（旧来の`EnvironmentKey`準拠+`EnvironmentValues`拡張が1行に）
- **MeshGradient**: 格子状の制御点間を補間する多色グラデーション
- **TabView刷新**: サイドバーとタブバーの表現をOS/デバイスに応じて自動切替、タブがコンテンツ上にフロート
- **Document Launch Scene**: ドキュメント型アプリ専用のカスタム起動画面
- **Metal shaders** のSwiftUI事前コンパイル対応
- **TableColumnForEach**: テーブル列を動的生成
- UIKitビューをSwiftUIの`Animation`型でアニメーションさせられるように

**アプリアイデアへの示唆**: `@Entry`は設定値（ダークモード切替等、CLAUDE.mdにある共通実装パターン）の集約レイヤーに向く。`Chart3D`は統計・可視化系アプリ（例: Bide系のトラッキングアプリ）で差別化要素になり得る。リッチテキスト`TextEditor`はメモ・日記系アプリの実装コストを大幅に下げる。

---

## 3. UIKit の新機能

### 3.1 iOS 26

- **Liquid Glass採用**: コントロール・ナビゲーション・アイコン・ウィジェット全般。`UIBarButtonItem`等は自動対応
- **Swift Observation統合**: `layoutSubviews`等の更新メソッド内で参照した`Observable`を自動追跡し、依存配線・再描画を自動化。`setNeedsLayout`の手動呼び出しが不要になるケースが増える
- **`flushUpdates`アニメーションオプション**: アニメーション開始/終了時に保留更新を自動適用し、`layoutIfNeeded()`呼び出しを省略可能
- **`UISplitViewController`にインスペクタ対応**: 選択コンテンツの詳細パネルを標準サポート（Preview.appのメタデータ表示相当）
- **iPadのメニューバー**: macOS風メニューバーがiPadに導入。物理キーボードなしでも上端スワイプで表示可能
- **検索UIの刷新**: iPhoneでは検索バーがツールバーに統合され余白に応じて展開ボタン/フィールドに自動切替。iPadでは分割ビュー時にナビゲーションバー末尾、または`UITabBarController`の専用検索タブとしてタップで展開
- **スライダー強化**: モーメンタム保持、ストレッチ、目盛り表示、ニュートラル値、つまみ無しのプログレスバー風スタイル

### 3.2 iOS 18（前世代）

- ControlWidget API（第5項参照）
- SF Symbols アニメーション効果の拡充（Wiggle, Breathe等）

**アプリアイデアへの示唆**: SwiftUIメインの本パイプラインではUIKit直接利用は少ないと想定されるが、`WebView`が来る前まではUIKit `WKWebView`ラッパーが必要だった経緯があり、規約ページ表示など軽量Web埋め込みは今後SwiftUI純正で完結できる。

---

## 4. 新しいコントロール・コンポーネント（ツールバー/タブバー/検索/bottom accessory）

- **タブバー**: Liquid Glass化しフロート表示。検索タブは視覚的に分離され、選択すると検索フィールドに変形。`tabBarMinimizeBehavior`でスクロール時の最小化制御、`tabViewBottomAccessory`でタブバー上にCTAを浮かせられる（`tabViewBottomAccessoryPlacement`で配置制御）
- **ツールバー**: 検索バーがツールバー内に統合される新レイアウト（iPhone）。`searchToolbarBehavior()`で折りたたみ制御
- **split-toolbarスタイル**: フローティングボタン風の新ツールバー表現がTabViewに追加

**アプリアイデアへの示唆**: 3〜5タブ構成の典型的ユーティリティアプリでは、`tabViewBottomAccessory`で「今日のアクション」CTAを常時浮かせる、といった演出が低コストで作れる。

---

## 5. ウィジェット/コントロールの新機能

### 5.1 iOS 26 での更新

- **視覚面が中心の更新**: インタラクティブウィジェット自体はiOS 17、Control CenterウィジェットはiOS 18で既に導入済み。iOS 26は既存の仕組みにLiquid Glassの見た目を適用する年
- **`containerBackground`**: ウィジェットの背景ビューを指定するAPI。ユーザーが色/クリアのテーマを設定した際、システムがこの背景をガラス素材ビューに自動置換
- **アクセントレンダリングモード**: システムがウィジェットコンテンツを自動的に白ティントし、背景をテーマ化されたガラスに置換。画像は`desaturated`/`accented desaturated`（アイコン的画像向け）と`fullColor`（アルバムアート等メディア画像向け）を使い分ける
- **Control Center刷新**: 複数ページ化、リサイズ可能なコントロール、コントロールギャラリー、サードパーティウィジェットをControl Centerに直接追加可能に
- **ウィジェットの関連性（Relevance）**: watchOS 26のSmart Stackにおいて、ルーティン・位置情報等の文脈に応じて複数インスタンスが同時表示（重複する予定・ハッピーアワー等の例）

### 5.2 StandBy

- StandByモードのウィジェットもLiquid Glass適用対象。インタラクティブウィジェット（Reminders等のチェック操作）をStandByでも利用可能で、2つのウィジェットスタックを並べて表示

### 5.3 Apple Watch（watchOS 26）

- Smart Stackが予測アルゴリズム強化、コンテキストデータ（センサー・ルーティン）を活用した「Smart Stack hints」（Liquid Glass製のプロアクティブな提案カード、例: 圏外でのBacktrack提案）
- Smart Stack内のウィジェットがカスタマイズ可能（Apple製/サードパーティ問わず選択可）
- Control Centerもカスタマイズ可能に

### 5.4 CarPlay / visionOS への拡張

- **CarPlayウィジェット**（iOS 26で新規）: 「CarPlay対応アプリ」でなくても、任意アプリのウィジェットを車載画面に追加可能。車種の画面サイズにより1〜2スタック配置。マップのETA、Now Playing、天気などが典型例
- **visionOS**: Vision Proに「空間ウィジェット」がvisionOS 26で追加

### 5.5 iOS 18（Control Center基盤・前世代）

- **`ControlWidget` API**（WWDC24新規）: Control Center・ロック画面・アクションボタンに設置できる、App Intentsベースのボタン/トグル。`ControlWidgetButton`等で構築

**アプリアイデアへの示唆**: P0実装（`03_implement_app`）にウィジェット拡張を含めると差別化になるが、Widget Extension追加はXcodeプロジェクト構成・Xcode Cloud CI設定への影響があるため、`01_create_xcode_cicd`のやり直しリスクを踏まえて検討要。

---

## 6. Live Activities / Dynamic Island の新機能

- **スケジューリングAPI開放**: これまでApple純正Sportsアプリ限定だった「未来時刻に開始するLive Activityの事前スケジュール」が、iOS 26で全サードパーティアプリに新規開発者APIとして開放された
- **Dynamic Islandのランドスケープ対応**: 横向き利用時に情報量を増やせる新スタイルが追加。ただしcompact/minimal表示はportraitのような可変幅を持たない制約あり
- 実例: 新しいWallet搭乗券のLive Activity対応、フィットネスワークアウト（iPhone/Apple Watchどちらからでも開始→ロック画面とDynamic Islandに反映、一時停止操作可）

**アプリアイデアへの示唆**: タイマー・カウントダウン系、進捗トラッキング系のアプリはLive Activityとの相性がよい。スケジューリングAPI開放により「予定された将来のイベント」をLive Activityで先出し表示する体験が作りやすくなった。

---

## 7. App Icon の新仕様（まとめ）

| 項目 | 内容 |
|---|---|
| ソース形式 | 1024×1024 PNG、アルファチャンネルなし、sRGB/Display P3、72dpi |
| 生成ツール | Icon Composer（`.icon`バンドル、レイヤー構成）または従来のAsset Catalog単一画像 |
| 見た目バリエーション | Default / Dark / Clear Light / Clear Dark / Tinted Light / Tinted Dark の6種を自動生成 |
| 禁止事項 | 角丸の作り込み（システムが自動マスク）、独自の視覚エフェクト重畳 |
| 互換性の罠 | Xcode 16由来のアセットカタログ（単一PNG）はiOS 26上でLiquid Glass効果が適用されない個体差が報告されている → Icon Composer製`.icon`への移行が望ましい |

---

## 8. テキスト関連

- **`TextEditor` + `AttributedString`**（iOS 26.0+）: プレーンテキストからリッチテキストへの移行が`AttributedString`バインディングへの変更のみで完了。太字/斜体/下線/取り消し線/フォント/サイズ/前景色・背景色/カーニング/トラッキング/ベースラインオフセット/Genmoji/段落スタイルに対応
- **`AttributedTextSelection`**: 選択範囲の属性取得・カーソル位置の`typingAttributes`操作により、カスタムの書式設定ツールバー（太字ボタン等）をシステム標準の見た目で実装可能
- Markdown・リンク・属性変換にも対応しており、「メモアプリのMarkdown入力→リッチテキスト表示」のような機能が大幅に低コスト化

**アプリアイデアへの示唆**: 日記・メモ・ノート系アプリのP0スコープに「太字/箇条書き程度のリッチテキスト」を含めても、iOS 26ではもはや大きな実装コストにならない。

---

## 9. 全体まとめ：このパイプラインでの活用優先度

1. **Icon Composer / Liquid Glassアイコン** — 既に`icon-crafting`スキルで運用済み。継続が最優先
2. **`tabViewBottomAccessory` / `tabBarMinimizeBehavior`** — 既存の集約レイヤー（Tokens/Strings等）に組み込みやすく、低コストで「今っぽさ」を出せる
3. **`TextEditor`+`AttributedString`** — メモ・記録系アプリのP0機能を安く底上げできる
4. **Live Activityスケジューリング開放** — 「予定管理」系アイデアの新規差別化ポイント
5. **CarPlay/watchOSウィジェット拡張** — 実装コストとXcode Cloud CI再設定コストが見合うか、アプリごとに判断が必要
6. **`.glassEffect()`の手動適用** — システム標準コントロールは自動追従するため、独自コンポーネント（カスタムカード等）にのみ選択的適用が無難。過剰使用はAppleのHIGでも非推奨

---

Sources（主要のみ）:
- https://developer.apple.com/documentation/swiftui/view/glasseffect(_:in:)
- https://developer.apple.com/icon-composer/
- https://developer.apple.com/videos/play/wwdc2025/243/ (What's new in UIKit)
- https://developer.apple.com/videos/play/wwdc2025/256/ (What's new in SwiftUI)
- https://developer.apple.com/videos/play/wwdc2025/278/ (What's new in widgets)
- https://developer.apple.com/videos/play/wwdc2025/280/ (Rich text in SwiftUI)
- https://developer.apple.com/videos/play/wwdc2025/313/ (Swift Charts 3D)
- https://www.donnywals.com/opting-your-app-out-of-the-liquid-glass-redesign-with-xcode-26/
- https://9to5mac.com/2025/12/04/ios-26-made-live-activities-even-better-on-iphone-heres-whats-new/
- https://9to5mac.com/2025/10/30/ios-26-adds-carplay-widgets-a-major-new-feature-for-your-vehicle/
