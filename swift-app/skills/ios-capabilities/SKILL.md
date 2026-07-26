---
name: ios-capabilities
description: 最新iOS（現在はiOS 26世代）でサードパーティアプリができること（新API・制約・最低OSバージョン・エンタイトルメント要否・審査上の注意）の調査知識を提供します。新規アプリのアイデア出し・コンセプト作成・機能設計で「iOSでできるか」「新機能で差別化できないか」を検討する場合、実装中のAPI選定・実現可能性判断、および「iOS調査を更新して」と頼まれた場合に使用してください。
---

# iOS でできること — 能力カタログ (ios-capabilities)

## 概要

最新iOSでアプリが「できること」の網羅調査。アイデアを新APIで差別化し、実現不可能な企画を早期に弾くための知識ベース。
7領域の詳細レポートが `sections/` にあり、このSKILL.mdは索引とクイックリファレンス。

- **調査日: 2026-07-11**（Sonnet 5 サブエージェント7班による並列Web調査）
- **対象: iOS 26系**（現行安定版）+ iOS 18世代の積み残し。iOS 27（ベータ中）は各レポート内で「プレビュー」として分離
- **鮮度ルール**: 新しいiOSメジャーの正式リリース後、またはWWDC直後、または調査日から6ヶ月経過したら [UPDATE.md](UPDATE.md) の手順で更新する。古い調査を根拠に断定しない

## 逆引き索引 — どのレポートを読むか

| 知りたいこと | 読むファイル |
|---|---|
| オンデバイスLLM・生成AI・Writing Tools・Genmoji・Visual Intelligence | [sections/01_apple_intelligence.md](sections/01_apple_intelligence.md) |
| Liquid Glass・SwiftUI/UIKit新API・ウィジェット・Live Activities・アイコン仕様 | [sections/02_ui_design.md](sections/02_ui_design.md) |
| 共有画面・キーボード・通知UI・Control Center・App Clips・デフォルトアプリ | [sections/03_extension_points.md](sections/03_extension_points.md) |
| App Intents・Shortcuts・Siriの実態・翻訳・バックグラウンド・AlarmKit・Wallet | [sections/04_system_integration.md](sections/04_system_integration.md) |
| カメラ・録音・文字起こし・空間写真・Metal・AR/3D・ゲーム | [sections/05_media_camera_ar.md](sections/05_media_camera_ar.md) |
| Core ML・Vision・埋め込み・音声合成・オフライン翻訳・llama.cpp/MLX | [sections/06_ondevice_ml.md](sections/06_ondevice_ml.md) |
| NFC/Suica・UWB・Wi-Fi Aware・BLE・HealthKit・Watch/AirPods・CarPlay | [sections/07_hardware_connectivity.md](sections/07_hardware_connectivity.md) |

各レポートは「できること／制約／最低OS／アプリアイデア例」の形式で書かれ、末尾に出典がある。

## クイックリファレンス — iOS 26 の大きな解禁

| 解禁 | API | 一言 | 主な制約 |
|---|---|---|---|
| オンデバイスLLM | `FoundationModels` | 3B級LLMが無料・オフライン・APIキー不要。`@Generable`で構造化出力保証、Tool calling可 | 4,096トークン固定、画像不可、**A17 Pro+限定**、シミュレータ不可 |
| デザイン全面刷新 | Liquid Glass / Icon Composer | 再ビルドで標準UI自動追従。`.icon`バンドル6モード（icon-craftingスキル対応済み） | 独自ビューへの`.glassEffect()`乱用はHIG非推奨 |
| 貫通アラーム | `AlarmKit` | サイレント/Focus貫通の本物のアラームが初開放。ポモドーロ・習慣化に | iOS 26+ |
| 長時間文字起こし | `SpeechAnalyzer` | 完全オンデバイスで数時間規模。Whisper比約2倍速の計測報告 | iOS 26+、言語モデルは都度DL |
| 全入口の統一窓口 | App Intents 2.0 | 1つのIntentがSiri/Spotlight/ショートカット/物理ボタンに横展開。Interactive Snippets、Visual Intelligence統合 | SiriKitは非推奨宣告済み。**App Intentsの作り込みが最も投資対効果が高い** |
| Live Activities強化 | `ActivityKit` | 事前スケジュール開放（未来時刻に自動開始）、CarPlayウィジェット解禁 | iOS 26+ |
| オフラインP2P | Wi-Fi Aware | ルーター不要のデバイス間高速直接通信（AirDrop相当技術の開放） | iOS 26+、エンタイトルメント自己付与可 |
| リッチテキスト | `TextEditor`+AttributedString | メモ・日記系のリッチテキスト編集がSwiftUI純正で低コスト化 | iOS 26+ |
| Watch不要ワークアウト | `HKWorkoutSession` iPhone対応 | Watch非所持ユーザー向けワークアウトアプリが作れる | iOS 26+ |
| 撮影後フォーカス編集 | Cinematic Video API | 自動追従フォーカス撮影+非破壊編集がサードパーティに開放 | iOS 26+、ファイル大 |
| 文書構造OCR | `RecognizeDocumentsRequest` | 表・リスト・データ検出込みの文書解析。レシート家計簿の土台 | iOS 26+ |
| 無料オフライン翻訳 | Translation framework | 自前API課金なしでアプリ内翻訳 | SwiftUI専用、シミュレータ不可 |

## 個人開発の機会マップ

- **狙い目（新しい×参入可）**: Foundation Models、AlarmKit、SpeechAnalyzer、Wi-Fi Aware、HealthKitワークアウトiPhone単体、AirPods Pro 3心拍（HealthKit経由・追加API不要）、Live Activityスケジューリング、AccessorySetupKit（MFi不要BLE連携）、CLMonitor（場所トリガー）
- **堅実（枯れているが有効）**: Share Extension、Core NFCタグ/Suica残高読み取り、Core Motion/気圧計/頭部モーション、VisionKitスキャン、SoundAnalysis、HomeKit連携
- **条件付き**: State of Mind（効能を謳わない設計必須）、UWBアクセサリ（個別承認）、Location Push（要申請）、CarPlay（カテゴリ別申請・待ち期間）
- **手を出せない**: HCE決済/NFC&SE（法人契約前提）、EnergyKit（OEM限定・米国のみ）、External Accessory/MFi、環境光センサー（API非公開）、Verify with Wallet（日本の身分証非対応）

## 罠 — 企画判断に直結する7点

1. **Apple Intelligence系はすべて iPhone 15 Pro 以降限定**。非対応機のフォールバック体験を最初から設計する
2. **SwiftDataは複数ユーザー共有（家族・友達と共同編集）が未サポート**。共有が中核ならCore Data + CloudKit Sharing
3. **Screen Time / DeviceActivityはiOS 26で閾値不発火の不具合報告多数**。「使いすぎに反応する」系は実機検証必須
4. **`ImageCreator` はiOS 27で廃止予定**。画像生成は `imagePlaygroundSheet` 側を使う
5. **Foundation Models・Translation・Visual Intelligence等はシミュレータで動かない**。`03_implement_app` のシミュレータ検証では確認できないことを認識し、可用性チェック（`SystemLanguageModel.default.availability`等）とフォールバックを必ず実装する
6. **医療・メンタルヘルス系は効能を謳うと審査厳格化**（State of Mind等）。「自己観察・記録」の枠で設計する（CLAUDE.mdの作法と同じ）
7. **「App ClipsのiOS 26上限緩和」のような誤伝播に注意**（実際はiOS 17の変更）。年式が曖昧な言説は sections/ の出典か一次情報で裏を取る

## 差別化しやすい組み合わせ（コンセプト出しの種）

- 記録系 × Foundation Models — 自然文入力→構造化データ、要約タイトル自動生成。オフライン・無料が訴求点
- 習慣化 × AlarmKit × Live Activity — 貫通アラームで確実に起動し、進行中はロック画面に常駐
- 音声メモ × SpeechAnalyzer × NLContextualEmbedding — オフライン文字起こし+意味検索。プライバシー完結型
- スキャン系 × RecognizeDocumentsRequest × DetectLensSmudgeRequest — 表構造ごと取り込み+撮影品質ゲート
- P0の底上げ — リッチテキストTextEditor、`tabViewBottomAccessory` は低コストで今っぽさが出る

**注意**: Widget / Extension / watchOSターゲットをP0に含める場合、Xcodeプロジェクト構成とXcode Cloud CI（スキル `01_create_xcode_cicd`）への影響を先に確認する。

## パイプラインでの使いどころ

- `concept-crafting` の前後 — アイデアの差別化要素として新APIを当てる。実現不可能な前提（機会マップの「手を出せない」欄）を早期に弾く
- `design-crafting` — Liquid Glass・アイコン6モード等のデザイン前提は sections/02 を参照
- `03_implement_app` — API選定時に最低OSバージョンと制約（実機必須・エンタイトルメント）を確認

## 調査の更新

[UPDATE.md](UPDATE.md) に、7領域並列サブエージェント調査の再実行手順がある。更新したらこのSKILL.mdの調査日とクイックリファレンスも直す。
