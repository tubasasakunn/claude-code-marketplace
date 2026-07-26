#!/usr/bin/env bash
# Shared ADB helpers for UI-automated posting (TikTok / Lemon8).
# Source this:  source lib.sh
# Requires: adb (device in USB debug mode, unlocked).

set -uo pipefail

WORKDIR="${WORKDIR:-/tmp/sns_post}"
mkdir -p "$WORKDIR"

ADBKB_APK_URL="https://github.com/senzhk/ADBKeyBoard/raw/master/ADBKeyboard.apk"
ADBKB_IME="com.android.adbkeyboard/.AdbIME"

adb_dev() { adb devices -l | grep -E "\sdevice\s" | head -1; }

# --- screen / power ---
wake_unlock() {
  # $1 = optional PIN. Wakes screen and unlocks with swipe-up + PIN if given.
  adb shell input keyevent KEYCODE_WAKEUP; sleep 0.6
  local showing
  showing=$(adb shell dumpsys window 2>/dev/null | grep -m1 mIsShowing | tr -d ' \r')
  adb shell input swipe 540 1900 540 600 200; sleep 0.6
  if [ -n "${1:-}" ]; then
    adb shell input text "$1"; sleep 0.3
    adb shell input keyevent KEYCODE_ENTER; sleep 1
  fi
}

keep_awake_on()  { adb shell settings put system screen_off_timeout 600000; adb shell svc power stayon true; }
keep_awake_off() { adb shell settings put system screen_off_timeout 30000;  adb shell svc power stayon false; }

# Cancel background dex optimization (artd/dex2oat) that hogs CPU and causes ANRs
# right after an app update. Safe: the OS reschedules it later.
free_cpu() { adb shell pm bg-dexopt-job --cancel >/dev/null 2>&1; adb shell cmd package bg-dexopt-job --cancel >/dev/null 2>&1; }

# --- screenshots ---
shot() { # shot <name> -> saves $WORKDIR/<name>.png and prints the path
  local f="$WORKDIR/${1:-shot}.png"
  adb exec-out screencap -p > "$f"; echo "$f"
}
focus() { adb shell dumpsys window 2>/dev/null | grep -m1 mCurrentFocus; }

# --- ADBKeyboard (UTF-8 / emoji / newline input) ---
kb_install() {
  if ! adb shell pm list packages 2>/dev/null | grep -q com.android.adbkeyboard; then
    curl -sL -o "$WORKDIR/ADBKeyboard.apk" "$ADBKB_APK_URL"
    adb install -r "$WORKDIR/ADBKeyboard.apk" >/dev/null 2>&1
  fi
  adb shell ime enable "$ADBKB_IME" >/dev/null 2>&1
}
kb_save_orig() { adb shell settings get secure default_input_method | tr -d '\r' > "$WORKDIR/orig_ime.txt"; }
kb_on()  { adb shell ime set "$ADBKB_IME" >/dev/null 2>&1; sleep 0.5; }
kb_off() { local o; o=$(cat "$WORKDIR/orig_ime.txt" 2>/dev/null); [ -n "$o" ] && adb shell ime set "$o" >/dev/null 2>&1; }

kb_type() { # kb_type "text with japanese / emoji / \n"  (inserts at cursor)
  local b64; b64=$(printf '%s' "$1" | base64 | tr -d '\n')
  adb shell am broadcast -a ADB_INPUT_B64 --es msg "$b64" >/dev/null 2>&1
}
kb_type_file() { # kb_type_file path  (file content -> input, preserves newlines/emoji)
  local b64; b64=$(base64 -w0 "$1")
  adb shell am broadcast -a ADB_INPUT_B64 --es msg "$b64" >/dev/null 2>&1
}
kb_clear() { adb shell am broadcast -a ADB_CLEAR_TEXT >/dev/null 2>&1; }

# --- gestures ---
tap()   { adb shell input tap "$1" "$2"; }
swipe() { adb shell input swipe "$1" "$2" "$3" "$4" "${5:-250}"; }
back()  { adb shell input keyevent KEYCODE_BACK; }

# --- media ---
push_images() { # push_images <dest_dir_on_device> <local_file...>
  local dest="$1"; shift
  adb shell mkdir -p "$dest" >/dev/null 2>&1
  for f in "$@"; do
    adb push "$f" "$dest/$(basename "$f")" >/dev/null 2>&1
    adb shell "am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file://$dest/$(basename "$f")" >/dev/null 2>&1
  done
}

launch() { # launch <package>
  adb shell monkey -p "$1" -c android.intent.category.LAUNCHER 1 >/dev/null 2>&1
}

# ============================================================
# Memory management — the #1 cause of flaky posting runs.
# Root cause (verified 2026-06-23): when MemAvailable is low the device
# thrashes ZRAM swap; the foreground app (TikTok/Lemon8 each hold ~750MB-1.2GB)
# lags on every transition, so fixed-coordinate `input tap`s land on the
# wrong / still-rendering UI -> non-deterministic derailment (1 tap selects
# 6 images, toggles don't register, etc). We have NO root (no drop_caches),
# so we reclaim with shell-uid primitives only.
# ============================================================

# Heavy, non-essential apps safe to force-stop before a run. NEVER list the
# target apps, systemui, launcher, ADBKeyboard, or the active IME here.
# Override per-environment by exporting MEM_HEAVY_APPS before sourcing.
MEM_HEAVY_APPS="${MEM_HEAVY_APPS:-com.instagram.android com.instagram.barcelona vivino.web.app com.linkedin.android com.Slack com.android.chrome com.google.android.apps.youtube.music com.google.android.gm com.google.android.apps.maps app.whoo com.theswitchbot.switchbot pl.powsty.colorharmony com.google.android.apps.chromecast.app com.google.android.apps.messaging com.google.android.GoogleCamera jp.naver.line.android}"

mem_avail() { # -> MemAvailable in MB (integer)
  adb shell cat /proc/meminfo 2>/dev/null | awk '/MemAvailable/{print int($2/1024)}'
}

mem_reclaim() { # free RAM: cancel dexopt + kill cached bg + force-stop heavy non-target apps
  free_cpu
  adb shell am kill-all >/dev/null 2>&1
  local p
  for p in $MEM_HEAVY_APPS; do adb shell am force-stop "$p" >/dev/null 2>&1; done
  sleep 1
}

# Ensure enough free RAM before driving an app. Reclaims if below threshold,
# re-measures, and (best effort) keeps going. Call right before launching the
# target app. Default threshold 2500MB leaves headroom for a ~1.2GB app + image decode.
mem_guard() { # mem_guard [min_mb]
  local min="${1:-2500}" a
  a=$(mem_avail); echo "[mem] available=${a}MB (want>=${min}MB)" >&2
  if [ "${a:-0}" -lt "$min" ]; then
    mem_reclaim
    a=$(mem_avail); echo "[mem] after reclaim=${a}MB" >&2
  fi
  [ "${a:-0}" -ge "$min" ]
}

# Force-stop the target app then relaunch it cold. A freshly-started app uses
# far less RAM than a long-lived one with leaked/cached state, and starts from
# a known screen — both make the flow more deterministic.
fresh_launch() { # fresh_launch <package>
  adb shell am force-stop "$1" >/dev/null 2>&1; sleep 1
  launch "$1"; sleep 4
}

# ============================================================
# UI introspection & self-healing taps (uiautomator-based).
# Tapping on-screen *content* (relocated each time) + verifying the result
# is what survives lag, layout shifts and thrash. uiautomator dump works on
# the TikTok/Lemon8 picker & edit screens (NOT the TikTok camera/secure
# surface — there, keep using measured coords + screenshots).
# ============================================================

ui_dump() { # dump hierarchy -> $WORKDIR/ui.xml (retry); prints path, rc=1 if all fail
  local out="$WORKDIR/ui.xml" i
  for i in 1 2 3; do
    if adb shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1; then
      adb pull /sdcard/ui.xml "$out" >/dev/null 2>&1 && [ -s "$out" ] && { echo "$out"; return 0; }
    fi
    sleep 0.8
  done
  echo "$out"; return 1
}

ui_has() { # ui_has <substring>  -> rc 0 if present in a fresh dump
  ui_dump >/dev/null; grep -qF -- "$1" "$WORKDIR/ui.xml"
}

ui_center() { # ui_center <needle>  -> "x y" center of first node whose tag contains needle
  ui_dump >/dev/null
  python3 - "$1" "$WORKDIR/ui.xml" <<'PY'
import sys,re
needle, path = sys.argv[1], sys.argv[2]
xml = open(path, encoding='utf-8', errors='replace').read()
for m in re.finditer(r'<node\b[^>]*?/?>', xml):
    tag = m.group(0)
    if needle in tag:
        b = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', tag)
        if b:
            x1,y1,x2,y2 = map(int,b.groups())
            print((x1+x2)//2,(y1+y2)//2); break
PY
}

ui_settle() { # wait until two consecutive dumps are identical (screen stopped moving)
  local prev="" cur i tries="${1:-6}"
  for i in $(seq 1 "$tries"); do
    adb shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1
    cur=$(adb shell md5sum /sdcard/ui.xml 2>/dev/null | awk '{print $1}')
    [ -n "$cur" ] && [ "$cur" = "$prev" ] && return 0
    prev="$cur"; sleep 0.6
  done
  return 0
}

# Self-healing tap: locate the node by content and tap its CENTER, retrying up
# to 3x. Success = a verify needle appears, or (if none given) the tapped node
# is gone. Falls back to fixed coords if the node can't be located. This is the
# core fix for thrash-induced mis-taps: re-locating + verifying beats blind coords.
tap_node() { # tap_node <find_needle> [verify_needle] [fallback_x fallback_y]
  local find="$1" verify="${2:-}" fx="${3:-}" fy="${4:-}" i xy
  for i in 1 2 3; do
    xy=$(ui_center "$find")
    if [ -n "$xy" ]; then adb shell input tap $xy
    elif [ -n "$fx" ]; then adb shell input tap "$fx" "$fy"; fi
    ui_settle 4 >/dev/null
    if [ -n "$verify" ]; then ui_has "$verify" && return 0
    else ui_has "$find" || return 0; fi
  done
  return 1
}
