---
name: icon-crafting
description: Icon Composer の `.icon` バンドル（Liquid Glass アプリアイコン）を、GUIアプリを一切開かずスクリプトで生成し、actool でコンパイル検証し、Xcodeプロジェクトへ組み込みます。design-crafting のchapter06（AppIconの方向性）で決めたレイヤー構成をもとに、`03_implement_app` で本番AppIconを作るときに使ってください。
---

# .icon（Icon Composer）バンドルの生成・検証 (icon-crafting)

## このスキルが解決する問題

Icon Composer は macOS の GUI アプリで、一見するとアプリアイコン作りが自動化できないように見える。
だが `.icon` ファイルの正体は**ただのフォルダ（パッケージ）で、中身は素の JSON（`icon.json`）と PNG/SVG（`Assets/`）**でしかない。
Icon Composer.app を一度も開かずに、`icon.json` をテンプレートとして直接書き出せば `.icon` バンドルを作れる（2026-07-10、Xcode 26.6 で実機検証済み）。

一方で、これに付随する2つの罠がある。

1. **`ictool`（Icon Composer.app 内蔵のCLI）は当てにならない。** 2025年のXcode 26 betaを取材したブログには `ictool AppIcon.icon --export-preview iOS Light 512 512 1 out.png` のようなプレビュー書き出し構文が紹介されているが、Xcode 26.6 GA では同じ引数が軒並み `Unknown argument` エラーになる（実機再現済み）。内部・非公開ツールで版間の互換性が無いので、パイプラインの正規ルートとして依存しない。
2. **`.icon` から1024×1024のApp Store掲載用マーケティングPNGを綺麗に書き出す公式手段が無い。** ストア画像用の1024アイコンが要るときは、別途 `canva-image-gen` 等で元絵から書き出す（Icon Composerの出力を経由しない）。

このスキルが提供するのは、上記の罠を踏まずに済む**検証済みの経路**（icon.json直書き＋`actool`によるコンパイル検証）である。

## いつ使うか

- `design-crafting` の [chapter06](../design-crafting/chapters/06-icon.md) でAppIconのレイヤー構成（背景/中景/前景、配色）を言語化した**後**
- `03_implement_app` で「本番のAppIcon」を作るとき（それまではプレースホルダのままでよい）
- 既存アプリのAppIconをLiquid Glass対応に差し替えるとき

## 前提条件

```bash
# Xcode 26以降が入っているか（Icon Composerの.icon対応はXcode 26から）
xcodebuild -version

# actool の所在確認（Xcodeに同梱、GUIアプリの起動は不要）
xcrun --find actool

# xcodegen運用ならproject.ymlでAppIconの名前を確認
grep ASSETCATALOG_COMPILER_APPICON_NAME project.yml
```

design-crafting のDESIGN.mdから、以下が決まっていること:
- モチーフ図形（背景/中景/前景のレイヤー構成、多くて2〜3層）
- 各レイヤーの色（Tokensのhex値）
- レイヤーの元絵（1024×1024、白抜き・透過背景のSVG/PNG。canva-image-gen等で書き出したもの）

## 経路の選択: 旧来の `Assets.xcassets` vs 新しい `.icon`

| | `Assets.xcassets/AppIcon.appiconset`（旧） | `AppIcon.icon`（Icon Composer） |
|---|---|---|
| 実体 | 1024×1024 PNG 1枚 | `icon.json` + レイヤー画像（Assets/） |
| Liquid Glass対応 | 非対応（iOS 26のホーム画面で平面表示） | 対応 |
| 生成方法 | 画像1枚を書き出すだけ | このスキルの手順が必要 |
| 現状 | swift-baseテンプレート・既存アプリ（kasaneru等）はこちら | まだパイプライン未導入 |

**新規アプリはLiquid Glass対応の `.icon` を使う**のがこのスキルの前提。ただし `.icon` を置いても `ASSETCATALOG_COMPILER_APPICON_NAME` の指す名前（拡張子抜き）を `.icon` バンドルのbasenameに合わせれば、xcodegenの `sources: - path: <Target>` （シンクロ済みルートグループ）配下に置くだけで自動的に拾われる（`.xcassets` と同じ扱い）。旧形式との併存は不要——`.icon` 単体でiOS 17のような低いdeploymentTargetでも、`actool` がビルド時に自動で旧OS互換PNGを生成する（後述のStep 3で実証済み）。

## `.icon` バンドルの構造

```
AppIcon.icon/
  icon.json       # レイヤー構成・色・エフェクトを記述するJSON
  Assets/
    layer1.png    # 各レイヤーの元絵（透過PNG or SVG）
    layer2.png
```

`icon.json` は非公開フォーマットだが、既存アプリ11件の実物を突き合わせて以下のフィールドを確認済み（Apple公式ドキュメントには載っていない。今後のIcon Composerの版で構造が変わりうる前提で扱う）。

```jsonc
{
  // 背景。単色 "srgb:r,g,b,a"("display-p3:..."/"extended-srgb:..."/"extended-gray:w,a" も可、値は0-1の5桁小数)、
  // またはグラデーション "automatic-gradient": "srgb:r,g,b,a"、または "system-dark" のようなキーワード文字列でもよい
  "fill": { "solid": "srgb:0.89020,0.65882,0.34118,1.00000" },

  "groups": [
    {
      "layers": [
        {
          "image-name": "layer1.png",   // Assets/ 内のファイル名と一致させる
          "name": "layer1",
          "opacity": 1,
          "glass": true,                  // Liquid Glassマテリアルを適用するか
          "fill": { "solid": "srgb:1,1,1,1" },  // レイヤーの塗り（image-nameの画像はマスクとして使われる）
          "position-specializations": [
            { "value": { "scale": 1, "translation-in-points": [0, 0] } },
            { "idiom": "square", "value": { "scale": 1, "translation-in-points": [0, 0] } }
          ],
          // 特定の外観（tinted等）だけブレンドモードを変えたい場合のみ
          "blend-mode-specializations": [
            { "appearance": "tinted", "value": "darken" }
          ]
        }
      ],
      "shadow": { "kind": "neutral", "opacity": 0.5 },
      "translucency": { "enabled": true, "value": 0.5 },
      "specular": false
    }
  ],

  "supported-platforms": { "circles": ["watchOS"], "squares": "shared" }
}
```

**重要: ライト/ダーク/ティント対応は「別の絵を用意する」ものではない。**
実物11件のどれにも `appearance: dark` のような明示的なダーク専用レイヤーは無かった。旧来の `Assets.xcassets` の暗色バリアント画像とは発想が違い、**単色の白抜きシルエット1枚 + `fill`（背景）+ `glass`/`translucency`（マテリアル）を渡せば、システムがライト/ダーク/ティントを自動で描き分ける**。個別の外観だけ挙動を変えたいとき（例: ティント時だけブレンドモードを変える）に限り `*-specializations` 配列へ `"appearance": "tinted"` のエントリを足す。design-crafting chapter06 の「ダークモード用の構成」は、`.icon` では主に「`fill` に何を渡すか」に翻訳される。

## Step 1. レイヤー画像を `Assets/` に用意する

DESIGN.mdの配色・レイヤー構成に沿って、各レイヤーを1024×1024・白抜き（塗りは`icon.json`側の`fill`で指定）・透過背景のPNGかSVGで用意する。`canva-image-gen`等で生成する。

## Step 2. `icon.json` を組み立てる

上のテンプレートをベースに、レイヤー数・色・グループのシャドウ/透明度を埋める。`supported-platforms` はwatchOS対応が無ければそのまま流用してよい。

```bash
mkdir -p AppIcon.icon/Assets
cp layer1.png layer2.png AppIcon.icon/Assets/
# icon.json を上のテンプレートを埋めて書き出す
```

## Step 3. `actool` でコンパイル検証する

Xcodeビルドに組み込む前に、単体で壊れていないか確認する。

```bash
mkdir -p /tmp/icontest/out
xcrun actool AppIcon.icon --app-icon AppIcon \
  --compile /tmp/icontest/out \
  --output-partial-info-plist /tmp/icontest/out/info.plist \
  --target-device iphone --target-device ipad \
  --minimum-deployment-target 18.0 --platform iphoneos \
  --output-format human-readable-text
```

成功時の出力（実測、mygadgetの実icon.jsonで検証済み）:

```
/tmp/icontest/out/AppIcon60x60@2x.png       # iPhone用旧OS互換PNG
/tmp/icontest/out/AppIcon76x76@2x~ipad.png  # iPad用旧OS互換PNG
/tmp/icontest/out/Assets.car                 # iOS 26以降用の多層アイコン本体
/tmp/icontest/out/info.plist                 # Info.plistへマージする断片
```

`com.apple.actool.errors` キーが出力に含まれていたら `icon.json` のどこかが壊れている。`--output-format human-readable-text` にするとエラー箇所が読みやすい。

## Step 4. Xcodeプロジェクトへ組み込む

xcodegen運用（`sources: - path: <Target>` でターゲットフォルダをまるごと同期する構成）なら、`AppIcon.icon/` をターゲットフォルダ直下に置くだけでよい。追加で `project.yml` の `resources:` に明示登録する必要は無い（`.xcassets` と同じ扱い）。

```yaml
settings:
  base:
    ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon   # .icon の basename（拡張子抜き）と一致させる
```

旧来の `Assets.xcassets/AppIcon.appiconset` が残っている場合は削除する（1つのターゲットに複数のAppIcon定義があるとビルドが曖昧になる）。

組み込み後は実際に `xcodebuild build` を通して、ビルドログに `.icon` のコンパイルエラーが出ていないか確認する。この確認は代替不可——Step 3の単体actool検証はあくまで事前チェックで、Xcodeプロジェクトの設定（`ASSETCATALOG_COMPILER_APPICON_NAME`の一致など）まではカバーしない。

## Step 5. 目視で確認する（省略しない）

`icon.json` を手書き/スクリプト生成しただけでは、実際の見映え（レイヤーの重なり、色のコントラスト、Liquid Glassの反射のかかり方）は保証されない。ここは他工程と違い「APIやビルドが通れば完了」ではなく**視覚資産の最終検証**が要る。

```bash
# シミュレータでホーム画面表示を確認するか、
xcrun simctl launch booted <bundle-id>

# または Icon Composer.app で開いて見た目だけ確認する（編集はしなくてよい）
open -a "Icon Composer" AppIcon.icon
```

明らかに崩れている（レイヤーが真っ黒に潰れる、位置がずれている等）場合のみ `icon.json` の `translation-in-points` / `scale` / `opacity` を調整して Step 3 に戻る。Icon Composer.appのGUIでの微調整は禁止していない——スクリプト生成はあくまで「ゼロから人間がGUIで組み立てる手間を無くす」ためのもので、最後の微調整まで自動化を強制する必要は無い。

## 踏み抜いた罠

- **`ictool`のプレビュー書き出し構文はXcodeの版で壊れる。** `--export-preview`/`--render`/`--export`/`--preview`いずれもXcode 26.6 GAで`Unknown argument`（2026-07-10実機確認）。プレビュー確認はStep 5の`simctl`/GUI起動で代替する
- **1024マーケティングPNGの公式CLI書き出し手段が無い。** ストア掲載用の1024アイコンは`.icon`経由ではなく元絵から別途書き出す
- **`icon.json`は非公開フォーマット。** Apple公式ドキュメントに構造の記載が無く、このスキルの内容は実物11件からの観察に基づく。Icon Composerの版が上がるとフィールドが増減する可能性があるので、新しいXcodeで動かなくなったら実在の`.icon`（他アプリや`open -a "Icon Composer"`で一度保存したファイル）と突き合わせて差分を確認する
- **旧`Assets.xcassets/AppIcon.appiconset`と`.icon`を同一ターゲットに混在させない。** `ASSETCATALOG_COMPILER_APPICON_NAME`が指す先が曖昧になる

## 完了条件

- [ ] `AppIcon.icon/icon.json`がDESIGN.mdのレイヤー構成・配色と一致している
- [ ] `xcrun actool --compile`が`com.apple.actool.errors`無しで成功する
- [ ] `project.yml`の`ASSETCATALOG_COMPILER_APPICON_NAME`が`.icon`のbasenameと一致し、旧`AppIcon.appiconset`が残っていない
- [ ] `xcodebuild build`が通り、ビルドログにアイコン関連のエラー/警告が無い
- [ ] シミュレータのホーム画面（またはIcon Composer.appのプレビュー）で目視確認済み——レイヤーの重なり・位置・コントラストが崩れていない
