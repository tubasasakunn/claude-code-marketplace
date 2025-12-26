---
name: ios-testing
description: Maestroを使用したiOSアプリのUIテストとスクリーンショット撮影を支援します。テストフロー作成、画面撮影、UI自動化について質問された場合に使用してください。
---

# iOS Testing with Maestro

MaestroによるiOSアプリのUIテスト自動化ガイドです。

## 概要

**Maestro** はモバイルアプリのUIテスト自動化ツールです。
YAMLでテストフローを記述し、シミュレータ/実機でUIを操作します。

### 用途

- 各画面のスクリーンショット自動撮影
- UI操作の自動テスト
- 画面遷移の検証
- リグレッションテスト

---

## セットアップ

### 1. maestroディレクトリを作成

**プロジェクトのルートディレクトリ（カレント）に`maestro/`を作成します。**

```bash
mkdir -p maestro/flows/_common
mkdir -p maestro/screenshots
```

### 2. 必要なファイルを配置

```
maestro/
├── DOCUMENT.md        # 画面一覧とファイル対応表（必須）
├── run.sh             # 単一フロー実行
├── run_all.sh         # 全フロー実行
├── reinstall.sh       # アプリ再インストール
├── flows/
│   ├── _common/       # 共通サブフロー
│   └── *.yaml         # 画面ごとのフロー
└── screenshots/       # 出力先（自動生成）
```

### 3. DOCUMENT.mdを作成

**`maestro/DOCUMENT.md`は必須です。** 画面一覧とフローの対応を管理します。

```markdown
# DOCUMENT.md - Maestro UIテスト ドキュメント

## 画面一覧

| No | 画面名 | フローファイル | スクリーンショット |
|----|--------|---------------|-------------------|
| 01 | ホーム | flows/01_home.yaml | screenshots/01_home.png |
| 02 | 検索 | flows/02_search.yaml | screenshots/02_search.png |

## 実行方法

./run.sh flows/01_home.yaml
```

### 4. シェルスクリプトを配置

このスキルの`scripts/`ディレクトリから以下をコピー:
- `run.sh` - 単一フロー実行
- `run_all.sh` - 全フロー実行
- `reinstall.sh` - アプリ再インストール

```bash
cp <skill-path>/scripts/*.sh maestro/
chmod +x maestro/*.sh
```

---

## クイックスタート

### 単一フローの実行

```bash
cd maestro
./run.sh flows/01_home.yaml
```

### 全フローの実行

```bash
cd maestro
./run_all.sh
```

### Maestro直接実行

```bash
maestro test flows/01_home.yaml
maestro studio  # GUI で操作確認
maestro record  # 操作を記録してYAML生成
```

---

## YAMLフローの基本構造

```yaml
# 画面名のスクリーンショット
# 使用方法: ./run.sh flows/01_home.yaml
appId: com.example.myapp
name: "ホーム画面"
---
- launchApp:
    clearState: true

# 画面への遷移操作
- tapOn: "ボタン名"

# 画面表示待機
- extendedWaitUntil:
    visible: "表示される要素"
    timeout: 5000

# スクリーンショット
- takeScreenshot: screenshots/01_home
```

---

## 主要コマンド

| コマンド | 説明 | 例 |
|----------|------|-----|
| `launchApp` | アプリ起動 | `- launchApp` |
| `launchApp: clearState: true` | 状態クリアして起動 | オンボーディング用 |
| `tapOn` | 要素をタップ | `- tapOn: "検索"` |
| `tapOn: id` | IDでタップ | `- tapOn: id: "button_id"` |
| `tapOn: point` | 座標でタップ | `- tapOn: point: "100,200"` |
| `swipe` | スワイプ | 下記参照 |
| `inputText` | テキスト入力 | `- inputText: "検索ワード"` |
| `scroll` | スクロール | `- scroll` |
| `back` | 戻る | `- back` |
| `takeScreenshot` | スクショ撮影 | `- takeScreenshot: path/name` |
| `extendedWaitUntil` | 要素を待機 | 下記参照 |
| `runFlow` | サブフロー実行 | `- runFlow: _common/setup.yaml` |

### tapOnの詳細

```yaml
# テキストで検索（部分一致）
- tapOn: "検索"

# IDで検索（accessibilityIdentifier）
- tapOn:
    id: "magnifyingglass"

# 座標指定（x, y）
- tapOn:
    point: "100,200"

# パーセント指定
- tapOn:
    point: "50%, 50%"
```

### swipeの書き方

```yaml
# 右から左へスワイプ（次ページ）
- swipe:
    start: "80%, 50%"
    end: "20%, 50%"

# 下から上へスワイプ（スクロール）
- swipe:
    start: "50%, 80%"
    end: "50%, 20%"
```

### 待機の書き方

```yaml
# 要素が表示されるまで待機
- extendedWaitUntil:
    visible: "本棚"
    timeout: 10000  # ミリ秒

# 固定時間待機
- extendedWaitUntil:
    timeout: 2000
```

---

## 新しい画面のフロー追加手順

1. **YAMLファイル作成**
   ```bash
   touch maestro/flows/07_new_screen.yaml
   ```

2. **基本構造を記述**
   ```yaml
   # 新画面のスクリーンショット
   # 使用方法: ./run.sh flows/07_new_screen.yaml
   appId: com.example.myapp
   name: "新画面"
   ---
   - launchApp:
       clearState: true

   # 共通セットアップ（必要な場合）
   - runFlow: _common/setup.yaml

   # 画面への遷移操作
   - tapOn: "ボタン名"

   # 画面表示待機
   - extendedWaitUntil:
       visible: "画面の特徴的なテキスト"
       timeout: 5000

   # スクリーンショット
   - takeScreenshot: screenshots/07_new_screen
   ```

3. **動作確認**
   ```bash
   ./run.sh flows/07_new_screen.yaml
   ```

4. **DOCUMENT.md更新**
   - 画面一覧に追加

---

## 共通サブフローの作成

複数のフローで使う処理は`flows/_common/`に切り出す:

```yaml
# flows/_common/setup_with_sample_data.yaml
appId: com.example.myapp
---
# オンボーディング完了まで待機
- extendedWaitUntil:
    visible: ".*"
    timeout: 5000

# オンボーディングをスキップ
- swipe:
    start: "80%, 50%"
    end: "20%, 50%"

# 「開始」ボタンをタップ
- tapOn: "開始"

# ホーム画面表示待機
- extendedWaitUntil:
    visible: "ホーム"
    timeout: 10000
```

使用方法:
```yaml
- runFlow: _common/setup_with_sample_data.yaml
```

---

## 詳細リファレンス

詳細なコマンドやトラブルシューティングは[REFERENCE.md](REFERENCE.md)を参照。

---

## ルール

### 1. ファイル命名規則

- メイン画面: `XX_screen_name.yaml`（XX = 01-99）
- オンボーディング: `onboarding_XX.yaml`

### 2. スクリーンショット命名

- フロー名と一致させる
- 例: `flows/01_home.yaml` → `screenshots/01_home.png`

### 3. コメント必須

各YAMLの先頭に以下を記載:
- 画面名
- 使用方法
- 注意事項（あれば）

### 4. 更新時の対応

- 新しいフローを追加したら DOCUMENT.md を更新
- `run_all.sh` への追加が必要か確認
