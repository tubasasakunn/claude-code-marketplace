# iOS Testing with Maestro - 詳細リファレンス

Maestroコマンドの詳細リファレンスとトラブルシューティングガイドです。

---

## ディレクトリ構成

```
maestro/
├── DOCUMENT.md        # 画面一覧とファイル対応表（必須）
├── run.sh             # 単一フロー実行
├── run_all.sh         # 全フロー実行
├── run_bulk.sh        # 全画面一括撮影（高速）
├── reinstall.sh       # アプリ再インストール
├── flows/
│   ├── _common/       # 共通サブフロー
│   │   └── setup_with_sample_data.yaml
│   ├── bulk_all.yaml  # 一括撮影フロー
│   ├── onboarding_01.yaml ~ onboarding_XX.yaml  # オンボーディング
│   └── 01_home.yaml ~ XX_screen.yaml            # メイン画面
└── screenshots/       # 出力先（自動生成）
```

---

## DOCUMENT.mdテンプレート

**`maestro/DOCUMENT.md`は必須です。** 以下をテンプレートとして使用:

```markdown
# DOCUMENT.md - Maestro UIテスト ドキュメント

## 概要

このディレクトリには、{アプリ名}の各画面のスクリーンショットを自動撮影するMaestroフローが含まれています。

**全てのフローは `clearState: true` で毎回クリーンスタートします。**

---

## 画面一覧とファイル対応表

### オンボーディング

| No | 画面名 | フローファイル | スクリーンショット | 説明 |
|----|--------|---------------|-------------------|------|
| OB1 | オンボーディング1 | flows/onboarding_01.yaml | screenshots/onboarding_01.png | ウェルカム画面 |

### メイン画面

| No | 画面名 | フローファイル | スクリーンショット | 説明 |
|----|--------|---------------|-------------------|------|
| 01 | ホーム | flows/01_home.yaml | screenshots/01_home.png | メイン画面 |

---

## 共通サブフロー

| ファイル | 説明 |
|----------|------|
| flows/_common/setup_with_sample_data.yaml | オンボーディング完了 + サンプルデータ生成 |

---

## 実行スクリプト

| ファイル | 説明 | 使用方法 |
|----------|------|----------|
| run.sh | 単一フロー実行 | ./run.sh flows/01_home.yaml |
| run_all.sh | 全フロー実行 | ./run_all.sh |
| reinstall.sh | アプリ再インストール | ./reinstall.sh |

---

## 前提条件

- **Maestro CLI**: インストール済み（`maestro --version` で確認）
- **シミュレータ**: 起動中
- **アプリ**: ビルド済み、シミュレータにインストール済み

---

## 更新履歴

| 日付 | 内容 |
|------|------|
| YYYY-MM-DD | 初版作成 |
```

---

## 全コマンドリファレンス

### アプリ操作

#### launchApp

```yaml
# 通常起動
- launchApp

# 状態をクリアして起動（オンボーディング用）
- launchApp:
    clearState: true

# 特定のアプリを起動
- launchApp:
    appId: com.example.myapp
```

#### stopApp

```yaml
- stopApp
- stopApp:
    appId: com.example.myapp
```

#### clearState

```yaml
- clearState
- clearState:
    appId: com.example.myapp
```

---

### タップ操作

#### tapOn

```yaml
# テキストで検索（部分一致）
- tapOn: "検索"

# 正確なテキストマッチ
- tapOn:
    text: "検索"

# IDで検索（accessibilityIdentifier）
- tapOn:
    id: "search_button"

# 座標指定（絶対値）
- tapOn:
    point: "100,200"

# 座標指定（パーセント）
- tapOn:
    point: "50%, 50%"

# オプショナル（見つからなくてもエラーにしない）
- tapOn:
    text: "今はしない"
    optional: true

# 複数条件
- tapOn:
    id: "button"
    index: 0  # 複数マッチした場合の順番
```

#### longPressOn

```yaml
# 長押し（テキスト）
- longPressOn: "削除"

# 長押し（座標）
- longPressOn:
    point: "50%, 50%"

# 長押し時間指定
- longPressOn:
    text: "編集"
    duration: 2000  # ミリ秒
```

#### doubleTapOn

```yaml
- doubleTapOn: "ズーム"
- doubleTapOn:
    point: "50%, 50%"
```

---

### スワイプ・スクロール

#### swipe

```yaml
# 右から左へスワイプ（次ページ）
- swipe:
    start: "80%, 50%"
    end: "20%, 50%"

# 下から上へスワイプ（上スクロール）
- swipe:
    start: "50%, 80%"
    end: "50%, 20%"

# 上から下へスワイプ（下スクロール）
- swipe:
    start: "50%, 20%"
    end: "50%, 80%"

# 左から右へスワイプ（前ページ）
- swipe:
    start: "20%, 50%"
    end: "80%, 50%"

# 速度指定
- swipe:
    start: "50%, 80%"
    end: "50%, 20%"
    duration: 500  # ミリ秒
```

#### scroll

```yaml
# デフォルトスクロール
- scroll

# 方向指定
- scroll:
    direction: DOWN  # UP, DOWN, LEFT, RIGHT
```

---

### テキスト入力

#### inputText

```yaml
# テキスト入力
- inputText: "検索ワード"

# 改行を含む
- inputText: "1行目\n2行目"
```

#### eraseText

```yaml
# 文字を削除
- eraseText: 10  # 10文字削除

# 全削除
- eraseText: 100
```

#### pressKey

```yaml
# Enterキー
- pressKey: Enter

# バックスペース
- pressKey: Backspace

# ホームボタン
- pressKey: Home
```

---

### 待機

#### extendedWaitUntil

```yaml
# 要素が表示されるまで待機
- extendedWaitUntil:
    visible: "ホーム"
    timeout: 10000  # ミリ秒

# 要素が消えるまで待機
- extendedWaitUntil:
    notVisible: "ローディング"
    timeout: 10000

# 正規表現で待機
- extendedWaitUntil:
    visible: ".*"
    timeout: 5000

# 固定時間待機
- extendedWaitUntil:
    timeout: 2000
```

---

### アサーション

#### assertVisible

```yaml
# 要素が表示されていることを確認
- assertVisible: "ホーム"
- assertVisible:
    text: "ホーム"
```

#### assertNotVisible

```yaml
# 要素が表示されていないことを確認
- assertNotVisible: "エラー"
```

---

### スクリーンショット

#### takeScreenshot

```yaml
# スクリーンショット撮影
- takeScreenshot: screenshots/01_home

# 拡張子は自動で.pngが付く
```

---

### サブフロー

#### runFlow

```yaml
# サブフローを実行
- runFlow: _common/setup_with_sample_data.yaml

# 相対パス（flowsディレクトリからの相対）
- runFlow: _common/login.yaml
```

---

### 条件分岐

#### runFlow with condition

```yaml
# 条件付き実行
- runFlow:
    when:
        visible: "ログイン"
    file: _common/login.yaml
```

---

## トラブルシューティング

### 要素が見つからない

```yaml
# テキストが見つからない場合は座標を使う
- tapOn:
    point: "200,300"

# または accessibilityIdentifier を確認
- tapOn:
    id: "accessibilityIdentifier"

# maestro studioで要素を確認
# maestro studio
```

### 画面遷移が速すぎる

```yaml
# 待機を追加
- extendedWaitUntil:
    visible: "表示される要素"
    timeout: 5000
```

### オンボーディングが表示されない

```bash
# アプリを再インストール
./reinstall.sh
```

### シミュレータが起動していない

```bash
# シミュレータ起動
xcrun simctl boot "iPhone 16 Pro"
open -a Simulator
```

### Maestroがインストールされていない

```bash
# インストール
curl -fsSL "https://get.maestro.mobile.dev" | bash

# パス追加（zsh）
echo 'export PATH="$PATH:$HOME/.maestro/bin"' >> ~/.zshrc
source ~/.zshrc

# 確認
maestro --version
```

### フローが途中で失敗する

```bash
# デバッグモードで実行
maestro test --debug flows/01_home.yaml

# studioでステップ実行
maestro studio
```

---

## 応用パターン

### 一括撮影フロー

1回の実行で複数画面を撮影する`bulk_all.yaml`を作成:

```yaml
# 全画面一括スクリーンショット撮影フロー
appId: com.example.myapp
name: "全画面一括撮影"
---
- launchApp:
    clearState: true

# オンボーディング1
- extendedWaitUntil:
    visible: ".*"
    timeout: 5000
- takeScreenshot: screenshots/onboarding_01

# オンボーディング2
- swipe:
    start: "80%, 50%"
    end: "20%, 50%"
- takeScreenshot: screenshots/onboarding_02

# ... 続く
```

### 環境変数の使用

```yaml
appId: ${APP_ID}
---
- inputText: ${TEST_USER}
```

実行:
```bash
APP_ID=com.example.myapp TEST_USER=testuser maestro test flows/login.yaml
```

### 繰り返し処理

```yaml
# 3回スワイプ
- repeat:
    times: 3
    commands:
      - swipe:
          start: "80%, 50%"
          end: "20%, 50%"
```

---

## ベストプラクティス

### 1. clearStateを活用

毎回クリーンスタートで再現性を確保:

```yaml
- launchApp:
    clearState: true
```

### 2. 適切な待機を入れる

アニメーション後、API通信後に待機:

```yaml
- tapOn: "保存"
- extendedWaitUntil:
    visible: "保存完了"
    timeout: 10000
```

### 3. 共通処理はサブフローに

オンボーディングスキップ等は`_common/`に:

```yaml
- runFlow: _common/setup.yaml
```

### 4. optionalを活用

表示されない可能性があるダイアログ:

```yaml
- tapOn:
    text: "許可しない"
    optional: true
```

### 5. IDを優先

テキストより`accessibilityIdentifier`が安定:

```yaml
# Good
- tapOn:
    id: "save_button"

# Bad（テキスト変更で壊れる）
- tapOn: "保存する"
```

---

## 参考リンク

- [Maestro公式ドキュメント](https://maestro.mobile.dev/)
- [Maestro コマンドリファレンス](https://maestro.mobile.dev/reference/commands)
- [Maestro GitHub](https://github.com/mobile-dev-inc/maestro)
