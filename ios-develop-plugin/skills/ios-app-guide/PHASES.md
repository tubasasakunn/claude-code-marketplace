# 開発フェーズと手順

## Phase 1: 初期構築（基盤）

**やること:**
- Xcode プロジェクト作成（SwiftData テンプレート）
- `.gitignore` を**最初に**設定（node_modules, DerivedData, .DS_Store 等）
- MVVM 基本構造の構築（Models / Network / Services / Features）
- APIClient / Endpoint プロトコルの実装
- SwiftData モデルの定義（`@Attribute(.unique)` で重複防止）
- 基本画面の実装（ホーム、追加、詳細、編集）

**教訓:**
- `.gitignore` をプロジェクト作成直後に設定しないと、node_modules 等を含む巨大コミットが発生する
- API プロキシがある場合は、iOS と API を同一リポジトリで管理するとデプロイが楽

---

## Phase 2: UI リファクタ + デザインシステム

**やること:**
- タブ構成の確定（早めに決める）
- DesignTokens（スペーシング・角丸・グリッド定数）の整備
- セマンティックカラーの定義（`Color+Theme.swift`）
- テーマシステムの実装（カラー選択 + 永続化）
- 共通コンポーネントの抽出（ポスター表示、ボタンスタイル等）

**教訓:**
- タブ構成の変更は NavigationStack との整合に影響が大きいため、**早期に確定させる**
- テーマカラーはライトモード・ダークモードの**両方**で背景色を用意する
- `Color.mix` で背景にアクセントカラーをティントすると統一感が出る

---

## Phase 3: バックエンド + データ同期

**やること:**
- D1 データベース（マイグレーション SQL）
- API エンドポイント実装（CRUD）
- Zod バリデーション
- iOS 側の同期サービス（fire-and-forget パターン）
- 新機能に伴うモデル拡張（デフォルト値を忘れない）

**教訓:**
- SwiftData の lightweight migration のため、新フィールドには**必ずデフォルト値**を設定する
- 同期は `Task.detached` で fire-and-forget にすることで UI をブロックしない
- **SwiftData が source of truth、API は非同期バックアップ**という設計思想を一貫させる

---

## Phase 4: オンボーディング + レビューリクエスト

**やること:**
- TabView(.page) による複数ページオンボーディング
- `@AppStorage` フラグで初回のみ表示
- `requestReview()` の呼び出し（最終ページ）
- Accessibility Identifier の付与（テスト自動化の準備）

**教訓:**
- オンボーディングは ZStack overlay + spring animation で表示制御すると自然
- `requestReview()` は最終ページの「はじめる」ボタンで呼ぶのが自然なタイミング

---

## Phase 5: ユーザーシステム + ソーシャル機能

**やること:**
- ユーザー登録 API（起動時に fire-and-forget）
- UUID ベースの公開 URL 生成
- 共有ボタン（`UIActivityViewController`）
- Web フロントエンド（公開ページ）
- テーマ色の API 同期

**教訓:**
- `HTTPMethod` enum に `.patch` を追加する必要がある場合がある
- フロントエンド側の色パレットは iOS 側と合わせる
- `escapeHtml` で XSS 対策を必ず行う

---

## Phase 6: デザイン統一 + ブランディング

**やること:**
- 全画面でセマンティックカラーを統一適用
- サードパーティロゴ・法的リンクの追加（TMDb 等）
- アプリ表示名の確定（`INFOPLIST_KEY_CFBundleDisplayName`）
- アプリアイコンの追加

**教訓:**
- API 提供元の利用規約でロゴ表示が求められる場合がある
- 表示名変更は `project.pbxproj` を直接編集する

---

## Phase 7: ナビバー・検索バー問題の修正

最も苦労したフェーズ。6コミット連続で格闘した問題。

| 試行 | 対策 | 結果 |
|------|------|------|
| 1回目 | 個別 View で背景設定 | 不十分 |
| 2回目 | `UINavigationBarAppearance` | 部分的に効果あり |
| 3回目 | ナビバー + タブバー完全透過 | 影が残る |
| 4回目 | `UISearchBar.appearance()` | 他に影響 |
| 5回目 | 不要なコード削除 + 整理 | 改善 |
| 6回目 | `toolbarBackgroundVisibility(.hidden)` 全画面 | **解決** |

**最終的な解決策:**
- `UIAppearance`（AppDelegate）でグローバル設定 + `.toolbarBackgroundVisibility(.hidden)` を各画面に適用
- `.searchable` を廃止し、カスタム `SearchBar` コンポーネントに置換

→ 詳細: [NAVIGATION-UIKIT.md](NAVIGATION-UIKIT.md)

---

## Phase 8: 最終ポリッシュ

**やること:**
- 細かい padding / spacing の調整
- ダークテーマの専用背景色追加
- ポスター角丸の除去等のデザイン微調整
- フロントエンドの色パレット・favicon 整備

**教訓:**
- デザインの微調整は**最後にまとめてやる**のが効率的
- 機能追加中にデザインを気にしすぎると手戻りが増える
