# 推奨ディレクトリ構成

```
ProjectName/
├── .gitignore                    # 最初に作成!
├── CLAUDE.md                     # プロジェクトドキュメント
├── ProjectName/                  # iOS アプリ
│   ├── ProjectNameApp.swift      # エントリポイント
│   ├── ContentView.swift         # ルートナビゲーション
│   ├── Core/
│   │   ├── Models/               # SwiftData モデル + DTO
│   │   ├── Network/              # APIClient, Endpoint, APIError
│   │   └── Services/             # ThemeManager, UserIDManager, SyncService
│   ├── DesignSystem/
│   │   ├── Theme/                # Color+Theme, DesignTokens
│   │   └── Components/           # 共通 UI コンポーネント
│   └── Features/
│       ├── Home/                  # View + ViewModel
│       ├── AddItem/               # View + ViewModel
│       ├── ItemDetail/            # DetailView + EditView
│       ├── Search/                # View + ViewModel
│       ├── Settings/              # View
│       └── Onboarding/            # ContainerView + Pages/
├── ProjectName-api/              # Cloudflare Workers API
│   ├── src/
│   │   ├── index.ts
│   │   ├── routes/
│   │   ├── services/
│   │   └── types/
│   ├── migrations/
│   └── wrangler.jsonc
├── ProjectName-front/            # Web フロントエンド（任意）
│   └── src/
└── scripts/
    ├── take_screenshots.sh
    └── flows/                    # Maestro YAML
```
