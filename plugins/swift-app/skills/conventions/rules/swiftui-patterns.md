---
paths:
  - "**/*.swift"
---

# SwiftUI パターン規約

状態管理・ビュー構成・ナビゲーション・性能の定石。観測まわりの土台は
`@Observable`（`.claude/rules/swift-conventions.md` 参照）、隔離は MainActor デフォルト
（`.claude/rules/swift-concurrency.md` 参照）が前提。

## 状態の置き場所（迷ったらこの表）

| 状況 | 使うもの |
|---|---|
| ビューが所有する値型の状態 | `@State`（`private` 必須） |
| ビューが所有する `@Observable` モデル | `@State`（`@StateObject` は使わない） |
| 親から渡される読み取り参照 | 素の `let` |
| 親から渡され、書き込みも必要 | `@Bindable` / `Binding` |
| 画面ツリー全体で共有 | `@Environment`（カスタムは `@Entry` で定義） |
| 軽い設定値の永続化 | `@AppStorage`（キーは `AppStorageKeys` 経由） |

- **状態は使う場所の直近に置く**（state を不必要に持ち上げない）。逆に、複数ビューが
  同じ真実を必要とするなら親へ持ち上げて単一の source of truth にする。
- `@State` を初期値注入に使うときの再生成問題（親の再描画で `init(initialValue:)` が
  効かない）に注意。外から更新したい値は `Binding` か `task(id:)` で同期する。

## body は安く保つ

- **body 内で計算・生成をしない**。フォーマッタ生成・ソート・フィルタは
  モデル側の stored/computed へ。`body` は「今ある値を並べるだけ」にする。
- 非同期処理の起動は **`.task { }` / `.task(id:)`**。`onAppear` + `Task { }` は書かない
  （task はビュー消滅時に自動キャンセルされる）。
- `ForEach` の要素は **安定した identity**（`Identifiable` の `id` は保存された一意値）。
  `id: \.self` を可変コレクションに使わない。配列 index を id にしない。
- 大きいリストは `LazyVStack` / `List`。`ScrollView + VStack` で全展開しない。
- `AnyView` で型を消さない（分岐は `@ViewBuilder` で表現できる。AnyView は
  構造的 identity を壊し、差分計算とアニメーションを退化させる）。
- **表示/非表示で view の型を切り替えない**。identity を保ちたい show/hide は
  `if` 分岐より `.opacity(0)` 等の不活性 modifier（状態・アニメーションが生き残る）。
- リスト内の `.shadow` / `.blur` / `.mask` は GPU コストが高い。行数が多い画面では
  合成を減らすか `.drawingGroup()` を検討（ただし計測してから）。
- アニメーション起点は値変更に紐づける：`withAnimation` かビュー側 `.animation(_:value:)`。
  値引数なしの `.animation(_:)`（deprecated 系）は使わない。

## ビューの分割

- 分割は **サブビュー struct の抽出**を優先（computed property による分割は
  Instruments の SwiftUI 計測で原因単位にならない）。
- 「イベント → 状態変更 → 描画」の一方向を守る。ビューから直接別ビューの状態を
  いじらない。ビジネスロジックはモデル（`@Observable`）へ、ビューには置かない。
- ビュー struct に stored なサービス参照を増やさない。依存は `@Environment` で受ける
  （`.claude/rules/swift-architecture.md`）。

## ナビゲーション

- **`NavigationStack(path:)` + 値ベース遷移**（`navigationDestination(for:)`）を標準とする。
  `NavigationView` は使わない。
- 遷移先を表す値は `Hashable` な enum（ルート型）に集約し、パスをモデルで保持すると
  ディープリンク（`DeepLink`）とプログラム遷移が同じ入口になる。
  パスの型は同種ルートなら `[Route]`（中身を検査・保存できる）、
  異種混在が本当に必要なときだけ `NavigationPath`。
- モーダルは `sheet(item:)` を優先（`sheet(isPresented:)` + optional 状態の二重管理を避ける）。
- 画面（遷移先ビュー）はスタックの存在を知らない形に保つ。push/pop の操作は
  ルーターに寄せ、画面からは「イベントを投げる」だけにする。

## プレビューと確認

- 新しいビューには `#Preview` を付ける（旧 `PreviewProvider` は使わない）。
  状態が要るプレビューは `@Previewable @State` を使う。
- プレビューが用意できない依存（カメラ等）はモック注入できる形（`@Environment` 経由）に
  しておく。「プレビューできないビュー」は設計の警報として扱う。

## 性能でハマったら

- 推測で直さない。Instruments の **SwiftUI テンプレート**で「どのビューの body が
  何回呼ばれたか」を見てから手を入れる。開発中の即席調査は body 先頭に
  `let _ = Self._printChanges()`（コミットには残さない）。
- 頻繁に再評価される重いサブツリーは、依存する値だけを受け取る小さな struct に切り出す
  （`@Observable` の観測はプロパティ単位なので、渡す粒度を細かくするだけで再描画が減る）。

## iOS 26（Liquid Glass）を意識するとき

- 標準コンポーネントを使っていれば Xcode 26 SDK で再ビルドするだけで新デザインに乗る。
  **クロームを自作しない**ことが最大の適応戦略。
- 独自のガラス表現は `.glassEffect()` + `GlassEffectContainer` に限定し、
  コンテンツ領域には使わない（ガラスの重ね合わせは高コスト・視認性低下）。
  「透明度を下げる」設定と実機で必ず確認する。
