#!/usr/bin/env bash
# Capture a platform's profile grid (for reading per-post view counts) into a dir.
# The numbers are READ by the Claude session from these screenshots (model vision),
# not by an OCR binary — so this script only needs to navigate + capture cleanly.
#
# Usage: scrape_profile.sh <tiktok|lemon8> <outdir> [rows_scrolls]
#   outdir            where grid_NN.png are written
#   rows_scrolls      how many scroll-and-capture passes (default 3 ~= 9-12 posts)
#
# Coords are Pixel-7 (1080x2400, 3-button nav) starting points — re-verify if the
# device/profile layout differs. The session should open the first screenshot and
# sanity-check it actually shows the profile grid before trusting the rest.

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"; source "$DIR/lib.sh"

PLAT="${1:?platform: tiktok|lemon8}"
OUT="${2:?outdir}"; mkdir -p "$OUT"
PASSES="${3:-3}"

case "$PLAT" in
  tiktok) PKG=com.ss.android.ugc.trill; PROFILE_TAP="965 2265";;
  lemon8) PKG=com.bd.nproject;          PROFILE_TAP="945 2258";;
  *) echo "unknown platform $PLAT" >&2; exit 2;;
esac

free_cpu
mem_guard 2500 || mem_reclaim   # low RAM -> swap thrash -> laggy scroll/capture; reclaim first
keep_awake_on          # critical: profile scroll/capture takes >30s; don't let the screen sleep
# wake the (dozing) screen and get to a clean home; no PIN keyguard on this device.
adb shell input keyevent KEYCODE_WAKEUP; sleep 0.5
adb shell input keyevent KEYCODE_HOME;   sleep 0.5     # dismiss notification shade / stale view
adb shell am force-stop "$PKG"; sleep 2   # clean state: avoid landing on a stale view/other profile
launch "$PKG"; sleep 10
tap $PROFILE_TAP; sleep 4          # go to profile
# if the tap opened a video/other view instead of the profile, back out and retry once
focus | grep -qi "$PKG" || { back; sleep 1; tap $PROFILE_TAP; sleep 3; }

# CRITICAL: scroll to the ABSOLUTE TOP of the profile first. Hioto posts (distinctive
# film-look covers with the "h Hioto" wordmark) sit at/near the top (pinned or recent),
# while this account's many other posts (walks/app-promos) push them down if we capture
# mid-grid. Swipe DOWN repeatedly to reach the top, then capture top-first.
for i in 1 2 3 4 5 6; do swipe 540 800 540 1900 250; sleep 0.5; done
sleep 1

for i in $(seq 1 "$PASSES"); do
  f=$(printf "%s/grid_%02d.png" "$OUT" "$i")
  adb exec-out screencap -p > "$f"
  echo "captured $f"
  [ "$i" -lt "$PASSES" ] && { swipe 540 1700 540 800 350; sleep 1.5; }   # next: reveal older
done
echo "DONE platform=$PLAT out=$OUT (top-first)"
