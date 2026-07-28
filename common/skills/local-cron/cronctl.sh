#!/usr/bin/env bash
# cronctl — ローカル crontab を安全に操作する汎用ドライバ。
#
#   once   : 指定日時に1回だけ実行し、発火した瞬間に自分の crontab 行を消す
#   repeat : 5フィールドの cron 式で繰り返し実行する
#   list / cancel / clear : 登録済みエントリの確認と削除
#
# 設計上の約束（他サーバーへ持って行っても壊れないための3点）:
#   1. crontab に書くパスは $HOME 配下なら "$HOME/..." というリテラルで書く。
#      cron はコマンド欄を /bin/sh -c で実行するので、実行するマシンの $HOME に展開される。
#      ＝ ユーザ名やホームの場所が違うサーバーでも同じ行がそのまま通る。
#   2. 実行したいコマンドは argv を NUL 区切りにして base64 で埋め込む。
#      crontab のコマンド欄は「エスケープされていない % が改行に化ける」という仕様があり、
#      引用符の入り組んだコマンドを直に書くと壊れる。base64 の文字種には % が無いので安全。
#      引数の境界も保たれる＝スペースを含む引数がバラけない。
#   3. crontab の読み書きは flock で直列化する。crontab -l | ... | crontab - は
#      read-modify-write なので、ワンショットの自己削除と別プロセスの登録が重なると行が消える。
#
# Usage:
#   cronctl.sh once   <when>      [opts] -- <command> [args...]
#   cronctl.sh repeat <cron-expr> [opts] -- <command> [args...]
#   cronctl.sh now                [opts] -- <command> [args...]
#   cronctl.sh list   [--tag TAG]
#   cronctl.sh cancel <id>
#   cronctl.sh clear  [--tag TAG] [--match SUBSTR]
#
#   <when>      "HH:MM" | "YYYY-MM-DD HH:MM" | "+15m" | "+2h" | "now"
#   <cron-expr> "M H DOM MON DOW"  例: "12 0 * * *"
#
#   opts:
#     --tag TAG      グループ名。list/clear の絞り込みに使う（既定: CRONCTL）
#     --label TEXT   人間向けの識別子。clear --match の対象にもなる
#     --log FILE     実行の stdout/stderr をこのファイルに追記する
#     --id ID        ID を自分で決める（既定: <epoch ms>-<label>）
#
# Examples:
#   cronctl.sh once "21:10" --tag SNS --label app=hioto --log ~/sns.log -- ~/bin/post.sh hioto
#   cronctl.sh repeat "12 0 * * *" --tag SNS --label nightly -- ~/bin/analyze.sh
#   cronctl.sh list --tag SNS
#   cronctl.sh clear --tag SNS --match app=hioto
set -uo pipefail

export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

SELF="$(readlink -f "${BASH_SOURCE[0]}")"
LOCK="${TMPDIR:-/tmp}/cronctl.$(id -u).lock"
DEFAULT_TAG="CRONCTL"

die() { echo "cronctl: $*" >&2; exit 2; }

# --- $HOME 配下の絶対パスを "$HOME/..." リテラルに畳む（可搬性の肝） ------------
portable_path() {
  local p="$1"
  case "$p" in
    "$HOME"/*) printf '"$HOME/%s"' "${p#"$HOME"/}" ;;
    *)         printf '%q' "$p" ;;
  esac
}

# --- 内部ハンドラ: cron から呼ばれる ------------------------------------------
case "${1:-}" in
  __fire|__run)
    verb="$1"; id="${2:?id}"; b64="${3:?payload}"; logf="${4:-}"
    if [ "$verb" = "__fire" ]; then
      # 先に自分を消す。コマンドが失敗しても長時間走っても、行は必ず片付く。
      exec 9>"$LOCK"; flock 9
      crontab -l 2>/dev/null | grep -v "# CRONCTL-ID ${id}\$" | grep -v '^$' | crontab - 2>/dev/null
      exec 9>&-
    fi
    mapfile -d '' -t RAW < <(printf '%s' "$b64" | base64 -d)
    # printf '%s\0' は末尾にも NUL を付けるので空の最終要素が出る。ここで捨てつつ、
    # 登録時に畳んだ %HOME% を実行するマシンの $HOME に戻す（＝別サーバーでも通る）。
    ARGS=()
    for a in "${RAW[@]}"; do
      [ -z "$a" ] && continue
      case "$a" in
        "%HOME%/"*) ARGS+=("$HOME/${a#%HOME%/}") ;;
        *)          ARGS+=("$a") ;;
      esac
    done
    [ "${#ARGS[@]}" -eq 0 ] && exit 0
    if [ -n "$logf" ]; then
      mkdir -p "$(dirname "$logf")" 2>/dev/null
      echo "===== $(date '+%F %T %Z') cronctl fire id=$id cmd=${ARGS[*]} =====" >> "$logf"
      exec "${ARGS[@]}" >> "$logf" 2>&1
    fi
    exec "${ARGS[@]}"
    ;;
esac

ACTION="${1:-}"; shift || true
[ -z "$ACTION" ] && die "action required (once|repeat|now|list|cancel|clear). See --help in the file header."

# --- list / cancel / clear -----------------------------------------------------
case "$ACTION" in
  list)
    TAG=""
    while [ $# -gt 0 ]; do case "$1" in --tag) TAG="${2:?}"; shift 2;; *) shift;; esac; done
    out="$(crontab -l 2>/dev/null | grep '# CRONCTL-ID ')"
    [ -n "$TAG" ] && out="$(printf '%s\n' "$out" | grep "# CRONCTL-TAG $TAG ")"
    if [ -z "$out" ]; then echo "(no cronctl entries${TAG:+ for tag $TAG})"; else printf '%s\n' "$out"; fi
    exit 0;;
  cancel)
    id="${1:?cancel <id>}"
    exec 9>"$LOCK"; flock 9
    before="$(crontab -l 2>/dev/null | wc -l)"
    crontab -l 2>/dev/null | grep -v "# CRONCTL-ID ${id}\$" | grep -v '^$' | crontab -
    after="$(crontab -l 2>/dev/null | wc -l)"
    exec 9>&-
    [ "$before" -eq "$after" ] && { echo "no entry with id=$id"; exit 1; }
    echo "cancelled $id"; exit 0;;
  clear)
    TAG=""; MATCH=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --tag)   TAG="${2:?}";   shift 2;;
        --match) MATCH="${2:?}"; shift 2;;
        *) shift;;
      esac
    done
    [ -z "$TAG" ] && [ -z "$MATCH" ] && die "clear needs --tag and/or --match (refusing to wipe every entry)"
    exec 9>"$LOCK"; flock 9
    keep="$(crontab -l 2>/dev/null)"
    drop="$(printf '%s\n' "$keep" | grep '# CRONCTL-ID ')"
    [ -n "$TAG" ]   && drop="$(printf '%s\n' "$drop" | grep "# CRONCTL-TAG $TAG ")"
    [ -n "$MATCH" ] && drop="$(printf '%s\n' "$drop" | grep -F -- "$MATCH")"
    n=0
    if [ -n "$drop" ]; then
      n="$(printf '%s\n' "$drop" | grep -c .)"
      keep="$(printf '%s\n' "$keep" | grep -vxF -f <(printf '%s\n' "$drop"))"
    fi
    printf '%s\n' "$keep" | grep -v '^$' | crontab -
    exec 9>&-
    echo "cleared $n entry(ies)"; exit 0;;
esac

# --- once / repeat / now -------------------------------------------------------
WHEN=""
[ "$ACTION" != "now" ] && { WHEN="${1:?<when> or <cron-expr> required}"; shift; }

TAG="$DEFAULT_TAG"; LABEL=""; LOGF=""; ID=""
while [ $# -gt 0 ]; do
  case "$1" in
    --tag)   TAG="${2:?}";   shift 2;;
    --label) LABEL="${2:?}"; shift 2;;
    --log)   LOGF="$(readlink -m "${2:?}")"; shift 2;;
    --id)    ID="${2:?}";    shift 2;;
    --)      shift; break;;
    *) die "unknown option: $1";;
  esac
done
[ $# -eq 0 ] && die "no command after --"

# タグ/ラベルは crontab のコメント欄に入る。空白と % を持ち込ませない。
sanitize() { printf '%s' "$1" | tr -c 'A-Za-z0-9_.:=+-' '-'; }
TAG="$(sanitize "$TAG")"
LABEL="$(sanitize "$LABEL")"

# 実行するコマンド。相対パスは cron の作業ディレクトリ($HOME)基準になって事故るので、
# 先頭要素がファイルとして見つかるなら絶対パスへ解決しておく。
CMD=("$@")
if [ -e "${CMD[0]}" ]; then CMD[0]="$(readlink -f "${CMD[0]}")"; fi
# base64 の中身は exec に直接渡る＝シェルを通らないので "$HOME" と書いても展開されない。
# そこで登録時に $HOME 配下のパスを %HOME% に畳み、発火時に実マシンの $HOME へ戻す。
# これで crontab の行が丸ごとマシン非依存になる（cronctl 自身のパスもコマンドのパスも）。
PCMD=()
for a in "${CMD[@]}"; do
  case "$a" in
    "$HOME"/*) PCMD+=("%HOME%/${a#"$HOME"/}") ;;
    *)         PCMD+=("$a") ;;
  esac
done
PAYLOAD="$(printf '%s\0' "${PCMD[@]}" | base64 -w0)"

[ -z "$ID" ] && ID="$(date +%s%N | cut -c1-13)${LABEL:+-$LABEL}"

# 即時実行（cron を経由せずデタッチして走らせる）
if [ "$ACTION" = "now" ]; then
  if [ -n "$LOGF" ]; then
    mkdir -p "$(dirname "$LOGF")" 2>/dev/null
    echo "===== $(date '+%F %T %Z') cronctl now cmd=${CMD[*]} =====" >> "$LOGF"
    setsid "${CMD[@]}" >> "$LOGF" 2>&1 < /dev/null &
  else
    setsid "${CMD[@]}" >/dev/null 2>&1 < /dev/null &
  fi
  echo "launched now (pid $!)${LOGF:+ — tail -f $LOGF}"
  exit 0
fi

if [ "$ACTION" = "repeat" ]; then
  # 5フィールドの cron 式をそのまま使う。
  # set -f を挟まないと "12 0 * * *" の * がカレントディレクトリのファイル名に
  # glob 展開されて cron 式が壊れる（crontab が bad day-of-month で弾く）。
  set -f; set -- $WHEN; set +f
  [ $# -ne 5 ] && die "cron-expr must have 5 fields: \"M H DOM MON DOW\" (got: $WHEN)"
  SCHED="$1 $2 $3 $4 $5"; VERB="__run"; HUMAN="$SCHED"
elif [ "$ACTION" = "once" ]; then
  read -r MIN HOUR DOM MON HUMAN < <(python3 - "$WHEN" <<'PY'
import sys, datetime, re
w = sys.argv[1].strip()
now = datetime.datetime.now()
dt = None
m = re.fullmatch(r'\+(\d+)([mh])', w)
if m:
    n = int(m.group(1))
    dt = now + (datetime.timedelta(minutes=n) if m.group(2) == 'm' else datetime.timedelta(hours=n))
elif re.fullmatch(r'\d{1,2}:\d{2}', w):
    t = datetime.datetime.strptime(w, "%H:%M").time()
    dt = datetime.datetime.combine(now.date(), t)
    if dt <= now:                       # 過ぎていれば翌日
        dt += datetime.timedelta(days=1)
else:
    for fmt in ("%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            dt = datetime.datetime.strptime(w, fmt); break
        except ValueError:
            pass
    if dt is None:
        print("ERR"); sys.exit(0)
    if dt <= now:                       # 過ぎた指定は「すぐ」に倒す（1年待たせない）
        dt = now + datetime.timedelta(minutes=2)
print(dt.minute, dt.hour, dt.day, dt.month, dt.strftime("%Y-%m-%d %H:%M"))
PY
)
  [ "${MIN:-ERR}" = "ERR" ] && die "bad time: $WHEN (use HH:MM / 'YYYY-MM-DD HH:MM' / +15m / +2h)"
  # DOW は * のまま。DOM と MON を固定すれば年内で一意に決まり、発火時に自分を消すので重複しない。
  SCHED="$MIN $HOUR $DOM $MON *"; VERB="__fire"
else
  die "unknown action: $ACTION"
fi

SELF_P="$(portable_path "$SELF")"
LOG_P=""; [ -n "$LOGF" ] && LOG_P=" $(portable_path "$LOGF")"
LINE="$SCHED /bin/bash $SELF_P $VERB $ID $PAYLOAD$LOG_P   # CRONCTL-TAG $TAG # CRONCTL-ID $ID"

exec 9>"$LOCK"; flock 9
( crontab -l 2>/dev/null; printf '%s\n' "$LINE" ) | grep -v '^$' | crontab - || { exec 9>&-; die "crontab install failed"; }
exec 9>&-

echo "scheduled: id=$ID tag=$TAG at $HUMAN"
echo "  cmd:    ${CMD[*]}"
echo "  cancel: $SELF cancel $ID"
