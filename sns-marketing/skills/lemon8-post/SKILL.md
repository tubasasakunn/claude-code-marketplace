---
name: lemon8-post
description: Post an image carousel + title + body + hashtags to Lemon8 on a USB-debugging Android phone via adb UI automation. Use when the user wants to publish/post a Hioto post (postN) or a set of images to Lemon8 from the connected device. Handles image download, Japanese/emoji long-body input, ordered multi-image selection, the 5-hashtag limit, and disabling cross-post to TikTok.
---

# Lemon8 image-carousel posting (Android / adb)

Automates publishing a carousel post to Lemon8 (`com.bd.nproject`) on a USB-debug Android
device through `adb` UI automation.

This is a **real public post to the user's account** — confirm scope (which post, which
account) before the final tap, then publish.

## Inputs
- A Hioto post id like `post3` (content from `https://hioto.basaapp.com/post/manifest.json`),
  OR user-supplied images (carousel order) + title/body/hashtags. The sns-daily-pipeline
  drives any apps.json app (hioto / tone / anki / …) via this second path: a device album
  `<album_prefix>_<id>_<platform>` + that platform's `index.json` — the source app is
  irrelevant to this skill.
- Device PIN if locked.

## ⚠️ Coordinates are device-specific
Coords below are from **Pixel 7, 1080x2400, 3-button nav** and are **starting points**.
Album rows and the gallery grid order shift between runs — **screenshot and re-measure** before
taps that matter. `scripts/crop.py <img> x0 y0 x1 y1 out 2` zooms a region; `real = crop_offset + measured`.
Lemon8's normal screens DO expose the view hierarchy, so `adb shell uiautomator dump` can help
locate elements when a screenshot is ambiguous.

## Setup (run once per session)
```bash
cd ${CLAUDE_PLUGIN_ROOT}/skills/lemon8-post/scripts
source lib.sh
adb devices -l
wake_unlock "<PIN>"          # only if locked
keep_awake_on
free_cpu                     # cancel bg dexopt (ANR prevention)
mem_guard 2500               # ⚠️ #1 reliability fix: reclaim RAM so taps don't derail (see below)
kb_install; kb_save_orig; kb_on
```

## ⚠️ Memory is the #1 cause of failure — reclaim before driving (verified 2026-06-23)
Lemon8 holds ~750MB; under low `MemAvailable` the device thrashes ZRAM swap, transitions lag,
and **fixed-coordinate `tap`s land on the wrong / still-rendering UI** (selection toggles dead,
stale picker frame, mis-ordered carousel). No root (no `drop_caches`), so reclaim with:
- `mem_guard 2500` — call right before launching: cancels dexopt, `am kill-all`, force-stops heavy
  non-target apps (`MEM_HEAVY_APPS` in lib.sh), re-measures.
- `fresh_launch com.bd.nproject` — force-stop + cold launch (less RAM, known start screen).
- Taps misbehaving mid-flow → `mem_reclaim`, wait ~3s, retry the step. On Lemon8 (hierarchy IS
  exposed) prefer `tap_node`/`ui_center` to relocate the node each time instead of blind coords.

Fetch + push content (Lemon8 images are 3:4):
```bash
python3 fetch_post.py post3 lemon8
push_images /sdcard/Pictures/post3_lemon8 /tmp/sns_post/post3_lemon8/*.png
```
Build a labelled contact sheet of the images — in the picker you identify cells by **content**.

## Posting flow (screenshot + verify after every step)
| # | Step | Pixel-7 coords | Notes |
|---|------|----------------|-------|
| 1 | `mem_guard 2500; fresh_launch com.bd.nproject`; wait ~10s | — | reclaim RAM, then cold-launch; feed (MainActivity) |
| 2 | Tap **+** (yellow, center) | `540 2240` | opens picker (PostToolsEntranceActivity) |
| 3 | Open **album dropdown** ("ギャラリー ▾", top-left) | `140 410` | tap the label center; pick the album with just your images |
| 4 | Select album (e.g. post3_lemon8) | re-measure row | grid then shows only those 6 |
| 5 | **Select images in carousel order** | per image: tap cell → preview → "選択する" `160 2235` → BACK | In Lemon8 the cell **circle is small/unreliable** and tapping the cell opens a **preview**. The robust path: tap the cell, the preview's top shows `NN/06`, tap **選択する** (bottom-left), press BACK, repeat for 01→06. Selection order = carousel order. |
|   | grid cell centers (this album) | row1 `(180,680)(540,680)(900,680)` row2 `(180,1180)(540,1180)(900,1180)` | content order is NOT filename order — confirm each via the preview's `NN/06` |
| 6 | Confirm **次へ(6)**, tap it | `920 2235` | → image editor (EditorActivity) |
| 7 | Editor **次へ** (yellow) | `540 2225` | → publish (PublishActivity). Keep taps off the nav bar (y>2300 → home) |
| 8 | Tap **title field** ("見出しを追加") | `250 565` | |
| 9 | Type title with `kb_type` | — | e.g. `SNSじゃない“自分だけ”の動画日記が落ち着く📔` |
| 10 | Tap **body field** ("投稿について説明しましょう") | `250 720` | |
| 11 | Type body + **≤5 hashtags** with `kb_type_file body.txt` | — | **Lemon8 hashtag max = 5** — more triggers a warning and can block publish. Lemon8 allows a long body, so put the full post body + 5 tags. Re-enter via `kb_clear` then type again if needed. |
| 12 | Turn **OFF "TikTokにシェア"** toggle | `990 1355` | default ON → would cross-post a duplicate to TikTok. Confirm it goes grey. |
| 13 | Tap **投稿する** (yellow) | `710 2200` | publishes; returns to MainActivity |
| 14 | Dismiss any post-publish share sheet / notification dialog | BACK / × `984 963` | |

## Body + hashtags (full body OK, 5 tags max)
Lemon8 allows a long description. Put the full post body, then 5 hashtags. Input from a file to
preserve newlines/emoji:
```bash
kb_type_file /tmp/sns_post/post3_lemon8/body.txt   # body (from manifest)
# then append 5 hashtags (trim the manifest's 10 → 5 most relevant):
kb_type $'\n#日記 #ライフログ #日記アプリ #動画日記 #プライバシー'
```
(fetch_post.py writes title.txt / body.txt / hashtags.txt; the manifest may list 10 hashtags —
keep only 5.)

## Verify success
After 投稿する, Lemon8 returns to the feed and shows a share sheet / your post. Open **profile**
(bottom-right ≈ `980 2310`) and confirm your post appears with the title, body, and the
carousel (the share-sheet card shows a `01/06` first slide).

## Teardown
```bash
kb_off
keep_awake_off
```

## Self-recovery — solve irregularities yourself, don't bail to the user
Goal = **a correct post lands**. Recover in-flow rather than stopping. Verify after every step
that matters; if wrong, back out and retry. Lemon8 exposes its view hierarchy, so use it:
1. **Verify, don't assume.** `ui_dump` / screenshot and confirm: the preview's `NN/06`, `次へ(6)`,
   the "TikTokにシェア" toggle is OFF (grey), title/body populated. If it doesn't match, recover.
2. **Recover to a known state.** `back` to the prior screen (or force-stop + `fresh_launch`;
   the draft of selected images is preserved and you resume in the editor). Re-measure from a
   fresh screenshot each retry.
3. **Non-deterministic taps = memory thrash** → `mem_reclaim`, wait ~3s, retry; prefer
   `tap_node`/`ui_center` over blind coords for the picker cells and the share toggle.
4. **Bounded retries.** Step ≤3×, whole post ≤2× (force-stop → fresh_launch → re-enter). Schedule
   stays `queued` until success — a lost attempt retries next run; a **wrong post does not**.
5. **Hard stop only to avoid a wrong post** (e.g. duplicate cross-post toggle stuck ON, wrong
   carousel order you can't fix). Stop BEFORE 投稿する, leave `queued`, notify (below).

### Known failure modes & in-flow fix
- **Tapping a cell opens a preview, not a selection** → expected; use the preview's **選択する** button.
- **Publish blocked / hashtag warning** → more than 5 hashtags; cut to 5 and retry.
- **A duplicate appears on TikTok** → "TikTokにシェア" left ON; verify it's OFF (grey) before 投稿する.
- **Edit screen jumped to launcher** → re-open Lemon8; the draft is preserved, resume in editor.
- **ANR / sluggish / dead toggles** → `free_cpu` + `mem_reclaim`, `ui_settle`, retry.

## harness report (Slack on success, LINE on exception)
- **On success** — including a post that needed in-flow recovery — send ONE **Slack** completion
  report (llms.txt routine-report channel):
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sns-daily-pipeline/scripts/harness.py slack --text "[<app>] Lemon8 公開: <title/what>"`.
- **On hard failure** — retries exhausted and you stopped to avoid a wrong post, or adb/device is
  gone — send ONE **LINE** alert (not Slack):
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sns-daily-pipeline/scripts/harness.py push --text "[<app>] <what failed, after N retries>"`.
Token in `sns-daily-pipeline/.harness.env`.
