# MATERIALS — 素材カタログ & 「素材をどこに載せるか」spec レシピ

ユーザーは大量の実素材（実アプリ画面・footage写真・アイコン）を用意済み。**表紙含め全スライドに必ず実素材を敷く**のが
このスキルの最重要方針（[[DESIGN_SPEC]] §0）。本書は各アプリの在庫と、エンジン別にどの spec フィールドで素材が載るかをまとめた正本。

> 大前提：spec は `gen.py --app <app> <spec.json> <outdir>` に渡す。slides はそのアプリの `build_posts.py` が読む形。
> `gen.py` は repo を汚さない（フォントは /tmp、素材は参照のみ）。tone は `gen.py` が footage 解決を拡張済みで **bg/footage にrepo相対パスを渡せる**。

---

## 0. 共通：ルート素材バンク（cover/photo 背景の主力）

`material/`（各 repo の material とは別物）。`index.json` = `[{name, prompt, tags[]}]`、実体は `images/<name>.jpg`。
**縦長**＋アプリのテーマタグで引いて、ヒットした素材を **`material/images/<name>.jpg`（リポジトリルート相対）** の形で cover/photo の `bg` に渡す。
（パスはリポジトリルート基準でエンジンが解決＝CWD非依存・自己完結。絶対パスも可だが repo 相対を推奨。）

```bash
python3 - <<'PY'
import json; b="material"
want={"hioto","縦長"}      # tone:{"tone","縦長"} / anki:{"anki","縦長"} / connect:{"カレンダー","縦長"}
for e in [x for x in json.load(open(b+"/index.json")) if want<=set(x["tags"])][:20]:
    print(b+"/images/"+e["name"]+".jpg", e["tags"])
PY
```

| アプリ | バンク検索タグ | 注意 |
|---|---|---|
| hioto | `hioto`(48)/`日記`/`film`/`night` + `縦長` | **顔・人物入りを避ける**（プライバシー軸） |
| tone | `tone`(72)/`メンズ`(56) + `縦長` | 美容トーン。くすみ/大人。人物可 |
| anki | 専用タグ無し → `flatlay`/`interior`/`部屋`/`日常`/`小物` + `縦長` | 机・教材・スキマ時間の空気感。`勉強`/`anki`タグは0件 |
| connect | 専用タグ無し → `interior`/`部屋`/`日常`/`flatlay` + `縦長` | 手帳/机まわり。ミント基調と喧嘩しない素材。`カレンダー`タグは0件の場合あり |

> タグは実在を必ず確認（`index.json` を上のスニペットで grep）。専用タグが無いアプリ（anki/connect）は汎用の暮らし/机系タグで代用する。
> 人物NGは hioto のみ。tone は人物（メイクシーン）むしろ歓迎。

---

## 1. エンジン別 spec レシピ（素材を載せる場所）

> **spec.json の全体構造**（gen.py が読む）：
> ```json
> { "id": "<post id>", "accent": "<アプリのaccent名>", "template": "standard",
>   "slides": [ {…各スライド…} ],
>   "copy": { "tiktok": {"title":"…","body":"…","hashtags":["#…",…]},
>             "lemon8": {"title":"…","body":"…","hashtags":["#…",…]} } }
> ```
> **`copy` は必須**：投稿キャプション(title/body/hashtags)はここから `index.json` に書かれる。**省略すると index.json の文言が空**になり投稿時に手書きが要る（gen.py が空なら警告を出す）。TikTok 3〜5タグ/90字、Lemon8 5〜8タグ。

> **★スライド仕様（最新の standard 雛形・全アプリ共通／chrome無し・太い丸/角ゴシック）**：
> - 見出しフォントは `brand.head`（material/manifest）＝maru(丸)/kaku(角)/antique/mincho。アプリ毎に設定済（明朝の"AIっぽさ"回避）。
> - `cover` variant：`editorial`(断定)/`card`(**写真を暗くせずクリーンな角丸パネル＝暗幕に頼らない**)/`question`/`quote`/`split`/`versus`/`numeric`/**`giant`**(巨大数字＝`big`+`unit`+`kicker`/`teaser`)/**`magazine`**(雑誌の柱＝`headline`+`en`+`issue`)。フィールドは従来通り＋`bg`必須・`kicker`任意。**暗幕＋文字の一辺倒を避け `card` 等も混ぜる**。
> - ★**`dark`（cover/photo 共通・任意）**：背景写真の暗さ（既定 cover 0.42–0.56 / photo 0.46）。photo を連投して時間帯を見せるときは 0.28→0.52 の階調を与える（一律だと朝も夜も同じ暗さになって変化が消える）。
> - ★**新スライド型（2026-07-27）**
>   - `grid`：`title` + `cells`[2–4]（`{icon,label,text}`）。**1セル＝ラベル1語＋本文1行**に絞る。
>   - `callout`：`shot`(+`footage`) + `title`(+`sub`) + `spot`[x,y]（端末内の相対座標）+ `spot_r` + `spot_label`。**強調は1点のみ受け付ける**。
>   - `scrap`：`prints`[{`src`,`at`[x,y],`w`,`rot`,`ratio`,`memo`}] + `title`/`memo` + `mark`(`circle`|`band`)。手描きは**1枚に1つだけ**。
>   - `panorama`：`pano`[i,n] + `stops`[accent名…] + `frames`[{`src`,`at`(全体幅比),`w`,`ratio`,`rot`,`at_label`}] + `rail`/`rail_y` + `caption`。
>     ⚠️ **全スライドで `stops`/`frames` を同一に**（1枚の絵を切り出すため）。コマは境界（i/n）の上に置くと隣へまたがる。
> - ★**アプリ紹介の定番型（2026-07-27 追加）**
>   - `rank`：`rank`(順位) + `label` + `sub` + `shot`(+`footage`) / `bg`。**1位を最後に**。位置は全枚数で固定。
>   - `table`：`title` + `cols`[2] + `rows`[{`label`,`a`,`b`}] + `mark_col`(0|1)。⚠️ 他社比較は不可（景表法）。
>   - `bleed`：`num` + `title` + `shot`(+`footage`) + `card_label` + `card`。端末枠なしの全面ブリード＋白カード。
>   - `spec`：`num` + `name` + `icon`(SVG名) + `specs`[{`k`,`v`}]×3 + `caption`。**全枚数で同じ様式**にする。
>   - `steps`：`title` + `steps`[{`label`,`text`}]（3〜4手）。
>   - `stats`：`title` + `stats`[{`n`,`unit`,`label`}]（2〜3個） + `note`。仕様から言い切れる数だけ。
>   - `recap`：`title` + `items`[]（5〜7個）。**最終スライドの手前**に置く。
> - ★**`layout`（写真×文字の別解・2026-07-27）**：`mode` で8通り
>   （`margin`/`band`/`frame`/`light`/`duotone`/`cutout`/`stripe`/`edge`）。
>   `bg` + `title` + `sub` + `kicker` + `hl` + `big`(表紙サイズ) + `at`(edge の上下) + `on_dark`(edge で白文字) + `dark`(cutout の濃さ)。
>   **暗幕（黒＋白文字）を1投稿で2枚までに抑えるための型**。→ [[LAYOUTS]] §6。
> - `photo`：`bg`+`caption`(+`note`)。`\n`改行可・各行短く。
> - `shot`：`shot`(実画面)+`title`(+`sub`,`footage`,`bg`)。見出し特大＋端末見切れ。
> - `info`：`title`+`bullets[]`。**bullets は文字列 or `{"icon":"<SVG名>","text":"…"}`**（アイコンは `engine/assets/svg/index.json` からタグ検索。例 concept-camera-shutter / concept-trend-up-graph / concept-clock-time / concept-checklist-tasks）。**項目は3〜4個まで・短文・余白大**。`ポイント`等のラベルや小さい文字は書かない。
> - `cta`：**検索バー＋大アイコン＋「今すぐダウンロード」の3要素だけ**（小見出し・ラベルなし）。`cta_foot`で末尾文言を変更可（既定=今すぐダウンロード）。`headline`/`sub`は不要。

> ⚠️**accent 名はアプリごとに違う**（不一致だと KeyError でクラッシュ）：
> hioto / tone = `morning/forenoon/afternoon/evening/night/midnight`、anki = `blue/indigo/purple/green/orange/red/teal`、connect = それ＋`mint`。
> spec の `accent`（トップ or 各slide）は必ずそのアプリのキーから選ぶ。

### A. hioto系（**hioto / anki / connect**）= build_posts: `SIZES`+`RENDERERS(spec,W,H)`
スライド型：`cover`(6 variant) / `photo` / `shot` / `info` / `cta`。

- **cover**：`{"type":"cover","variant":"editorial|question|quote|split|versus|numeric","accent":"...","bg":"<repo相対パス>", ...}`
  - `bg` = ルートバンクの jpg repo相対パス（推奨）。hioto は **bg 必須**。anki/connect は bg 省略で手続き背景（灰色）→ **省略禁止、必ず bg を渡す**。
  - hioto は FT キー（`"night"`等）も可。variant 別の本文フィールド：editorial=`headline`(+`hl`強調語,`kicker`)、question=`question`(+`answer`は表紙で伏せる)、quote=`quote`、split=`before`/`after`、versus=`a`/`b`/`question`、numeric=`big`/`teaser`/`kicker`。
- **photo**：`{"type":"photo","bg":"<repo相対パス>","caption":"...","note":"..."}`（`caption`/`note` は `\n` で改行可・各行短く＝長文は見切れる。1行20字目安） — `bg` 必須級。背景に素材、下スクリムに白文字。
- **shot**：`{"type":"shot","shot":"<material内の実画面.png>","footage":"<FTキー/repo相対パス>","title":"...","sub":"..."}`
  - `shot` = そのアプリの実画面。クロマキー緑があれば `footage` で世界観を差替（hioto系は `key_out_green`）。**実画面を毎回複数枚**入れる。
- **info / cta**：型ベースのグラフィック（素材不要）。`info`=`title`+`bullets[]`(+`kicker`)、`cta`=`headline`+`sub`。

### B. swiftbase（**tone** / mensmakeupadvisor）= build_posts: `PLATFORMS`+`RENDERERS(size,spec,accent,idx,total)`
スライド型：`cover` / `photo` / `shot` / `info` / `cta`（cover variant なし＝単一レイアウト）。

- **cover**：`{"type":"cover","bg":"<footage名 or repo相対パス>","kicker":"...","headline":"...\n..."}`
  - footage/ が**空**なので名前指定だとベタ赤に落ちる。→ **`bg` にrepo相対パス**（ルートバンク tone/メンズ、または自前 `material/05_diagnosis_top.png` 等）を渡す（`gen.py` 拡張で有効）。
- **photo**：`{"type":"photo","bg":"<repo相対パス>","caption":"...","note":"..."}`
- **shot**：`{"type":"shot","shot":"<material/直下の実画面.png>","footage":"<名/repo相対パス>","title":"...","sub":"..."}`
- **info / cta**：`info`=`title`+`bullets[]`、`cta`=`headline`+`sub`(+`store`)。

> 補足：tone の cover/photo 背景にルートバンク jpg を入れると一気に「写真の上に文字」の格になる。診断シーンを見せたい時は自前 `material/05_diagnosis_top.png` 等を bg にしてもよい（暗くなりすぎたら photo より shot 推奨）。

---

## 2. アプリ別 素材在庫

### hioto（engine=hioto / accent: morning/forenoon/afternoon/evening/night/midnight・ブランド h サーモン）
- 実画面（`material/`直下）：`app-lock.png` `calendar.png` `calendar-month-picker.png` `camera.png` `clip-review.png` `month-insights.png` `onboarding-{welcome,start,capture,keep,privacy}.png` `shorts-{feed,edit,share-sheet}.png` `settings.png`（計18）
- footage（`material/footage/`・**実体6枚**）：FTキー `sunset`=shorts.jpg / `morning`=camera.jpg / `coffee`=review.jpg / `park`=calendar.jpg / `night`=night.jpg / `desk`=desk.jpg
- 活用度：**高**。cover は FT or バンク、shot は実画面＋footage差替が完成形。顔NG。

### tone / mensmakeupadvisor（engine=swiftbase / accent: morning/forenoon/afternoon/evening/night/midnight・赤〜温色基調）
- 実画面（`material/`直下・各2MB級）：`01_splash`〜`17_progress.png`（splash/onboarding/capture/analyzing/diagnosis_top/diagnosis_mesh/diagnosis_proportions/tutorial/studio/studio_arrange_compare/studio_arrange_color/mirror/save_title_sheet/completion/home/archive/progress）＋`app_icon_1024.png`
- footage：**空（PROMPTS.md のみ）** → cover/photo は **bg にrepo相対パス**で素材を入れる（最優先改善）。
- 活用度：**低→要改善**。診断系の実画面（05_diagnosis_top, 09_studio, 06_mesh）が強い証拠。knowledge=`tone_posts/KNOWLEDGE.md`。

### anki / createQuestionApple（engine=hioto系 / accent: blue/indigo/purple/green/orange/red/teal・勉強・信頼トーン）
- 実画面（`material/screenshots/`・26枚）：`01_onboarding_*`〜`07`、`08_login`、`10_home_populated`/`11_home_empty`、`12_subject_detail`、`13_question_list`、`14_question_edit`、`15_subject_creation`、`17_account`、`20_study_question`/`21_study_answer`/`22_study_result`、`30〜34_qc_*`（撮影→生成）、`40_notice`/`41_notification_permission`
- 教材モック（`material/assets/textbooks/`・TBキー6）：`legal/diagram/vocab/math/history/bullet`
- footage：なし → cover/photo は **bg にルートバンク jpg**（机/教材）。shot は実画面（撮影=31_qc_image_processing、解く=20_study_question、結果=22_study_result が鉄板）。
- 活用度：**中**。バンク背景を入れれば表紙が一気に良くなる。

### connect / connectcalendar（engine=hioto系 / accent: blue/indigo/purple/green/orange/red/teal/**mint**・ミント #2DD4BF 基調）
- 実画面（`material/`直下・JP名 多数）：`01_カレンダー_月表示`〜`29_オンボーディング_*`（月/日/リスト表示・タスク・シフト入力/確認・一括入力・写真ソース選択 等）
- 実画面（`material/screenshots/`・英名12枚）：`01_calendar_month` `03_calendar_list` `12_event_detail` `13_search` `16_task_add` `17_event_add` `18_recurring` `19_bulk_input` `24_shift_confirm` `25_shift_detail` `33_photo_camera` `37_photo_analysis`
- footage：なし → cover/photo は **bg にルートバンク jpg**（手帳/カレンダー/シフト）。shot は撮影=33_photo_camera、解析=37_photo_analysis、月表示=01_calendar_month が鉄板。
- 活用度：**低→要改善**。bg 省略の手続き背景（灰色）をやめてバンク背景に。

---

## 3. footage ギャップと埋め方（任意・段階的）

| アプリ | footage | 当面の手当て | 本格対応（任意） |
|---|---|---|---|
| hioto | 6枚あり | そのまま | 追加シーンを `/canva-image-gen` 等で増やす |
| tone | **空** | cover/photo の `bg` に**repo相対パス**（バンク or 自前実画面） | `material/footage/` に診断シーン（鏡/スタジオ/スウォッチ）数枚を生成 |
| anki | なし | cover/photo の `bg` にバンク jpg | `material/footage/` に勉強机/教材シーン |
| connect | なし | cover/photo の `bg` にバンク jpg | `material/footage/` に手帳/カレンダー操作シーン＋`FT`辞書定義 |

> footage を増やすと shot のクロマキー差替で「実画面＋世界観」の最上位表現ができる。ただし**まずは bg repo相対パスで全アプリの表紙を実素材化**するのが最小コスト・最大効果。

---

## 4. 最終確認（素材まわり）
- [ ] 表紙に `bg`（実素材）が入っているか（全アプリ・**省略しない**）
- [ ] shot スライドが実画面で複数枚あるか
- [ ] tone は cover/photo bg を**repo相対パス**で指定したか（footage名だとベタ赤）
- [ ] hioto は顔/人物入り素材を避けたか
- [ ] `qa.py --spec` が NO-MATERIAL を出していないか（[[SKILL]] の自己レビュー）

---

## 6. SVGアセットバンク（汎用・リッチ／ルート共通）

`engine/assets/svg/` に汎用SVGを多数用意（CTA/装飾/アイコン/バッジ/UI部品/矢印）。**台帳は `engine/assets/svg/index.json`**
（`{name, file, description, tags[], mode, category}`）＝名前・概要・タグで検索して選ぶ。

- **mode=`mono`**：単色（tint）。`paste_svg(canvas, name, x, y, h, color)` に**ブランド色**を渡す（accent/ink等）。
- **mode=`multi`**：自前のリッチ配色（影レイヤ付き）。`paste_svg(canvas, name, x, y, h, None)` と **color=None** で自前色のまま描画。
- `B.has_svg(name)` で存在確認、`B.svg_image(name, color_or_None, height)` でRGBA取得。

```python
# 例: tag で探す
import json; idx=json.load(open("engine/assets/svg/index.json"))
hits=[e for e in idx if "検索" in e["tags"]]          # search-box / magnifier / search …
# 多色アセットはそのまま、単色はブランド色で
B.paste_svg(canvas, "search-box", x, y, 180, None)     # multi=自前色
B.paste_svg(canvas, "magnifier", x, y, 60, brand.ink)  # mono=tint
```

代表例：CTA=`search-box`/`magnifier`/`install-badge`/`get-pill-button`/`phone-download`/`bookmark-save`/`follow-plus`、
バッジ=`star-rating`系/メダル/リボン/トロフィー/`verified`、UI=`search-bar`/吹き出し/`tag-label`/`number-badge`/トグル/進捗ドット、
装飾=`sparkle`/`star`/ハイライト帯/コーナー枠、アイコン=カメラ/時計/電球/グラフ/チェックリスト/ターゲット等。
新規追加時は `index.json` に追記（描画エンジンの制約＝グラデ/transform/text/ellipse不可・穴は塗りで作らない、は [[engine/brand.py]] svg_image 準拠）。
