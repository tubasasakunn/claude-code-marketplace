# 第6章: 自動化 — 撮影から提出まで

app-builder パイプラインでの無人化を前提とした構成。ASC認証まわりの共通手順は asc-automation-playbook（メモリ）側を参照。

## パイプライン全体像

```
① 撮影: XCUITest / xcrun simctl で実UIをキャプチャ（6.9"相当のシミュレータ）
② 合成: 背景+キャプション+（必要なら）フレームを合成 → 1290×2796 PNG
③ 検証: 寸法・枚数・squintテスト・CHECKLIST
④ 提出: fastlane deliver または ASC API
```

## ① 撮影

- シミュレータは iPhone 17 Pro Max 等の6.9"クラスを使用（出力が1320×2868なら最終合成を1320×2868に合わせるか1290×2796へ）
- 架空データを仕込んだデモ用状態でアプリを起動（空画面を撮らない）
- ステータスバー整形: `xcrun simctl status_bar <udid> override --time "9:41" --batteryLevel 100 --cellularBars 4`
- fastlane snapshot を使えば UIテスト駆動で多言語×多画面の一括撮影が可能

## ② 合成

選択肢（上ほどapp-builder向き）:

1. **スクリプト合成（推奨）**: Python Pillow / ImageMagick で YAML/JSON 駆動の合成。文言・フォントサイズを設定ファイルで一元管理すればコード修正なしでコピー変更できる（個人開発の実績あり構成）。フォントはヒラギノ角ゴ（macOS同梱）W6/W3
2. fastlane frameit: フレーム+タイトル合成の定番。`Framefile.json` で背景・タイトル指定（ImageMagick依存）
3. Figmaテンプレート: 手動調整したいとき（無料コミュニティテンプレート多数）

合成時の検証: 出力寸法が許容値（01章）と完全一致すること。1pxでもずれると deliver が別デバイス扱い or 拒否する。

## ④-a fastlane deliver

```ruby
deliver(
  api_key_path: "fastlane/asc_api_key.json",
  skip_binary_upload: true,
  skip_metadata: true,
  overwrite_screenshots: true,   # 確認プロンプトなしで既存を置き換え
  screenshots_path: "fastlane/screenshots"  # ja-JP/ en-US/ 配下に配置
)
```

- 画像の**解像度からデバイスクラスを自動判定**。曖昧な場合のみファイル名でヒント（例: `iPad Pro (12.9-inch) (3rd generation)` を含める）
- 認証は ASC API Key（無人実行可）

## ④-b ASC API 直叩き（fastlaneを使わない場合）

リソース階層: `AppStoreVersionLocalization` → `AppScreenshotSet`（displayType×locale） → `AppScreenshot`

```
1. POST /v1/appScreenshotSets   { screenshotDisplayType: "APP_IPHONE_67", locale }
2. POST /v1/appScreenshots      { fileName, fileSize, set関連付け } → uploadOperations が返る
3. uploadOperations の指示どおり画像バイナリをチャンク分割 HTTP PUT
4. PATCH /v1/appScreenshots/{id}  { uploaded: true, sourceFileChecksum: <MD5> } でコミット
```

- displayType は歴史的内部名: 6.9" = **`APP_IPHONE_67`**、13" iPad = **`APP_IPAD_PRO_3GEN_129`**（新名称ではない点に注意）
- 削除は DELETE /v1/appScreenshots/{id}、順序は set の appScreenshots 関係を PATCH

## 運用メモ

- 初回提出はバージョンに紐づけて提出 → 承認後の差し替えは新バージョン or PPO（01章）
- 多言語展開: 合成スクリプトの文言辞書を言語別に持てば、撮影1回で全言語分を生成できる（UIも翻訳されている場合は言語別に撮影）
- 生成物は `Idea/ddd_アプリ名/screenshots/<locale>/` に置き、SCREENSHOTS.md から参照する
