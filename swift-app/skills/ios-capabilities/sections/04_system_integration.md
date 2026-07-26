# iOS システム統合・自動化・インテント系機能 調査レポート（iOS 26 基準、2026年7月時点）

## 調査の前提

- 対象は **iOS 26**（2025年9月リリース、2026年7月現在は iOS 26.5 前後の点リリースが最新）。
- WWDC26（2026年6月開催）で **iOS 27**（2026年秋リリース予定、現在デベロッパーベータ）の新機能が既に発表されている。本レポートは iOS 26 を主眼に置きつつ、企画時に知っておくべき iOS 27 の変更点は「iOS 27 プレビュー」として明示的に分離して記載する。
- Apple Intelligence 系機能の多くは **iPhone 15 Pro / iPhone 16e 以降（A17 Pro+）** が要件。この制約はアプリ企画上、無視できない前提条件になる。

---

## 1. App Intents の全体像と iOS 26 での強化

### 全体像
App Intents は Siri・Spotlight・ショートカット・ウィジェット・Control Center・Action Button・Focus フィルタなど、iOS のあらゆるシステム面から自分のアプリの機能を呼び出させるための唯一の窓口になりつつある枠組み。`AppIntent` プロトコルで1つのアクションを定義すると、それが複数の入口に同時展開される。

### iOS 26 での主な強化点

| 機能 | 内容 | 制約 |
|---|---|---|
| **Interactive Snippets** | 意図の実行結果として、ボタンや入力欄を持つ SwiftUI ビュー（Snippet）を Spotlight・Siri 応答面などシステムUI内にその場でポップアップ表示できる。Snippet 上で操作を続けて別の Intent に連鎖させ、一連のフローを完結できる | iOS 26+ |
| **Visual Intelligence 統合** | カメラや画面キャプチャ経由のビジュアル検索にアプリのコンテンツを出す。`IntentValueQuery` プロトコルを実装し、`SemanticContentDescriptor` を受け取って `AppEntity` の配列を返す。`OpenIntent` で該当コンテンツへ直接遷移 | iOS 26+ |
| **`@DeferredProperty`** | エンティティの重いプロパティを「表示に必要になった時点」で非同期計算するプロパティラッパー | iOS 26+ |
| **Spotlight でのアクション実行** | **macOS Tahoe 26** で新規に「Spotlight からアプリのアクションを直接実行」できるようになった。**iOS は元々対応済み**で、iOS 26 での強化点は Visual Intelligence 検索結果の統合が中心 | `IndexedEntity` 準拠とドネートが必要 |
| **`UndoableIntent`** | Intent 実行を既存のUndo UI（シェイク/3本指スワイプ）で戻せるようにするプロトコル。`undoManager` をシステムが注入 | iOS 26+ |

### アプリアイデアへの示唆
- 家計簿アプリで「レシートを撮る→Visual Intelligence 経由でアプリの支出記録エンティティとして検索可能に」
- タスク管理アプリで「Spotlight から直接『完了にする』を実行→間違えたら取り消しジェスチャーで戻せる」
- Interactive Snippet で「Siri に聞いた瞬間、アプリを開かずにその場で選択肢を選んで完結する」体験

---

## 2. Shortcuts 連携と Apple Intelligence モデル呼び出し

### 何ができるか
- iOS 26 の Shortcuts に **25以上の新アクション**が追加。目玉が **「モデルを使用（Use Model）」** アクションで、ショートカットの1ステップとして LLM を呼び出し、結果を後続ステップに渡せる。
- モデルは3種類から選択:
  - **オンデバイス**: 端末上の Apple Intelligence モデル。ネットワーク不要
  - **Private Cloud Compute**: 複雑なリクエストをAppleのプライバシー保護クラウドで処理
  - **拡張機能モデル**: ChatGPT 連携
- App Intents を実装したアプリは自動的に Shortcuts アプリの「アクション」候補になる。

### 制約
- Apple Intelligence 対応端末（iPhone 15 Pro 以降）が前提。
- 1アプリが宣言できる **App Shortcut は最大10個**、トリガーフレーズは**ロケールごとに合計1000個**まで。
- 「モデルを使用」の出力は構造が不安定になりうるため、後続ステップでの型変換・エラーハンドリング設計が必要。

### アプリアイデアへの示唆
- 自アプリの機能をApp Intent化するだけで、ユーザーが「Use Model」と組み合わせて"アプリ機能×LLM"の独自オートメーションを作れる
- オンデバイスモデルのみで完結する軽量AI機能ならネットワーク不要・プライバシー訴求できる

---

## 3. Siri でできること・できないこと（2026年7月時点の実態）

### 現状の到達点
- 2025年3月にApple自ら「パーソナライズドSiri」の延期を発表して以来、第二世代のLLMベースへの作り直しが進行中。
- **2026年7月現在、刷新版Siriはまだ未リリース**。報道によれば **2026年9月、iOS 27と同時に**、Google CloudのGemini + Nvidia Blackwell GPUを使うハイブリッド構成で登場する見込み。
- **WWDC26（2026年6月）で SiriKit が正式に非推奨（deprecated）を宣告**され、新規開発でSiriへ機能を繋ぐ唯一の経路は **App Intents** になった。
  - ソフト期限: **2026年9月（iOS 27公開）** — Siriの新しいクロスアプリ・エージェントチェイニング機能から取り残される
  - ハード期限: **2028〜2029年頃** — SiriKitが実際に動かなくなる想定

### 現状（iOS 26）でSiriができること
- App Intentsを実装したアプリの機能を、決まったフレーズ／自然文である程度呼び出す
- Focus フィルタ経由でアプリの状態を制御

### 現状でSiriができない・弱いこと
- 深い「パーソナルコンテキスト理解」は**未提供**
- 複数アプリをまたいだ自律的なタスク遂行は**iOS 27で初出**予定

### iOS 27 プレビュー（ベータ中、企画の前提にはまだできない）
- **App Schemas**によるより高度なSiri連携
- ストリーミング応答、マルチターン会話、View Annotations API（「その写真」のような画面参照）
- Foundation Models フレームワークが**マルチプロバイダ対応**（Claude・Gemini等を選択可能に）
- 新設の **Core AI Framework**（Apple silicon最適化でフルスケールLLMをオンデバイス実行）

### アプリアイデアへの示唆
- 今の時点でSiri統合をウリにするなら「App Intentsの完成度」自体が差別化になる
- iOS 27のApp Schemas対応を見据えてApp Intentsを丁寧に作り込むのが妥当な投資判断

---

## 4. 通知・Focus・Screen Time / DeviceActivity

### 通知
- iOS 26で **Apple Intelligenceによる「インテリジェント・ブレイクスルー＆サイレンシング」**が導入。Focus中でも「本当に重要」と判断された通知だけ通す。
- 通知センターは**「ユーザーが最初に反応しそうな順」でグルーピング・ランキング**する方式に変化。

### Focus
- **Focus Filters API**: アプリが現在アクティブなFocusモードに応じて自身の挙動・表示内容を動的に変える仕組み。
  - 例: SNSアプリが「パーソナルFocus」では親しい友人の投稿のみ表示、健康アプリが「公開Focus」では機微な数値を隠す、等。

### Screen Time / DeviceActivity（要注意の不具合あり）
| フレームワーク | 役割 |
|---|---|
| `FamilyControls` | 同意取得、対象アプリ・カテゴリの選択（トークン化されたセレクション） |
| `ManagedSettings` | 制限（ブロック・シールド表示等）のルール適用 |
| `DeviceActivity` | 使用時間の監視。`DeviceActivityMonitor`拡張が開始/終了/しきい値到達イベントを受信 |

- **しきい値通知**は `DeviceActivityMonitor` の `eventDidReachThreshold` で実現可能。
- **制約**: `DeviceActivityMonitor`拡張の**メモリ上限は6MB**と非常に厳しい。
- **既知の不具合（要警戒）**: iOS 26ベータ以降、**DeviceActivityのしきい値が発火しない**、拡張がメモリ圧迫でクラッシュする、という報告が多数。**「使用時間に反応するアプリ」を企画する場合、iOS 26時点では動作信頼性の検証が必須**。

### アプリアイデアへの示唆
- デジタルウェルビーイング系は王道だが、DeviceActivityの現状の不安定さがリスク。実機で閾値発火のテストを厚めに
- Focus Filters APIによる「集中モード中は表示を変える」ミニマルな付加価値は実装コストが低く効果が見えやすい

---

## 5. Live Translation と Translation API

### Live Translation（システム機能）
Apple Intelligence搭載のシステムレベル翻訳機能。**すべて端末上で処理**。

| 場面 | 動作 | 制約 |
|---|---|---|
| **メッセージ** | 送信テキストを相手の設定言語に自動翻訳、返信も自分の言語に翻訳 | — |
| **電話** | 通話中に相手の発言を音声で翻訳して聞かせ、自分の発言も翻訳して伝える | **1対1通話のみ**、対応言語は**英・仏・独・葡・西のみ**（2026年7月時点） |
| **FaceTime** | **リアルタイム字幕**として翻訳表示 | — |

- 要件: **iPhone 15 Pro 以降**

### Translation フレームワーク（アプリ内翻訳API）
- `TranslationSession` でアプリ内テキストをオンデバイスMLモデルで翻訳。**SwiftUI専用**（`translationTask` モディファイア経由）。
- 言語ごとにローカルモデルが必要で、未ダウンロードならシステムがダウンロードシートを自動提示。
- バッチ翻訳リクエストに対応。**完全オフライン翻訳が可能**、APIは無料。

### アプリアイデアへの示唆
- 旅行系・語学系アプリで「Apple純正の高品質オフライン翻訳を無料で組み込む」ことが可能（自前でAPI課金する翻訳エンジンが不要）

---

## 6. バックグラウンド実行

| 手法 | 用途 | 制約・特徴 |
|---|---|---|
| **`BGAppRefreshTask`** | 短時間の定期コンテンツ更新 | 実行機会はシステム裁量、確実性は低い |
| **`BGProcessingTask`** | 充電中・Wi-Fi接続時などにまとまった処理 | 実行タイミングは非保証 |
| **Background Push** | サーバー起点でアプリを起こしてフェッチ | 低優先度扱い、即時起動は非保証 |
| **`BGContinuedProcessingTask`（iOS 26新規）** | **フォアグラウンドでユーザーが開始した処理**（書き出し、エクスポート等）をバックグラウンド遷移後も継続。システムが進捗UIを表示し、対応デバイスでは**バックグラウンドGPUアクセス**も可能 | **iOS/iPadOS 26のみ**。「見える化されたユーザー起点の作業」専用。進捗報告が必須 |
| **Live Activities 経由の更新** | ロック画面/Dynamic Island上のリアルタイム情報更新。APNs経由でサーバーから直接更新可能 | **iOS 26で新規スケジューリングAPI**（特定時刻に自動開始）追加。CarPlay/Mac/iPadにも展開。**iOS 26.5で`AccessoryLiveActivities`**追加 |

### アプリアイデアへの示唆
- 「エクスポート」「レンダリング」などユーザーが明示的に押した重い処理を裏に回すなら `BGContinuedProcessingTask` が本命
- 配達・スコア速報・タイマー系はLive Activities + APNsプッシュ更新が定番。スケジューリングAPIで「予定時刻に自動でLive Activity開始」が新しい設計余地

---

## 7. CloudKit / SwiftData の新機能

- **SwiftData（iOS 26）**: モデル継承のサポート、`Codable`プロパティへのPredicate対応、履歴フェッチへの`sortBy`追加など地道な強化。
- **重大な制約が継続**: SwiftDataの自動iCloud同期は**プライベートDBのみ対応**。**パブリック/共有DB（複数ユーザー間の共同編集・共有）は2026年7月時点でも未サポート**。
  - 複数ユーザーが絡む共有アプリは「Core Data + CloudKit Sharing（`NSPersistentCloudKitContainer`）を使うべき」とApple DTSも案内。
  - 共有には `CKShare` + `UICloudSharingController` を使ったCloudKit直叩き実装が必要。

### アプリアイデアへの示唆
- **「家族で共有」「友達と共同編集」系のアプリは要注意**。共有要件が中核なら最初からCore Data + CloudKit Sharing構成を選ぶか、「まず個人利用版をSwiftDataでリリースし、共有は後日対応」という段階的判断が現実的

---

## 8. WidgetKit の push 更新

- **Widget Push Notifications**: サーバー側でデータ変化を検知したらAPNsにプッシュを送り、**プッシュトークン経由でWidgetKitに届いて該当ウィジェットのタイムラインを自動リロード**させる仕組み（`WidgetPushInfo`でトークン取得）。
- **予算制（budget）あり**: リロード頻度は制限される。開発時はWidgetKit Developer Modeで予算を無視できる。

### アプリアイデアへの示唆
- 株価・スポーツスコア・配送状況など「サーバー側が変化の起点」のウィジェットで即時反映したい場合に有効

---

## 9. Wallet / PassKit・Apple Pay の新機能

### Digital ID / 身分証
- **iOS 26.1**で米国パスポートによる Digital ID がWallet内で作成可能に。TSAチェックポイント、対応アプリ/Webでの本人確認に使用可。

### チケット/パス
- **複数イベントチケット**: シーズンパス向けに1パスで複数日程をカバー。遠隔で動的更新可能。
- **セマンティック搭乗券**: 動的レイアウト、Live Activity連携。

### Verify with Wallet API（年齢/本人確認）
- アプリ内で**運転免許証・州発行ID・パスポート**をWallet経由で提示させ、年齢確認や本人確認をノーカメラ・ノー書類アップロードで実現。
- 導入要件: "In App Identity Presentment" capability、Identity Access Certificate。
- **対応IDは限定的**（米国中心。日本の身分証は非対応）。

### Apple Pay
- Apple Payボタンにデフォルトカードのアートワークが動的表示。
- Apple CashがグループiMessage内での割り勘送金に対応。

### iOS 27 プレビュー
- カスタムWalletパスの作成をユーザー自身が可能に
- レシートをカメラでスキャン→Apple Intelligenceが品目認識しApple Cashで割り勘

### アプリアイデアへの示唆
- Verify with Walletは日本市場向けアプリでは実用性が低い点に注意
- イベント/会員系アプリはWalletの複数イベントチケットやセマンティックパスとの連携で差別化できる

---

## 10. SMS/通話のスパムフィルタ

### メッセージ: `IdentityLookup` フレームワーク
- **Message Filter Extension**を実装し、`.filter`/`.allow`/`.none`を返す。
- **重要な制約**: **連絡先にない送信者からのSMS/MMSのみが対象**。iMessageや連絡先登録済みの相手には**一切効かない**。
- ユーザーは設定で任意のフィルタアプリをONにする必要がある。

### 通話: Unwanted Communication拡張 / Call Directory
- **Call Directory Extension**で着信番号のブロックリスト/識別リストをシステムに提供（Truecaller、Hiya等が採用）。
- **制約**: 同時に有効化できるUnwanted Communication拡張は1つだけ。

### アプリアイデアへの示唆
- 迷惑SMS/通話ブロックは先行プレイヤーが強い競争領域。日本語フィッシングSMS特化などニッチな切り口なら勝ち筋はあり得る

---

## 11. RelevanceKit / AlarmKit / EnergyKit 等 iOS 26 新フレームワーク

### AlarmKit（iOS 26）★注目
- サードパーティアプリに**Clockアプリと同等のアラーム権限**を初めて開放。フルスクリーンアラート、**サイレント/Focus貫通の音**、ロック画面UI、Dynamic Island統合。
- **スケジュールベース**（毎朝7:30）と**カウントダウンベース**（今から25分後、ポモドーロ用途）の両方に対応。
- 従来はCritical Alert entitlement（個別許可制）でしか実現できなかったことが正式APIとして解禁。
- 複数のアラーム/睡眠系アプリ（RealAlarm、AutoSleep等）が既に採用。

### RelevanceKit（iOS/watchOS 26、ベータ扱い）
- **主眼はApple Watchのスマートスタック**。オンデバイスのコンテキスト手がかり（時間・場所・ヘッドフォン装着・ワークアウト中等）を使い、ウィジェットを適切なタイミングで浮上させる。
- 「GM前にAPIが変わりうるベータフレームワーク」との明記あり。

### EnergyKit（iOS 26）
- HomeKitと連携し、自宅ロケーションに基づいた電力グリッド予報（クリーン/安い電力の時間帯）をアプリに提供。
- 想定用途はEV充電アプリ・スマートサーモスタットアプリ。
- **米国本土限定**（日本では現状使えない）。

### アプリアイデアへの示唆
- AlarmKitは睡眠・習慣化・生産性（ポモドーロ）系アプリにとって明確な新機会。「通知が無視される」「サイレントモードで鳴らない」という積年の弱点が解消される

---

## 総括: 最低OSバージョン早見表

| 機能 | 最低OS | 端末要件 |
|---|---|---|
| Interactive Snippets / Visual Intelligence統合 / UndoableIntent | iOS 26 | — |
| Use Model（Shortcuts） | iOS 26 | iPhone 15 Pro以降 |
| Live Translation | iOS 26 | iPhone 15 Pro以降 |
| Translation framework（アプリ内翻訳） | iOS 17.4〜、SwiftUI限定 | 言語モデルは都度ダウンロード |
| BGContinuedProcessingTask | iOS/iPadOS 26のみ | — |
| Live Activitiesスケジューリング | iOS 26 | — |
| AccessoryLiveActivities | iOS 26.5 | アクセサリ側の対応要 |
| AlarmKit | iOS 26 | — |
| RelevanceKit | iOS/watchOS 26（ベータ） | 主にApple Watch向け |
| EnergyKit | iOS 26 | 米国本土限定 |
| Digital ID（Wallet） | iOS 26.1 | 米国パスポート/一部州ID |
| DeviceActivity | iOS 15〜、iOS 26は不具合報告あり | 拡張メモリ上限6MB |
| WidgetKit push notifications | iOS 17系〜 | 予算制あり |

## 企画判断に直結する4点

1. **App Intentsの丁寧な実装が今後2年の投資対効果として最も高い**（Siri刷新・Spotlight・Shortcuts・Visual Intelligenceすべての入口になる）
2. **DeviceActivity/Screen Time系はiOS 26時点で信頼性リスクがあり実機検証必須**
3. **SwiftDataは単独では複数ユーザー共有機能を実現できない**
4. **AlarmKit/Live TranslationはApple Intelligence対応機限定という制約付きだが訴求力の強い新機能**

主要ソース:
- https://developer.apple.com/documentation/appintents
- https://blakecrosley.com/blog/app-intents-2-ios-26-additions
- https://developer.apple.com/documentation/AlarmKit
- https://developer.apple.com/documentation/RelevanceKit
- https://developer.apple.com/energykit/
- https://developer.apple.com/videos/play/wwdc2025/227/ (Finish tasks in the background)
- https://developer.apple.com/documentation/WidgetKit/Updating-widgets-with-widgetkit-push-notifications
- https://developer.apple.com/wallet/whats-new/
- https://www.macrumors.com/guide/llm-siri/
