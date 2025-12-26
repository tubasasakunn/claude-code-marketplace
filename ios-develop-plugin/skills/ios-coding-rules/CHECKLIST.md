# iOS Coding Rules - チェックリスト

各シーンで使用するチェックリストです。

---

## 新規ファイル作成時

### 配置チェック
- [ ] 正しいディレクトリに配置したか
  - SwiftData Model → `Core/Models/`
  - API関連 → `Core/Network/`
  - Repository → `Core/Repositories/`
  - 機能View/ViewModel → `Features/{機能名}/`
  - 共通UI → `DesignSystem/Components/`
  - 拡張 → `DesignSystem/Extensions/`
- [ ] ファイル名は命名規則に従っているか
  - View: `{機能名}View.swift`
  - ViewModel: `{機能名}ViewModel.swift`
  - Extension: `{型名}+{機能}.swift`

### コード品質チェック
- [ ] ファイルヘッダーを記述したか（責務・依存・使用場所）
- [ ] `// MARK:` でセクションを分けたか
- [ ] インポート順序は正しいか（Foundation → Apple → サードパーティ）
- [ ] 型名・変数名は意図を明確に表しているか

---

## View実装時

### 構造チェック
- [ ] プロパティ順序は正しいか
  1. `@Bindable` ViewModel
  2. `@Binding`
  3. `let/var` 外部プロパティ
  4. `@State`
  5. `@Environment`
  6. `@Query`

### スタイルチェック
- [ ] ハードコード値を使用していないか
  - spacing → `DesignTokens.Spacing.*`
  - padding → `DesignTokens.Spacing.*`
  - cornerRadius → `DesignTokens.CornerRadius.*`
- [ ] 直接色指定を使用していないか
  - `Color.white/black` → セマンティックカラー
- [ ] モディファイアは1行に1つか
- [ ] モディファイア順序は正しいか（テキスト属性→余白→サイズ→背景→透明度→アニメーション→インタラクション）

### ナビゲーションチェック
- [ ] ツールバーは`.toolbar`モディファイアを使用しているか（ZStackオーバーレイ禁止）
- [ ] `.toolbarBackground`を設定しているか
- [ ] `ToolbarItem(placement:)`で配置しているか

### サイズチェック
- [ ] View全体が200行以下か（推奨）/ 300行以下か（絶対上限）
- [ ] 10行超のサブビューは`private var`に分割したか
- [ ] 50行超のコンポーネントは別ファイルに分離したか

### プレビューチェック
- [ ] `#Preview`を用意したか
- [ ] 複数状態（Default/Loading/Empty/Error）のプレビューがあるか

---

## ViewModel実装時

### 構造チェック
- [ ] `@Observable` + `@MainActor` を付与したか
- [ ] プロパティ順序は正しいか
  1. 公開状態プロパティ
  2. Computed Properties
  3. Private Properties
  4. Initializer
- [ ] 依存性注入のパターンに従っているか

### サイズチェック
- [ ] 250行以下か（推奨）/ 400行以下か（絶対上限）
- [ ] 関数は30行以下か（推奨）/ 50行以下か（絶対上限）
- [ ] 大きい場合はExtensionに分割したか

### 非同期処理チェック
- [ ] UI更新は`@MainActor`で行っているか
- [ ] `async/await`を使用しているか（completion handler禁止）
- [ ] エラーハンドリングは適切か（握りつぶし禁止）

---

## SwiftData Model実装時

### 定義チェック
- [ ] `@Model` を付与したか
- [ ] 必須プロパティとオプショナルプロパティを明確に分けたか
- [ ] リレーションに`inverse`を明示したか
- [ ] `deleteRule`を指定したか（`.nullify` or `.cascade`）

### 操作チェック
- [ ] 保存時に`try modelContext.save()`を明示的に呼んでいるか
- [ ] `@Query`にソート順序を明示しているか
- [ ] ViewModelでは`FetchDescriptor`を使用しているか

---

## Repository実装時

### 設計チェック
- [ ] Protocolを定義したか（テスト可能性）
- [ ] シングルトン + DI対応パターンに従っているか
- [ ] ローカルファースト戦略に従っているか
  1. ローカルに即座に保存
  2. APIに非同期で同期
  3. 失敗時はPendingOperationに保存

### エラー処理チェック
- [ ] APIError型でswitch文を使用しているか
- [ ] 409 (Conflict)は成功として扱っているか
- [ ] ネットワークエラー時はPendingOperationに保存しているか
- [ ] ログ出力形式は`[クラス名] メッセージ: 詳細`か

---

## コンポーネント実装時

### 配置判断チェック
- [ ] 2つ以上のFeatureで使用される → `DesignSystem/Components/`
- [ ] 1つのFeature専用 → `Features/{Feature}/Components/`
- [ ] 10行以下 → View内の`private var`

### 設計チェック
- [ ] 具象ViewModelに依存していないか
- [ ] クロージャで依存を注入しているか
- [ ] 類似コンポーネントは統合できないか

---

## API連携実装時

### Endpointチェック
- [ ] `path`, `method`, `body`を定義したか
- [ ] HTTPMethodは適切か（GET/POST/PUT/DELETE）

### 通信チェック
- [ ] ローカルファースト戦略に従っているか
- [ ] リトライ機構はPendingOperationで実装しているか
- [ ] タイムアウト設定は適切か

---

## テスト実装時

### 配置チェック
- [ ] `mylibraryTests/{対応ディレクトリ}/`に配置したか

### 命名チェック
- [ ] `test_{テスト対象}_{条件}_{期待結果}`形式か

### 設計チェック
- [ ] Protocolを使ってモック注入しているか
- [ ] 正常系・異常系の両方をテストしているか

---

## プルリクエスト前

### ビルドチェック
- [ ] ビルドが通るか
- [ ] 警告は出ていないか

### コード品質チェック
- [ ] 行数制限を超えていないか
- [ ] 不要な`print()`を削除したか
- [ ] ハードコード値は残っていないか
- [ ] 直接色指定は残っていないか

### ドキュメントチェック
- [ ] 新規ファイルにヘッダーコメントを記述したか
- [ ] 複雑なロジックにコメントを追加したか

### Git運用チェック
- [ ] ブランチ名は命名規則に従っているか（feature/fix/refactor/docs）
- [ ] コミットメッセージはtype: 説明形式か
- [ ] 1コミット1変更になっているか

---

## コードレビュー時

### 設計チェック
- [ ] 責務は適切に分離されているか
- [ ] 依存関係のルールに違反していないか
- [ ] 命名は意図を表しているか

### パフォーマンスチェック
- [ ] 不要な再レンダリングはないか
- [ ] 重い処理はバックグラウンドで実行しているか
- [ ] メモリリークの可能性はないか

### セキュリティチェック
- [ ] ユーザー入力のバリデーションは適切か
- [ ] 機密情報がログに出力されていないか

---

## リファクタリング前

### 確認チェック
- [ ] 同様のコンポーネントが既に存在しないか
- [ ] 既存コンポーネントを拡張して対応できないか
- [ ] 重複コードはExtensionに統合できないか
- [ ] private structは本当にそのファイル専用か
