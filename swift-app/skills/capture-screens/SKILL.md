---
name: capture-screens
description: アプリの全画面スクリーンショットを material/screens/ に撮り揃える。Debug ビルドの CLI フック（<APP>_DEMO_*）で任意の画面を直接開き、simctl で撮る方式。ストア画像・SNSカルーセル・LP・デザイン検討の元素材になる。新機能を作った後、ストア素材を作る前、デザインを見直すときに使う。
---

# 全画面スクショの取得（capture-screens）

## 方式

**Debug ビルドに「画面を直接開く CLI フック」を仕込み、環境変数を変えながら simctl で撮る。**
UI を人手で辿らないので、画面が増えても撮り直しが機械的に終わる。

hanasu で11画面、hioto でも同じ方式が動いている。**新規アプリでは実装時にこのフックを
先に入れておく**（後付けは面倒）。

## 1. フックの規約

`ContentView`（またはアプリのルート）で `#if DEBUG` 下に環境変数を読み、初期状態を差し替える。

| 環境変数 | 役割 |
|---|---|
| `<APP>_DEMO_ONBOARDED=1` | オンボーディングを完了済みにして本体を出す |
| `<APP>_DEMO_SEED=1` | デモデータを撒く（`DemoSeeder` / `seedDemoData()`） |
| `<APP>_DEMO_TAB=<name>` | 起動直後に開くタブ |
| `<APP>_DEMO_<SCREEN>=1` | 特定画面を直接開く（詳細・生成中・ペイウォール等） |

`<APP>` はアプリ名の大文字（`HANASU_DEMO_TAB`、`HIOTO_OPEN_SHORTS`）。
**`simctl launch` に渡すときは `SIMCTL_CHILD_` プレフィックスが必要**（これが無いと
アプリに届かない）。

デモデータは**ストア画像に写る**ので、医療・セラピー・メンタルヘルスの効能を思わせる文言を
入れない。実在の人名・店名も避ける。

## 2. 撮る

```bash
APP=Hanasu; SLUG=hanasu; BUNDLE=com.tubasasakun.hanasu; DEV="iPhone 17 Pro"

xcrun simctl boot "$DEV" 2>/dev/null || true
xcodebuild -project $APP.xcodeproj -scheme $APP -configuration Debug \
  -destination "platform=iOS Simulator,name=$DEV" build
APPPATH=$(xcodebuild -project $APP.xcodeproj -scheme $APP -configuration Debug \
  -destination "platform=iOS Simulator,name=$DEV" -showBuildSettings \
  | awk -F'= ' '/ BUILT_PRODUCTS_DIR /{d=$2} / FULL_PRODUCT_NAME /{n=$2} END{print d"/"n}')
xcrun simctl install booted "$APPPATH"

shot() {  # shot <出力名> <env...>
  out=$1; shift
  xcrun simctl terminate booted $BUNDLE 2>/dev/null || true
  env "$@" xcrun simctl launch booted $BUNDLE
  sleep 3
  xcrun simctl io booted screenshot "material/screens/$out"
}

shot 01_onboarding.png
shot 03_home.png SIMCTL_CHILD_HANASU_DEMO_ONBOARDED=1 SIMCTL_CHILD_HANASU_DEMO_SEED=1 \
                 SIMCTL_CHILD_HANASU_DEMO_TAB=home
xcrun simctl ui booted appearance dark
shot 04_home_dark.png SIMCTL_CHILD_HANASU_DEMO_ONBOARDED=1 SIMCTL_CHILD_HANASU_DEMO_SEED=1 \
                      SIMCTL_CHILD_HANASU_DEMO_TAB=home
xcrun simctl ui booted appearance light
```

- **`sleep` は画面ごとに調整する。** アニメーションや生成演出の途中を撮りたい画面がある
  （hanasu の `08_assembly.png` は起動 ~4秒の途中）
- 撮り漏れは後から効く。**画面を足したらこのリストにも足す**

## 3. 置き場と命名

```
material/
  screens/            全画面スクショ（iPhone 17 Pro / 1206×2622 @3x）
    01_onboarding.png   NN_画面名.png の連番。ダーク版は NN_名_dark.png
  ipad13/             iPad Pro 13-inch（2064×2752 @2x）。ファイル名は iPhone 版と同一
  footage/            背景・動画素材
  layouts/            レイアウト検討用の出力
  <store_slides.json が参照する名前>.png   ストア画像用（例 screen-hero.png）
```

**iPad 版はファイル名を iPhone 版と揃える。** ストア画像の生成スクリプトが同名で引く。

## 4. 対応表はアプリ側に置く

**画面と環境変数の対応表は各アプリの `material/README.md` に書く**（スキルは手順、アプリは
対応表）。この形式で:

| ファイル | 画面 | 撮り方 |
|---|---|---|
| `03_home.png` | ホーム（大カード + 目次・ライト） | `HANASU_DEMO_ONBOARDED=1 …_SEED=1 …_TAB=home` |
| `08_assembly.png` | 組版の見せ場（生成中） | `HANASU_DEMO_ASSEMBLY=1`（起動 ~4秒の途中） |

## 5. 撮った後

- **ストア画像**: `/app-store-optimize:screenshot-crafting` で構図を決め、
  `scripts/make_store_images.py` が `material/` を元素材に `release/<ver>/img/` を作る
- **SNS カルーセル**: `/sns-marketing:carousel-craft` が `material/` の実画面を敷く
- クロマキー合成する画面は背景 `#00FF00` で撮る（`store_slides.json` の指定に従う）

> Simulator と実機は挙動が違う領域がある（AVCaptureSession、CloudKit、課金）。
> **実機でしか正しく写らない画面は実機で撮る**（`xcrun devicectl` または手動）。
