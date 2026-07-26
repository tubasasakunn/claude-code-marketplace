---
paths:
  - "**/*Tests/**/*.swift"
  - "**/*Tests.swift"
  - "**/*UITests/**/*.swift"
---

# テスト規約（Swift Testing）

新規テストは **Swift Testing**（`import Testing`）で書く。XCTest は UI テスト
（`XCUIApplication`）と性能計測（`measure`）だけに使う。既存 XCTest の書き換えは
触るついでに行い、専用の書き換え作業はしない。

## 基本形

```swift
import Testing
@testable import <AppTarget>

@Suite struct LibraryTests {
    @Test func 追加した項目が先頭に来る() throws {
        var library = Library()
        library.add(.fixture(title: "A"))
        #expect(library.items.first?.title == "A")
    }
}
```

- 検証は `#expect`。**継続不能な前提**（nil なら以降が無意味）だけ `#require` で早期脱出。
  `XCTAssert*` 系の直訳（全部 `#require`）はしない。
- エラーパスは `#expect(throws: MyError.self) { ... }` で検証する
  （typed throws なら具体の case まで比較できる）。
- suite は **struct** を基本にする（テストごとに新インスタンス＝状態が漏れない）。
  teardown が要るときだけ final class + `deinit`。
- テスト名は日本語で「何がどうなるべきか」を書いてよい（関数名がそのままレポートに出る）。
- 1 テスト 1 関心。Arrange / Act / Assert を空行で区切る。

## パラメータ化と整理

- 同型の入力違いは for ループやコピペではなく **`@Test(arguments:)`** で書く
  （ケースごとに独立実行・独立レポートになる）。
- 期待失敗が既知のバグなら `withKnownIssue { }` か `.bug("issue URL")` trait、
  環境依存スキップは `.enabled(if:)` / `.disabled("理由")` を使う。
  コメントアウトでテストを殺さない。ハングしうる統合テストは `.timeLimit(.minutes(1))`。
- 共有状態に触るテスト（UserDefaults・ファイル・シングルトン SDK）は
  suite に **`.serialized`** を付ける。付けない限り並列実行が前提
  （テスト間の実行順依存を書かない）。

## 何をテストするか

- 優先順位：**ドメインロジック（モデル・変換・状態機械）> サービスの境界 > View**。
  SwiftUI View の描画テストは書かない（プレビューと実機確認で担保）。
- 依存はテスト用実装を **`@Environment` / init 注入**で差し替える
  （`.claude/rules/swift-architecture.md` の DI 規約が効いていればモックは素直に書ける）。
- 時刻は `Date()` 直呼びではなく注入（`now: () -> Date` かクロック）にしておく。
  乱数はシード注入。「たまに落ちるテスト」を最初から作らない。
- フィクスチャは `.fixture(...)` 静的ファクトリをテストターゲット側の extension に置く。
  プロダクションコードにテスト専用コードを混ぜない。

## 非同期・並行

- async 関数はそのまま `@Test func ... async throws` で await する。
  セマフォ・`XCTestExpectation` の移植はしない（完了ハンドラ API は
  `withCheckedContinuation` でラップしてから await）。
- 「コールバックが N 回呼ばれる」の検証は `confirmation(expectedCount:)` を使う。
- MainActor 隔離が要るテストは suite ごと `@MainActor` を付ける。
- 「時間が経つのを待つ」テストを書かない（`Task.sleep` でのタイミング合わせ禁止）。
  待つ対象を値の変化（AsyncSequence・コールバック）として公開させる。
