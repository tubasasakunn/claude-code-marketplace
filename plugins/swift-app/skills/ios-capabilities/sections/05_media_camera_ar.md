# iOS 26 メディア・カメラ・グラフィックス・AR系機能 調査報告（2026年7月時点）

対象は2025年9月リリースのiOS 26系（現行の最新安定版）。WWDC 2025発表分が中心。明記した箇所以外はすべてiOS 26で確定済みの機能。

---

## 1. カメラ（AVFoundation / Camera）

### Cinematic Video API
- **できること**: `AVCaptureDeviceInput.isCinematicVideoCaptureEnabled = true` を立てるだけで、被写体を自動でラック&トラッキングフォーカスする「シネマティックモード」動画を撮影できる。出力は本編動画+視差トラック+メタデータトラックの3本立てで、撮影後に**非破壊で**フォーカス位置・被写界深度を編集可能（`Cinematic` フレームワーク）。
- **制約**: 3トラック構成のためファイルサイズが大きい。処理負荷が高い。
- **最低OS**: iOS 26
- **アプリアイデア**: 撮影後にピント送り演出を編集できる動画日記アプリ、インタビュー動画で話者間に自動でフォーカスを移すアプリ。

### Camera Control ボタン / リモートシャッター
- **できること**: `AVCaptureEventInteraction`（SwiftUIは `onCameraCaptureEvent`）で、iPhone 16以降の物理Camera Controlボタン、音量ボタン、Actionボタンの押下フェーズを取得しシャッターに割り当てられる。iOS 26では**AirPods（H2チップ搭載）のステム押下**もこのAPIに乗り、既存アプリは無改修でリモートシャッターに対応する。
- **最低OS**: API自体はiOS 18、AirPods対応はiOS 26。
- **アプリアイデア**: AirPodsをリモコン代わりにしたグループ集合写真アプリ、ワークアウト中に手を触れず動画を撮り始めるフィットネスアプリ。

### Center Stage フロントカメラAPI
- **できること**: iPhone 17世代の正方形センサー・広視野角前面カメラを制御。`dynamicAspectRatio` でセッション再構築なしにアスペクト比変更、顔・視線検出で自動フレーミングし集合セルフィーでも全員を収める。`preferredVideoStabilizationMode = .lowLatency` でリアルタイム低遅延手ぶれ補正。
- **制約**: iPhone 17世代の一部モデル限定。
- **最低OS**: iOS 26

### ProRAW・ゼロシャッターラグ・センサー補正
- ゼロシャッターラグは`isZeroShutterLagEnabled`（iOS 17〜）。`cameraSensorOrientationCompensationEnabled`（iOS 26）で端末回転時のセンサー補正挙動を制御。

### DockKit
- **できること**: モーター駆動スタンド（Insta360 Flow等）をiPhoneが制御する被写体追尾API。iOS 26で**人物+動物のトラッキングと、特定ターゲットの指名追尾**に対応。Visionフレームワークの検出結果をトラッキング対象として渡すことも可能。
- **制約**: DockKit対応の物理スタンドが必要。
- **最低OS**: iOS 17（基本）/ iOS 26（動物・指名追尾）
- **アプリアイデア**: ペットや子供を自動追尾するホームビデオアプリ、一人配信者向けの自動カメラワークアプリ。

---

## 2. 写真・動画（PhotosKit / 空間写真・動画 / Image I/O）

### Photos アプリ / PhotosKit
- iOS 26でタブバーナビゲーション復活、イベント認識、Apple Intelligence+ChatGPT連携の画像生成が統合。開発者向けの写真編集拡張は従来通り。`PHPickerViewController` が引き続き外部連携の主軸。

### 空間写真・空間ビデオ（Spatial Photo / Video）
- **できること**: iPhone 15 Pro以降は `AVCaptureDevice` + `AVCaptureMovieFileOutput` のスパシャル対応プロパティで**ステレオの本物の空間動画/写真**を撮影可能（iOS 17.2世代のAPI）。iOS 26では**「空間シーン」機能**が登場し、AI生成の深度マップで**任意の1枚の2D写真から擬似3Dパララックスシーン**を自動生成。RealityKitのiOS 26新コンポーネント `ImagePresentationComponent` は、2D画像・ステレオ空間写真・空間シーンの3種類すべてを表示できる。
- **制約**: ステレオ空間キャプチャはiPhone 15 Pro以降。空間シーンのサードパーティ公開APIはvisionOS側が中心。
- **アプリアイデア**: 過去の平面写真を空間シーンに自動変換する思い出アプリ、Vision Pro所有者と空間動画をやり取りするSNS。

### Image I/O — Adaptive HDR / ゲインマップ
- **できること**: **ISO 21496-1標準の「Adaptive HDR」**の読み書きAPIをサポート。iOS 26ではデュアルレイヤーHEIC構造が**スクリーンショット**にも拡張。
- **最低OS**: Adaptive HDR基盤はiOS 18〜、スクリーンショット対応はiOS 26。

---

## 3. オーディオ

### 入力デバイス選択（AVInputPickerInteraction）
- **できること**: アプリ内から**入力デバイス選択メニュー**（リアルタイム音量メーター付き）を表示。マイクモード（Voice Isolation等）もその場で切替可能。
- **最低OS**: iOS 26
- **アプリアイデア**: 収録前にマイク品質を即確認できるポッドキャスト録音アプリ。

### AirPods高音質録音
- **できること**: H2チップ搭載AirPodsで**48kHzの新しいBluetoothメディアチューニング**が使用可能、LAVマイク相当の音質。
- **最低OS**: iOS 26
- **アプリアイデア**: AirPodsを無線ラベリアマイクとして使うVlogアプリ。

### Audio Mix / ボイス分離
- **できること**: 収録した音声を**発話とアンビエント（環境音）に分離**して、撮影後・再生時に非破壊でミックス比率を調整できる新API。
- **最低OS**: iOS 26
- **アプリアイデア**: 撮影後にナレーションと環境音のバランスを調整できる動画日記アプリ、教室の雑音から先生の声だけ強調する語学学習アプリ。

### 空間オーディオ収録
- **できること**: `AVAssetWriter` でマイクアレイの収録を**First Order Ambisonics（FOA）**に変換して空間オーディオとして書き出し可能。
- **最低OS**: iOS 26
- **アプリアイデア**: AirPods Proで没入再生できる自然音・ASMR収録アプリ。

### MusicKit / Apple Music Feed / ShazamKit
- MusicKit（iOS 15〜）はカタログ検索・再生・ライブラリアクセスの中核API。**Apple Music Feed**でアルバム・楽曲・アーティストのバルクメタデータ取得も可能。
- ShazamKit（iOS 15〜）: `SHCustomCatalog` によるカスタム音声指紋カタログ、マッチング、履歴取得。
- **アプリアイデア**: 年間音楽統計（Wrapped風）アプリ、カスタムカタログ化で曲名+歌詞タイミングを同期するカラオケアプリ。

---

## 4. 音声認識 — SpeechAnalyzer / SpeechTranscriber ★注目

- **できること**: `Speech` フレームワークの新エンジン。3モジュール構成:
  - `SpeechTranscriber`: 長時間（数十分〜数時間）の連続音声を想定した文字起こし
  - `DictationTranscriber`: 句読点・文章構造付きの短発話文字起こし
  - `SpeechDetector`: 音声活動検出（VAD）
  - すべて**完全オンデバイス**で動作し、サードパーティ計測ではWhisper Large V3 Turbo比で約2倍高速。言語モデルの管理も自動。
- **旧SFSpeechRecognizerとの違い**: 旧APIはオンデバイス処理が短時間（数十秒〜1分）向けだった。SpeechAnalyzerは数時間規模の連続音声を想定して設計されている点が最大の違い。
- **制約**: iOS 26以降限定。ロケールごとの音声モデルはオンデマンドダウンロード。
- **アプリアイデア**: 完全オフラインで数時間の会議・講義をローカル文字起こしするノートアプリ、プライバシー重視のボイス日記アプリ、長時間講演のライブ字幕アプリ。

---

## 5. 動画配信

- **Low-Latency HLS**: 遅延2秒以下。iOS 14以降で成熟済み。
- **Picture in Picture**: `AVPictureInPictureController`。ビデオ通話向けPiP採用の公式ガイドあり。
- **iPadOS 26 のウィンドウ管理刷新**: 上限なしにウィンドウを開ける「Windowed Apps」モード、外部モニター接続時のメニューバー表示。複数シーン対応アプリは自動的に恩恵を受ける。

---

## 6. グラフィックス

### Metal 4
- **できること**: 明示的なメモリ/リソース管理、シェーダーコンパイル高速化、**シェーダー内で直接AI推論を実行できるML統合**（テンソル演算がシェーダーコードに埋め込める）、`MTL4CommandBuffer`。
- **最低OS**: iOS 26

### MetalFX
- **できること**: iOS 26で**フレーム補間**（`MTLFXFrameInterpolator`）が追加。少ない描画コストで体感フレームレートを引き上げる。デノイズ統合、Neural Engineを活かした再設計テンポラルアップスケーラー。
- **制約**: モーションベクトル・深度バッファの提供が必要。GPU負荷の高い3D描画アプリ向け。

### Core Image
- 安定した`CIFilter`パイプラインが継続。RAW処理v9はiOS 27で提供予定。

---

## 7. AR / 3D

### ARKit（iOS 26）
- **オブジェクトトラッキングがiOSにも解放**。Create MLで作った参照オブジェクトをiOS・visionOS両方で利用可能。
- **アプリアイデア**: 特定の実物商品を認識してARで説明を重ねる小売アプリ。

### RealityKit（iOS 26）
- `PresentationComponent`（モーダル表示）、`GestureComponent`（SwiftUIジェスチャー統合）、`ImagePresentationComponent`、`ViewAttachmentComponent`（SwiftUIビューをエンティティに直接添付）などを追加。**SceneKitは非推奨化**されRealityKitへの移行が推奨。
- **アプリアイデア**: AR家具配置アプリ、SwiftUIビューを3D空間に埋め込むインタラクティブ図鑑アプリ。

### Object Capture
- 一連の写真から3Dモデルを生成するフォトグラメトリ。**再構成処理を含めてiPhone上で完結**（iOS 17〜）。
- **制約**: LiDAR搭載機（iPhone 12 Pro以降）が必要。
- **アプリアイデア**: フリマ出品用に商品を3Dスキャンするアプリ、実物デジタルアーカイブアプリ。

### RoomPlan
- LiDARで部屋の寸法・家具種別を含む3Dフロアプランを生成。複数部屋のマージ（iOS 17〜）。
- **アプリアイデア**: 引っ越し・不動産内見アプリの自動間取り図生成、保険の被害申告用の部屋3D記録アプリ。

### Quick Look（AR Quick Look / USDZ）
- `.usdz`をコード不要で3Dプレビュー・AR配置。Web向けにも新しい`<model>`HTML要素が追加。
- **アプリアイデア**: 独自コードほぼ不要で「タップしてARで部屋に置いてみる」を実現できる家具・雑貨ECアプリ。

---

## 8. ゲーム

- **Apple Games アプリ**（iOS 26）: Game Centerを刷新した専用アプリ。リーダーボード起点でリアルタイム対戦できる**Challenges**、**Activities**が新規追加。
- **GameKit**: Xcode 26で**GameKitバンドル**によりGame Center設定をXcode内で直接構成しASCと同期可能に。旧`GKChallenge`は非推奨化、`GKChallengeDefinition`ベースへ移行推奨。
- **アプリアイデア**: フレンドとスコアを競うカジュアルゲーム、リーダーボードから発火するデイリーチャレンジ機構を持つパズルゲーム。

---

## 9. PDFKit / VisionKit

### PDFKit
- 大きな新API追加なし。`PDFView` / `PDFDocument` / `PDFAnnotation` による既存機能が引き続き中核。

### VisionKit
- `ImageAnalyzer`によるLive Text、`DataScannerViewController`によるライブカメラでのテキスト・コードのリアルタイムスキャン、Subject Lifting（被写体切り抜き）が主要3本柱。
- **アプリアイデア**: レシート・名刺をリアルタイムスキャンして構造化データに変換する家計簿/名刺管理アプリ、被写体を切り抜いてコラージュを作るクリエイティブアプリ。

---

## 参考: iOS 27（2026年秋予定・現在ベータ）で見えている続き

- **RealityKit**: 物理空間ライティング、リアルタイム布シミュレーション、**3D Gaussian Splatting**のネイティブレンダリング対応。
- **Core Image**: RAW処理v9でシャープネス・色再現が向上。

主要ソース:
- https://developer.apple.com/videos/play/wwdc2025/319/ (Cinematic video)
- https://developer.apple.com/videos/play/wwdc2025/253/ (Capture controls)
- https://developer.apple.com/videos/play/wwdc2025/277/ (SpeechAnalyzer)
- https://developer.apple.com/videos/play/wwdc2025/251/ (Audio recording)
- https://developer.apple.com/videos/play/wwdc2025/205/ (Metal 4)
- https://developer.apple.com/videos/play/wwdc2025/287/ (RealityKit)
- https://developer.apple.com/videos/play/wwdc2025/214/ (Game Center)
- https://developer.apple.com/documentation/DockKit
- https://developer.apple.com/documentation/roomplan/
- https://developer.apple.com/documentation/visionkit
