# iOS 拡張ポイント & 共有画面 網羅調査（iOS 26 時点）

調査基準日: 2026年7月。iOS 26（2025年9月リリース）を最新として扱い、WWDC26（2026年6月）で発表された iOS 27 情報は参考として区別して記載する。

---

## 1. Share Extension / Action Extension（共有画面）

### 何ができるか
- **Share Extension**: 他アプリの共有シート（`UIActivityViewController`）に自アプリのアイコンを表示し、渡されたコンテンツ（テキスト・URL・画像・ファイル等）を受け取って処理する。
  - **標準UI**: `SLComposeServiceViewController` を継承すると、Apple 標準の「投稿」型UI（本文入力＋プレビュー＋文字数カウンタ）がほぼコード無しで使える。`charactersRemaining`、プレースホルダー、下部への追加オプション項目（`configurationItems`）などをカスタマイズ可能。
  - **フルカスタムUI**: `SLComposeServiceViewController` を使わず `UIViewController`（`UINavigationController` 経由）を自作すれば、レイアウト・ボタン配置・遷移を完全に自由設計できる。SwiftUI で組むことも可能（`UIHostingController` 経由）。
  - **プレビュー編集**: `extensionContext` から受け取った `NSExtensionItem.attachments`（`NSItemProvider`）の中身を検査し、画像ならサムネイル、URLならOGP風プレビューなど独自プレビューを描画できる。テキストは編集可能なフィールドとして提示するのが一般的。
  - **ボタン**: 完了/キャンセルは `SLComposeServiceViewController` のナビゲーションバーが標準提供。フルカスタムUIなら任意のボタン（保存/共有/フォーマット切替等）を自由に追加できる。
  - **シートの高さ・スワイプ**: `UISheetPresentationController`（iOS 15+）で `detents`（`.medium()`/`.large()`/`.custom`）を指定し、下スワイプでの段階的縮小・ドラッグダウンでの閉じる挙動を自作extensionに実装可能。ただしOS標準の共有シート自体の挙動（下部お気に入りアプリの横スワイプ、"アクションを編集"での並べ替え）はユーザー側のカスタマイズ機能であり開発者側では制御不可。
- **Action Extension**: 共有シートの「アクション」領域（画像編集・翻訳・リーダー化など、コンテンツを変換して**呼び出し元に返す**タイプ）に表示される。`completeRequest(returningItems:)` で加工結果を戻せる。
- **どのコンテンツで表示されるか**: `Info.plist` の `NSExtensionActivationRule` で制御。定義済みキー（`NSExtensionActivationSupportsImageWithMaxCount` など）か、`NSPredicate` 文字列による複雑な条件式（例: 動画は不可・画像は20枚まで）を書ける。**述語の構文ミスはサイレントに失敗し拡張自体が一切表示されなくなる**ため要注意。
- **共有シートのお気に入り管理**: ユーザーは共有シート下部で「アクションを編集」からアプリ・アクションの並び替え・お気に入り登録ができるが、これは**アプリ側では制御できないユーザー操作**。開発者側は「魅力的なアイコン・名前・素早い処理」でお気に入り化を狙う程度。

### iOS 26 での変更点
- **Liquid Glass**: 共有シート自体が透過・光の屈折を伴う新マテリアルで再描画された。開発者が独自に作るExtension UIも、Liquid Glass API（`glassEffect` 系のSwiftUIモディファイア）に対応させることでシステムと統一感のある見た目にできる。UI自体の新規APIというより「見た目の刷新」が主。
- 機能面での大きなAPI追加（例: 新しい共有アクション種別）は今回の調査では確認できず、**マテリアル/ビジュアルの刷新が中心**という位置づけ。

### 制約
- Extensionプロセスはメモリ制限が本体アプリより厳しい（数十MB程度、明確な公称値はOS内部実装で非公開・機種依存）。重い画像処理は要注意。
- 拡張機能はサンドボックスが本体アプリと別。データ共有には App Groups が必須。
- 起動が遅い・落ちる場合、システムがサイレントに次回以降候補から除外することがある。

### 最低OSバージョン
iOS 8.0〜（App Extensions全般の初出）。`UISheetPresentationController` のカスタム検討は iOS 15+。

### アプリアイデア例
- 「あとで読む」的な保存アプリ（URL/画像を共有シートから1タップ保存、プレビューでタグ付け）
- 翻訳・要約アクション拡張（選択テキストをその場で変換して返す）
- 家計簿アプリへのレシート画像共有→OCR取り込み

---

## 2. カスタムキーボード（Keyboard Extension）

### 何ができるか
- `UIInputViewController` を継承したキーボード拡張により、システム全体（他アプリのテキストフィールド）で使える独自キーボードを提供できる。
- `UITextDocumentProxy` 経由で入力中テキストの前後文脈を読み書きでき、予測変換・自動補完・絵文字提案などを実装できる。
- **コンテナアプリ + キーボード拡張**の2ターゲット構成。設定はコンテナアプリ側、実際の入力はExtension側という役割分担。
- "フルアクセス"許可（`RequestsOpenAccess`）を得れば、ネットワーク通信やクリップボードへのアクセスも可能（AIアシスト変換などに必要）。ただしユーザーはプライバシー上フルアクセスを警戒しやすい。
- 2026年時点のトレンドとして、軽量なオンデバイスAIモデルを組み込んだ文脈予測（エッジAI）が実装例として挙げられている。

### 制約
- パスワード欄など `isSecureTextEntry` な入力欄では自動的にシステム標準キーボードにフォールバックし、カスタムキーボードは使えない。
- フルアクセス無効時はネットワーク通信不可。
- App Store 審査でプライバシー説明が厳しく見られる。

### 最低OSバージョン
iOS 8.0〜。

### アプリアイデア例
- 特定言語・方言・専門用語（医療略語、プログラミング用語）に特化したキーボード
- ステッカー/GIF/よく使う定型文を素早く挿入するキーボード
- 絵文字・顔文字生成AIキーボード

---

## 3. Safari Web Extension / Content Blocker

### 何ができるか
- **Content Blocker Extension**（iOS 9〜）: JSON形式のルール（トリガー/アクション）をSafariに渡し、広告・トラッカー・特定要素の非表示、リソースの読み込みブロック、Cookie除去などを宣言的に実行させる。実行はSafariプロセス内で行われ、ユーザーの閲覧データはアプリ側に渡らないプライバシー設計。
- **Safari Web Extension**（iOS/iPadOS 15〜）: HTML/CSS/JS のWeb Extension標準技術（Chrome拡張とほぼ共通のManifest形式）でSafariに機能追加できる。宣言的コンテンツブロッキングにも対応が進んでいる。
- 4種類のSafari拡張形態（Content Blocker／Share Extension／App Extension／Web Extension）が存在し、AppleはWeb Extensionへの投資を強めている（Safari 17以降）。
- App Store の「Extensions」カテゴリで単体配布・発見が可能。

### 制約
- Content BlockerはSafari内限定（アプリ内WebView等には効かない）。
- ルール数に上限がある（宣言的ルール方式のため、動的なJS判断による広範なブロックはできない）。
- Web Extensionは配布に変換ツール（`safari-web-extension-converter`）が必要な場合がある。

### 最低OSバージョン
Content Blocker: iOS 9.0〜。Safari Web Extension: iOS/iPadOS 15.0〜。

### アプリアイデア例
- 特定サイトの不要要素除去・読みやすさ改善（リーダー系）
- 広告/トラッキングブロッカー
- パスワードマネージャーのSafari連携（フォーム自動入力ボタンの注入）

---

## 4. 通知関連（Service/Content Extension、優先度通知）

### 何ができるか
- **Notification Service Extension**（`UNNotificationServiceExtension`、iOS 10〜）: リモート通知が表示される**前**に内容を書き換えられるバックグラウンド処理専用拡張。暗号化ペイロードの復号、画像/動画の事前ダウンロード添付、パーソナライズされた文言生成などに使う。UIは持たない。
- **Notification Content Extension**（`UNNotificationContentExtension`、iOS 10〜）: 通知をロングプレス/展開した際に表示するカスタムUIを提供する。`Info.plist` の重要キー:
  - `UNNotificationExtensionCategory`: 対象とする通知カテゴリ名（複数可）
  - `UNNotificationExtensionDefaultContentHidden`: 標準タイトル/サブタイトルを隠すか
  - `UNNotificationExtensionUserInteractionEnabled`: 独自ボタン等のインタラクションを有効化するか（無効なら通知タップで即アプリ起動）
- **優先度通知（Priority Notifications, Apple Intelligence）**: iOS 18.1のApple Mail向けセマンティック解析を土台に、iOS 18.4で全体展開。iOS 26では強化され、オンデバイスAIが通知内容の緊急性・関連性を分析し、通知センター上部の「優先」表示に浮上させる。開発者が直接呼び出すAPIというより、既存の `UNMutableNotificationContent.interruptionLevel`（`.active`/`.timeSensitive`/`.passive`/`.critical`）や `relevanceScore` を正しく設定することがシグナルとして働く。
- iOS 26では**Communication notification API**（会話スレッドとして優先表示される仕組み）が対象アプリカテゴリを拡大。コラボ/ソーシャル系アプリはこのentitlement採用の検討価値あり。

### 制約
- Service Extensionの処理時間は数十秒程度に制限（タイムアウトでシステムが強制的に元の通知を表示）。
- Content ExtensionのカスタムボタンはUIガイドラインの範囲内。
- Priority Notificationsはユーザー設定でオフにできるため、確実な優先表示は保証されない。

### 最低OSバージョン
Service/Content Extension: iOS 10.0〜。Priority Notifications: iOS 18.1〜（本格運用は18.4〜）、iOS 26で強化。

### アプリアイデア例
- チャットアプリで通知内に返信ボタン・スタンプボタンを直接埋め込む
- ニュースアプリで速報通知に画像・要約を添えて表示
- リマインダーアプリで通知内チェックボックスの即完了操作

---

## 5. Control Center / ロック画面ウィジェット / アクションボタン / カメラコントロール

### Control Centerへの独自コントロール（`ControlWidget`）
- iOS 18で新設。**ボタン型**（単発アクション、アプリ起動含む）と**トグル型**（真偽値state切り替え）の2種があり、いずれもApp Intentで動作する。
- `ControlWidget` に `kind`（一意識別子）と種別定義（`ControlWidgetButton`/`ControlWidgetToggle`）を実装。アイコンはSF Symbolsのみサポート（カスタム画像不可、カスタムSF Symbolテンプレートは使用可）。
- ユーザーがControl Centerに追加するかはユーザー自身の操作で、アプリ側は追加を強制できない。
- ロック画面下部にも同じControlを配置可能（カメラアイコンのように）。

### ロック画面ウィジェット（WidgetKit accessory families）
- iOS 16〜。`accessoryCircular`（円形）、`accessoryRectangular`（矩形、複数行/簡易グラフ）、`accessoryInline`（1行テキスト）の3ファミリー。
- `AccessoryWidgetBackground()` を背景に敷くことで、壁紙を問わず見やすい標準的な背景処理を自動適用できる（ただし `accessoryInline` では効果なし）。

### アクションボタン（Action Button）
- iPhone 15 Pro以降（iOS 17〜）で搭載。設定アプリからApp Intent（App Shortcuts）を割り当てられる。開発者は `AppShortcutsProvider` でApp Intentを公開すれば、ユーザーがアクションボタンにアサイン可能になる。

### カメラコントロールボタン
- iPhone 16シリーズ以降（iOS 18〜）の物理ボタン。`AVCaptureEventInteraction` APIでサードパーティのカメラアプリも同等のジェスチャーハンドリング（軽押しでフォーカス、深押しでシャッター等）を実装できる。設定アプリからサードパーティアプリへの割当も可能。
- **iOS 26の変更点**: `AVCaptureEventInteraction` がAirPods（H2チップ搭載モデル）のステム押下イベントにも対応。既存実装アプリは追加コードなしでこの恩恵を受けられる。

### 制約
- Control Center/ロック画面へのControl/Widget追加は最終的にユーザーの手動操作に依存。
- アクションボタン/カメラコントロールボタンは対応機種限定。

### 最低OSバージョン
ControlWidget: iOS 18.0〜。Lock Screen Widget: iOS 16.0〜。Action Button: iOS 17.0〜（対応機種限定）。Camera Control: iOS 18.0〜（iPhone 16シリーズ以降）。

### アプリアイデア例
- タイマー/瞑想アプリのControl Centerワンタップ開始トグル
- 記録系アプリのロック画面ウィジェットで直近値を常時表示
- カメラアプリでカメラコントロールボタンにフィルター切替を割当

---

## 6. App Clips

### 何ができるか
- QRコード/App Clip Code/NFCタグ/Safariバナー/メッセージ/Mapsピン/検索結果などから、フルアプリをインストールせず軽量な機能の一部だけを瞬時に起動できる。
- Apple Pay・Sign in with Apple など軽量な購入/認証フローに強い。

### サイズ上限（注意: 「iOS 26で緩和」は確認できず）
**App Clipサイズ上限の大幅緩和は iOS 17（2023年）時点で既に実施済み**であり、iOS 26時点での追加緩和は公式ドキュメント上確認できなかった。現行値:

| 起動経路 | 上限 |
|---|---|
| iOS 16以前 | 10 MB |
| **物理的起動**（App Clip Code / QRコード / NFCタグ、iOS 17〜） | 15 MB |
| **デジタル起動のみ**（Web・Spotlight・メッセージ・Safariバナー・通知等、iOS 17〜） | **100 MB** |

### 制約
- 起動後の体験は「特定の1タスク」に絞るのが前提。
- 8時間で自動的に破棄される一時的なコンテナ（再訪問時は再ダウンロードのケースあり）。

### 最低OSバージョン
iOS 14.0〜。

### アプリアイデア例
- 駐車場/自販機/レンタサイクルのQR起動決済
- レストランのテーブルQRからメニュー閲覧・注文だけを行うApp Clip

---

## 7. Message/Sticker Extension、CallKit・Call Directory、VoIP

### iMessage App / Sticker Extension
- `MSMessagesAppViewController` を起点に、メッセージアプリ内で完結するミニアプリを提供できる。
  - **スタンドアロンiMessageアプリ**: 単独配布、Apple Pay・課金対応も可能。
  - **既存アプリへの拡張として追加**: 同じApp Store掲載でデータ連携。
  - **ステッカーパック**: 画像をXcodeにドラッグするだけでコード不要、最も実装コストが低い。
- メッセージのカメラUI、FaceTimeのエフェクトにもステッカーパックを登録可能。
- 実装例: ゲーム・投票・共同編集ツール・Apple Pay決済・リッチなインタラクティブメッセージバブル。

### CallKit / Call Directory / VoIP
- **CallKit**（iOS 10〜）: サードパーティ通話アプリの着信/発信UIをシステム標準の電話UI（ロック画面着信画面含む）に統合。`CXProvider`、`CXCallController`/`CXTransaction` が中核。
- **Call Directory Extension**（iOS 10〜）: 発信者ID表示・迷惑電話ブロックリストをシステムに提供する拡張。
- **VoIP Push（PushKit）**: バックグラウンド/未起動状態でも着信を即時受信できる特別なプッシュ経路。**受信したら必ずCallKitに着信を報告する義務**（iOS 13以降、怠るとペナルティ）。

### 制約
- Call Directory Extensionは登録可能な電話番号エントリ数に上限があり、増分更新の仕組みも必要。
- VoIP Pushはユーザーの許可と即応答が必須。

### 最低OSバージョン
iMessage App / CallKit / Call Directory: iOS 10.0〜。

### アプリアイデア例
- 家族・友人限定の合言葉ゲームをiMessage内で遊べるミニアプリ
- ブランド独自スタンプパック
- 国際通話アプリでの発信者ID表示・詐欺電話ブロック

---

## 8. Spotlight / Core Spotlight / App Shortcuts / App Intents

### 何ができるか
- **Core Spotlight**（iOS 9〜）: `CSSearchableItem` をインデックスし、システム検索結果にアプリ内コンテンツを表示させる。
- **App Intents / App Shortcuts**（iOS 16〜、Swift専用）: アプリの主要機能を `AppIntent` として宣言すると、Siri・Spotlight・ショートカット・アクションボタン・ウィジェット・Control Center・Dynamic Islandなど**システム全体の「同じ導線」で横展開**される（1つのIntent定義を1回書けば多所に反映される設計思想）。
- **iOS 26 の拡張**:
  - Visual Intelligence（カメラ撮影/スクリーンショットからの画像検索）にサードパーティアプリの検索結果を統合可能に。
  - インタラクティブ・スニペット: システムUI内に小さなポップアップ操作UIを差し込める。
  - エンティティのビュー注釈（`IndexedEntity`＋`indexingKey`）でSpotlightの絞り込み検索をアプリのパラメータ選択に利用できる。
  - `@DeferredProperty` による非同期計算プロパティのサポート。

### 制約
- App Shortcutsのフレーズには自アプリ名を含める必要がある。
- インデックス更新はバックグラウンド処理のクォータ制約を受ける。

### 最低OSバージョン
Core Spotlight: iOS 9.0〜。App Intents/App Shortcuts: iOS 16.0〜（iOS 17/18/26で順次拡張）。

### アプリアイデア例
- レシピアプリでレシピをSpotlight検索対応・Siriで「〇〇のレシピを開いて」呼び出し
- タスク管理アプリでタスク作成をアクションボタン・ショートカット・Spotlightから起動できるように統一実装

---

## 9. File Provider、Document-based apps

### 何ができるか
- **File Provider Extension**（iOS 11〜）: 自社クラウドストレージ等のファイル/フォルダを、標準の「ファイル」アプリや他アプリから直接参照・編集できるようにする（"Open in Place"）。iCloud Driveと同格の存在としてシステムに統合される。
- **Document-based apps**（`DocumentGroup`, SwiftUI, iOS 14〜）: ファイルを主役に据えたアプリ構造。
- **WWDC26の変更点（参考）**: SwiftUIに新しい **`Document` プロトコル**が追加され、ディスクへの直接アクセスとスナップショットベースの差分検出により、高性能なドキュメントアプリを構築しやすくなった。`WritableDocument`/`ReadableDocument` の分離、非同期の `DocumentWriter`、`DocumentCreationSource` API など。

### 制約
- 旧来のUI版File Provider（Document Provider Extension）は非推奨方向。
- 大容量ファイルの同期・競合解決はアプリ側の責務。

### 最低OSバージョン
File Provider Extension: iOS 11.0〜。SwiftUI DocumentGroup: iOS 14.0〜。

### アプリアイデア例
- 独自クラウドメモアプリをFile Provider化し「ファイル」アプリから直接編集
- 大容量CADファイル/楽譜ファイルを扱う高性能ドキュメントアプリ

---

## 10. Audio Unit Extension、AutoFill Credential Provider、デフォルトアプリ設定

### Audio Unit Extension（AUv3）
- iOS 9〜。楽器音源・エフェクト・シーケンサーなどをプラグインとしてGarageBand/Logic等のホストアプリに提供できる。MIDIレコーディング対応。

### AutoFill Credential Provider Extension
- `ASCredentialProviderViewController` を継承し、パスワードマネージャーとしてシステムのオートフィルに候補を提供できる。
- **パスキー対応**（iOS 17〜）: `ASCredentialProviderExtensionCapabilities > ProvidesPasskeys` を `YES` にすると、パスキー生成時にも自社拡張が候補に出る。
- データ共有は App Groups / Shared Keychain 経由。

### デフォルトアプリ設定
- iOS 14で「デフォルトのブラウザ/メールアプリ」が初導入。以降段階的に拡大し、**iOS 26では「設定 > App > デフォルトのApp」に統合され、世界的に以下カテゴリが選択可能**（地域規制により変動）:
  - Eメール、メッセージ、通話、通話フィルタリング、ブラウザ、翻訳、パスワード＆コード（パスキー含む）、キーボード、コンタクトレス決済（NFC）
  - **EU/日本など特定地域では追加でナビゲーション（地図）、代替アプリマーケットプレイスなどが選択肢に加わる**
  - **EU限定**では、通話（Phoneアプリの完全置き換え）、メッセージング（SMS/RCSの完全移譲）まで踏み込んでいる。

### 制約
- Credential Provider Extensionは有償Apple Developer Programのentitlementが必要。
- デフォルトアプリ変更対応には、対象アプリが該当インテントに正しく適合している必要がある。

### 最低OSバージョン
AUv3: iOS 9.0〜。Credential Provider: iOS 12.0〜（パスキーはiOS 17.0〜）。デフォルトアプリ（ブラウザ/メール）: iOS 14.0〜、翻訳/ナビ: iOS 18.4〜、大幅拡張: iOS 26。

### アプリアイデア例
- シンセ/エフェクトのAUv3プラグイン単体販売＋GarageBand連携訴求
- パスキー対応の独自パスワードマネージャー
- 独自翻訳アプリをシステムのデフォルト翻訳先に設定してもらう導線設計

---

## 11. ニッチな連携: FinanceKit、Journaling Suggestions、Sensitive Content Analysis

### FinanceKit（iOS 17.4〜）
- Apple Card / Apple Cash / Apple Savings の残高・取引履歴に、ユーザーが許可した範囲でアクセスできるAPI。データはオンデバイスのWallet内リポジトリから取得され、**Appleサーバーを経由しない**。entitlementはbundle ID単位で個別申請が必要（審査制）。
- 家計簿/資産管理アプリ（YNAB, Monarch, Copilot が先行採用）に直結。

### Journaling Suggestions API（iOS 17.2〜）
- 位置情報・写真・ワークアウトなど複数カテゴリの「最近の個人的な出来事」を、**個別の権限プロンプト無しで**まとめてピッカーUIとして提示できるAPI。ピッカーは別プロセスでレンダリングされ、ユーザーが選択したものだけがアプリに渡る（プライバシー配慮設計）。
- iOS 18でピッカーが画面回転設定に追従するよう改善。

### Sensitive Content Analysis（iOS 17〜）
- オンデバイスでヌード等のセンシティブな画像/動画を検出し、表示前に警告・介入UIを挟めるフレームワーク（`SCSensitivityAnalyzer`）。解析結果はAppleに送信されない。
- 専用entitlement（`com.apple.developer.sensitivecontentanalysis.client`）が必要。

### アプリアイデア例
- 「今日の出来事」から自動で日記の下書きを作る内省アプリ（Journaling Suggestions活用）
- Apple Card連携の可視化・予算管理アプリ（FinanceKit）※日本ではApple Card未提供な点に注意
- マッチングアプリ/匿名チャットでの不適切画像自動警告（Sensitive Content Analysis）

---

## 12. 最低OSバージョン早見表

| 拡張ポイント | 最低iOS | 補足 |
|---|---|---|
| Share / Action Extension | 8.0 | Liquid Glass対応は26〜 |
| Custom Keyboard | 8.0 | |
| Content Blocker | 9.0 | |
| Safari Web Extension | 15.0 | |
| Notification Service/Content Extension | 10.0 | |
| Priority Notifications | 18.1（本格運用18.4） | 26で強化 |
| Core Spotlight | 9.0 | |
| App Intents / App Shortcuts | 16.0 | 26でVisual Intelligence等拡張 |
| Lock Screen Widget | 16.0 | |
| Control Center ControlWidget | 18.0 | |
| Action Button割当 | 17.0 | 対応機種限定 |
| Camera Control | 18.0 | iPhone 16以降、26でAirPods対応 |
| App Clips | 14.0 | サイズ上限緩和は17.0 |
| iMessage App / Sticker | 10.0 | |
| CallKit / Call Directory | 10.0 | |
| File Provider Extension | 11.0 | |
| Document-based apps（DocumentGroup） | 14.0 | |
| Audio Unit Extension (AUv3) | 9.0 | |
| Credential Provider Extension | 12.0 | パスキーは17.0 |
| デフォルトアプリ（ブラウザ/メール） | 14.0 | 大幅拡張は26 |
| FinanceKit | 17.4 | |
| Journaling Suggestions | 17.2 | |
| Sensitive Content Analysis | 17.0 | |

---

## 補足: 事実確認メモ

「**App ClipsのiOS 26での上限緩和**」については、公式ドキュメント・複数の技術記事を確認した限り、**サイズ上限拡大（100MBへの倍増）はiOS 17（2023年）時点の変更**であり、iOS 26固有の追加緩和は確認できなかった。

主要ソース:
- https://developer.apple.com/documentation/appintents
- https://developer.apple.com/videos/play/wwdc2025/260/ (App Intents for Shortcuts and Spotlight)
- https://developer.apple.com/videos/play/wwdc2025/253/ (Capture controls)
- https://developer.apple.com/videos/play/wwdc2024/10157/ (Controls across the system)
- https://developer.apple.com/help/app-store-connect/reference/app-uploads/maximum-build-file-sizes/
- https://developer.apple.com/documentation/financekit
- https://developer.apple.com/documentation/journalingsuggestions
- https://developer.apple.com/documentation/sensitivecontentanalysis
- https://www.courier.com/blog/developer-guide-to-ios-26-priority-notifications
- https://9to5mac.com/2026/01/09/ios-26-lets-you-change-your-default-iphone-apps-heres-how/
