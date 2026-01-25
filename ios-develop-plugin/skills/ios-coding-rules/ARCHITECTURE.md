# iOS Coding Rules - アーキテクチャ

ディレクトリ構成、ファイル配置、レイヤー設計のルール。

---

## 1. ディレクトリ構成

```
mylibrary/
├── App/                     # アプリエントリーポイント
├── Core/                    # データ層・インフラ
│   ├── Models/              # SwiftDataモデル
│   ├── Network/             # API通信基盤
│   ├── Repositories/        # データアクセス層
│   └── Sync/                # 同期処理
├── Features/                # 機能別モジュール
│   └── {FeatureName}/
│       ├── Components/      # 機能固有のコンポーネント
│       ├── {FeatureName}View.swift
│       └── {FeatureName}ViewModel.swift
├── DesignSystem/            # UIコンポーネント・スタイル
│   ├── Theme/               # 色、フォント、アニメーション
│   ├── Components/          # 再利用可能なUIコンポーネント
│   ├── GlassEffect/         # エフェクト関連
│   └── Extensions/          # View拡張
├── Services/                # ドメインサービス
└── Resources/               # アセット
```

## 2. 各ディレクトリの責務

| ディレクトリ | 責務 | 配置するもの |
|-------------|------|-------------|
| `App/` | アプリ起動・設定 | `@main` App, ContentView, AppDelegate |
| `Core/Models/` | データ定義 | SwiftDataモデル、DTO、Enum |
| `Core/Network/` | 通信基盤 | APIClient、Endpoint定義、エラー型 |
| `Core/Repositories/` | データアクセス抽象化 | Repository実装、Protocol |
| `Core/Sync/` | 同期処理 | SyncManager、PendingOperation処理 |
| `Features/{Name}/` | 機能実装 | View、ViewModel、機能固有コンポーネント |
| `DesignSystem/Theme/` | デザイントークン | 色定義、フォント、アニメーション定数 |
| `DesignSystem/Components/` | 共通UI | 2つ以上の機能で使われるUIコンポーネント |
| `Services/` | ドメインロジック | ビジネスロジック、外部API連携 |
| `Resources/` | 静的リソース | Assets、MLモデル、フォント |

---

## 3. ファイル配置ルール

### 新規ファイルの配置判断フロー

```
新しいファイルを作成する
    │
    ├─ SwiftDataの@Modelか？ → Core/Models/
    │
    ├─ API通信関連か？ → Core/Network/
    │
    ├─ データの取得・保存を抽象化するか？ → Core/Repositories/
    │
    ├─ 特定の画面のViewか？
    │   └─ その画面専用か？ → Features/{機能名}/
    │   └─ 複数画面で使うか？ → DesignSystem/Components/
    │
    ├─ ViewModelか？ → Features/{機能名}/
    │
    ├─ View拡張・モディファイアか？ → DesignSystem/Extensions/
    │
    ├─ 色・フォント・定数か？ → DesignSystem/Theme/
    │
    └─ ビジネスロジック・外部連携か？ → Services/
```

### コンポーネントの配置基準

| 使用箇所 | 配置先 |
|---------|--------|
| 1つの機能でのみ使用 | `Features/{機能名}/Components/` |
| 2つ以上の機能で使用 | `DesignSystem/Components/` |
| アプリ全体で使用（TabBar等） | `DesignSystem/Components/` |

### 禁止事項

- `Features/` 直下にファイルを置かない（必ず機能フォルダを作成）
- `Core/` に UI 関連のコードを置かない
- `DesignSystem/` にビジネスロジックを含めない
- ルートディレクトリにSwiftファイルを置かない

---

## 4. ファイルサイズ制限

### 行数制限

| ファイル種別 | 推奨上限 | 絶対上限 | 超過時の対応 |
|-------------|---------|---------|-------------|
| View | 200行 | 300行 | コンポーネント分割 |
| ViewModel | 250行 | 400行 | ヘルパークラス抽出 |
| Model | 100行 | 150行 | Extension分割 |
| Service | 200行 | 350行 | 責務分割 |
| Repository | 200行 | 300行 | 操作別に分割 |
| Extension | 100行 | 150行 | 機能別に分割 |

### 関数サイズ制限

| 項目 | 推奨上限 | 絶対上限 |
|-----|---------|---------|
| 関数の行数 | 30行 | 50行 |
| 関数の引数 | 4個 | 6個 |
| ネストの深さ | 3レベル | 4レベル |
| 1ファイル内の型定義 | 1個 | 3個（関連する場合のみ） |

---

## 5. レイヤー構成

```
┌─────────────────────────────────────────┐
│              Features (UI)               │
│         View ←→ ViewModel                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│              Services                    │
│      ドメインロジック・外部連携          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│           Core/Repositories              │
│         データアクセス抽象化             │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         Core/Network + Models            │
│          API通信・データ定義             │
└─────────────────────────────────────────┘
```

### 依存関係のルール

```
許可される依存:
View → ViewModel → Repository → Network/Models
View → DesignSystem
ViewModel → Services
Services → Repositories

禁止される依存:
Models → View（逆方向）
Network → ViewModel（逆方向）
DesignSystem → Features（逆方向）
Repository → View（逆方向）
```
