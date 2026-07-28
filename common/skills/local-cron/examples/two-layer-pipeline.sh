#!/usr/bin/env bash
# =============================================================================
# サンプル: cronctl.sh を使った2層パイプライン
#
#   [毎晩 00:12] analyze  … 対象を日替わりで1つ選び、考えて、成果物を作り、
#                            「その日のうちの最適な時刻」に実行ジョブを仕込む
#   [その日 21:10] run    … 仕込まれたワンショットが発火。**まず自分の crontab 行を
#                            消してから**本番処理を実行する
#
# そのままコピーして自分のドメイン向けに書き換えることを想定した雛形。
# 動作を見たいだけなら:  ./two-layer-pipeline.sh install   →  ./two-layer-pipeline.sh list
# =============================================================================
set -uo pipefail
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

# --- 自分の位置から全部を導出する（絶対パスを直書きしない＝別サーバーでも動く） ---
SELF="$(readlink -f "${BASH_SOURCE[0]}")"
HERE="$(dirname "$SELF")"
CRONCTL="$(readlink -f "$HERE/../cronctl.sh")"

TAG="DEMO"                                  # このパイプラインが使う crontab 上のグループ名
LOG="${DEMO_LOG:-$HOME/.local/state/two-layer-demo.log}"
TARGETS=(alpha bravo charlie)               # 日替わりローテーションの対象

log() { mkdir -p "$(dirname "$LOG")"; echo "$(date '+%F %T %Z') | $*" >> "$LOG"; }

# --- 日替わりで対象を1つ選ぶ（年内通算日 % 個数）------------------------------
pick_target() {
  local doy; doy="$(date +%j)"
  echo "${TARGETS[$((10#$doy % ${#TARGETS[@]}))]}"
}

# --- 実行時刻を決める（ここに自分のドメインのルールを書く）--------------------
# 例: 平日は 21:10、金土は 18:30。
golden_time() {
  case "$(date +%u)" in
    5|6) echo "18:30" ;;
    *)   echo "21:10" ;;
  esac
}

case "${1:-}" in

  # ---------------------------------------------------------------------------
  # 1層目: 毎晩の分析。crontab に repeat で常駐させる。
  # ---------------------------------------------------------------------------
  analyze)
    TARGET="$(pick_target)"
    log "analyze start target=$TARGET"

    # …ここで本来の分析・立案・生成をする…
    # 例: claude -p "<プロンプト>" --dangerously-skip-permissions >> "$LOG" 2>&1
    log "analyze done target=$TARGET"

    # --- 後続を仕込む -------------------------------------------------------
    # 冪等にするため、**仕込む前に自分のタグ＋対象の分だけ消す**。
    # 毎晩 clear→再arm すれば、途中で失敗した日があっても翌晩に自然に復旧する。
    "$CRONCTL" clear --tag "$TAG" --match "target=$TARGET" >> "$LOG" 2>&1

    WHEN="$(golden_time)"
    "$CRONCTL" once "$WHEN" \
      --tag "$TAG" --label "target=$TARGET" --log "$LOG" \
      -- "$SELF" run "$TARGET"
    log "armed one-shot target=$TARGET at $WHEN"
    ;;

  # ---------------------------------------------------------------------------
  # 2層目: ワンショットから発火する本番処理。
  # cronctl の __fire が「先に自分の crontab 行を削除」してからこれを呼ぶので、
  # ここでは後始末を気にしなくてよい（失敗しても長時間走っても行は残らない）。
  # ---------------------------------------------------------------------------
  run)
    TARGET="${2:?run <target>}"
    log "run start target=$TARGET"

    # …ここで本番の実行（実機操作・投稿・デプロイなど）…
    log "run done target=$TARGET"
    ;;

  # ---------------------------------------------------------------------------
  # 常駐させる／外す／見る
  # ---------------------------------------------------------------------------
  install)
    "$CRONCTL" repeat "12 0 * * *" --tag "$TAG" --label nightly --log "$LOG" -- "$SELF" analyze
    echo "installed. log: $LOG"
    ;;
  uninstall)
    "$CRONCTL" clear --tag "$TAG"
    ;;
  list)
    "$CRONCTL" list --tag "$TAG"
    ;;
  *)
    echo "usage: $(basename "$SELF") {install|uninstall|list|analyze|run <target>}" >&2
    exit 2
    ;;
esac
