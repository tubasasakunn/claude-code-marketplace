---
name: tone-post
description: Tone（メンズメイク診断アプリ / target/mensmakeupadvisor）の TikTok・Lemon8 向けカルーセル画像投稿を1本作って実際に公開する。swift-baseテンプレの post/ エンジンを流用し、診断・スタジオ等の実アプリ画面で6枚カルーセルを生成、tiktok-post/lemon8-post で投稿する。Hiotoのsns-postに相当するTone版。
allowed-tools: Bash, Read, Write, Edit, Skill
---

# Tone（メンズメイク診断）カルーセル投稿

アプリ **Tone（トーン / メンズメイク診断）** = 撮るだけでAIが顔型・バランス・7項目を採点 →
似合うメイクを提案 → スタジオでBefore/After試着 → 推移。ブランドは**ダーク×ウォーム高級感**
（accent=warm red, wordmark "Tone"）。リポジトリ: `target/mensmakeupadvisor`（swift-baseテンプレ由来）。

Hiotoと同じ `post/` エンジン（`_brand.py`＋`build_posts.py`）を使う。ブランド色・ワードマークは
`appstore.config.json` が正本（コードは触らない）。**footage は無い**が `footage_or_solid()` が
**単色ブランド背景にフォールバック**するので cover/photo はそのまま描ける。shot は repo 内 `material/` の
実アプリ画面（例 `05_diagnosis_top.png`, `09_studio.png`）を phone モックで見せる。

**cover/photo の背景は、単色フォールバックのほかルートの汎用素材バンク
`material/` から流用してもよい**（repo 内 `material/` とは別物）。
`index.json`（`{name(uuid), prompt, tags[]}`）を `tone`/`メンズ`/`縦長` 等でタグ検索し、
`images/<name>.jpg` をコンテンツの `imgs/` 等にコピーして `bg` に指定する（ダーク×ウォームに合う縦長を選ぶ）。
```bash
python3 - <<'PY'
import json; b="material"
want={"tone","縦長"}
for e in [x for x in json.load(open(b+"/index.json")) if want <= set(x["tags"])][:20]:
    print(b+"/images/"+e["name"]+".jpg", e["tags"])
PY
```

## コンテンツ作成
1. 切り口を決める（メンズメイクは"盛る"より"整える"訴求が芯）。フックは playbook §4：
   疑問形「あなたの顔、何点か知ってる？」／ターゲット「メンズメイク何から始める人へ」／数字。
   既存と角度を変える。2フィルター相当＝アプリの実価値（顔診断→似合うメイク）に正直に。
2. spec.json を書く（`gen_post_swiftbase.py` 冒頭スキーマ）。スライドは cover/photo/shot/info/cta。
   - cover/photo: `bg` は省略可（省略＝単色ブランド背景）。kicker＋短い強フック headline。
   - shot: `shot` に `material/` の画面名（`05_diagnosis_top.png`=診断73点, `09_studio.png`=Before/After,
     `07_diagnosis_proportions.png`=7項目, `17_progress.png`=推移 等）。title＋sub。
   - info: kicker＋title＋bullets[3]。cta: headline＋sub（"無料でダウンロード"）。
   - copy: TikTokタグ3〜5（#メンズメイク #メンズ美容 #顔診断 #垢抜け 等）／Lemon8タグ5〜8（大中小＋年号 #2026垢抜け）。
3. 生成（repo非改変）:
   ```bash
   cd ${CLAUDE_PLUGIN_ROOT}/skills/tone-post/scripts
   python3 gen_post_swiftbase.py <content_dir>/spec.json <content_dir>/imgs \
       --repo target/mensmakeupadvisor
   rm -rf target/mensmakeupadvisor/post/__pycache__
   ```
   → `imgs/{tiktok,lemon8}/NN_*.png` ＋ index.json。**全スライドを Read で目視確認**（フック強度・実画面・ブランド）。
   コンテンツ置き場の既定: `tone_posts/<id>/`。

## 投稿（実公開）
端末アルバムへ転送 → 投稿スキルを使う（Hiotoと同手順）:
```bash
source ${CLAUDE_PLUGIN_ROOT}/skills/tone-post/scripts/lib.sh; keep_awake_on
push_images /sdcard/Pictures/tone_<id>_tiktok <content_dir>/imgs/tiktok/*.png
push_images /sdcard/Pictures/tone_<id>_lemon8 <content_dir>/imgs/lemon8/*.png
kb_install; kb_save_orig; kb_on
```
- **TikTok**: `tiktok-post` スキル（素材=tone_<id>_tiktok アルバム、文言=imgs/tiktok/index.json、
  カバー=01・6枚カルーセル・選択は「タップ→プレビュー→選択→戻る」が確実・トレンド音源推奨）。
  キャプションは90字上限＝タイトル(疑問フック)＋核フレーズ＋タグ。
- **Lemon8**: `lemon8-post` スキル（素材=tone_<id>_lemon8、タグ5、TikTokにシェアOFF）。
- 公開後は実機スクショで確認（TikTok=ドット枚数, Lemon8=共有シートのカード）。終わったら `kb_off; keep_awake_off`。

## アカウント注意
同一端末の「ばさ」アカウントで投稿（Hiotoと同じ）。Tone と Hioto が同居するので、
切り口・ハッシュタグはアプリごとに分ける。視聴計測は hioto-daily-pipeline と同様にプロフィール最上部から読む。

## harness 連携（成功＝Slack定常報告 / 失敗＝LINE例外通知）
- **成功時**：共通クライアントで Slack に1通だけ完了報告（llms.txt 準拠の進捗・完了報告）：
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sns-daily-pipeline/scripts/harness.py slack --text "[tone] <TikTok/Lemon8 どちらに何を公開したか>"`。
- **失敗時**（adb無し/枚数ミス/解消できないANR）：Slack ではなく **LINE** に1通だけ通知：
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sns-daily-pipeline/scripts/harness.py push --text "[tone] <何が失敗したか>"`。
実DL計測や詳細レポートは日次の `sns-daily-pipeline` 側が担う。トークンは `sns-daily-pipeline/.harness.env`。
