---
name: sns-daily-pipeline
description: target/配下のアプリ(Hioto / Tone など apps.json 登録のいずれか)の SNS 運用を毎日まわす本番パイプライン。app を引数で切替。夜の好機(21時台)に1回走り、過去投稿の視聴を計測→長期記憶(LEARNINGS)で学習→キュー先頭を実投稿(tiktok-post/lemon8-post)→次の実験カルーセルを作成・予約。各投稿を仮説(実験)として翌日検証し試行錯誤で伸ばす。
allowed-tools: Bash, Read, Write, Edit, Skill, AskUserQuestion, WebSearch, WebFetch
---

# SNS 毎日パイプライン（複数アプリ対応・計測→学習→投稿→作成）

**特定の1アプリ(app)について**、計測・学習・**実投稿**・次の実験作成を行う。**本番運用：実際に公開する。**
各投稿を「1要素だけ変えた実験」として出し、翌日に結果を見て `LEARNINGS.md` を更新する。

## ⚙️ 実行モード（分析と投稿を分離）
`run_daily.sh [app] [mode]` の mode で実行範囲が変わる：
- **analyze**（深夜00:12 cronの既定）：手順 **0,1,2,2b,2c,4,5,6,7**（計測→学習→機能アイデアをissue化→外部リサーチ&考察→次の実験を生成・予約）。**投稿(手順3)はしない**。
  ラン後、wrapperが queued 投稿それぞれに対し golden time で **postモードの単発を仕込む**
  （crontab 操作は common プラグインの [[local-cron]] スキル `cronctl.sh` が正本。仕込まれた行は**発火時に自分を消す**）。
- **post**（投稿one-shotが golden time に発火）：手順 **0 と 3 のみ**（due最古1件を公開・mark・record）。計測/学習/作成はしない。
- **full**（手動/即時）：全手順を一度に。
→ つまり日々は「深夜に分析、golden時刻に投稿one-shotが公開」の2層。下の手順表はモードに応じて該当ステップだけ実行する。

## アプリの切替（apps.json）
対象アプリは `apps.json` に登録（`hioto`, `tone`, `anki`=撮るだけ暗記カード, `connect`=Manager/写真でカレンダー登録, …）。各エントリ：
`repo`（target/配下）/ `engine`（hioto|swiftbase）/ `content_dir`（成果物＝analytics相当）/
`album_prefix`（端末アルバム名の接頭辞）/ `bundleId`＋`asc_app_id`（App Store Connect の実DL計測用）/
`concept`（切り口の土台）/ `*_tags_seed`。
**1ランは1アプリ**。cron は `run_daily.sh`（無引数＝日替わりローテーション、または `run_daily.sh <app>`）。

## 🔗 harness 連携（実DL計測・定常報告=Slack・例外通知=LINE・意志のpull）
`scripts/harness.py`（トークンは `../.harness.env`＝chmod600）で **harness API**（https://harness.basaapp.com）を使う。用途：
1. **分析精度↑＝実DL数**：SNS視聴は中間指標。最終KPIは App Store Connect の**新規インストール数**。
   `python3 harness.py dl-series --bundle <bundleId> --end $DATE --days 8` で過去8日の `{date: units}` を取得
   （当日/未確定日は `missing`＝ASCは翌日確定）。投稿日とDLの増減を突き合わせて学習する。
   ⚠️**新規DLとアップデートを混同しない**：Apple の Sales SUMMARY は「新規DL(Product Type `1*`)」「アプデ(`7*`)」「IAP/サブスク(その他)」を**同じ Units 列に混載**する。`dl-series` の `series` は**新規DLのみ**（KPI）、アプデは別建て `updates` に分離済み。
   アプデは**バージョン配信日に数百件の偽スパイク**を作る（例: 既存ユーザの一斉更新）＝SNS投稿の成果ではない。**`series`(新規DL)だけを投稿効果の判定に使い、`updates`/`totalUnits` をKPIにしない**。「DL急増」を疑う時はまず新バージョンを出していないか確認する。
2. **定常報告＝Slack**：`python3 harness.py slack --text "..."` で Slack に送る（llms.txt 準拠＝進捗・完了・「今回やったこと」）。
   **順調な run の終わりに必ず1通**：何を計測/学習したか、何を公開したか、次の実験と予約日を簡潔に（app名を先頭に `[hioto]` 等）。
   分析のみ run も「計測・学び・次の実験」を1通で報告。**沈黙にしない**＝定常報告は Slack に出す。
2b. **例外通知＝LINE（今まで通り）**：`python3 harness.py push --text "..."` で LINE に送る。
   送るのは**“特別なこと”だけ**＝失敗（adb無し/投稿失敗/生成崩れ）・顕著な異常（DLの急増/急減、ある投稿が桁違いに伸びた/死んだ）・
   人の判断が要る時。これらは Slack ではなく **LINE**（リッチ表示・双方向のため）。
3. **意志確認＝pull型**：`python3 harness.py inbox --limit 10` で直近のLINE発言を読む。
   ユーザが「止めて／○○に変えて／今日は出さないで」等を送っていたら**その指示を最優先で尊重**
   （該当appを停止／次の実験を差し替え／投稿skip）。指示が無ければ**確認は求めず予定通り自律実行**（＝常に投稿でOK）。
   どうしても人の判断が要る時のみ `harness.py ask`（フォーム＋通知）→ 後ラン `harness.py answers --id <pid>` で回収。
4. **機能アイデア＝アプリの issue に起票**（手順2b）：分析でアプリ機能の改善案が出たら `gh issue create -R <gh_repo>`
   でそのアプリの repo（apps.json の `gh_repo`）に issue を立て、**issue リンク付きで `harness.py push`** する
   （issue 起票は“特別なこと”＝例外通知に該当）。`gh` は `~/.local/bin/gh`（要 `gh auth login` 一度）。

## 0. 準備（app を決める）
```bash
cd ${CLAUDE_PLUGIN_ROOT}/skills/sns-daily-pipeline/scripts
APP=hioto    # or tone … (cron は run_daily.sh が自動選択して prompt で渡す)
CFG=$(python3 appmeta.py get "$APP")   # apps.json(運用) + material/manifest.json(素性) をマージ
export ANALYTICS_DIR=$(echo "$CFG" | python3 -c "import json,sys;print(json.load(sys.stdin)['content_dir'])")
export REPO=$(echo "$CFG" | python3 -c "import json,sys;print(json.load(sys.stdin)['repo'])")
export PREFIX=$(echo "$CFG" | python3 -c "import json,sys;print(json.load(sys.stdin)['album_prefix'])")
export TODAY=$(date +%Y%m%d); export DATE=$(date +%F)
adb devices | grep -qw device || { echo "no device — abort"; exit 1; }
# 全モード共通: まず ROOT(marketing.git 本体) を pull（schedule.json/history.json/LEARNINGS.md/apps.json
# やスキル自体の更新を先に取り込む。失敗してもローカルで続行）。headless cron では run_daily.sh が自動で同じ pull を行う。
GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" timeout 90 git pull --ff-only \
  || echo "git pull skip (ROOT) — ローカルで続行"
# analyze/full のみ: 最新のアプリ内容/エンジンで生成するため target repo(サブモジュール) も pull（失敗してもローカルで続行）。
# post モードは生成しないので pull 不要。
GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" timeout 90 git -C "$REPO" pull --ff-only \
  || echo "git pull skip ($REPO) — ローカルで続行"
mkdir -p "$ANALYTICS_DIR/$TODAY/imgs"
[ -f "$ANALYTICS_DIR/schedule.json" ] || echo '{"posts":[]}' > "$ANALYTICS_DIR/schedule.json"
[ -f "$ANALYTICS_DIR/history.json" ]  || echo '{"posts":[]}' > "$ANALYTICS_DIR/history.json"
[ -f "$ANALYTICS_DIR/LEARNINGS.md" ]  || cp ../templates/LEARNINGS.seed.md "$ANALYTICS_DIR/LEARNINGS.md" 2>/dev/null || true
```
まず そのアプリの `LEARNINGS.md`（content_dir直下）と `GROWTH_PLAYBOOK.md`（skill直下・全アプリ共通）を Read。
**アプリの素性・コンテンツ知識は `$REPO/material/OVERVIEW.md`（＋`material/manifest.json`）が正本**（concept/タグ/bundleId は CFG に merge 済み）。画像の作り方・デザインは [[carousel-craft]]（共通＝ルート）。
**続けて `python3 harness.py inbox --limit 10` でユーザのLINE指示を確認**（止めて/変えて/出さないで 等があれば最優先で尊重。無ければ予定通り）。

## 1. 計測（実験の結果回収＝SNS視聴 ＋ 実DL）
```bash
bash scrape_profile.sh tiktok "$ANALYTICS_DIR/$TODAY/raw/tiktok" 3
bash scrape_profile.sh lemon8 "$ANALYTICS_DIR/$TODAY/raw/lemon8" 2
BUNDLE=$(echo "$CFG" | python3 -c "import json,sys;print(json.load(sys.stdin).get('bundleId',''))")
python3 harness.py dl-series --bundle "$BUNDLE" --end "$DATE" --days 8   # App Store Connect 実DL
```
force-stop→プロフィール最上部→撮影。`grid_*.png` を Read し、**このアプリのカバー特徴**（例: Hioto=film調＋hワードマーク／Tone=ダーク赤＋Toneワードマーク／anki=紙＋光のエディトリアル＋スキャン枠ワードマーク「撮るだけ暗記カード」・システムブルー基調）に一致する投稿の数字を読む（TikTok=▶, Lemon8=👁）。**Lemon8は現行UIで視聴数が表示されないことがある→その時は捏造せず「取得不可」と記録**。
`python3 schedule_lib.py --app $APP record-view --ref <id> --platform <pf> --date $DATE --count <N>`。見つからなければ捏造しない。raw は確認後削除。
**DLは最終KPI**：`dl-series` の各日 units（＝**新規DLのみ**。アプデ`updates`は除外済み）を当日 README に記録し、投稿日（schedule.json の posted）と突き合わせる。
**`updates` や `totalUnits` を新規DLと取り違えない**＝バージョン配信日のアプデ偽スパイクを「投稿が当たった」と誤読しないこと。
DLの**急増/急減**や、ある投稿だけ視聴が桁違い（大当たり/全滅）なら、その旨を `harness.py push` で**1通だけ**LINE通知（＝特別なこと）。ただし通知前に**新バージョン配信由来のアプデ増でないか**を必ず確認。順調なら通知しない。

## 2. 学習（LEARNINGS.md 更新）
`history.json`（SNS視聴）＋ `dl-series`（実DL）で直近実験の仮説が当たったか判定 → `$ANALYTICS_DIR/$TODAY/README.md` に当日分析、
`$ANALYTICS_DIR/LEARNINGS.md` を更新（確定知見へ昇格／棄却／次に試す1つを今日の実験に）。**1回1要素**。

## 2b. 機能アイデア → アプリの GitHub issue 化（analyze/full のみ）★人へ報告
分析していて「**このアプリに XX の機能があれば伸びる／ユーザの課題が解ける**」と気づいたら、
ローカルメモに留めず、その**アプリ自身の repo に issue として上げる**（バックログ化する）。
SNS の数字・DL・LEARNINGS から導けた“プロダクト改善仮説”が対象（投稿の作り方の話は LEARNINGS 側で扱い、ここではアプリ機能の話だけ）。

判定の目安（無理に毎日出さない・無ければ立てない）：視聴/DLの傾向や定性から
**アプリ側を変えれば効きそう**な具体策が出たときだけ。例＝「○○への導線が無い」「初回○日でDL離脱＝オンボに△が要る」「××機能があればこの切り口が刺さる」。

手順（`gh` CLI を使う。repo は apps.json の `gh_repo`。認証は一度 `gh auth login` 済みなら headless でも通る）：
```bash
GH_REPO=$(echo "$CFG" | python3 -c "import json,sys;print(json.load(sys.stdin).get('gh_repo',''))")
gh auth status >/dev/null 2>&1 || { echo "gh未認証→issue起票スキップ(harnessで通知)"; }
# 1) 重複ガード：タイトル語で既存 open issue を検索、ヒットしたら立て直さない
gh issue list -R "$GH_REPO" --state open --search "in:title <キーワード>" --limit 5
# 2) 無ければ作成（label=enhancement）。bodyに「課題/根拠(視聴・DL)/提案/期待効果」
URL=$(gh issue create -R "$GH_REPO" --label enhancement \
  --title "<簡潔なタイトル>" \
  --body "$(printf '## 背景/課題\n<SNS視聴・DLから見えたこと>\n\n## 提案\n<入れたい機能 XX>\n\n## 期待する効果\n<なぜ伸びる/離脱が減ると考えるか>\n\n— SNS分析(sns-daily-pipeline) %s 自動起票' "$DATE")")
echo "$URL"   # 末尾に https://github.com/<repo>/issues/N が出る
```
（`enhancement` ラベルが repo に無いと失敗するので、その時は `--label` を外す。）
作成したら**必ず issue リンク付きで LINE 通知**（これは“特別なこと”＝例外通知に該当・方針に沿う）：
```bash
[ -n "$URL" ] && python3 harness.py push --text "[SNS:$APP] 機能アイデアをissue化: <タイトル>
$URL"
```
起票した issue は当日 `$ANALYTICS_DIR/$TODAY/README.md` と `LEARNINGS.md`（または `$ANALYTICS_DIR/ISSUES.md`）に1行記録し、次ランの重複起票を防ぐ。
失敗時（gh未認証/APIエラー）は `harness.py push` で1通通知し、状態は保持。

## 2c. 外部リサーチ&考察（analyze/full のみ）★数字を読むだけで終わらせない
harness の数字（視聴・実DL）は「何が起きたか」しか教えてくれない。**「なぜ」と「次どう動くか」は外部知見で裏取り・考察してから手順4の企画に渡す**。
WebSearch / WebFetch（深い時は `deep-research` スキル）で、毎ラン**次の4観点**を調べて当日 README に「## リサーチ」節として要点＋出典URLを残し、LEARNINGS と手順4の切り口に反映する。**捏造しない・出典を必ず残す**。
1. **コンテンツ知識の正確性**：次の実験で使う統計/理論/数字/手順を事実確認（一次情報・公式・論文を優先）。apps.json の `knowledge`（例: Tone=`tone_posts/KNOWLEDGE.md`）と矛盾しないか突合。怪しい数字は使わない。
2. **投稿の伸び要因の裏取り**：直近の大当たり/全滅について、プラットフォーム傾向・アルゴリズム・類似事例を調べ「なぜ伸びた/死んだ」の仮説精度を上げる（推測のままにしない）。
3. **トレンド/時事**：そのアプリのジャンルで今伸びてるネタ・季節性・話題（例: メンズメイクの新トレンド、勉強法の流行、日記/メンタルの時事）を拾い、刺さる切り口に反映。
4. **競合/他アカウント**：同ジャンルで伸びている投稿・アカウントの型（フック/構成/タグ/頻度）を調べ、学習に取り込む（パクリではなく型の抽出）。

**深さは適応型＋水曜固定**（コストは毎晩 headless なので無駄打ちしない）：
- **通常**：4観点を WebSearch 数本＋必要なら WebFetch で軽く回す（考察を伴う。机上で終わらせない）。
- **`deep-research` スキルにエスカレーション**するのは次のいずれか：
  - **毎週水曜**（曜日固定。run_daily.sh が analyze 時に `DEEP_RESEARCH=1` を prompt に注入。手動なら `date +%u` が `3`）→ その週の主テーマ（伸び要因 or 次の実験の土台知識）を1本フル deep-research。
  - シグナル時：**DLの急増/急減**、ある投稿が**桁違い（大当たり/全滅）**、**実験の方向転換**、**新トピック投入** など「ちゃんと裏を取る価値がある」と判断した時。
- deep-research を回したら、その**結論サマリ＋出典**を README「## リサーチ」と LEARNINGS に残す（次ランが再利用できるように）。リサーチで知った重要事実は手順4・6の文言/数字の根拠にする。

ネットワーク不通/検索失敗で取れない時は**捏造で埋めず**、その旨を README に1行残してローカル知見（LEARNINGS/knowledge）だけで企画を続行する（中断はしない）。

## 3. 投稿（キュー先頭を本番公開）★実公開
> **dueが空でも特定postを今すぐ公開したい時**（手動full/検証ラン等）：`schedule_lib.py --app $APP due` が `[]` でも、対象 `content_dir/<date>` の index.json/imgs を指定して tiktok-post/lemon8-post を直接回し、公開後に `schedule_lib.py --app $APP mark --id <id> --status posted` ＋ record-view 0。post modeは「due日基準」なので即時公開はこの手動経路を使う。
```bash
python3 schedule_lib.py --app $APP due --date $DATE
```
最古の queued 1件を公開（無ければ 4 へ）。素材アルバム＝`${PREFIX}_<id>_<platform>`、文言＝`imgs/<pf>/index.json`。
- TikTok: `tiktok-post` スキル（カバー=01・6枚・選択は「タップ→プレビュー→選択→戻る」・トレンド音源推奨・キャプション90字）。
- Lemon8: `lemon8-post` スキル（タグ5・TikTokにシェアOFF。**見出し欄/本文欄はタップ位置がシビア**、テスト文字で焦点確認）。
- 公開を実機スクショで確認（TikTok=ドット枚数, Lemon8=共有シート）。`schedule_lib.py --app $APP mark --id <ID> --status posted`、record-view 0 で計測開始。失敗時 `--status failed`。

## 4. 次の1本を企画（今日の実験）
**冪等ガード**：`$ANALYTICS_DIR/$TODAY/imgs/tiktok/index.json` が既存かつ schedule に `content_dir==$ANALYTICS_DIR/$TODAY` の予約があれば作成済み→ 4〜7 をスキップ（1〜3 は実行）。
`GROWTH_PLAYBOOK.md` ＋ そのアプリの **`$REPO/material/OVERVIEW.md`（コンテンツ正本＝concept/コンテンツ知識・旧sns-post＋KNOWLEDGEを集約）** ＋ **手順2cのリサーチ知見（当日READMEの「## リサーチ」節）** に沿い、
**1要素だけ変えた**次の実験を決める（切り口・数字・フックはリサーチで裏取りした事実を根拠にする）。**OVERVIEW.md は必ず読む**
（例: Tone は統計フック/理論/5ステップ/失敗例の正本がここに集約済み。切り口・info内容・数字は捏造せずここから引く）。1枚目＝強いフック（疑問形／○○な人へ／数字…）。5〜10枚・各スライド価値あり。
**デザインは [[carousel-craft]] スキルが正本**（フック/タイポ/配色/セーフゾーン/構成は `DESIGN_SPEC.md`、素材在庫とspecレシピは `MATERIALS.md`）。企画時に必ず参照する。
**素材ファースト＝表紙含め全スライドに実素材を敷く（ベタ塗り/グラデ/単色の背景を作らない）**：
- **cover/photo の `bg` は必ず指定**（省略禁止）。anki/connect の `bg`省略＝手続き背景(灰色)、tone の footage名→ベタ赤 はいずれも**禁止**。素材は下記バンクの**絶対パス**を渡す（tone も gen.py 拡張で絶対パスOK）。
- **shot は実app画面を複数枚**（hioto=`material/`、tone=`material/`直下、anki/connect=`material/screenshots/`、
  **hanasu=`material/screens/`**＝spec には `screens/09_paper.png` のように書く）。緑クロマキーがあれば `footage` で世界観差替（hioto/tone）。
- フッテージ: hioto=FTキー(`sunset`等6種)／tone=footage空→bg絶対パス／anki・connect・**hanasu**=footage無し→bg絶対パス。
- **hanasu 固有**: 差別化の核が「レイアウトが毎回変わる」なので、`material/layouts/` のページ見本（`genre_*`/`density_*`）を
  複数並べて見せる構成が効く。`09_paper.png`（完成ページ）は表紙候補。
**cover/photo の背景＝ルートの汎用素材バンク `material/`**（repo 内 material とは別物）。`index.json`（`{name(uuid), tags[]}`）をテーマ＋`縦長`でタグ検索し `images/<name>.jpg` の絶対パスを `bg` 指定。
タグ：hioto→`hioto`/`日記`/`film`、tone→`tone`/`メンズ`、**anki/connect/hanasu→専用タグ無し→`flatlay`/`interior`/`部屋`/`日常`/`cozy`/`journal`**（`勉強`/`カレンダー`は0件のこと多し＝必ず実在確認）。
**hanasu は hioto と同じく顔・人物入りを避ける**（個人の記録という軸）。
**hioto は顔・人物入りを避ける**（プライバシー軸）／tone は人物（メイクシーン）歓迎。
```bash
python3 - <<'PY'
import json; b="material"
want={"hioto","縦長"}  # tone なら {"tone","縦長"}
for e in [x for x in json.load(open(b+"/index.json")) if want <= set(x["tags"])][:20]:
    print(b+"/images/"+e["name"]+".jpg", e["tags"])
PY
```

## 5. 画像 + index.json を生成（repo非改変・統合gen）
spec を `$ANALYTICS_DIR/$TODAY/spec.json` に書く（`gen.py` 冒頭スキーマ。slides はそのアプリ build_posts の形）。
タグ: TikTok 3〜5 / Lemon8 5〜8（大中小・年号語1つ／UI上限5なら5）。
```bash
python3 gen.py --app $APP "$ANALYTICS_DIR/$TODAY/spec.json" "$ANALYTICS_DIR/$TODAY/imgs"
# gen.py は cover/photo に bg(実素材) が無いと素材ファースト違反でエラー停止する（灰色背景の素通り防止）。出たら spec に bg を足して再生成。
rm -rf "$REPO/post/__pycache__" 2>/dev/null
# 客観チェック＋セーフゾーン枠付きコンタクトシート生成（carousel-craft）
python3 ${CLAUDE_PLUGIN_ROOT}/skills/carousel-craft/scripts/qa.py "$ANALYTICS_DIR/$TODAY/imgs" --spec "$ANALYTICS_DIR/$TODAY/spec.json"
```
**自己レビュー（[[carousel-craft]] §5）＝コードでなく自分の目で採点する**：
1. `qa.py` が `hard_flags>0`（NO-MATERIAL）なら素材未使用＝**spec を直して再生成**（exit非0）。
2. `imgs/_qa/<platform>_contact.png`（全スライド一覧＋セーフゾーン枠）と表紙・shot を **Read で目視**：フック強度・上の死に空間・実素材の有無・オチを割ってないか・写真上文字の可読性・右いいね列/下UI被り・整列・既存被り。
3. ダメなら**文言/素材/配色/レイアウトを直して納得いくまで反復**（1発で終わらせない）。崩れも同様。

## 6. POST.md（仮説を明記）
`$ANALYTICS_DIR/$TODAY/POST.md`：app名・切り口・**今日の仮説（変えた1要素）**・各スライド内容・両PFの文言/タグ・
**使用スキル(tiktok-post/lemon8-post)・素材アルバム(`${PREFIX}_$TODAY_<platform>`)**。LEARNINGS の実験ログにも1行追加。

## 7. 予約
```bash
python3 schedule_lib.py --app $APP add-post --content-dir "$ANALYTICS_DIR/$TODAY" --theme "<切り口/仮説>" --platforms tiktok,lemon8
python3 schedule_lib.py --app $APP list
```
予約日時は playbook 時間ルール（平日21:10/金土18:30/月曜回避）で自動決定。キューは1〜数本のバッファ。

## 8. 後始末
```bash
source lib.sh && keep_awake_off; kb_off 2>/dev/null
```
最後に app名・計測結果・学び・公開した投稿・次の実験/予約日を簡潔に報告。

## 失敗時
adb無し→中断し状態保持。ANR/もたつき→`lib.sh` の `free_cpu`。投稿UIの罠は各スキルの SKILL.md。
**失敗・中断したら `python3 harness.py push --text "[SNS:<app>] <何が起きたか>"` で LINE 通知**（adb無し/投稿失敗/生成崩れ＝特別なこと）。状態は保持して次ランで復帰。

## スケジューラ
本番は **深夜 00:12 JST** の system cron → `run_daily.sh`（無引数＝日替わりで apps をローテーション）→
`claude -p ... --dangerously-skip-permissions`。analyze が終わると、queued 投稿それぞれの golden time に
**postモードのワンショット**が仕込まれ、発火時に自分の crontab 行を消してから公開する（2層構成）。

crontab の登録・削除は **common プラグインの [[local-cron]] スキル**（`cronctl.sh`）に集約してある。
このスキル側で crontab を直に叩かない。

```bash
CRONCTL="$HOME/.claude/plugins/cache/tubasasakunn-marketplace/common"/*/skills/local-cron/cronctl.sh
$CRONCTL list --tag SNS                      # 予定を見る（深夜の常駐＋仕込まれた投稿）
$CRONCTL clear --tag SNS --match app=hioto    # あるアプリの投稿予定だけ止める
```

**別サーバーで動かすとき**：リポジトリルートが自動で見つからなければ `SNS_ROOT=/path/to/marketing` を
環境変数で渡す（`appmeta.py root` が解決の正本）。crontab に書かれるパスは `$HOME` 基準に畳まれるので、
ユーザー名やホームの位置が違うマシンでもそのまま通る。

詳細は `analytics/SCHEDULING.md`。新アプリ追加は apps.json に1エントリ足すだけ（cron は自動でローテに含める）。
