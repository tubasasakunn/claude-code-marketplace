---
paths:
  - "**/*.swift"
---

# Swift コーディング規約

新しい Swift / SwiftUI アプリで一貫した品質を保つための骨子。
コードを書く・直すときはこの規約に揃える。新しいパターンを導入したくなったら、
まず既存コードに前例がないか探すこと。違反の全走査は `/swift-app:audit-conventions`。

関連規約（同ディレクトリ・Swift を触ると自動読み込み）：
命名と API 設計は `swift-api-design.md`、並行性は `swift-concurrency.md`、
SwiftUI は `swiftui-patterns.md`、構造と DI は `swift-architecture.md`、
テストは `swift-testing.md`、AI 保守前提のコメント運用は `ai-era-coding.md`。

> このテンプレートは「集約レイヤを必ず通す」設計を前提にしている。新規プロジェクトでは
> 早い段階で以下の集約ファイルを作っておく（無ければ作ってから使う）。

## 集約レイヤを必ず通す

| 何を書くとき | 通す場所（推奨ファイル） | 直書きの例（禁止） |
|---|---|---|
| 色・余白・角丸・サイズ・フォント | `Tokens.*`（`Design/DesignTokens.swift`） | `.padding(16)` / `.frame(width: 44)` / `Font.custom(...)` |
| ユーザー向け文字列 | `Strings.*`（`Resources/Strings.swift`） | `Text("完了")` |
| 日付の表示フォーマット | `DisplayDate.*`（`Resources/DateFormatters.swift`） | ビュー内で `DateFormatter()` を生成 |
| `@AppStorage` / UserDefaults キー | `AppStorageKeys.*` | `@AppStorage("someKey")` |
| ハプティクス | `Haptics.*`（`Design/Haptics.swift`） | `UIImpactFeedbackGenerator` 直叩き |
| ディープリンク構成要素 | `DeepLink`（`AppNavigator.swift`） | `url.scheme == "..."` の直比較 |
| 通知名・識別子類 | 定数化した namespace（`Notification.Name` extension 等） | 文字列リテラルの直書き |

- 集約先に欲しい定数が無ければ**先に定数を足してから**使う。意味の違う既存定数の
  流用（別画面用の文言を借りる等）はしない。
- 例外：別ターゲット（ウィジェット拡張等）からは本体の `Tokens` / `Strings` が
  見えないため、拡張内のリテラルは許容（コメントで対応元を示す）。

## 安全性

- **強制アンラップ `!` 禁止**。`guard let` / `if let` で逃がす。
  例外は `layerClass` オーバーライド済みビューの `layer as!`（型が構造的に保証される）等、
  構造で保証できる箇所のみ（理由コメント必須）。
- **`try!` / 根拠のない `as!` も同罪**。コンパイル時に成立が保証される箇所
  （バンドル内リソースのデコード等）だけ、理由コメント付きで許容。
- **`fatalError` は最後の砦**。永続化スタックの起動時フォールバック最終段のような
  「ここまで来たら継続不能」な箇所だけ。それ以外は `Logger` でログ + early return。
  到達不能分岐の明示は `fatalError("unreachable")` ではなく網羅 switch で型に語らせる。
- **エラーを握りつぶさない**。`try?` を使ってよいのは「失敗しても続行が正しい」と
  コメントで説明できる箇所だけ。保存・生成系の失敗は必ず `Logger` に残す
  （`privacy:` 指定を忘れない）。`print()` は使わない。
- SwiftData + CloudKit ミラーリングを使うなら：モデルに `@Attribute(.unique)` を
  使わない（CloudKit 非互換。一意性は upsert で担保）。新フィールドは optional か
  デフォルト値付き。長い `await` を跨いだモデル書き込みの前は主キーで refetch する
  （ゾンビ書き込みクラッシュ防止）。判断したら ADR に残す。

## エラー処理とログ

- エラーは**回復する場所で捕まえる**。途中の層で catch → ログ → 握りつぶしをしない
  （ログは出すなら rethrow とセット）。
- 自前エラーは機能単位の enum で定義。ユーザーに見せる文言は
  `LocalizedError.errorDescription` に置き、ビュー側で error の型 switch をしない。
- ログは `os.Logger` を型ごと・機能ごとの `static let logger = Logger(subsystem:category:)`
  で持つ。レベルを使い分ける：開発時の追跡は `.debug`、通常運転の節目は `.info`、
  回復した異常は `.error`、継続不能な障害は `.fault`。
- ユーザーデータ（タイトル・URL・位置情報等）を補間するときは既定の redact に任せるか
  `\(value, privacy: .private)` を明示。ID などデバッグに要る値だけ `.public`。

## 構造

- 新規の参照型は `@Observable`。`ObservableObject` / `@Published` / `@StateObject` は使わない。
  所有は `@State`、共有は `@Environment`、受け取りは素の `let`。
- **1 ファイル 1 主要型**。ファイル名は型名と一致させる。private なヘルパー型・
  extension は同居してよい。
- protocol 準拠は **`extension` で分けて実装**し、`// MARK: - <Protocol>` を付ける
  （型宣言の本体には stored property と designated init だけが残る形が理想）。
- ファイルは **500 行を超えたら分割を検討**。
- ビューの分割は「computed property で body を返す」より「サブビュー struct の抽出」を優先
  （Instruments の SwiftUI 計測で原因追跡できる単位になる）。
- 触ったファイルに `// MARK: -` 区分けが無ければ追加する。
- Xcode の `PBXFileSystemSynchronizedRootGroup` を採用しているプロジェクトでは
  `.swift` を増やすだけでターゲットに入る（`pbxproj` 編集不要・してはならない）。
  ファイルを**削除**したら `git status` の `deleted:` を必ず確認する
  （「ファイルだけ消えてビルドが直る」静かな事故が起きやすい）。

## スタイル

- **early return を基本形に**。ネストした `if` のピラミッドではなく `guard` で
  前提条件を先に片づける。`guard` の `else` に本処理を書かない。
- 単一の値を選ぶ分岐は **`if` / `switch` 式**で書く（三項演算子のネスト禁止）。
- `!(x?.isEmpty ?? true)` のような二重否定は `x?.isEmpty == false` と書く。
- optional の自己シャドーイングは短縮形で：`if let user`（`if let user = user` と書かない）。
- 空判定は `isEmpty`（`count == 0` と書かない。文字列では計算量も違う）。
- `.onChange(of:)` で新旧値を使わないときは引数なしクロージャ形式（iOS 17+）を使う。
- `DispatchQueue.main.async` を書かない。`@MainActor` 文脈の 1 ターン遅延は `Task { }` で足りる。
- 末尾クロージャは 1 個まで trailing closure。複数クロージャ引数はラベル付きで縦に並べる。
- `self.` は初期化・キャプチャで必要な場合のみ書く。
- 型推論に任せられる型注釈は書かない（公開 API の戻り値・空コレクション初期化を除く）。
- マジックナンバーを式に埋めない。意味があるなら `Tokens` / 定数へ、
  ロジック上の閾値なら名前付き `let` にして「なぜその値か」をコメント。

## コメント

- 「なぜそうなっているか」を書く。何をしているかは命名で表す。
- 仕様の根拠は仕様書のセクション番号、設計判断の経緯は `docs/adr/NNNN` を引用する。
- 一見「統一できそうで統一してはいけない」コードには、その旨のコメントを必ず残す。
- **バグ修正・直感に反するコードには現地コメント必須**（バグ台帳コメント・
  ガードコメント・`AIDEV-NOTE:` アンカーの運用は `ai-era-coding.md`）。
- 消したコードをコメントアウトで残さない（履歴は git にある）。TODO を書くなら
  `// TODO: <期限 or 条件> <内容>` の形で、放置される裸の TODO を作らない。

## 変更を確定する前に

1. macOS 環境なら `/swift-app:verify-build` でビルド検証（`.swift` 由来 warning/error = 0 を維持）。
   ビルドできない環境では diff 全体のコンパイル整合性レビューで代替し、その旨を明記する。
2. `/swift-app:bug-check` で diff を挙動バグ観点（並行性・状態管理・境界値・リソース）で精査する。
3. `/swift-app:audit-conventions` で規約違反の混入をチェック。
4. アーキテクチャ・データモデル・依存・並行性の判断をしたら `/swift-app:adr` で記録する。
