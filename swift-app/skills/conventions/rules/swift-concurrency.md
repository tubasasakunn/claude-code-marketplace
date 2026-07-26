---
paths:
  - "**/*.swift"
---

# Swift Concurrency 規約

推奨する前提：**Swift 5 言語モード + `SWIFT_APPROACHABLE_CONCURRENCY = YES` +
`SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor`。** UI 中心のアプリでは Swift 6 の
完全データ分離より、この構成のほうが移行コストと安全性のバランスが良い
（採用したらその経緯を ADR に残す。切り替え判断は実機検証体制と相談）。

## この構成で前提になる挙動

- 注釈の無い型・関数は **MainActor 隔離がデフォルト**。UI コードに `@MainActor` を
  書く必要はほぼ無い。逆に、MainActor から外したいものだけ `nonisolated` を明示する。
- `nonisolated` な **async 関数は呼び出し側の actor で走る**（SE-0461 が既定）。
  「async にすれば勝手にバックグラウンドへ行く」は誤り。重い CPU 処理を off-main に
  したいなら actor に置くか `@concurrent` を明示する（`@concurrent` は引数・戻り値に
  Sendable を要求。採用時は計測してから）。

## off-main に逃がすときの優先順位

1. **そもそも逃がすべきか計測する**。「なんとなく重そう」で並行化しない。
2. 状態を持つ処理 → **専用 actor**（例：`actor ThumbnailStore`）。
3. 状態を持たない純関数的な重い処理 → `nonisolated` + **`@concurrent`**。
4. どちらでも書けないレガシー API → 素の `Task { }` + `@preconcurrency`。
   `Task.detached` はこの目的に使わない（下記）。

## 構造化並行性

- **並行の基本形は `async let` と `withTaskGroup`**。独立した 2〜3 個の await は
  `async let`、可変個は TaskGroup。順に await するだけの直列コードに Task を挟まない。
- **`Task { }` は「イベントから非同期世界への入口」専用**（ボタンアクション・
  通知ハンドラ等）。async 関数の中から `Task { }` で枝分かれさせるのは
  構造化の破壊（キャンセルが伝播しなくなる）。並行にしたいなら TaskGroup。
- ビューに紐づく非同期処理は `.task { }` / `.task(id:)` に置く（消滅時に自動キャンセル）。
  自前で `Task` を stored property に持つのは、ビューの寿命と切り離したい場合のみ。
  持ったら **deinit/onDisappear で `cancel()` する所有者を明確に**。

## キャンセル対応

- 長時間ループ・多段パイプラインには **`Task.checkCancellation()` か
  `Task.isCancelled` の確認点**を入れる（await が無い CPU ループは特に）。
- キャンセルは「例外的失敗」ではなく正常系。`CancellationError` を握って
  エラー UI を出さない（catch で `is CancellationError` を先に分岐）。
- 「新しい入力が来たら前の処理を破棄」は自前フラグではなく `.task(id:)` か
  Task の付け替え（`task?.cancel(); task = Task { ... }`）で表現する。
- キャンセルで即座に止めたい非 async リソース（ネットワークハンドル・continuation）は
  `withTaskCancellationHandler(operation:onCancel:)` で結びつける。
- 長寿命の Task には名前を付ける：`Task(name: "thumbnail-prefetch")`（SE-0469）。
  Instruments・クラッシュログでの追跡が段違いになる。

## actor 設計

- actor は **リエントラント**：`await` を跨ぐと他の呼び出しが割り込める。
  「チェックしてから使う」の間に await を挟まない。跨ぐ必要があるなら
  in-flight 管理（進行中 Task を dictionary に持って合流させる等）で守る。
- actor メソッド内の await 前後で **stored property の再読込**を徹底する
  （await 前に読んだ値は await 後には古い可能性がある）。
- 1 つの actor に何でも載せない。保護したい状態の単位で小さく切る
  （巨大 actor は直列化ボトルネックになる）。

## AsyncStream / AsyncSequence

- コールバック・delegate の連続イベントを async の世界へ渡すときは
  **`AsyncStream`**（エラーあり系は `AsyncThrowingStream`）で橋渡しする。
- **AsyncStream は単一消費者**。同じ stream を複数の `for await` で読まない
  （2 本目には値が来ない）。複数購読が要るなら消費側で分配する。
- `continuation.onTermination` で**購読解除・リソース解放を必ず書く**
  （書かないと消費側キャンセル時にリークする）。
- バッファリング方針を明示する：UI 状態の最新値だけ要るなら
  `bufferingPolicy: .bufferingNewest(1)`。既定の unbounded を高頻度イベントに
  使わない。
- 単発の値 1 個の橋渡しに Stream を使わない → `withCheckedContinuation`。
- `@Observable` モデルの変化を SwiftUI の外（サービス層等）で監視するときは、
  自前 Stream より **`Observations`**（SE-0475）を第一候補にする（OS 要件を確認）。

## よく出る対処パターン

| 状況 | 対処 |
|---|---|
| Sendable 注釈待ちの SDK 型を main actor から await したい | `@preconcurrency import <Module>` |
| 非 Sendable な型（`AVAssetExportSession` 等）を Task に渡す | `Task.detached` は使わず、actor 隔離を継承する素の `Task { }` |
| `@MainActor` クラスの mutable stored property を隔離から外したい | `@ObservationIgnored` + `nonisolated(unsafe)` ＋ **直列化の根拠コメント必須** |
| `@Observable` クラスの deinit から MainActor プロパティに触りたい | 触らない。明示的に `onDisappear` で後始末を呼ぶ規約にする |
| `[weak self]` クロージャの中から Task を起こす | Task 側にも `[weak self]` を明示（self 再キャプチャが Swift 6 で error になる） |
| 同期コールバックが main 到着保証ありの場合 | `MainActor.assumeIsolated`（KVO / time observer 等） |
| 完了ハンドラ API を async にしたい | `withCheckedContinuation`（resume は必ず**ちょうど 1 回**） |

## 禁止・要注意

- **`Task.detached` を使わない**。例外はブロッキング I/O を utility 優先度で逃がす等の
  限定ケースのみ（必ずコメントで理由を説明する）。
- **新規の `nonisolated(unsafe)` / `@unchecked Sendable` は理由コメント必須**。
  「直列キューで保護」「生成後イミュータブル」など安全性の根拠を書く。
  既存の意図的な使用箇所を一覧化しておき、`/swift-app:audit-conventions` で増分を検知する。
- **セマフォで async を待たない**。橋渡しは `withCheckedContinuation`
  （continuation は必ず一度だけ resume。タイムアウトを付けるなら id 方式）。
- Sendable にできない型を「とりあえず `@unchecked Sendable`」で通さない。
  まず値型に直せないか・actor に置けないか・境界を跨ぐのをやめられないかを検討する。
- AVFoundation 等のプロパティは **async ロード**（`load(.duration)` 等）。同期アクセサは
  deprecated。
- 50ms 級の高頻度ループ（録画 ticker・カスタム compositor 等）は Timer /
  DispatchQueue のままで良い。構造化並行性への置換はリズム保証が無いので慎重に。
- 優先度は既定のまま（`Task(priority:)` を根拠なく撒かない）。UI 応答に効く場面だけ
  `.userInitiated`、明確なバックグラウンド作業だけ `.utility` を検討する。
