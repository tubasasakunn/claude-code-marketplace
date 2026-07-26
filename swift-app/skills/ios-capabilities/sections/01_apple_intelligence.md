# Apple Intelligence / オンデバイスAI 技術調査レポート（2026年7月時点）

**前提の整理**: 2026年7月現在の最新出荷版は **iOS 26.6系目前（26.5系が最新安定）**。2026年6月のWWDC26で **iOS 27**（2026年秋出荷）がプレビューされ、Foundation Modelsフレームワークに大型刷新（マルチモーダル画像入力、他社LLM接続、第3世代モデル等）が予告されているが、**これらはまだ審査提出アプリには使えない**。本稿では「今すぐ使えるiOS 26.x」と「まだ使えないiOS 27プレビュー」を明確に分けて記載する。

---

## 1. Foundation Models framework（オンデバイスLLM）★最重要

### 概要
- `import FoundationModels`。Apple Intelligenceを支える**約30億パラメータのオンデバイスLLM**にSwiftから直接アクセスできる。iOS 26で正式リリース。
- 得意タスク: 要約、エンティティ抽出、分類、テキスト理解・言い換え、短い対話、創作文生成。
- **完全無料・オフライン動作・APIキー不要・従量課金なし**。推論はデバイス上で完結し、ネットワークに一切データが出ない。

### 基本形（コード例）
```swift
// 1. 素朴な呼び出し
let session = LanguageModelSession()
let result = try await session.respond(to: "この文章を3行で要約して: ...")

// 2. Guided Generation（構造化出力）
@Generable
struct Movie {
    let title: String
    @Guide(description: "アクション映画のジャンル")
    let genre: String
    @Guide(.anyOf(["PG-13", "R", "PG", "G"]))
    let rating: String
}
let movie = try await session.respond(to: "...", generating: Movie.self)

// 3. Tool calling（モデルが自アプリのコードを呼び出す）
final class FindRestaurantsTool: Tool {
    let name = "findRestaurants"
    let description = "近くのレストランを検索する"
    @Generable
    struct Arguments {
        @Guide(description: "検索したい料理名・店名")
        let query: String
    }
    func call(arguments: Arguments) async throws -> ToolOutput {
        ToolOutput("Pasta Place, Sushi Spot, Burger Barn")
    }
}

// 4. 可用性チェック
switch SystemLanguageModel.default.availability {
case .available: /* 使える */
case .unavailable(let reason): /* デバイス非対応 / Apple Intelligence未ON など */
}

// 5. ストリーミング
let stream = try await session.streamResponse(to: "レポートを書いて")
for try await partial in stream { updateUI(with: partial) }
```

### できること
- **Guided Generation**（`@Generable`/`@Guide`マクロ）: 制約付きデコーディングにより、出力が必ず指定したSwift構造体/enumの形式に収まることを構造的に保証。
- **Tool calling**: `Tool`プロトコルを実装するだけで、モデルが自律的に並列・直列にツールを呼び出す。ツール名・引数のハルシネーションも構造的に防止。
- **ストリーミング**: `streamResponse(to:)`で部分出力を逐次受け取れる。

### できないこと・制約
| 項目 | 内容 |
|---|---|
| コンテキスト長 | **4,096トークン固定**（instructions＋prompt＋tool出力＋会話履歴を含む入出力共有バジェット）。iOS 26.4で`contextSize`と`tokenCount(for:)`が追加され動的に消費量を把握可能に |
| マルチモーダル（画像入力） | **iOS 26.xでは未対応**。iOS 27で初実装予定 |
| 対応デバイス | iPhone 15 Pro以降（A17 Pro以上）、Apple Silicon Mac、M系iPad。設定でApple IntelligenceをONにする必要あり |
| 対応言語 | iOS 26.1時点で16言語（日本語含む）。**英語が最も精度が高く、他言語は品質にばらつき** |
| レート制限 | 公式な数値はないが、短時間連続リクエストでガードレール起因のエラーが出る開発者報告あり。リトライ・エラーハンドリング前提で設計する |
| ガードレール | コンテンツ安全フィルタが常時強制適用、無効化不可。iOS 26.4で誤検知が削減 |
| Acceptable Use | 医療・法律・金融・雇用など人による監督なしの高リスク判断への利用等を明示的に禁止 |
| シミュレータ | **Xcode Simulatorでは実推論不可**。実機またはApple Intelligence有効なMac上での確認が必要 |

### アプリのアイデアへの応用例
- レシートOCR結果をGuided Generationで「品目・金額・カテゴリ」に構造化 → 家計簿アプリ
- 長文の日記メモを要約して一言タイトルを自動生成
- 感想文からジャンル/評価/キーワードを抽出してタグ付けする読書メモアプリ
- 「牛乳と卵と洗剤も」のような自然文をToolで構造化リストに変換する買い物リストアプリ

---

## 2. Writing Tools のアプリ内統合

- iOS 18.1から提供。校正・言い換え・要約・箇条書き/表への変換をシステムレベルでテキスト入力欄に提供。
- **標準UI採用の場合はコード不要**: `UITextView`/`NSTextView`が**TextKit 2**を使っていれば自動対応。`WKWebView`も対応。
- カスタムテキストビュー: `UITextInteraction`採用でコンテキストメニューにWriting Toolsが出る。独自テキストエンジンは`UIWritingToolsCoordinator`で統合。
- カスタマイズ: `writingToolsBehavior`で挙動制御、`UIWritingToolsResultOptions`で「校正のみ許可」等のフィルタ可能。

**応用例**: 日記/メモアプリの入力欄をTextKit 2ベースにするだけで「もっと丁寧に」「短く要約」等が使える。

---

## 3. Image Playground / ImageCreator API、Genmoji

### Image Playground
| API | 内容 | 最低OS |
|---|---|---|
| `ImageCreator`（コードから直接生成、非UI） | `images(for:style:limit:)`で画像生成 | iOS 18.4〜。**iOS 27で非推奨・動作停止予定**（要注意） |
| `ImagePlaygroundViewController` / `imagePlaygroundSheet` | ユーザーがスタイル選択・生成をアプリ内シートで完結 | iOS 18.2〜 |

- **いずれも実機必須、Simulatorでは`notSupported`エラー**。
- コンテンツポリシーに準拠（著名キャラクター等は生成拒否される場合あり）。

### Genmoji
- `NSAdaptiveImageGlyph`型でリッチテキストに絵文字的画像を埋め込む。
- `UITextView.supportsAdaptiveImageGlyph = true`でキーボードにGenmoji生成ボタンが出る。
- iOS 18.2で導入。**iOS 26で強化**（複数絵文字の合成、既存絵文字+テキスト説明の組み合わせ生成）。

**応用例**: 日記アプリで気分をGenmojiスタンプとして残す機能。プロフィール/アバター作成にImage Playgroundシートを組み込む。

---

## 4. Visual Intelligence とアプリ連携

- **サードパーティアプリがVisual Intelligenceの検索結果に自アプリのコンテンツを出せるようになったのはiOS 26から**（App Intents経由）。
- 実装: `IntentValueQuery`に準拠したクエリを実装し、`SemanticContentDescriptor`を受け取り`AppEntity`の配列を返す。カメラ/スクショで撮った対象にマッチすれば検索結果に表示され、タップで自アプリに遷移。
- 対応デバイス: iPhone 15 Pro以降＋iOS 26.0＋Apple Intelligence有効。**Simulator非対応**。

**応用例**: 蔵書管理アプリで本の表紙をかざすと自アプリ内の該当ページにジャンプ。レシピアプリで食材/料理写真から類似レシピを検索結果として提示。

---

## 5. Siri / App Intents との統合（iOS 26 = App Intents 2.0）

| 新機能 | 内容 |
|---|---|
| **Assistant Schemas** | `AssistantIntent(schema:)` 等のマクロで、Siriが理解する定型スキーマに自アプリのIntent/Entityを適合。フレーズ定義なしで自然言語対応 |
| **エンティティへの直接アクセス＋画面理解** | Siriが「今画面に表示されている内容」を会話的に参照できる |
| **Interactive Snippets** | `SnippetIntent`で、Siri/Shortcuts/Spotlight上に自アプリのミニUI（ボタン付き）をその場表示 |
| **Visual Intelligence統合** | 上記4章参照 |
| **App Intents Testing framework** | UI自動化なしでSiri/Shortcuts/Spotlightの実経路をテスト可能 |

（参考・未出荷）iOS 27では汎用「App Schemas」へ置き換え・拡張、`View Annotations API`で画面上のSwiftUI Viewとentityを直接紐付け予定。

---

## 6. Smart Reply、要約API

### Smart Reply（正式なUIKit API）
- **iOS 18.4から利用可能**。`UITextField`/`UITextView`の`conversationContext`に`UIMailConversationContext`をセットすると、キーボード候補バーにシステムが返信案を自動生成。
- **UIKit専用でSwiftUI単体では非対応**。実機必須。

### 要約API
- 独立フレームワークは存在しない。**Foundation Modelsフレームワーク自体が要約・抽出・分類に最適化**されているため、自前プロンプト＋Guided Generationが標準パターン。

---

## 7. iOS 26.1以降のアップデートまとめ

| バージョン | Apple Intelligence関連の変更 |
|---|---|
| **iOS 26.1**（2025年11月） | 対応言語に8言語追加、**合計16言語**に。AirPods Live Translation拡張 |
| **iOS 26.4**（2026年3月頃） | `SystemLanguageModel.contextSize`と`tokenCount(for:)`追加。ガードレールの誤検知削減 |
| **iOS 26.5**（2026年6月） | 主にセキュリティ修正 |

---

## 参考: iOS 27（WWDC26プレビュー、未出荷）

- **第3世代Apple Foundation Models**: オンデバイス2種＋PCC上3種の計5モデル構成。`AFM 3 Core Advanced`は200億パラメータのスパースアーキテクチャ
- **マルチモーダル画像入力の正式対応**: `UIImage`等を渡して画像について質問できる。PCC経由なら32Kコンテキスト
- **「Bring your own LLM provider」API**: Claude・Gemini等を`LanguageModelSession`に差し替え可能に
- **App Store Small Business Program向け特典**: PCC上の次世代モデルをクラウドAPI費用ゼロで利用可能
- **Image Playground刷新**: `ImageCreator`は非推奨化・動作停止
- **Smart Reply**: `UISmartReplySuggestion`による精度向上

---

## 主要参考リンク

- https://developer.apple.com/documentation/FoundationModels
- https://developer.apple.com/videos/play/wwdc2025/286/ (Meet the Foundation Models framework)
- https://developer.apple.com/videos/play/wwdc2025/301/ (Deep dive)
- https://developer.apple.com/documentation/technotes/tn3193-managing-the-on-device-foundation-model-s-context-window
- https://developer.apple.com/apple-intelligence/acceptable-use-requirements-for-the-foundation-models-framework/
- https://developer.apple.com/documentation/uikit/writing-tools
- https://developer.apple.com/documentation/ImagePlayground/ImageCreator
- https://developer.apple.com/documentation/VisualIntelligence/
- https://developer.apple.com/videos/play/wwdc2025/275/ (App Intents advances)
- https://developer.apple.com/documentation/UIKit/adopting-smart-reply-in-your-messaging-or-email-app
