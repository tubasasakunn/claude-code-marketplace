# 調査の更新手順 (ios-capabilities)

前提知識ゼロのエージェントが、この知識ベースを最新のiOSに合わせて作り直すための手順。

## いつ更新するか

- 新しいiOSメジャーバージョンの正式リリース後（毎年9月頃）
- WWDC直後（毎年6月。次期iOSの「プレビュー」情報を各セクションに追記する）
- SKILL.md記載の調査日から6ヶ月経過したとき
- ユーザーに「iOS調査を更新して」と言われたとき

## 手順

### 1. 現状把握

- SKILL.md の調査日と対象バージョンを確認する
- 「今日の日付」から、現行の安定版iOSと、ベータ中の次期iOSを特定する（Web検索で確認。憶測しない）

### 2. 7領域の並列調査

**Sonnet系モデルのサブエージェントを7体、並列で起動する**（1メッセージ内で全員起動。逐次実行しない）。
各エージェントへの共通指示:

- Web検索を駆使し、サードパーティアプリ開発者が実際に使える機能に絞って調査する
- 各項目について「API/フレームワーク名・できること・制約（エンタイトルメント要否含む）・最低OSバージョン・アプリのアイデアに使えそうな具体例」を必ず書く
- 現行安定版を主眼とし、ベータ中の次期iOS情報は「プレビュー」として明示的に分離する
- 出力は日本語Markdown、前置きなしで本文のみ（最終メッセージがそのまま報告書になる）
- 末尾に出典URL一覧を付ける
- 確度が低い情報は「未確認」と明記させる

| # | 担当領域 | 必須カバー項目 |
|---|---|---|
| 01 | Apple Intelligence / オンデバイスAI | Foundation Models（コンテキスト長・対応デバイス・言語・Guided Generation・Tool calling）、Writing Tools、Image Playground/Genmoji、Visual Intelligence、Siri統合、Smart Reply、ポイントリリース（26.1等）での追加 |
| 02 | UI・デザイン | デザイン言語の刷新（Liquid Glass等）、SwiftUI/UIKitの新API、アイコン仕様（Icon Composer）、ウィジェット/コントロール、Live Activities/Dynamic Island、テキスト編集 |
| 03 | 拡張ポイント | Share/Action Extension、カスタムキーボード、Safari拡張/Content Blocker、通知Service/Content Extension、Control Center/ロック画面/物理ボタン、App Clips、iMessage/CallKit、Spotlight、File Provider、AutoFill、デフォルトアプリ、ニッチ連携（FinanceKit/Journaling Suggestions/Sensitive Content Analysis） |
| 04 | システム統合・自動化 | App Intents全体像と年次強化、Shortcuts連携（LLMアクション）、Siriの実態（報道ベースの現状も）、通知/Focus/Screen Time/DeviceActivity、Live Translation/Translation API、バックグラウンド実行（BGタスク各種）、CloudKit/SwiftData、WidgetKit push、Wallet/PassKit、スパムフィルタ、新設フレームワーク（AlarmKit/RelevanceKit/EnergyKit級のもの） |
| 05 | メディア・カメラ・AR | AVFoundation新機能（Cinematic等）、物理ボタン/リモートシャッター、DockKit、空間写真/動画、Image I/O、オーディオ（入力選択・AirPods録音・ボイス分離・空間音声）、音声認識（SpeechAnalyzer系）、動画配信/PiP、Metal/MetalFX、ARKit/RealityKit/Object Capture/RoomPlan/Quick Look、ゲーム（Game Center）、PDFKit/VisionKit |
| 06 | オンデバイスML（FM以外） | Core ML新機能と量子化、実例（Whisper/SD/小型LLM）、Vision全検出機能の棚卸し、Natural Language/埋め込み、音声合成/Personal Voice、SoundAnalysis、Create ML（アプリ内学習）、Translation framework、MLX、BNNS/MPSGraph、llama.cpp系の実情とApp Store審査上の扱い |
| 07 | ハードウェア・周辺連携 | NFC（タグ読み書き/HCEの制度と個人開発可否/日本の状況）、UWB、iBeacon/CLMonitor、Bluetooth/AccessorySetupKit、Wi-Fi Aware/Multipeer/Network、Core Motion/気圧計/Core Location、HealthKit/WorkoutKit、Watch連携、AirPods連携、バッテリー/EnergyKit、HomeKit/Matter/CarPlay、外部アクセサリ、（簡潔に）デバイス管理系 |

### 3. 保存

各班の報告を `sections/0X_<領域名>.md` に上書き保存する（ファイル名は現行のまま）。
明らかな重複・矛盾は統合時に調整してよいが、**出典は削らない**。

### 4. スポットチェック（検証）

報告のうち企画判断に響く主張を2〜3個選び、Apple公式ドキュメント（developer.apple.com）で裏を取る。
特に「年式の誤伝播」（古いOSの変更が最新OSの新機能として語られるパターン）を疑う。
過去の実例: 「App ClipsのiOS 26上限緩和」→ 実際はiOS 17の変更だった。

### 5. SKILL.md の更新

- 調査日・対象バージョンを更新
- 「クイックリファレンス」「機会マップ」「罠」「組み合わせ」を新しい調査結果で書き直す
- 前回の「プレビュー」項目が正式リリースされていたら本文へ昇格させる
- 廃止されたAPI（例: ImageCreator）を機会マップ・組み合わせから外す

## 完了条件

- [ ] sections/01〜07 の全ファイルが新しい調査で上書きされ、各ファイルに調査基準日と出典がある
- [ ] スポットチェックで一次情報と矛盾する記述が残っていない
- [ ] SKILL.md の調査日・クイックリファレンス・機会マップ・罠が更新済み
- [ ] ベータ中の次期iOS情報が「プレビュー」として分離されている（確定情報と混ざっていない）
