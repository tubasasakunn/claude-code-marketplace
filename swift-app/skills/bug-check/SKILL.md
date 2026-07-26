---
name: bug-check
description: コミット直前に diff をバグ観点で精査する。強制アンラップ等の規約違反ではなく「動かすと壊れる」挙動バグ（並行性・状態管理・境界値・リソース管理・日付/文字列処理）を、変更点の周辺コードまで読んで検証つきで報告する。/swift-app:verify-build /swift-app:audit-conventions と併用。
argument-hint: "[--staged | --range <base>..<head>]"
allowed-tools: Grep, Glob, Read, Bash
---

# バグ精査（コミット直前）

対象 diff を「コンパイルは通るが挙動が壊れる」バグの観点で精査する。
スタイル・規約違反は扱わない（それは `/swift-app:audit-conventions`）。ビルド可否も扱わない
（それは `/swift-app:verify-build`）。ここで探すのは**実行時に牙をむくもの**だけ。

引数: $ARGUMENTS
- 無指定: `git diff HEAD`（未コミットの全変更）+ untracked の `.swift`
- `--staged`: `git diff --cached`
- `--range <base>..<head>`: 指定範囲のコミット済み変更

## 手順

1. **diff の全量を読む**（`git diff` を Bash で取得）。変更ファイル一覧と hunk を把握する。
2. **変更ファイルは hunk の前後だけでなく関数全体・型全体を Read する**。
   バグの大半は「変更行そのもの」ではなく「変更が既存の前提を壊した境目」にいる。
   特に：変更した関数の呼び出し元（Grep で全列挙）、変更したプロパティの全読み書き箇所。
3. 下のチェックリストを**カテゴリごとに** diff へ適用する。機械的に grep で済むものは
   grep、データフローを追う必要があるものは Read で追う。
4. 疑わしい箇所ごとに**発火条件を特定する**：「どの入力・状態・タイミングで壊れるか」を
   具体的に言えるまで周辺コードを読む。言えないものは「要検証」として区別する。
5. 報告する（形式は末尾）。**確認して潔白だったものは報告しない**（ノイズ制御）。

## チェックリスト

### 1. 並行性（最優先。クラッシュ・データ破壊の温床）

- [ ] **actor リエントランシー**：`await` を跨ぐ check-then-act。
      「`if !items.contains(x)` → await → `items.append(x)`」は await 中に他の呼び出しが
      割り込んで重複する。await の前後で stored property の値が同じと仮定している箇所を探す。
- [ ] **continuation の resume 回数**：`withCheckedContinuation` 内のコールバックが
      「複数回呼ばれる」「エラーパスで呼ばれない」経路がないか。delegate 系 API は特に
      成功・失敗・キャンセルの 3 経路全部で resume されるか追う。
- [ ] **Task の self 捕捉**：stored property に持つ長寿命 `Task` が `self` を強参照して
      いないか（`[weak self]` 無しの `Task` を `@Observable` クラスが保持 → 循環）。
      逆に、単発の `.task {}` / ボタンアクションの weak 化は不要（過剰 weak も報告対象外）。
- [ ] **キャンセルの握りつぶし**：`catch { showError() }` が `CancellationError` まで
      エラー表示していないか。`.task(id:)` は id 変化のたびに前の Task を cancel する ——
      その catch で UI をエラー状態にすると画面遷移のたびに誤発火する。
- [ ] **隔離の穴**：`nonisolated(unsafe)` / `@unchecked Sendable` が付いた型・プロパティに
      **今回の変更で新しいアクセス経路が増えていないか**（根拠コメントの前提が今も成立するか）。
- [ ] **UI 更新のスレッド**：delegate / コールバック（URLSession, AVFoundation, CoreLocation,
      KVO）から `@MainActor` の状態を直接触っていないか。`assumeIsolated` の根拠は有効か。

### 2. SwiftUI 状態管理

- [ ] **`@State` の初期値注入**：`init` で親から受けた値を `@State` に入れていないか。
      親が再描画しても `@State` は初期化されない —— 値が古いまま固定されるバグの定番。
      渡すなら `Binding`、同期するなら `.task(id:)` / `.onChange`。
- [ ] **ForEach の identity**：id が可変（index、`\.self` の可変配列）だと、削除・並べ替えで
      行の状態（`@State`・アニメーション）が別の要素に化ける。
- [ ] **onChange の連鎖・自己ループ**：`onChange(of: x) { x = ... }` 系の自己代入、
      A→B→A と伝播するペア。無限ループか「1 フレーム遅れの値」になる。
- [ ] **sheet/alert の状態残留**：`sheet(isPresented:)` + 別 optional の二重管理で、
      dismiss 時に optional を nil に戻し忘れて次回表示が古い内容になる経路。
- [ ] **body の副作用**：body 評価中に状態を変えるコード（ログ以外）。
      「Modifying state during view update」の実行時警告コース。

### 3. 境界値・コレクション

- [ ] **空・1 要素・最大**：変更したロジックに空配列・空文字列を通すとどうなるか机上実行する。
      `first!` / `last!` / `[0]` / `randomElement()!`、`count - 1`、`reduce` の初期値。
- [ ] **除算・剰余**：分母が 0 になる入力は本当に来ないか（`count` で割る・進捗率の計算）。
- [ ] **Range 境界**：`..<` と `...` の取り違え、`index(after:)` の終端、
      `prefix`/`suffix`/`dropFirst` に負数や過大値が渡る経路（これらは安全だが結果が空になり
      「静かに何も起きない」バグになる）。
- [ ] **Int 変換**：`Int(someDouble)` の切り捨て方向（負数で床関数と違う）、
      `UInt` への変換で負値クラッシュ、`Int32` 圧縮（動画フレーム数・タイムスタンプ）。

### 4. メモリ・リソース

- [ ] **クロージャの循環参照**：stored property に保持されるクロージャ
      （completion handler・observer・`sink` 相当）が self を強参照していないか。
      判定基準：「クロージャの寿命 ≧ self の寿命」なら weak が要る。
- [ ] **観測の解除漏れ**：`NotificationCenter.addObserver`（クロージャ版は token 保持必須）、
      KVO、`Timer`（`invalidate` しないと RunLoop が強参照）、
      AVPlayer の time observer（`removeTimeObserver` 必須）。追加した観測に対応する解除が
      同じ diff にあるか確認する。
- [ ] **AsyncStream の終端処理**：`onTermination` でリソース解放しているか。
      消費側が消えても producer が回り続ける構造は Instruments でしか気づけない。
- [ ] **一時ファイル・セッション**：書き出した一時ファイルの削除、
      `AVAudioSession` の activate/deactivate の対応、カメラセッションの start/stop 対応。

### 5. 日付・数値・文字列

- [ ] **DateFormatter のロケール**：サーバー通信など**固定フォーマットのパース**に
      `locale = Locale(identifier: "en_US_POSIX")` が無いと、和暦設定・12/24時間設定の
      端末で壊れる。表示用は逆に固定してはいけない。
- [ ] **「その日」の境界**：`Calendar.current` の日付比較（`isDate(_:inSameDayAs:)` を使わず
      86400 秒加算していないか）。DST がある地域で 1 日 ≠ 86400 秒。
- [ ] **浮動小数の等値比較**：`Double == Double`、特に「進捗が 1.0 になったら」系。
      閾値比較（`>= 1.0 - .ulpOfOne` 等）か整数カウントに直す。
- [ ] **String の長さと NSRange**：UITextField 系 API・正規表現の `NSRange` は UTF-16 基準。
      `count` と混ぜると絵文字入力で範囲がずれてクラッシュしうる。

### 6. 永続化・シリアライズ

- [ ] **Codable の欠損キー**：サーバー/旧バージョンのデータに新フィールドが無いケース。
      non-optional で decode すると既存ユーザーのデータが**全件読めなくなる**。
      新フィールドは optional か `decodeIfPresent` + デフォルト。
- [ ] **SwiftData/CoreData のコンテキスト越境**：モデルオブジェクトを別 actor / 別 Task に
      持ち出していないか（ID を渡して向こうで fetch が正しい）。
      長い await 後の書き込み前 refetch（`.claude/rules/swift-conventions.md` 参照）。
- [ ] **マイグレーション相当の互換性**：`@AppStorage` の型変更・キー再利用、
      enum の rawValue 変更（保存済み値が decode 不能になる）。

### 7. 状態機械・エラーパス

- [ ] **エラー時の状態復帰**：`isLoading = true` → throw → `isLoading` が戻らない経路。
      `defer { isLoading = false }` になっているか、全 throw 経路を追う。
- [ ] **二重実行ガード**：ボタン連打・通知の重複到達で同じ処理が並走したらどうなるか。
      「実行中フラグ」を立てるなら await を跨いだ再入（上記 1）とセットで確認。
- [ ] **到達しない分岐**：変更で条件が常に true/false になっていないか
      （`if x != nil` の直後に `guard let` 済み、リファクタで死んだ else）。

### 8. API 契約・プラットフォーム

- [ ] **権限拒否パス**：カメラ・通知・位置情報で「拒否された後」の UI 遷移が存在するか
      （無反応ボタンは審査リジェクト事由）。
- [ ] **バックグラウンド遷移**：録画・再生・タイマー処理は `scenePhase` 変化で何が起きるか。
- [ ] **availability**：新 API 使用箇所が deployment target で守られているか
      （`if #available` の分岐漏れはビルドで捕まるが、**挙動差**は捕まらない）。

## 報告形式

発見ごとに：

```
[重大度] ファイル:行 ── 一言サマリ
  発火条件: どの入力・状態・操作で壊れるか（具体的に）
  根拠: 読んで確認したコードパス
  修正案: 最小の直し方（1〜3 行で）
```

- 重大度: **crash**（落ちる）/ **data-loss**（ユーザーデータ破壊・不整合）/
  **wrong**（挙動が仕様と違う）/ **edge**（特定条件でのみ発生）
- 確度: **確実**（発火条件まで特定済み）/ **要検証**（怪しいが実機・実データが要る）。
  要検証のまま数を稼がない —— 読めば白黒つくものは読んで潰してから報告する。
- 最後にサマリ：精査した変更ファイル数・確認して問題なしだったカテゴリ・発見件数。
  **発見 0 なら「diff のどこを疑ってなぜ潔白と判断したか」を 3 行で書く**
  （0 件報告の信頼性はここで決まる）。

## 心得

- 変更行だけ見て指摘しない。**呼び出し元と既存の前提を読んでから**言う。
  偽陽性の指摘はレビュー全体の信頼を毀損する。
- 「規約違反だが挙動は正しい」は報告しない（`/swift-app:audit-conventions` の領分）。
- 修正まで頼まれていない限り、報告で止める（判断は人間に返す）。
- 修正まで行った場合は、修正箇所に**バグ台帳コメント**（症状・発火条件・理由）を
  残し、可能なら回帰テストを足す（`.claude/rules/ai-era-coding.md`）。
- diff 内の `AIDEV-NOTE:` が指す前提を壊していないかも確認対象にする。
- ここで見つかった**新種のバグパターン**は、このチェックリストに追記して蓄積する。
