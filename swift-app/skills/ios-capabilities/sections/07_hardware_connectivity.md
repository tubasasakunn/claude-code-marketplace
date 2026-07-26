# iOS ハードウェア・センサー・周辺機器・近接通信系機能 調査報告書（iOS 26 / watchOS 26）

各項目に「できること・制約・最低OS・アプリアイデア例」を記載。確度が低い情報は「未確認」と明記。

---

## 1. NFC

### 1.1 Core NFC（タグ読み書き）
- **できること**: NFC Forum Type 1〜5 タグの NDEF 読み書き。ISO7816（APDU）、ISO15693、**FeliCa**（`NFCFeliCaTag`）、MIFARE の生コマンド。バックグラウンドタグ読み取り（アプリ未起動でもシステムが検出→ポップアップ）。
- **制約**: エンタイトルメントは**申請不要・自動付与・無料**。`NFCReaderUsageDescription` 必須。
- **最低OS**: NDEF読み取り iOS 11 / 書き込み・FeliCa iOS 13 / バックグラウンド読み取り iOS 14
- **アイデア例**: NFCシールの物理ショートカット（タップでルーティン記録）、デジタル名刺、**交通系ICカードの残高・履歴読み取り→家計簿連携**（Suica読み取りは既存アプリで実績あり）

### 1.2 HCE（Host Card Emulation）— 2つの別制度が併存
| | (A) HCEベース無償ソリューション | (B) NFC & SE プラットフォーム |
|---|---|---|
| 対象地域 | **EEA限定** | **日本含む世界70地域超** |
| 最低OS | iOS 17.4 | 日本は **iOS 18.1** |
| 要件 | EEA域内事業拠点、Apple個別承認 | **Appleとの商用契約+NDA+決済ライセンス+第三者セキュリティ監査** |

- **結論: 個人開発では EEA でも日本でも事実上使えない**。読み取り側（Core NFC）で完結するアイデアに絞るべき。

---

## 2. UWB / iBeacon / Bluetooth

### 2.1 UWB（Nearby Interaction）
- **できること**: 対応デバイス間の**相対距離+3D方向ベクトル**測定。iPhone同士とUWBアクセサリの両方。iOS 16〜はカメラアシスト（ARKit連携）で精度拡張。
- **制約**: ピア間はエンタイトルメント不要。**アクセサリ連携用エンタイトルメントはApple個別承認**。**フォアグラウンド前提**。iPhone 11以降（U1）、iPhone 17は全モデルUWB搭載（17e除く）。
- **最低OS**: iOS 14（基本）/ iOS 16（カメラアシスト）
- **アイデア例**: 待ち合わせで「あと何m・どっち」をARで示すアプリ、精密探し物アプリ。

### 2.2 iBeacon
- **できること**: BLEビーコンの領域監視。**アプリ終了後もシステムが再起動してenter/exitイベントを配送**。iOS 17の新API **`CLMonitor`**（async/await）への移行が進行中。
- **制約**: 監視リージョンはアプリ全体で20個上限。常時位置情報の許可が必要。通知遅延は平均3〜5分。
- **アイデア例**: 部屋単位の入室検知ルーティン、場所トリガーのコンテキストTODO。

### 2.3 Bluetooth（Core Bluetooth / AccessorySetupKit）
- **Core Bluetooth**: BLE Central/Peripheral 両ロール。バックグラウンド動作・復帰可。iOS 5〜。
- **AccessorySetupKit（iOS 18新規）— 個人開発の狙い目**:
  - AirPods風のワンタップ・ペアリングUIをサードパーティBLE/Wi-Fiアクセサリに提供。**MFi認証不要**。
  - ピッカー表示自体が同意になり、**Bluetooth全体許可ダイアログをスキップできる**。
  - `NSAccessorySetupKitSupports`（忘れるとクラッシュ）+ 発見条件宣言必須。
- **アイデア例**: 自作ESP32/Arduino BLEガジェットを洗練されたUIで取り込むDIYガジェット管理アプリ、BLE環境センサーモニタ。

---

## 3. Wi-Fi Aware / Multipeer / Network

### 3.1 Wi-Fi Aware（**iOS 26 新フレームワーク**）★注目
- **できること**: ルーター・インターネット不要でデバイス間の**直接・高速・低遅延・暗号化Wi-Fi通信**。AirDropの内部技術相当を業界標準（NAN）ベースで開放。**Android等の他社機器とも規格上は通信可能**（相互接続の実状は流動的）。
- **制約**: エンタイトルメント `com.apple.developer.wifi-aware` 必須（Xcodeから追加可）。`WiFiAwareServices` でサービス名宣言。
- **最低OS**: iOS 26
- **アイデア例**: 会場・教室でのオフライン高速写真共有、オフライン多人数リアルタイム協働ホワイトボード。

### 3.2 Multipeer Connectivity
- deprecatedではないが実質保守モード。新規開発ならWi-Fi Aware優先。iOS 25以前もサポートしたい近距離マルチプレイでは現役。

### 3.3 Network framework（iOS 26 更新）
- iOS 26で: **structured concurrency 完全対応**、**Codable型の直接送受信**、組み込みTLVフレーマー、`.wifiAware` 統合。P2Pアプリの実装コストが大幅に下がった。

---

## 4. センサー

### 4.1 Core Motion
- `CMMotionManager`（加速度・ジャイロ・姿勢）、`CMPedometer`（歩数・距離・階数、過去7日分）、`CMMotionActivityManager`（歩行/走行/自転車/車/静止の推定）。
- 近年の追加: AirPodsからのモーションストリーミング、`CMWaterSubmersionManager`（水深、Watch Ultra）。
- iOS 26での大型新APIは確認できず。`NSMotionUsageDescription` 必須、エンタイトルメント不要。
- **アイデア例**: 移動手段の内訳を自動記録するライフログ、傾き・振動ジェスチャのミニゲーム。

### 4.2 気圧計（CMAltimeter）
- 相対高度+気圧（iOS 8〜）、**絶対高度**（海抜、iOS 15〜）。
- **アイデア例**: 階段昇降の可視化、登山用高度ロガー。

### 4.3 環境光センサー
- **公開APIなし。取得不可**。代替はダークモード設定への追従、またはカメラでの明度推定（審査リスクあり）。

### 4.4 Core Location（新機能）
| API | 内容 | 最低OS |
|---|---|---|
| `CLMonitor` | 円形リージョン+ビーコン条件を最大20件、async streamで監視 | iOS 17 |
| `CLServiceSession` | 権限を宣言的に扱う新モデル | iOS 18 |
| `CLBackgroundActivitySession` | バックグラウンド位置監視の継続用軽量セッション | iOS 18 |
| Location Push Service Extension | APNsトリガーでアプリ未起動でも位置取得。**専用エンタイトルメント要申請** | iOS 15 |

- **iOS 26 の変更**: `CLGeocoder` / `CLPlacemark` が非推奨化 → MapKit の `MKReverseGeocodingRequest` / `MKGeocodingRequest` へ移行。
- **アイデア例**: 場所の出入りを自動記録する無意識ログ（CLMonitor）。

---

## 5. HealthKit / WorkoutKit

### HealthKit 新機能
- **State of Mind（`HKStateOfMind`、iOS 18〜）**: 感情/気分の記録・読み取り。Valence（-1〜+1）、38種の感情ラベル。ガイドライン1.4.1（医療効能を謳うと厳格審査）に注意 — 効能を謳わない「自己観察・日記」の枠なら個人開発でも有望。
- **Medications API（iOS 26）**: Healthアプリの薬剤・服薬記録の読み取り（`HKUserAnnotatedMedication` 等）。
- **ワークアウトAPIのiPhone対応（iOS 26）★注目**: `HKWorkoutSession` / `HKLiveWorkoutBuilder` が iPhone/iPad 単体で使用可能に（従来Watch専用）。**Watch非所持ユーザー向けワークアウトアプリが作れる**。
- 睡眠時無呼吸（`appleSleepingBreathingDisturbances`、iOS 18.1）: サードパーティ読み取り可否は未確認。

### WorkoutKit（iOS 17〜）
- インターバル/ペースベース/カスタムワークアウトをアプリ内で作成し、`WorkoutPlan` として**Watchのワークアウトアプリへ同期**。
- **アイデア例**: 体調に合わせたインターバルメニュー自動生成→ワンタップでWatchへ送るランニング補助。

---

## 6. Apple Watch 連携（watchOS 26）

- **Smart Stack — Relevance API（watchOS 26新規）**: ウィジェットが場所・時間・睡眠スケジュール等の文脈で自動的にSmart Stackへ浮上。WidgetKitベース必須。
- **Control Widget（watchOS 26新規）**: iPhoneアプリのControlを、**Watchアプリなしで**WatchのControl Center / Action Button / Smart Stackに追加可能。
- **ダブルタップ**: `.handGestureShortcut(.primaryAction)` で独自アクション起動可（watchOS 11〜、1画面1つ）。
- **手首フリック（watchOS 26新ジェスチャ）**: システム固定アクション専用で、サードパーティ向け公開APIは見つからず。
- **アイデア例**: ジムや駅にいる時だけSmart Stackに浮上する文脈ツールウィジェット、ダブルタップで「今日のタスク1件完了」のミニマルToDo。

---

## 7. AirPods 連携

- **心拍センサー（AirPods Pro 3、2025年9月発売）**: PPG光学式心拍センサー搭載は**事実**。ワークアウト中の心拍を**HealthKitの`heartRate`経由**でサードパーティが読める。**専用APIは存在しない**（HealthKitを普通に読むだけ）。**HRVサンプルは生成されない**（HRVが要る場合はWatch必須）。
- **頭ジェスチャ（うなずき/首振り）**: システム機能で専用開発者APIは確認できず。
- **`CMHeadphoneMotionManager`（iOS 14〜）**: AirPodsの頭部の向き・加速度・回転をストリーミング取得。エンタイトルメント不要。
- **アイデア例**: 頭の向きで音像が動く瞑想/ASMRアプリ、うなずきでハンズフリー操作するリーダーアプリ（自前実装）、**Watch不要のAirPods心拍インターバルトレーニング補助**。

---

## 8. バッテリー・充電 / EnergyKit

- `UIDevice.batteryLevel / batteryState`: 従来通り約5%刻み。iOS 26での新API追加は確認できず。
- **EnergyKit（iOS 26新規）**: 電力網の「クリーン/安価な時間帯予報」。ただし**米国本土のみ+本番エンタイトルメントは事実上ハードウェアOEM限定**。**個人開発のアイデアには使えない**。

---

## 9. HomeKit / Matter、CarPlay

### HomeKit / Matter
- HomeKit（`HMHomeManager`）は現役。エンタイトルメントは**自己付与でき申請不要**。個人発の有料コントローラーアプリの前例多数（Controller for HomeKit等）。
- Matter: 独立Matterコントローラーを作るより、Apple Homeに追加済みのMatter機器をHomeKit経由で扱う設計が現実的。
- **アイデア例**: HomeKitセンサー値の見える化・履歴グラフ、高機能自動化ダッシュボード。

### CarPlay
- カテゴリ: Audio / Communication / Navigation / EV Charging / Parking / Fueling / Driving Task / Quick Food Ordering / **Voice-based conversational apps（iOS 26.4新設、AIチャット系）** / Video（駐車中）/ **Widgets・Live Activities（iOS 26新規）**。
- **全カテゴリで個別エンタイトルメント申請必須**（SLAなし・数日〜数ヶ月）。
- **個人開発の狙い目**: **Driving Task**（実装深度が浅い、走行距離ログ等）と**Voice-based conversational**（新設）。

---

## 10. 外部アクセサリ

- **External Accessory（MFi）**: メーカー提携前提で**個人開発では実質使えない** → AccessorySetupKit + CoreBluetoothが正解。
- **USB/HID**: キーボード・ゲームコントローラーは`GameController`フレームワークでエンタイトルメント不要。
- **外部ストレージ**: iPadOS 13〜、USBメモリ/SDカードをFiles経由でアクセス可。NTFS非対応。
- **DriverKit**: iPhoneには存在しない（macOS・M系iPadのみ）。

---

## 11. デバイス管理系

- Managed App Configuration / Declarative Device Management は**個人開発の消費者向けアプリには無関係**。B2B展開時のみAppConfig対応が差別化に。

---

## 総括 — 個人開発の観点での機会マップ

| 評価 | 領域 |
|---|---|
| **狙い目（新しい+参入可）** | Wi-Fi Aware（iOS 26新規、オフラインP2Pの新ジャンル）、AccessorySetupKit（MFi不要BLE連携）、HealthKitワークアウトのiPhone単体対応（Watch不要ワークアウトアプリ）、AirPods Pro 3心拍（HealthKit経由・追加API不要）、Smart Stack Relevance API、CarPlayのDriving Task/会話型カテゴリ、CLMonitor（場所トリガー）、Medications API |
| **堅実（枯れているが有効）** | Core NFCタグ読み取り（FeliCa残高読み取り含む）、iBeacon、Core Motion/CMPedometer、CMAltimeter、CMHeadphoneMotionManager、HomeKit連携、iPad外部ストレージ |
| **条件付き** | UWBアクセサリ連携（個別承認）、State of Mind（効能を謳わない設計が必須）、Location Push（要申請） |
| **手を出せない** | HCE/NFC&SE（法人契約前提）、EnergyKit（OEM限定+米国のみ）、環境光センサー（API非公開）、External Accessory/MFi、DriverKit、CarPlayのEV充電/駐車場/フード、MDM系 |

**要再検証の項目**: 睡眠時無呼吸データのサードパーティ読み取り可否、手首フリックの開発者API有無（現状なしと推測）、Wi-Fi AwareのiOS-Android相互接続の実状。
