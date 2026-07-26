---
name: release-assets
description: App Store 提出用のリリース素材一式（メタデータ .txt とストア画像）を release/<version>/ に用意・更新する。新バージョンの準備、ストア文言の変更、material/ スクショ更新後の画像再生成に使う。
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch
---

# リリース素材の用意（メタデータ + ストア画像）

`release/<version>/` に App Store Connect へ転記する素材一式を揃える。
正本の構成・ASO 方針・文字数上限は `release/README.md`。ここは手順だけ。
アプリ固有値は `appstore.config.json`。

## 0. バージョンディレクトリ

- ディレクトリ名は pbxproj の `MARKETING_VERSION` と**完全一致**させる
  （`grep MARKETING_VERSION <xcodeproj>/project.pbxproj | sort -u` で確認）。
- 新バージョンは前バージョンをコピーして開始する：`cp -r release/<prev> release/<new>`。

## 1. メタデータ（.txt）

1. 変更対象を編集する。フィールドと上限：
   app_name 30 / subtitle 30 / promotional_text 170 / description 4000 /
   keywords 100（半角カンマ区切り・空白なし）/ whats_new 4000。
2. ASO の原則（要点のみ。調査からの文言・画像設計は `/aso` スキルが正本）：
   - **同じ語をタイトル・サブタイトル・キーワード欄で重複させない**
     （Apple はフィールド横断で語を組み合わせて索引する）。
   - 競合ブランド名・価格表現（「無料」等）をアプリ名・サブタイトルに入れない
     （App Review ガイドライン 2.3.7）。
   - 訴求の軸はアプリのコンセプトに整合させる。
3. 検証（編集したら必ず）：

   ```bash
   python3 scripts/check_release_metadata.py <version>
   ```

   `PASS` 以外ならコミットしない。

## 2. ストア画像（img/）

1. 画面が変わっている場合は、まず `material/` のスクショを撮り直す
   （取得手順は `material/README.md`。動画・画像領域は #00FF00 クロマキーが前提）。
2. 生成：

   ```bash
   pip3 install Pillow numpy   # 初回のみ
   python3 scripts/make_store_images.py
   ```

   - スライドの構成・コピーは `scripts/store_slides.json`、ブランド色・ワードマークは
     `appstore.config.json` の `brand` から読む。
3. 生成後は**全枚数を Read で目視確認**する。チェック観点：
   - サイズが正しいシェルフ寸法（iPhone 6.9": 2868×1320 / iPad 13": 2752×2064）で
     1px もずれていない。不安なら App Store Connect の screenshot specifications を検索。
   - 半透明 UI（チップ・バー）に**緑かぶり**が残っていないか（デスピルは `key_out_green`）。
   - 見出し・サブコピーとモックアップが**重なっていない**か。
   - 文言が現行のメタデータ（subtitle / description）と矛盾していないか。
   - 並びは「コンセプト → コア操作 → 任意入力 → 振り返り → プライバシー」。
4. スライドの構成・コピーを変えるときは `scripts/store_slides.json` を編集する。
   新しいダミー映像が要るなら `material/footage/` に画像を置く（プロンプトは
   `material/footage/PROMPTS.md`）か、`make_store_images.py` の `scene_*` を足す。

## 3. 仕上げ

1. `release/README.md` の表・手順が現状と食い違っていないか確認し、ずれていれば直す。
2. 生成画像をユーザへ送って見た目の承認を得る。
3. main へマージされると CI（`.github/workflows/appstore-metadata.yml`）が
   App Store Connect へ自動反映する。名前の対応は `scripts/sync_fastlane_metadata.py`
   が正本（release/ にフィールドを足すときはここの MAPPING も更新する）。

## 4. App Store Connect 自動反映（CI）の知識

経路：main へ `release/**` の変更が push → workflow → 文字数チェック →
`sync_fastlane_metadata.py` → `fastlane ios push_metadata`。
バイナリと審査提出は扱わない。必要な Secrets・初回セットアップ・CI で踏んだ罠の
全リストは `release/README.md` と `SETUP.md` を正本とする。要点だけ：

- **未設定の Secrets は env 上「空文字列」**（nil でない）。Ruby では truthy なので
  Fastfile の `presence` で弾く。
- **fastlane#21272**：審査情報未保存だと deliver が `No data` で落ちる。
  `app_review_information` を必ず非空で渡す（実装済み・外さない）。
- **電話番号は E.164 のみ**（Fastfile が +81 へ正規化）。
- **年齢制限（rating.json）は全設問必須**（2025 年新設問を含む）。欠けると 409。
- **「アプリのプライバシー」だけは CI 不可**。`app_privacy.md` の回答シートで手動回答。

## 罠

- `1.0.0` のような 3 桁表記にしない。pbxproj の MARKETING_VERSION と完全一致。
- keywords は読点「、」や全角カンマ・空白が混ざりやすい。半角カンマのみで区切る。
- `material/` のスクショ更新と `img/` の再生成はセット。片方だけ更新すると
  ストア画像が旧 UI のまま残る。
