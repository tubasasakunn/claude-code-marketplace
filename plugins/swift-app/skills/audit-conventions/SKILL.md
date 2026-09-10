---
name: audit-conventions
description: コーディング規約（Tokens / Strings / DisplayDate / 強制アンラップ禁止など）への違反をリポジトリ全体から走査して報告する。引数に --fix を付けると自明な違反を修正までやる。リファクタ後・コミット前・定期点検に使う。
argument-hint: "[--fix]"
allowed-tools: Grep, Glob, Read, Bash
---

# 規約監査

`.claude/rules/` の各規約（swift-conventions / swift-api-design / swift-concurrency /
swiftui-patterns / swift-architecture / swift-testing）に対する違反を
Swift ファイルから洗い出す。

引数: $ARGUMENTS（`--fix` が含まれていたら、自明な違反は規約どおりに修正し、
判断が要るものは報告に留める）

## 走査パターン（Grep ツールで順に実行）

それぞれ `glob: "**/*.swift"` で検索し、**意図的な使用（理由コメントあり）を除いて**報告する。
プロジェクト固有の正当な例外は、見つけたらこの表に追記して監査可能に保つ。

| # | パターン | 検出する違反 |
|---|---|---|
| 1 | `DateFormatter\(\)` | 表示用フォーマッタの都度生成（DisplayDate を通す） |
| 2 | `\.frame\(width: \d|\.frame\(height: \d` | サイズの数値直書き（Tokens を通す） |
| 3 | `as! \|[a-zA-Z)\]]! ` | 強制キャスト・強制アンラップ |
| 4 | `fatalError` | 最後の砦以外での使用 |
| 5 | `ObservableObject\|@Published\|@StateObject` | レガシー観測パターン（@Observable へ） |
| 6 | `@AppStorage\("` | キー文字列の直書き（AppStorageKeys を通す） |
| 7 | `DispatchQueue.main` | @MainActor 文脈での GCD（`Task { }` へ） |
| 8 | `Task.detached` | 非構造化 detach（理由コメントの無いもの） |
| 9 | `print\(` | unified logging 未使用（os.Logger へ） |
| 10 | `onChange\(of:.*\) \{ _, _ in` | 旧形式 onChange（引数なし形式へ） |
| 11 | `"[ぁ-んァ-ヶ一-龠]`（`Strings.swift` 以外） | 日本語文字列の直書き（コメント行は除外。Strings へ） |
| 12 | `nonisolated\(unsafe\)\|@unchecked Sendable` | 新規追加の検出（理由コメントの有無を確認・前回からの増分を見る） |
| 13 | `try! ` | 強制 try（理由コメントの無いもの） |
| 14 | `static let shared` | 新設シングルトン（@Environment 注入へ。SDK ラッパは除く） |
| 15 | `NavigationView` | 廃止 API（NavigationStack へ） |
| 16 | `PreviewProvider` | 旧プレビュー（#Preview へ） |
| 17 | `id: \\.self` | 不安定な ForEach identity（Identifiable へ。定数コレクションは可） |
| 18 | `onAppear \{[^}]*Task \{` | onAppear + Task（`.task { }` へ） |
| 19 | `AnyView\(` | 型消去の乱用（@ViewBuilder 分岐へ） |
| 20 | `DispatchSemaphore` | async の同期待ち（continuation / await へ） |
| 21 | `import XCTest` | 新規テストの XCTest 使用（UI テスト・性能計測以外は Swift Testing へ） |
| 22 | `Task.sleep`（テストコード内） | タイミング合わせテスト（値の変化を await する形へ） |

## 報告形式

カテゴリごとに `ファイル:行` と違反内容を列挙し、最後に

- 違反件数のサマリ（カテゴリ別）
- 前回監査からの増減（分かる場合）
- `--fix` 時：修正したもの / 判断が要るため残したもの

を出す。違反 0 ならその旨を明言する。

## 注意

- 機械パターンなので偽陽性はありうる。報告前に該当行を Read して文脈を確認する。
- 新しい違反パターンを規約に足したら、この表にも追記して監査可能に保つ。
