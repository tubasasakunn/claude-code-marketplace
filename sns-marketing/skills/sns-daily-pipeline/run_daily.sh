#!/usr/bin/env bash
# Headless driver for the multi-app SNS pipeline. Split architecture:
#   - analyze (nightly cron): measure -> learn -> create next experiment -> reserve,
#     then ARM a one-shot to PUBLISH each queued post at its golden time. NO posting here.
#   - post (fired by an armed one-shot at golden time): publish the oldest due post only.
#   - full (manual / `now`): everything in one go (measure+learn+publish+create).
#
# Usage:
#   run_daily.sh [app] [mode]      # app: hioto|tone|... (default: daily rotation)
#                                  # mode: analyze (default) | post | full
# crontab (JST, nightly analysis): 12 0 * * * /…/run_daily.sh
set -uo pipefail

export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
CLAUDE="$(command -v claude || echo "$HOME/.local/bin/claude")"
# パスは自分の位置から導出（絶対パス直書きをしない）。symlink 経由でも実体を解決。
SELF_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
SKILL_DIR="$(dirname "$SELF_PATH")"
APPS="$SKILL_DIR/apps.json"

# リポジトリルートは appmeta.py に一本化する（解決ロジックを2箇所に持たない）。
# スキルは plugin cache に配られるので「自分の上へ辿る」だけでは見つからない。
# 別サーバーで候補に当たらない時は SNS_ROOT=/path/to/marketing を渡す。
REPO_ROOT="$(python3 "$SKILL_DIR/scripts/appmeta.py" root)" || exit 1

# ワンショットの仕込みは common プラグインの local-cron スキルに任せる。
# （旧 run_once.sh は廃止。crontab 操作は cronctl.sh が正本）
find_cronctl() {
  local c
  for c in "$SKILL_DIR"/../../../../common/*/skills/local-cron/cronctl.sh \
           "$HOME"/.claude/plugins/cache/*/common/*/skills/local-cron/cronctl.sh \
           "$HOME"/*/claude-code-marketplace/common/skills/local-cron/cronctl.sh; do
    [ -f "$c" ] && { readlink -f "$c"; return; }
  done
}
CRONCTL="$(find_cronctl)"
CRON_TAG="SNS"

LOG="$REPO_ROOT/analytics/cron.log"
mkdir -p "$(dirname "$LOG")"

APP="${1:-}"
MODE="${2:-analyze}"
if [ -z "$APP" ]; then
  APP=$(python3 - "$APPS" <<'PY'
import json, sys, datetime
# "_" 始まりは注記キー（_comment/_rotation）＝アプリではない。除外しないと
# その日のランが存在しない app 名で走って丸ごと失敗する。
# ここは apps.json のキーだけを見る（appmeta.py list は target/ を走査するので、
# ローテから外したはずのアプリが manifest 経由で戻ってきてしまう）。
keys = sorted(k for k in json.load(open(sys.argv[1])) if not k.startswith("_"))
if not keys:
    sys.exit("apps.json に対象アプリが1つもない")
print(keys[datetime.date.today().timetuple().tm_yday % len(keys)])
PY
) || exit 1
fi
LOCK="/tmp/sns_${APP}.lock"   # per-app lock: analyze(app A) and post(app B) can overlap

CFG="$APPS の \"${APP}\"（repo/engine/content_dir/album_prefix/concept/タグseed/knowledge）を正本とし、ANALYTICS_DIR=その content_dir を使う"

case "$MODE" in
  analyze)
    # 水曜(date +%u == 3)は手順2cの外部リサーチを deep-research スキルでフル稼働させる（適応型＋水曜固定）。
    if [ "$(date +%u)" = "3" ]; then
      DEEP="**今日は水曜＝DEEP_RESEARCH=1**：手順2cは適応判定を待たず deep-research スキルをフルで1本回し、その結論+出典を README「## リサーチ」と LEARNINGS に残す。"
    else
      DEEP="手順2cは適応型（通常は WebSearch/WebFetch で4観点を軽く＋考察。DL急変/大当たり/全滅/方向転換のシグナル時のみ deep-research へエスカレーション）。"
    fi
    PROMPT="sns-daily-pipeline スキルで【app=${APP}・モード=analyze（分析のみ／**投稿はしない**）】を実行。$CFG。SKILL.md に従い：(0)準備＋そのアプリ LEARNINGS.md と GROWTH_PLAYBOOK.md・apps.json の knowledge を読む＋**harness.py inbox でユーザのLINE指示を確認（止めて/変えて等あれば最優先で尊重）**、(1) scrape_profile.sh で計測し record-view＋**harness.py dl-series で実DLを取得しREADMEに記録**、(2) 視聴＋DLで直近実験の仮説を検証し README.md と LEARNINGS.md 更新、(2c) **外部リサーチ&考察＝数字を読むだけで終わらせず WebSearch/WebFetch(深い時は deep-research スキル)で[コンテンツ知識の正確性/伸び要因の裏取り/トレンド時事/競合]の4観点を調べ、要点+出典を当日READMEの「## リサーチ」節に残して企画の根拠にする（捏造禁止・出典必須）。${DEEP}**、(4) concept/knowledge ＋2cのリサーチ知見に沿い1要素だけ変えた次の実験を企画、(5) **carousel-craft 準拠**で spec を書き(表紙含め全スライドに実素材bgを必ず指定＝灰色グラデ/ベタ赤を作らない) gen.py --app ${APP} で生成(repo非改変・__pycache__削除)→qa.py で素材チェック＋コンタクトシート生成し**自分の目で**フック/可読性/被りを採点→納得まで反復、(6) POST.md に仮説明記、(7) schedule_lib.py add-post で予約。**ステップ3(公開)はしない**＝投稿は別の単発起動(post)が golden time に行う。(8) keep_awake_off。**通知方針：順調なら最後に harness.py slack で定常報告を1通（計測・学び・次の実験/予約日）。失敗/中断/DL急変/大当たり等“特別なこと”は Slack ではなく harness.py push でLINE1通**。adb 無ければ中断（harness.py push でLINE通知）。最後に計測・学び・次の実験/予約日を報告。" ;;
  post)
    PROMPT="sns-daily-pipeline スキルで【app=${APP}・モード=post（**公開のみ**）】を実行。$CFG。手順：準備(画面ウェイク/keep_awake_on)→ **harness.py inbox でLINE指示を確認（出さないで/止めて 等があれば skip し harness.py push で報告）**→ schedule_lib.py due で『今日以前の queued』最古1件を取得→ その素材アルバム(<album_prefix>_<id>_<platform>)と imgs/<pf>/index.json を使い **tiktok-post と lemon8-post スキルで実公開**→ 実機スクショで確認(TikTok=ドット枚数/Lemon8=共有シート)→ schedule_lib.py mark --status posted ＋ record-view 0。**計測・学習・新規作成はしない**。複数 due があっても1件だけ。**成功時は harness.py slack で完了報告を1通（どのアプリの何をどのプラットフォームに公開したか）。失敗時のみ harness.py push でLINE通知**。adb 無ければ中断（LINE通知）。最後に公開した投稿を報告。" ;;
  full)
    PROMPT="sns-daily-pipeline スキルで【app=${APP}・モード=full（計測+学習+公開+作成 を一度に）】を実行。$CFG。SKILL.md の全ステップ(0..8)を実行：harness.py inbox 確認→計測(scrape＋harness.py dl-series 実DL)→学習→**(2c)外部リサーチ&考察＝WebSearch/WebFetch(深い時は deep-research スキル)で[コンテンツ知識の正確性/伸び要因の裏取り/トレンド時事/競合]の4観点を調べREADMEの「## リサーチ」節に出典付きで残す(捏造禁止)**→(3)due最古1件を tiktok-post/lemon8-post で実公開し mark posted→2cの知見に沿い次の実験を**carousel-craft準拠**で生成(表紙含め全スライド実素材bg必須＝灰色/ベタ赤禁止、qa.py＋目視で反復)・予約。**順調なら最後に harness.py slack で定常報告を1通（計測・学び・公開・次の実験/予約日）。失敗/中断/DL急変/大当たり等“特別なこと”は harness.py push でLINE**。adb 無ければ中断（LINE通知）。最後に計測・学び・公開・次の実験/予約日を報告。" ;;
  *) echo "unknown mode: $MODE"; exit 2 ;;
esac

# claude をどこから起動するか。plugin は **project スコープ**で install されているため、
# cwd がその project でないと sns-daily-pipeline スキル自体が読み込まれない
# （plugin cache や marketing/ から起動すると素の claude になり、ランが無言で失敗する。実測済み）。
# データの置き場は REPO_ROOT(marketing) だが、スクリプトが返すパスは全て絶対なので
# 起動ディレクトリは workspace 側でよい。SNS_LAUNCH_DIR で明示上書きできる。
plugin_enabled() {
  [ -f "$1/.claude/settings.json" ] && grep -q 'sns-marketing@' "$1/.claude/settings.json" 2>/dev/null
}
LAUNCH_DIR=""
for d in "${SNS_LAUNCH_DIR:-}" "$HOME"/workspace/sns-marketing-workspace \
         "$HOME"/*/sns-marketing-workspace "$REPO_ROOT"; do
  [ -n "$d" ] && plugin_enabled "$d" && { LAUNCH_DIR="$d"; break; }
done
if [ -z "$LAUNCH_DIR" ]; then
  echo "sns-marketing plugin を有効にした project が見つからない（SNS_LAUNCH_DIR を設定してください）" >> "$LOG"
  python3 "$SKILL_DIR/scripts/harness.py" push \
    --text "[SNS:${APP}] plugin を有効にした作業ディレクトリが見つからず起動できません" >> "$LOG" 2>&1 || true
  exit 1
fi
echo "----- launch dir: $LAUNCH_DIR -----" >> "$LOG"
cd "$LAUNCH_DIR" || exit 1
echo "===== $(date '+%F %T %Z') run start app=${APP} mode=${MODE} =====" >> "$LOG"

# 0) always pull ROOT (marketing.git) first — schedule.json/history.json/LEARNINGS.md/apps.json
# and the skill scripts themselves live here, so every mode (analyze/post/full) needs the
# latest before reading them. Never block the run: ff-only + timeout + BatchMode ssh so a
# missing key / diverged history just logs and we proceed with local state.
echo "----- git pull ROOT $REPO_ROOT (from $(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null)) -----" >> "$LOG"
GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" \
  timeout 90 git -C "$REPO_ROOT" pull --ff-only >> "$LOG" 2>&1 \
  || echo "git pull failed/skipped for ROOT $REPO_ROOT — continuing with local state" >> "$LOG"

# analyze/full: also pull the target app SUBMODULE so generation uses the latest content/engine.
# (post mode doesn't generate, so it skips this one.) Same never-block guarantees as above.
if [ "$MODE" = "analyze" ] || [ "$MODE" = "full" ]; then
  REPO=$(python3 "$SKILL_DIR/scripts/appmeta.py" get "$APP" 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin).get('repo',''))" 2>/dev/null)
  if [ -n "$REPO" ] && [ -d "$REPO/.git" ]; then
    echo "----- git pull SUBMODULE $REPO (from $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null)) -----" >> "$LOG"
    GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=10" \
      timeout 90 git -C "$REPO" pull --ff-only >> "$LOG" 2>&1 \
      || echo "git pull failed/skipped for SUBMODULE $REPO — continuing with local state" >> "$LOG"
  fi
fi

# Deterministic memory reclaim BEFORE the agent drives the UI. Root cause of the
# 2026-06-23 failed run: low MemAvailable -> ZRAM thrash -> fixed-coord taps land on the
# wrong UI -> derailment. No root, so reclaim with shell primitives (kill cached bg +
# force-stop heavy non-target apps + cancel dexopt). Best-effort, never blocks the run.
if [ -f "$SKILL_DIR/scripts/lib.sh" ]; then
  # shellcheck disable=SC1091
  ( source "$SKILL_DIR/scripts/lib.sh" && adb get-state >/dev/null 2>&1 \
      && { echo "----- mem_reclaim (avail before: $(mem_avail)MB) -----"; mem_reclaim; echo "mem avail after: $(mem_avail)MB"; } ) >> "$LOG" 2>&1 || true
fi

flock -n "$LOCK" "$CLAUDE" -p "$PROMPT" --dangerously-skip-permissions >> "$LOG" 2>&1
rc=$?

# Headless backstop: if the run itself died (lock held / crash / claude error), the agent
# couldn't report. Push a single LINE alert directly (exceptions -> LINE). On rc=0 the agent
# has already sent its routine Slack report, so the backstop stays quiet.
if [ $rc -ne 0 ]; then
  python3 "$SKILL_DIR/scripts/harness.py" push \
    --text "[SNS:${APP}] run failed (mode=${MODE}, rc=${rc}). cron.log を確認してください。" \
    >> "$LOG" 2>&1 || true
fi

# analyze mode: (re)arm posting one-shots for every queued post at its golden datetime.
# 毎晩 clear→再arm で冪等にする（途中で失敗した日があっても翌晩に自然に復旧する）。
# 発火したワンショットは cronctl の __fire が自分の crontab 行を先に消すので溜まらない。
if [ "$MODE" = "analyze" ] && [ $rc -eq 0 ]; then
  if [ -z "$CRONCTL" ]; then
    echo "cronctl.sh not found — common プラグインの local-cron スキルが要る。投稿one-shotは仕込めない" >> "$LOG"
    python3 "$SKILL_DIR/scripts/harness.py" push \
      --text "[SNS:${APP}] cronctl.sh が見つからず投稿one-shotを仕込めませんでした（common/local-cron を確認）" >> "$LOG" 2>&1 || true
  else
    CONTENT_DIR=$(python3 "$SKILL_DIR/scripts/appmeta.py" get "$APP" 2>/dev/null | python3 -c "import json,sys;print(json.load(sys.stdin).get('content_dir',''))")
    "$CRONCTL" clear --tag "$CRON_TAG" --match "app=$APP" >> "$LOG" 2>&1 || true
    python3 - "$CONTENT_DIR/schedule.json" <<PY 2>>"$LOG" | while read -r dt; do
import json,sys
try: posts=json.load(open(sys.argv[1]))['posts']
except Exception: posts=[]
for p in posts:
    if p.get('status')=='queued' and p.get('scheduled_date'):
        print(f"{p['scheduled_date']} {p.get('scheduled_time','21:10')}")
PY
      "$CRONCTL" once "$dt" --tag "$CRON_TAG" --label "app=$APP" --log "$LOG" \
        -- "$SELF_PATH" "$APP" post >> "$LOG" 2>&1 || true
    done
    echo "----- armed post one-shots for $APP queued posts -----" >> "$LOG"
  fi
fi

echo "===== $(date '+%F %T %Z') run end app=${APP} mode=${MODE} (rc=$rc) =====" >> "$LOG"
exit $rc
