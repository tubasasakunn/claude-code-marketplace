# iOS 26 オンデバイス機械学習調査（Apple Intelligence / Foundation Models 除く）

対象OS: iOS 26（2026年7月時点で最新）。フレームワーク別に「何ができるか／性能感／制約／最低OS／アプリアイデア」を整理。

---

## 1. Core ML

### 1.1 Stateful Models（iOS 18〜）
推論呼び出しをまたいでGPU上に中間バッファ（典型的にはKVキャッシュ）を保持できる。`ct.StateType` で宣言 → `mlmodel.make_state()` → `predict(..., state:)`。
- **性能**: Mistral 7B実験（M3 Max）でトークン生成が約1.6倍高速化。
- **用途**: オンデバイスチャットボット、要約アシスタントなどトークンストリーミング生成を伴うオフラインアプリ。

### 1.2 MLTensor API（iOS 18〜）
NumPy/PyTorch風API（`matmul`, `softmax` 等）で、Core MLモデルの前後処理・サンプリングロジックを `MLMultiArray` の手作業なしに書ける。

### 1.3 量子化・圧縮（coremltools.optimize）
パレット化（1〜8bit LUT）、線形量子化（INT4/INT8、W8A8）、プルーニングの3手法。
| OS | 追加された圧縮機能 |
|---|---|
| iOS 16 | パレット化、8bit量子化、プルーニング |
| iOS 17 | 活性化量子化（W8A8）— A17 Pro/M4のint8パス |
| iOS 18 | グループ化チャネルLUT、3bit、INT4ブロック単位、joint compression |
| iOS 26（coremltools 9.0） | int8入出力dtype、state読み書きAPI拡張、PyTorch 2.7対応 |

### 1.4 実例
- **Whisper（WhisperKit, argmaxinc）**: iPhone 15 Proでlarge-v3-turboが10分音声を約82秒処理（5〜6倍速）、ストリーミングはsub-100ms。iPhone 17世代はGPUのNeural Acceleratorsで大型Transformer推論が2.5〜3.1倍高速化。
- **Stable Diffusion（apple/ml-stable-diffusion）**: iOS 16.2〜。iPhone 14 Pro Maxで1枚約7.9秒。`--quantize-nbits 6` 推奨。
- **小型LLM**: Llama 3.1 8BはInt4量子化で4.2GB。3B〜7B級はInt4で8GB RAM機（iPhone 15 Pro以降）が現実的な下限。

---

## 2. Vision framework（検出機能の棚卸し）

iOS 18で刷新された新スタイル（`VN`プレフィックス廃止、async/await）。30以上のリクエスト種別。

| API | 内容 | 最低OS |
|---|---|---|
| `DetectHumanBodyPoseRequest` / `3D` | 人体関節の2D/3Dキーポイント（3Dはメートル単位17関節、1人のみ） | iOS 14 / 17 |
| `DetectHumanHandPoseRequest` | 手の21関節。**iOS 26で新モデルに刷新**（旧モデルと座標非互換、分類器は再訓練必要） | iOS 14〜 |
| **`RecognizeDocumentsRequest`（iOS 26新規）** | 26言語のテキスト+文書構造解析: 段落・**テーブル**（結合セル対応）・**リスト**・文書内バーコード。DataDetectionフレームワーク連携でメール・電話・住所・通貨等を自動抽出 | **iOS 26** |
| **`DetectLensSmudgeRequest`（iOS 26新規）** | レンズ汚れ検出（純正カメラの「レンズを拭いて」と同じ）。閾値目安0.9 | **iOS 26**、A14以降 |
| `GenerateForegroundInstanceMaskRequest` | 被写体のインスタンスマスク生成（シミュレータ非対応） | iOS 17〜 |
| `ImageAnalysisInteraction`（VisionKit） | 「長押しで被写体が浮き上がる」UIを数行で実装 | iOS 16〜 |
| `DetectFaceLandmarksRequest` 等 | 顔矩形・76点ランドマーク・撮影品質スコア | iOS 11〜 |
| `DetectBarcodesRequest` / `DataScannerViewController` | 約25シンボロジー / テキスト+コード同時ライブスキャン標準UI | iOS 16〜 |
| `RecognizeTextRequest` | OCR（言語自動検出、customWords） | iOS 13〜 |
| `CalculateImageAestheticsScoresRequest` | 画像の見栄えスコア＋`isUtility`（書類/スクショ的画像かの判定） | iOS 18 |

**用途例**: レシート家計簿（RecognizeDocumentsRequestのテーブル抽出）、栄養成分表スキャン、名刺→連絡先自動生成、撮影プリフライトチェック（LensSmudge）、フォトアルバムから書類を自動除外（isUtility）。

---

## 3. Natural Language framework、埋め込み

| API | できること | 最低OS |
|---|---|---|
| `NLTagger` | 単語/文分割、品詞、固有表現(NER)、レンマ | iOS 12 |
| `NLEmbedding` | 単語/文の静的埋め込み、`neighbors()`で近傍探索 | iOS 13 |
| `NLContextualEmbedding` | **Transformerベースの文脈依存埋め込み**。27言語（日本語含むCJK対応）、512次元、ANE向け圧縮でDL約100MB未満 | iOS 17 |

- `NLContextualEmbedding`はサブワード単位出力のため、文全体の1ベクトルが欲しい場合はプーリングを自前実装。組み込み類似度ヘルパーはない。
- **用途例**: 日記アプリで過去の日記をベクトル化し「元気だった日」のような自然文検索をオフライン実現、類似メモ自動グルーピング、日英混在メモの意味検索。

---

## 4. 音声合成（AVSpeechSynthesizer / Personal Voice）

- `AVSpeechSynthesizer`（iOS 7〜）: `write()`で生オーディオバッファ取得可。音声品質は default / enhanced / premium（Siri品質、要DL）。
- **Personal Voice**: iOS 26で収録が**「10フレーズ・1分未満」に大幅短縮**（従来15分・150文）。完全オンデバイス処理。
  - 開発者API: `requestPersonalVoiceAuthorization()`（iOS 17〜）→ `voiceTraits.contains(.isPersonalVoice)`で絞り込み、通常の`AVSpeechUtterance`に設定するだけ。
  - AAC（拡張代替コミュニケーション）アプリを主眼とした機微機能。なりすまし回避が明記されている。
- **用途例**: 発話障害者向けAACアプリ、家族の思い出メッセージの本人音声化、絵本読み聞かせの親の声化（同意UI必須）。

---

## 5. SoundAnalysis（音の分類）

- `SNClassifySoundRequest`（iOS 13〜）: 組み込み分類器は**300種類以上**の音（動物、楽器、咳/笑い、警報、家電等）を識別。ファイル向けとライブ入力向けの2系統。
- カスタムモデル: Create ML / `MLSoundClassifier`（iOS 15〜、**アプリ内訓練も可**）で各カテゴリ最低10サンプル程度から。
- **用途例**: 聴覚障害者向け「音の見える化」通知、ペット/赤ちゃん見守り、楽器練習アプリの演奏音判定。

---

## 6. Create ML / Create ML Components（オンデバイス学習）

- **Create ML framework**（iOS 15〜）: `MLImageClassifier`/`MLSoundClassifier`等をSwiftから直接呼べ、**iOS上のアプリ内でその場で転移学習が可能**（数百枚なら訓練約5秒の報告）。チェックポイントAPIで訓練の一時停止・再開・追加学習。
- **Create ML Components**（iOS 16〜）: 特徴抽出器・推定器をレゴのように組み合わせる低レベルAPI。`HumanBodyPoseExtractor`、`HumanBodyActionCounter`（反復動作カウント）、`AudioFeaturePrint`等。`UpdatableEstimator`準拠でオンライン追加学習が可能。
- **用途例**: ユーザー独自ジェスチャー/ポーズを学習するフィットネス・リハビリアプリ、ユーザーの筆跡を学習する手書き認識。

---

## 7. Translation framework（オフライン翻訳）

- `.translationPresentation()`（iOS 17.4〜）: システム標準の翻訳ポップオーバー表示（最簡易）。
- `.translationTask()` + `TranslationSession`（iOS 18〜）: 独自UIに翻訳結果を組み込む。バッチ翻訳・AttributedString書式保持対応。
- すべてオンデバイス処理・無料。初回に言語モデルDLダイアログが自動表示。
- **制約**: SwiftUI専用。同一バッチ内に異なる言語ペア混在不可。**シミュレータでは機能せず実機テスト必須**。
- iOS 26: CallKitの**Call Translation API**（`CXSetTranslatingCallAction`）でサードパーティ通話アプリにも通話翻訳を統合可能に。

---

## 8. MLX（Apple製MLフレームワーク）

- `mlx-swift`はSPM配布で**iOS 17以上を公式サポート**。**シミュレータ非対応・実機必須**。大きめモデルには`increased-memory-limit`エンタイトルメントが必要。Core MLと異なり**訓練・ファインチューニングにも対応**。
- 実例: 公式`mlx-swift-examples`に`LLMEval`、`MLXChatExample`、`StableDiffusionExample`、`MNISTTrainer`。
- **性能感**: MLX（GPU）はバースト初速で優位、Core ML/ANEは熱スロットリングに強く持久力で逆転（「GPUは短距離走、ANEは長距離走」）。iPhone 17 Pro（12GB RAM）で1.2B・4bitが約70 tok/s。
- **実務上の上限**: iPhoneでは1B〜3B・4bit量子化が現実的範囲。**最大の制約は熱** — 短いリクエストを高速に返すバースト型UXが推奨。

---

## 9. BNNS / Accelerate、MPSGraph

- **BNNSGraph**（iOS 18〜）: グラフ全体を事前コンパイルし、ランタイムアロケーションなし・確定的レイテンシを保証。リアルタイム音声処理向け。**BNNSGraphBuilder**（iOS 26/WWDC25）はSwiftで直接グラフ記述。
- **MPSGraph**: Core MLより低レベル・高柔軟。Metalレンダリングと同一コマンドバッファ上でのML処理統合に向く。

| フレームワーク | 向いている用途 |
|---|---|
| Core ML | 既存学習済みモデルの本番デプロイ（標準選択肢） |
| MLTensor | Core ML前後の軽量テンソル演算 |
| BNNSGraph | CPU上でアロケーションなし・確定的レイテンシの小規模モデル/DSP |
| MPSGraph | カスタムレイヤー、Metalレンダリング統合 |

---

## 10. サードパーティ: llama.cpp / MLC / whisper.cpp の実情

- **llama.cpp**: 公式にiOS/SwiftUIサンプル同梱、GGUF実機動作。Swiftラッパー多数（`LocalLLMClient`等）。**App Store公開実例**: Enclave、Llama Compose、Private LLM。
- **MLC-LLM**: MLC ChatがApp Store公開済み（7Bクラス、6GB RAM目安）。
- **whisper.cpp / WhisperKit**: whisper.spm（SPM配布）。WhisperKitは2026年5月にv1.0.0（ASR+話者分離+TTSを1パッケージ化）。

### App Store審査上の扱い
- **ガイドライン2.5.2（コードDL・実行禁止）**: GGUFモデルは実行可能コードではなくデータ（重み）のため抵触しない、が実務上の共通理解（複数アプリの公開実績が傍証）。
- **ガイドライン5.1.2(i)（2025年11月施行）**: クラウドAIへのデータ送信時の同意モーダル義務化。**オンデバイス推論は対象外** — これがオンデバイスLLM採用の最大のコンプライアンス上のメリット。
- 実質的な審査論点は**1.2（生成コンテンツのモデレーション）と年齢レーティング**に移っている。

### 配布サイズの定石
- GGUF目安: 1B(Q4)約808MB、3B約2GB、8B約4.9GB。**モデルはアプリ本体に同梱せず実行時ダウンロードが定石**。
- オンデマンドリソース（ODR）は**iOS 27で非推奨化予定**、後継は**Background Assets**（Apple-Hosted、200GB相当まで無料）へ移行推奨。

---

## まとめ: アプリ企画に効く組み合わせ

- **オフライン日記/ジャーナリング**: `NLContextualEmbedding`意味検索 + Personal Voice読み上げ + 画像美的スコアで写真自動選別
- **書類・レシートスキャン**: `RecognizeDocumentsRequest`（テーブル抽出）+ `DetectLensSmudgeRequest`（品質チェック）
- **見守り/アクセシビリティ**: SoundAnalysis（異常音検知）+ Personal Voice/Live Speech（AAC）
- **オフライン旅行/多言語**: Vision OCR + Translation framework
- **パーソナライズ系フィットネス**: Vision 3Dポーズ + Create ML Components追加学習
- **プライバシー重視AIアシスタント**: MLX/WhisperKitでオンデバイス実行、5.1.2(i)同意ルール回避+「完全オフライン」訴求

主要出典:
- https://apple.github.io/coremltools/docs-guides/source/stateful-models.html
- https://machinelearning.apple.com/research/core-ml-on-device-llama
- https://github.com/argmaxinc/WhisperKit
- https://developer.apple.com/documentation/vision/recognizedocumentsrequest
- https://developer.apple.com/documentation/vision/detectlenssmudgerequest
- https://developer.apple.com/documentation/naturallanguage/nlcontextualembedding
- https://developer.apple.com/videos/play/wwdc2025/276/ (BNNS Graph)
- https://developer.apple.com/videos/play/wwdc2025/360/ (ML & AI frameworks)
- https://developer.apple.com/videos/play/wwdc2025/325/ (Background Assets)
- https://github.com/ml-explore/mlx-swift-examples
