---
paths:
  - "**/*.swift"
---

# Swift API 設計・命名規約

Swift API Design Guidelines（swift.org）の蒸留 + モダン言語機能の使い分け。
「使う側のコードが自然な英語として読める」ことを最優先にする。

## 命名の原則

- **使用時の明瞭さ > 簡潔さ**。宣言側が短くても、呼び出し側が読めなければ失格。
  `x.insert(y, at: z)` → 「insert y at z」と読める形にする。
- **不要な語を削る**。型情報の重複は書かない：
  `removeElement(_ member: Element)` ❌ → `remove(_ member: Element)` ✅
- **役割で命名し、型で命名しない**。`var string = "..."` ❌ → `var greeting = "..."` ✅
- 弱い型（`Any` / `Int` / `String`）のパラメータには**役割を示す名詞を補う**：
  `func add(_ observer: NSObject, for keyPath: String)` →
  呼び出しが曖昧なら `addObserver(_:forKeyPath:)` のように英文として補強。
- **頭字語は大小どちらかに揃える**：`userID`, `utf8Bytes`, `htmlBody`（`userId` 混在禁止）。
- ファクトリメソッドは `make` で始める：`makeIterator()`。
- public / 型の境界になる宣言には `///` の一文サマリを付ける（何を返すか・何を作るか）。

## 品詞の使い分け

| 対象 | 規則 | 例 |
|---|---|---|
| 副作用のないメソッド・プロパティ | 名詞句 | `distance(to:)`, `successor` |
| 副作用のあるメソッド | 動詞句（命令形） | `sort()`, `append(_:)` |
| mutating / non-mutating ペア（動詞ベース） | 命令形 / `-ed`・`-ing` | `sort()` / `sorted()` |
| mutating / non-mutating ペア（名詞ベース） | `form` 前置 / 名詞 | `formUnion(_:)` / `union(_:)` |
| Bool プロパティ・メソッド | 主語に対する**断定文**として読める形 | `isEmpty`, `line.intersects(rect)`, `canUndo` |
| 能力を表す protocol | `-able` / `-ible` | `Equatable`, `ProgressReporting` |
| 「何であるか」を表す protocol | 名詞 | `Collection`, `Sequence` |

## 引数ラベル

- 第一引数が前置詞句の一部なら**ラベルに前置詞を出す**：`move(to:)`, `remove(at:)`。
- 引数が対等で区別不要ならラベル省略：`min(a, b)`, `zip(xs, ys)`。
- 値を保存するだけの型変換イニシャライザはラベル省略：`Int64(someUInt32)`。
  情報が落ちる変換はラベルで明示：`Int32(truncating: someInt64)`。
- クロージャ引数にも意味のあるラベル：`replaceSubrange(_:with:)`。
- デフォルト引数を積極的に使い、**メソッドファミリー（オーバーロード群）より 1 本にまとめる**。

## モダン言語機能の使い分け（Swift 6.x 時点）

- **`if` / `switch` 式**（SE-0380）：単一の値を選ぶ分岐は式で書き、`let` の初期化に使う。
  三項演算子のネストは禁止（式分岐へ書き換える）。
- **typed throws**（SE-0413, Swift 6）：使うのは「エラー型が閉じていて呼び出し側が
  網羅 switch したい」内部 API のみ。公開境界・進化しうる API は素の `throws`（`any Error`）
  のままにする（型を固定すると後からの追加が破壊的変更になる）。
- **マクロ由来の糖衣**（`@Observable` / `#Preview` / `#expect`）を旧 API より優先。
- **定数の名前空間は case 無し enum**（インスタンス化不能）。struct やグローバル定数の
  羅列にしない。
- **`some` を第一候補**に。`any` は「異なる具象型を同じ変数・コレクションに入れる」
  必要があるときだけ（存在型は動的ディスパッチ＋ボックス化のコストがある）。
- **`@retroactive`**（SE-0364）：他モジュールの型 × 他モジュールの protocol の準拠追加は
  原則しない。やむを得ない場合のみ `@retroactive` を明示し、理由コメントを書く。
- 生ポインタ・`Unmanaged`・`unsafe` 系 API は、対応する安全 API（`withUnsafe...` の
  スコープ関数、`Span` 系）で置き換えられないか先に検討する。

## アクセス制御と型設計

- **デフォルトは最小可視性**。まず `private` / `fileprivate`、必要になったら広げる。
  アプリターゲット内で `public` は書かない（モジュール分割していない限り無意味）。
- **まず値型（struct / enum）**。参照の同一性・ライフサイクル・共有可変状態が
  本質的に必要なときだけ class（その場合 `final` を付ける。継承を設計していない
  class の非 final は禁止）。
- **状態の網羅は enum で型に語らせる**。「`isLoading` と `error` が両方 non-nil」の
  ような不正状態が表現できるフラグ群は enum（associated value 付き）に畳む。
- ジェネリック型パラメータは意味があるなら名詞（`Element`, `Key`）、無ければ `T`。
