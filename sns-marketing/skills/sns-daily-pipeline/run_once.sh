#!/usr/bin/env bash
# One-shot trigger for the SNS pipeline: run ONE app's pipeline once (a given MODE),
# now or at a given time — independent of the nightly analysis cron. Robust = uses
# crontab (always running, survives reboot/logout). Entries self-delete after firing.
#
# Usage:
#   run_once.sh <app> now [mode]                 # run immediately (background, detached)
#   run_once.sh <app> "HH:MM" [mode]             # once today (or tomorrow if past) at HH:MM JST
#   run_once.sh <app> "YYYY-MM-DD HH:MM" [mode]  # once at an explicit datetime (past -> ~now)
#   run_once.sh --list                           # list pending one-shots
#   run_once.sh --cancel <id>                    # cancel a pending one-shot
#   run_once.sh --clear-app <app>                # cancel all pending one-shots for an app
#   run_once.sh __fire <id> <app> [mode]         # (internal) fired by cron: self-delete + run
#
# mode = full (default) | analyze | post   (passed to run_daily.sh)
# Examples:
#   run_once.sh hioto now full
#   run_once.sh tone "2026-06-20 18:30" post
set -uo pipefail
# パスは自分の位置から導出（絶対パス直書きをしない）。symlink 経由でも実体を解決。
# crontab に書く $SELF は解決済み絶対パスになる＝cron からも正しく発火する。
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
SKILL_DIR="$(dirname "$SELF")"
find_root() { local d="$1"; while [ "$d" != "/" ]; do { [ -d "$d/target" ] && [ -f "$d/CLAUDE.md" ]; } && { echo "$d"; return; }; d="$(dirname "$d")"; done; }
RUN_DAILY="$SKILL_DIR/run_daily.sh"
APPS="$SKILL_DIR/apps.json"
LOG="$(find_root "$SKILL_DIR")/analytics/cron.log"
TAG="SNS-ONESHOT"

valid_app() { python3 -c "import json,sys;sys.exit(0 if '$1' in json.load(open('$APPS')) else 1)" 2>/dev/null; }

case "${1:-}" in
  --list)
    crontab -l 2>/dev/null | grep "# $TAG" || echo "(no pending one-shots)"; exit 0;;
  --cancel)
    id="${2:?id}"; crontab -l 2>/dev/null | grep -v "# $TAG $id\$" | crontab -; echo "cancelled $id"; exit 0;;
  --clear-app)
    app="${2:?app}"; crontab -l 2>/dev/null | grep -v "# $TAG [0-9]*-$app\$" | crontab -; echo "cleared one-shots for $app"; exit 0;;
  __fire)
    id="${2:?}"; app="${3:?}"; mode="${4:-full}"
    crontab -l 2>/dev/null | grep -v "# $TAG $id\$" | crontab -      # self-delete first
    echo "===== $(date '+%F %T %Z') one-shot fire id=$id app=$app mode=$mode =====" >> "$LOG"
    exec "$RUN_DAILY" "$app" "$mode";;
esac

APP="${1:?app (hioto|tone|...) required}"
WHEN="${2:-now}"
MODE="${3:-full}"
valid_app "$APP" || { echo "unknown app: $APP (see apps.json)"; exit 2; }

if [ "$WHEN" = "now" ]; then
  echo "===== $(date '+%F %T %Z') one-shot NOW app=$APP mode=$MODE =====" >> "$LOG"
  setsid bash "$RUN_DAILY" "$APP" "$MODE" >> "$LOG" 2>&1 < /dev/null &
  echo "launched $APP ($MODE) now (pid $!). tail -f $LOG"
  exit 0
fi

# compute the fire datetime. Past explicit datetimes fall back to ~now+2min so a
# backlogged post still goes out promptly instead of waiting a year for the DOM.
read -r MIN HOUR DOM MON ISO < <(python3 - "$WHEN" <<'PY'
import sys, datetime
w = sys.argv[1].strip()
now = datetime.datetime.now()
try:
    if len(w) <= 5:                       # "HH:MM" -> today, or tomorrow if past
        t = datetime.datetime.strptime(w, "%H:%M").time()
        dt = datetime.datetime.combine(now.date(), t)
        if dt <= now: dt += datetime.timedelta(days=1)
    else:                                 # "YYYY-MM-DD HH:MM"
        dt = datetime.datetime.strptime(w, "%Y-%m-%d %H:%M")
        if dt <= now: dt = now + datetime.timedelta(minutes=2)   # overdue -> soon
except ValueError:
    print("ERR"); sys.exit(0)
print(dt.minute, dt.hour, dt.day, dt.month, dt.strftime("%Y-%m-%d %H:%M"))
PY
)
[ "${MIN:-ERR}" = "ERR" ] && { echo "bad time: $WHEN (use HH:MM or 'YYYY-MM-DD HH:MM')"; exit 2; }

ID="$(date +%s%N | cut -c1-13)-$APP"
LINE="$MIN $HOUR $DOM $MON * $SELF __fire $ID $APP $MODE   # $TAG $ID"
( crontab -l 2>/dev/null; echo "$LINE" ) | crontab -
echo "scheduled one-shot: app=$APP mode=$MODE at $ISO JST (id=$ID)"
echo "  cancel: $SELF --cancel $ID   |   list: $SELF --list"
