# よくあるミスと対処法

## 致命的なミス

| ミス | 影響 | 対処法 |
|------|------|--------|
| `.gitignore` 未設定 | node_modules が GB 単位でコミット | **プロジェクト作成直後に設定** |
| SwiftData フィールドにデフォルト値なし | アプリクラッシュ | 新フィールドには必ずデフォルト値 |
| `import SwiftData` 忘れ | ビルドエラー | 使う全ファイルに追加 |

## UI の罠

| 問題 | 原因 | 解決策 |
|------|------|--------|
| ナビバー背景が消えない | SwiftUI だけでは制御不足 | UIAppearance + toolbarBackgroundVisibility |
| .searchable の背景色 | カスタマイズ API がない | カスタム SearchBar コンポーネント |
| タブバーの影 | デフォルト shadowImage | UITabBarAppearance で透過 |
| ダークモードで背景が変 | テーマ色がライト前提 | ライト/ダーク両方の色を用意 |

## API / 同期の罠

| 問題 | 原因 | 解決策 |
|------|------|--------|
| UI が固まる | 同期処理を await している | `Task.detached` で fire-and-forget |
| HTTPMethod に PATCH がない | enum に追加し忘れ | `.patch` case を追加 |
| D1 バインディングエラー | wrangler.jsonc の設定ミス | database_id を正しく設定 |
| XSS 脆弱性 | HTML エスケープ忘れ | `escapeHtml()` を必ず使う |
