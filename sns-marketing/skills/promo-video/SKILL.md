---
name: promo-video
description: target/<app> の宣伝動画（無音・縦9:16・~30秒・かっこいい系）を作る。carousel-craft のブランド描画ツールキットを流用し、PIL でフレームを1枚ずつ合成→ffmpeg でエンコード。文言/素材/アクセントは material/manifest.json と spec(JSON) から。SNS の "動画" 宣伝が欲しいとき（カルーセル静止画ではなく動く広告）に使う。Hioto/Tone など apps.json 登録のどのアプリでも。
allowed-tools: Bash, Read, Write, Edit, Glob
---

# promo-video — 宣伝動画の作り方（正本）

target/<app> の **無音・縦9:16・~30秒** の宣伝動画を作る。静止画カルーセルは `carousel-craft`、
**動く広告はここ**。デザインの正本は carousel-craft（`engine/brand.py`）で、このスキルは
その描画ツールキットに **時間軸を与える層**＝フレームを 1 枚ずつ合成し ffmpeg でエンコードする。

> 大原則は carousel-craft と同じ：**共通はルート / アプリ固有は material/manifest.json**。
> 色・ワードマーク・モチーフ・素材・アクセント名は manifest から来る。app 固有を一切ハードコードしない。

---

## 1. 何を作るか / 設計思想

- **PIL でフレーム生成 → ffmpeg でエンコード**。ブラウザや外部サービスに依存しない＝フレーム精度で
  動きを完全制御でき、carousel-craft の `brand.py`（フィルム枠ティック・三層タイポ・SVG モチーフの
  ラスタライズ・グレイン・クロマキー緑の差し替え・iPhone モック）をそのまま動かせる。
- **素材ファースト**（carousel-craft と同じ）：全シーンに実素材を敷く。footage（暖色フィルム）＋実アプリ画面。
  緑ビューファインダ(#00FF00)は `key_out_green` で footage に差し替え＝「実際に撮っている」絵にする。
- **エディトリアルな動き**：左寄せ見出し（manifest の head フォント）＋ DM Mono ラベル＋アクセント罫。
  テキストは rise+fade+blur で立ち上げ、中央寄せ・白カード・一律影は使わない（carousel-craft の規範を継ぐ）。
- 1 動画 = storyboard spec(JSON)。**シーン型を組み合わせるだけ**で新しい動画になる。

---

## 2. 構成（どこに何があるか）

```
promo-video/
  SKILL.md              ← この正本
  engine/video.py       ← 再利用ツールキット（easing/ken burns/anim text/assemble/encode/QA）
  templates/standard.py ← シーン型カタログ（cold_open/hook/day_cycle/app_magic/proof_gallery/privacy/cta）
  templates/<app>.json  ← その app の storyboard spec（hioto.json が実例＝納品済みの動画）
  scripts/render.py     ← CLI：spec → mp4（生＋共有サイズ）／--probe で代表フレーム
  scripts/qa.py         ← sheet（コンタクトシート）/ strip（連続フレーム）/ check（尺・解像度）
```

carousel-craft は `.claude/skills/` の兄弟。`video.py` が `parents[2]/carousel-craft/engine/brand.py` を
**ファイルパス直読み**で取り込む（`B` として公開）。パスは `__file__` 相対なので repo を移しても効く。
**namespace package の `from engine import` は使わない**（不安定）。

---

## 3. 使い方

```bash
SK=~/android/${CLAUDE_PLUGIN_ROOT}/skills/promo-video

# 依存（初回のみ・sudo 不要）。静的 ffmpeg 同梱の imageio をユーザ領域へ。
pip install --user --break-system-packages imageio imageio-ffmpeg

# まず probe で全シーンの代表フレームを目視（エンコードしない・速い）
python3 $SK/scripts/render.py --app hioto --probe        # -> ./hioto_probe.png を Read で確認

# 本生成（生 mp4 → CRF で共有サイズへトランスコード）
python3 $SK/scripts/render.py --app hioto --out /tmp/hioto_promo.mp4
#   既定 spec = templates/hioto.json。別 spec は位置引数で渡す。
#   出力: /tmp/hioto_promo.mp4（共有用 ~13MB）と <out>.raw.mp4（高品質の生 ~140MB）

# QA
python3 $SK/scripts/qa.py --app hioto strip --scene 2     # day_cycle の連続フレーム＝フリーズ確認
python3 $SK/scripts/qa.py --app hioto check /tmp/hioto_promo.mp4
```

作業物（生成物・一時 png・raw）は **tmp（git 対象外）** に出す。動画/画像は root では追跡されない
（`.gitignore`）。**追跡されるのは spec(JSON) とこのスキルのコード**。

---

## 4. storyboard spec（JSON）

```jsonc
{ "size": [1080,1920], "fps": 30,
  "scenes": [ { "type": "...", "frames": <int>, "accent": "<アクセント名>", ... } ] }
```
- `frames` = そのシーンの長さ（30fps）。隣接シーンは **D=9 フレームのクロスディゾルブ**で自動接続
  （総尺は `Σframes − 9×(シーン数−1)`）。~30秒なら frames 合計 ≒ 945。
- `accent` は **manifest.brand.accents のキー**（アプリで違う：hioto/tone=morning/forenoon/…、
  anki=blue/indigo/…）。不一致は KeyError ではなく default にフォールバックするが、合わせること。
- 文言は `kicker`(モノラベル) / `head[]`(見出し) / `sub[]` / `foot[]` / `tagline` / `cta`。
- 素材は `footage`（material/footage/<name>.jpg）/ `shot`（material/<name>.png）/
  `viewfinder`・`key`（緑を差し替える footage 名）/ `motif`（carousel-craft engine の svg 名）。

### シーン型カタログ（templates/standard.py）
| type | 役割 | 主なフィールド |
|---|---|---|
| `cold_open` | 表紙：モチーフが咲く＋ワードマーク＋タグライン | `tagline`,`kicker` |
| `hook` | フック：footage を Ken Burns＋見出し | `footage`,`kicker`,`head[]`,`sub[]` |
| `day_cycle` | 時間が流れる：複数 footage を連続クロスフェード＋時間帯アクセント循環 | `head[]`,`steps[{footage,accent,clock,word}]` |
| `app_magic` | 実機の瞬間：緑ビューファインダを footage 差し替え＋タップ波紋 | `footage_bg`,`shot`,`viewfinder`,`kicker`,`head[]` |
| `proof_gallery` | 証拠：実画面 3 台のパララックス・ギャラリー | `hero{shot,key?}`,`sides[{shot,key?}]`,`kicker`,`head[]`,`foot` |
| `privacy` | メッセージ：暗い footage＋モチーフ svg＋見出し | `footage`,`motif`,`kicker`,`head[]`,`sub[]`,`foot[]` |
| `cta` | 締め：モチーフ＋ワードマーク＋タグライン＋誘導＋アクセントドット | `tagline`,`cta` |

新しい見せ方が要るときだけ `standard.py` に型を足す（`TYPES` に登録）。普段は **spec を書くだけ**。

---

## 5. 作り方の手順

1. アプリの 2 フィルター/コンセプトと素材在庫を確認（manifest.json・OVERVIEW.md・material/）。
   footage と実アプリ画面（緑の有無）を `python3` でコンタクトシート化して**目で見る**。
2. `templates/<app>.json` を書く（hioto.json をコピーして文言・素材・アクセントを差し替え）。
   - 表紙→フック→展開→実機の証拠→メッセージ→CTA の流れ。frames 合計で尺を合わせる。
   - **同じ footage を全シーンで使わない**（1枚目で目を引くが死ぬ）。day_cycle で世界観に時間を与える。
3. `--probe` で全シーンを 1 枚に出して **Read で目視**→文言/配置/素材を直す（速い・エンコード不要）。
4. 本生成。`qa.py strip` で動きのあるシーン（day_cycle/app_magic）の**連続フレーム**を見て
   フリーズ/カクつきが無いか確認。
5. 生は数百 Mbps になるので **CRF でトランスコード**して共有（render.py が自動でやる）。
6. ユーザに提示し、指摘は spec で直す。新しい一般原則・教訓は**この SKILL.md に追記**する。

---

## 6. トラブルと教訓（必ず読む・新しい知見は追記）

- **カクつきの主因＝クロスフェード中に「入ってくる映像」を固定値で描くこと**。0.3 秒フリーズ→急発進で
  ガクッと見える。対策＝各素材を **“出現〜退出まで途切れず進む連続フェーズ”** で Ken Burns する
  （`DayCycle._phase`）。セグメント境界で `local` を 0 にリセットして渡すと段差になる。**t は常に連続値**。
- **ズームは緩く**。短いセグメント（~1.3秒）で大きくズームすると整数丸めの段差が目立つ。day_cycle は
  z=1.05→1.13、フェーズが ~1.5 セグメント分にまたがるので動きが滑らか。
- **テキストの切替はブラー無しのクロスフェード**（`fade_layer`）。毎回 rise+blur で出し直すと忙しく見える。
  立ち上げ（最初の一度）だけ `anim_layer`(rise+fade+blur)。
- **グレインは固定シード**。毎フレーム振り直すと切替でチラつく。写真背景にだけ薄く（amount 6〜7）、
  フラット面（紙・ベタ）には載せない（carousel-craft の質感ノートと同じ）。
- **assemble はストリーミング**（全フレームをメモリに持たない＝900枚×6MB は数 GB で破綻）。前シーンの
  末尾 D 枚だけ保持してディゾルブし、writer に流す（`video.assemble`）。
- **生は CRF 無し（quality=9）で ~38Mbps/140MB**。必ず `transcode_share`(CRF 19) で共有サイズ（~13MB）に。
- **ffmpeg は sudo 無しで入れる**：`pip install --user --break-system-packages imageio-ffmpeg`
  が静的バイナリを同梱（`imageio_ffmpeg.get_ffmpeg_exe()`）。apt は使わない。
- **フォント**：`ensure_fonts()` が /tmp に Noto Sans/Serif JP＋DM Mono を取得。head フォント
  （Zen Maru/Kaku 等）は carousel-craft/fonts。**head フォントが無いと Noto 明朝にフォールバックして
  雰囲気が変わる**ので carousel-craft が in-repo にあること。
- **carousel-craft の取り込みはファイルパス直読み**（`spec_from_file_location`）。`from engine import`
  は namespace package で不安定。正本は in-repo `.claude/skills/`（`__file__` 相対で解決＝絶対パス・symlink 不要）。
- **緑の差し替え**：`key_out_green(shot, footage_scene)` は緑が無い画面ならそのまま返す＝常に呼んでよい。
  緑のある画面（camera/shorts-feed/calendar の clip サムネ）は footage を入れて「実写を撮っている」絵に。
- **数値 QA で満足しない**。probe と strip を **Read で等倍に見て**定性判断する（carousel-craft と同じ）。

---

## 7. 別アプリの動画を足す

1. `templates/<app>.json` を作る（hioto.json をコピー→文言/素材/アクセントを差し替え。
   footage 名は material/footage/、shot 名は material/ の png、accent は manifest のキー）。
2. `render.py --app <app> --probe` で目視→本生成。コードは触らない（型が足りなければ standard.py に追加）。
3. アプリ追加自体は carousel-craft / sns-daily-pipeline と同じ＝material/manifest.json を置けば対象。
