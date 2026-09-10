---
name: conventions
description: Swift / SwiftUI のコーディング規約の正本（7領域・628行）。Swift ファイルを書く前・直す前に該当領域を読む。集約レイヤ・命名・並行性・SwiftUI の状態管理・アーキテクチャ・テスト・AI時代のコメント運用。違反の全走査は /swift-app:audit-conventions、コミット前のバグ精査は /swift-app:bug-check。
---

# Swift コーディング規約 — 正本

swift-base 由来の iOS アプリ全体で守る規約。**ここが正本**で、各アプリの `.claude/rules/` は
`/swift-app:sync-base` が配ったコピーにすぎない。**規約を変えるときはこのスキルを直す**
（marketplace リポジトリで編集して push する。アプリ側のコピーを直しても次の同期で消える）。

## 逆引き索引 — どれを読むか

| 何を書く・直すとき | 読むファイル |
|---|---|
| 色・文字列・日付・UserDefaults を触る／強制アンラップ／エラー処理／ファイル分割 | [rules/swift-conventions.md](rules/swift-conventions.md) |
| 型・関数・引数ラベルの命名／アクセス制御／モダン言語機能の選択 | [rules/swift-api-design.md](rules/swift-api-design.md) |
| 画面構成・状態の置き場所・ビュー分割・ナビゲーション・Liquid Glass | [rules/swiftui-patterns.md](rules/swiftui-patterns.md) |
| `async`/`await`・actor・`Task`・off-main・キャンセル・AsyncStream | [rules/swift-concurrency.md](rules/swift-concurrency.md) |
| 依存注入・protocol 境界・ディレクトリ設計・SPM 追加の判断 | [rules/swift-architecture.md](rules/swift-architecture.md) |
| テストを書く（Swift Testing） | [rules/swift-testing.md](rules/swift-testing.md) |
| バグ修正のコメント・アンカーコメント・次セッションへの引き継ぎ | [rules/ai-era-coding.md](rules/ai-era-coding.md) |

## 骨子（詳細は各ファイル）

- **集約レイヤを必ず通す** — 色は `Tokens`、表示文字列は `Strings`、表示用日付は `DisplayDate`、
  `@AppStorage` のキーは `AppStorageKeys`、触覚は `Haptics`。直書きの数値・文字列を作らない
- **強制アンラップ禁止**。`fatalError` は ModelContainer のフォールバック経路だけ
- **`@Observable` を使う**（`ObservableObject` は新規で使わない）
- **500 行で分割を検討する**。`// MARK:` で区分けする
- **コメントは「なぜ」だけ**。「何を」はコードが語る
- **Swift 5 言語モード + approachable concurrency + MainActor デフォルト隔離**が前提
  （Swift 6 言語モードには切り替えない。経緯は各アプリの ADR 0001）
- **バグを直したら「バグ台帳コメント」を残す** — 同じ穴に落ちないための唯一の仕組み

## 使い方

1. **Swift を触る前に、上の索引から該当ファイルを読む。** 全部読む必要はない
2. 書き終わったら `/swift-app:verify-build`（warning / error のベースライン 0 を維持）
3. リファクタ後・コミット前は `/swift-app:audit-conventions`（違反の全走査、`--fix` で修正まで）
4. 挙動バグの精査は `/swift-app:bug-check`（規約違反ではなく「動かすと壊れる」方）

> 各アプリの `.claude/rules/` は Swift ファイルを触ると自動読み込みされる。**この規約は
> それと同じ内容**で、アプリ側にコピーが無い／古い場合の正本として機能する。
> コピーの世代ズレは `/swift-app:sync-base` で検出・解消する。
