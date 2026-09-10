---
name: 05_release_assets
description: App Store のストア文言（アプリ名・サブタイトル・キーワード・説明文）とストアスクリーンショットを release/<version>/ に用意します。文字数チェックを通し、GitHub Actions でメタデータを App Store Connect に反映するところまで行います。審査提出の直前に実行してください。
---

# ストア文言とスクリーンショット (05_release_assets)

## このスキルの位置

```
04_build_front → [05_release_assets] → 06_submit_review
```

`03_implement_app` でスクリーンショットの素材（`material/screenshot_dev_*.png`）が撮れている前提。

## 何をするか

`release/<version>/` はテンプレートのプレースホルダのまま放置されがち。
**`check_release_metadata.py` はプレースホルダのままでも PASS する**ので、通っても安心しないこと。

| ファイル | 制限 | 内容 |
|---|---|---|
| `app_name.txt` | 30字 | **ASC のアプリレコード名と一致させる**（`01` で決めた名前） |
| `subtitle.txt` | 30字 | 別の検索語を担う |
| `keywords.txt` | 100字 | カンマ区切り。**アプリ名・サブタイトルと重複させない** |
| `description.txt` | 4000字 | 検索順位には効かないがコンバージョンに効く |
| `promotional_text.txt` | 170字 | 審査なしで差し替えられる枠 |
| `whats_new.txt` | 4000字 | 初回は「初回リリース」の文 |
| `copyright.txt` | — | `2026 tubasasakun` 形式 |
| `marketing_url.txt` / `support_url.txt` / `privacy_url.txt` | — | `04_build_front` で設定済み |
| `primary_category.txt` / `secondary_category.txt` | — | `PRODUCTIVITY` `LIFESTYLE` などの定数 |
| `rating.json` | — | 年齢レーティング。完全オフラインの無害アプリなら全て `NONE` / `false` |
| `app_privacy.md` | — | プライバシー回答の根拠メモ（`02` で API 宣言済み） |
| `img/` | — | ストアスクリーンショット |

## Step 1. 文言を書く

`CONCEPT.md` の ASO 仮案を土台に磨く。

### 審査リスクのある表現を避ける

- **医療・セラピー・メンタルヘルスの効能を謳わない。** 「気分が楽になる」程度でも危うい
- 機能の事実ベースで書く（「記録を手放す」「待ちを保留する」）
- 競合アプリ名・商標をキーワードに入れない

### 文字数を検証する

```bash
python3 scripts/check_release_metadata.py 1.0
```

`PASS` を確認する。ただし**中身がプレースホルダでも PASS する**ので、目視で読むこと。

```bash
head -c 200 release/1.0/description.txt
grep -l "MyApp\|<.*>" release/1.0/*.txt   # プレースホルダの残骸を探す
```

## Step 2. スクリーンショットを用意する

**詳細は `screenshot-crafting` スキルを読むこと。** ここでは配置と検証だけ扱う。

### サイズは2通りある。どちらも 6.9インチとして有効

| 方針 | サイズ | 前例 |
|---|---|---|
| 素の画面キャプチャをそのまま出す | **1320×2868**（縦） | nagasu |
| 横長キャンバスにコピーを載せて合成する | **2868×1320**（横） | hioto、`scripts/make_store_images.py` |

**1枚も混ぜてはいけない。** アプリ内で統一する。`make_store_images.py` は横向き前提で書かれている
（`CANVAS_DEFAULT = (2868, 1320)`）。縦のまま出すなら、このスクリプトは使わない。

```bash
sips -g pixelWidth -g pixelHeight material/screenshot_dev_1.png
```

### 素材は必ず全部「目で見る」★ファイル名を信用しない

```bash
# Read ツールで1枚ずつ開いて確認する
```

実際に起きたこと: ファイル名が `screenshot_dev_1_waiting.png` なのに中身はオンボーディング画面だった。
**別アプリの文言が写り込んでいることもある**（シミュレータに前のアプリが残っていた等）。

見るべき点:

- **他アプリの名前・画面が写っていないか**
- **デモデータに医療・健康・診断を連想させる文言がないか**（`03_implement_app` の注意点）
- 実在の企業名・人名・商標

### 配置する

ASO の定石順に4〜6枚選び、`release/1.0/img/` に連番で置く。

```
01_onboarding.png   コンセプトが一目で分かる
02_home.png         コア操作
03_ritual.png       シグネチャ演出
04_archive.png      蓄積・振り返り
05_settings.png     プライバシー・安心感
```

### 合成する場合の注意

`make_store_images.py` は `appstore.config.json` の `brand` の色を使う。
**プレースホルダのままだと、実際のアプリと色が違うマーケ画像ができる。** 先に実装の `Tokens.swift` と突き合わせること。

自作のデバイスフレーム（ベゼルやボタンを描いたもの）は `screenshot-crafting` のチェックリストに反する。
**迷ったらフレーム無し**で、画面キャプチャの上にコピー帯を載せるだけにする。

### 使える素材とスキル（common/marketing）

`~/workspace/sns-marketing-workspace/` は submodule。ストア画像と SNS 投稿の資産が入っている。

```bash
git submodule update --init --remote common/marketing
```

| 場所 | 中身 |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/skills/carousel-craft/` | カルーセル画像の作り方スキル。**装飾 SVG が 87 点**（`engine/assets/svg/`） |
| `target/<app>/material/` | アプリ固有の素材（過去アプリの実例が読める） |

ストア画像の装飾に SVG を流用でき、リリース後の SNS 投稿（TikTok / Lemon8）もここで作る。

## Step 3. fastlane のレイアウトへ同期する

```bash
python3 scripts/sync_fastlane_metadata.py
```

`synced release/1.0 -> fastlane/ (N texts, M app-info texts, K screenshots)` と出る。

`.xcodeproj` が無い環境（CI）でも動くことを確認する。

```bash
mv <App>.xcodeproj /tmp/_x && python3 scripts/sync_fastlane_metadata.py; mv /tmp/_x <App>.xcodeproj
```

`FileNotFoundError` なら `00_setup_repo` の Step 4-2 が済んでいない。

## Step 4. ASC へ反映する

`main` に push すると `appstore-metadata.yml` が走る（`release/**` の変更で発火）。

```bash
git add release/ fastlane/
git commit -m "release/1.0: ストア文言とスクリーンショットを実データに"
git push origin main

gh run watch $(gh run list --workflow=appstore-metadata.yml --limit 1 --json databaseId -q '.[0].databaseId') --exit-status
```

## Step 5. 反映を確認する

**文言は2つのリソースに分かれている。** ここを取り違えると、正しく入っているのに「入っていない」と誤診する。

| 項目 | どこにあるか |
|---|---|
| `description` / `keywords` / `promotionalText` / `whatsNew` / URL類 | `appStoreVersionLocalizations` |
| **`name`（アプリ名）/ `subtitle` / `privacyPolicyUrl`** | **`appInfoLocalizations`**（`/v1/apps/{id}/appInfos` 経由） |

```bash
export ASC_API=${CLAUDE_PLUGIN_ROOT}/scripts/asc_api.js
APP_ID=<appId>

# --- 版に紐づく文言
VID=$(node $ASC_API GET "/v1/apps/$APP_ID/appStoreVersions?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")

node $ASC_API GET "/v1/appStoreVersions/$VID/appStoreVersionLocalizations?limit=5" | tail -n +2 | python3 -c "
import json,sys
for l in json.load(sys.stdin)['data']:
    a=l['attributes']
    print(l['locale'] if 'locale' in l else a['locale'], '| desc:', len(a.get('description') or ''), '| kw:', (a.get('keywords') or '')[:40])
    print(' id:', l['id'])
"

# --- アプリ名・サブタイトル（別リソース）
AIID=$(node $ASC_API GET "/v1/apps/$APP_ID/appInfos?limit=1" | tail -n +2 | python3 -c "
import json,sys; print(json.load(sys.stdin)['data'][0]['id'])")
node $ASC_API GET "/v1/appInfos/$AIID/appInfoLocalizations?limit=5" | tail -n +2 | python3 -c "
import json,sys
for l in json.load(sys.stdin)['data']:
    a=l['attributes']; print(a['locale'], '| name:', a.get('name'), '| subtitle:', a.get('subtitle'))
"

# --- スクリーンショットの枚数と処理状態（LID は上で出た版ローカライズの id）
node $ASC_API GET "/v1/appStoreVersionLocalizations/<LID>/appScreenshotSets?include=appScreenshots" | tail -n +2 | python3 -c "
import json,sys
d=json.load(sys.stdin)
shots=[i for i in d.get('included',[]) if i['type']=='appScreenshots']
print('sets:', len(d['data']), '| shots:', len(shots))
for s in shots: print(' ', s['attributes'].get('fileName'), s['attributes'].get('assetDeliveryState',{}).get('state'))
"
```

> **初回リリースでは `whatsNew` が空でも正常。** fastlane のログに
> `Skipping 'release_notes'... this is the first version of the app` と出る（Apple の仕様）。

### 重複スクリーンショットの掃除 ★必ず起きると思って確認する

**発生機序**: `deliver` はアップロード直後に「本当に上がったか」を確認するが、
この確認が Apple 側の反映より速く走って「無い」と誤判定し、**全枚数を再アップロードする**。
ログに `Failed to upload all screenshots... Tries remaining: 4` と出ていたら、これが起きている。

結果、枚数がちょうど倍（5枚 → 10枚）になる。**同じファイル名のペアの、後から入った方を消す。**

```bash
# 一覧して重複を確認（同じ fileName が2つずつ並ぶ）
node $ASC_API GET "/v1/appStoreVersionLocalizations/<LID>/appScreenshotSets?include=appScreenshots" | tail -n +2 | python3 -c "
import json,sys
shots=[i for i in json.load(sys.stdin).get('included',[]) if i['type']=='appScreenshots']
seen={}
for s in shots:
    n=s['attributes']['fileName']
    seen.setdefault(n, []).append(s['id'])
for n, ids in seen.items():
    print(n, ids, '<- 重複' if len(ids)>1 else '')
"

# 各ペアの2つ目を消す
node $ASC_API DELETE "/v1/appScreenshots/<2つ目のid>"
```

消したあと、残った枚数と `assetDeliveryState: COMPLETE` を再確認する。

## 完了条件

- [ ] `check_release_metadata.py` が PASS
- [ ] プレースホルダ（`MyApp`、`<...>`）が1つも残っていない
- [ ] `app_name.txt` が ASC のアプリレコード名と一致
- [ ] `release/1.0/img/` に4〜6枚、全て 1320×2868
- [ ] `appstore-metadata.yml` の run が緑
- [ ] ASC 側で localization の description / keywords が入り、スクショが `COMPLETE` で重複なし

## 次のスキル

`06_submit_review` — production にマージして審査に出す。
