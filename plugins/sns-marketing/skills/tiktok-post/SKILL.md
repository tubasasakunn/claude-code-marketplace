---
name: tiktok-post
description: Post a photo carousel (multiple images) + caption + hashtags to TikTok on a USB-debugging Android phone via adb UI automation. Use when the user wants to publish/post a Hioto post (postN) or a set of images to TikTok from the connected device. Handles image download, Japanese/emoji caption input, multi-image selection, cover, and publish.
---

# TikTok photo-carousel posting (Android / adb)

Automates publishing a **photo carousel** post to TikTok (`com.ss.android.ugc.trill`)
on a USB-debug Android device, driven entirely through `adb` UI automation.

This is a **real public post to the user's account** — confirm scope (which post, which
account) before the final tap, then publish.

## Inputs
- A Hioto post id like `post3` (content from `https://hioto.basaapp.com/post/manifest.json`),
  OR a user-supplied set of images (carousel order) + title/body/hashtags. The
  sns-daily-pipeline drives any apps.json app (hioto / tone / anki / …) via this second
  path: a device album `<album_prefix>_<id>_<platform>` + that platform's `index.json`
  (title / body / hashtags / image order) — the source app is irrelevant to this skill.
- Device PIN if the screen is locked (only if needed).

## ⚠️ Coordinates are device-specific
All tap coordinates below are measured on **Pixel 7, 1080x2400, 3-button nav**. They are
**starting points**. UI elements (album list rows, gallery grid order, button centers) shift
between runs and devices. **Always screenshot and re-measure** before a tap that matters.
Use `scripts/crop.py <img> x0 y0 x1 y1 out 2` to zoom a region and read it; whatever you
measure in the crop maps back as `real = crop_offset + measured`. TikTok's camera/create
screens are a **secure surface** — `uiautomator dump` returns the launcher, not the real UI,
so you MUST locate elements visually from screenshots, not from the view hierarchy.

## Setup (run once per session)
```bash
cd ${CLAUDE_PLUGIN_ROOT}/skills/tiktok-post/scripts
source lib.sh                      # WORKDIR defaults to /tmp/sns_post
adb devices -l                     # confirm a device is connected
adb_pin                            # ⚠️ pin ONE transport if USB + Wi-Fi both show up (see below)
wake_unlock "<PIN>"                # only if locked; omit PIN arg if already unlocked
keep_awake_on                      # stop the screen sleeping mid-flow
free_cpu                           # cancel bg dexopt — prevents ANR storms after app updates
mem_guard 2500                     # ⚠️ #1 reliability fix: reclaim RAM so taps don't derail (see below)
kb_install; kb_save_orig; kb_on    # ADBKeyboard for Japanese/emoji caption
```

## ⚠️ Two transports = every adb call fails
A phone reachable over **both USB and Wi-Fi** (`adb tcpip 5555`) appears twice in
`adb devices`, and then every bare `adb` — i.e. every helper in `lib.sh` — aborts with
`adb: more than one device/emulator`. Mid-run this looks like a random device failure.

```
<serial>             device      ← USB
<phone-ip>:5555      device      ← Wi-Fi
```

`adb_pin` fixes it by exporting `ANDROID_SERIAL`, which adb applies to every later call,
so no helper needs `-s`. It prefers the **TCP** transport: a marginal USB cable
re-enumerates mid-session (`usb N-M: USB disconnect` in `journalctl -k`) and kills the run,
while Wi-Fi rides through it. An already-set `ANDROID_SERIAL` is left alone.

> **Call it bare — `adb_pin`, never `$(adb_pin)`.** Command substitution runs it in a
> subshell, so the `export` is lost and you get the same error one line later.

A dropping USB link is a **cable/port fault, not an adb problem** — data lines degrade long
before charging does. Prefer Wi-Fi for a posting run; `adb connect <ip>:5555` needs no
pairing once `adb tcpip 5555` has been issued (survives until the phone reboots).

## ⚠️ Memory is the #1 cause of failure — reclaim before driving (verified 2026-06-23)
TikTok holds ~750MB–1.2GB; with low `MemAvailable` the device thrashes ZRAM swap, every
screen transition lags, and **fixed-coordinate `tap`s land on the wrong / still-rendering
UI** → non-deterministic derailment (one tap selects 6 images, toggles don't register, the
picker shows a stale frame). The device has **no root** (no `drop_caches`), so reclaim with:
- `mem_guard 2500` — call right before launching. Cancels dexopt, `am kill-all`, force-stops
  a curated list of heavy non-target apps (`MEM_HEAVY_APPS` in lib.sh), re-measures. rc=0 if ≥2.5GB.
- `fresh_launch com.ss.android.ugc.trill` — force-stop then cold-launch: a fresh app uses far
  less RAM and starts from a known screen. Prefer this over a bare `launch` in step 1.
- If taps still misbehave mid-flow: `mem_reclaim` again, then retry the step (see self-recovery).

Fetch + push content (for a Hioto post):
```bash
python3 fetch_post.py post3 tiktok        # downloads 6 images (carousel order) + title/body/hashtags
# images land in /tmp/sns_post/post3_tiktok/  (01_cover.png .. 06_cta.png)
push_images /sdcard/Pictures/post3_tiktok /tmp/sns_post/post3_tiktok/*.png
```
Then build a labelled contact sheet of the images so you can map each one in the picker grid
(content, not filename, is what you see): load each into the conversation or montage them.

> **pickerに専用アルバムが出ない時**：push後にメディアスキャンが要る。各pushファイルに対し `adb shell am broadcast -a android.intent.action.MEDIA_SCANNER_SCAN_FILE -d file:///sdcard/Pictures/<album>/<f>.png`（or フォルダを `content` 経由で登録）。`content query` の bucket 名はクォートで `Invalid token` を踏みやすいので projection で確認する。

## Posting flow (screenshot + verify after every step)
> **★座標の大原則**：会話に表示される/Readするスクショは**縮小表示**（見た目の横幅 ~270px 等）。**tap 座標は実機解像度（1080×2400 等）基準**で渡す＝スクショの見た目pxを `input tap` にそのまま使うと外す。下表の座標は**目安**。**重要タップ（アルバム行・各セルの○・キャプション欄・投稿ボタン）の前は必ず `uiautomator dump`（picker/editor/publishはdump可）で対象 node の bounds 中心を実測**してから押す。`adb shell wm size` で実解像度を確認できる。
| # | Step | Pixel-7 coords | Notes |
|---|------|----------------|-------|
| 1 | `mem_guard 2500; fresh_launch com.ss.android.ugc.trill`; wait ~10s | — | reclaim RAM, then cold-launch; feed loads (splash first) |
| 2 | Tap **+** (create) | `540 2223` | opens camera (SAAActivity). If ANR dialog → tap 待機 and wait. **`2255` (the old value) is ~3px BELOW the button** — measured bottom edge is 2252, so it lands on the system nav bar and does nothing. Crop `0 2050 1080 2400` and measure the + before the first run. |
| 3 | Tap **gallery thumbnail** (bottom-left of camera) | `88 2117` | opens picker. x<70 risks back-gesture |
| 4 | Open **album dropdown** ("最近 ▾" 上部中央) → 専用アルバムを選ぶ | 開く=`540 195` | **★誤爆多発・別アプリ誤投稿の事故ポイント**。ドロップダウンは**トグル**(再タップで閉じる)。開いたら**座標の目分量で行を押さない**(「最近」「Live Photos」等を誤選択しがち)。必ず `uiautomator dump`(picker画面はdump可)で**目的アルバム行のテキスト＝`<album_prefix>_<id>_<platform>` の node bounds を実測**し、その中心をタップ。選択後はグリッドのセル位置も変わるので**再 dump**して○座標を取り直す。**フォールバック**: 専用アルバムが見つからない時のみ「最近」グリッド先頭の**新着N枚(=今アップした画像)** を直接○選択（badge番号で中身を必ず確認）。 |
| 5 | **Select 6 images via the top-right ○ of each cell** | circles ≈ y480 (row1) / y780 (row2), x≈316/655/995 | **CRITICAL**: tapping image CENTER only opens a preview and does NOT select → that bug = only 1 image posts. Tap the **circle**, confirm a red number badge ①②… and that "次へ(N)" increments. Tap in the order you want the carousel (01→06). |
|   | if a tap missed and opened the preview | preview "選択 ○" `1010 143` | select there, then swipe the image left to the next one and repeat |
| 6 | Confirm **選択済み⑥ / 次へ(6)**, then tap **次へ(6)** | `800 2200` | → editor (music auto-added) |
| 7 | **Set cover = image 01**: swipe the main image right→prev until it shows 01/06 | swipe `230 1000 → 900 1000` | **CRITICAL**: the image displayed when you press 次へ becomes the cover. Land on 01. **編集画面のメイン表示(03等)に惑わされない**＝最終確認は step8 公開画面の先頭『カバー』サムネ＋公開前プレビュー 1/N で 01 を確認。 |
| 7c | **トレンド音源に差し替え**（任意だが推奨） | 上部の「♪ <曲名>」をタップ → 音楽ピッカー | 写真投稿でもトレンド/人気音源で発見性が上がる（GROWTH_PLAYBOOK §音源）。「おすすめ」上位や急上昇の曲を選ぶ。自動付与のままでも可だが、可能なら差し替える |
| 8 | Editor **次へ** | `800 2190` | → publish screen; first thumbnail should read "カバー" = 01 |
| 9 | Tap **title field** ("キャッチーなタイトルを追加しよう") | `540 596` | counter shows `0/90` — **max 90 chars**. The publish screen now has **TWO** EditTexts (see below) — this is the upper one. |
| 10 | Type caption with `kb_type` / `kb_type_file` | — | 90-char cap ⇒ use title + one hook line + the 5 hashtags (see below) |
| 11 | Dismiss keyboard (`keyevent 111`), tap **投稿** (red) | `820 2210` | publishes. Returns to main view |
| 12 | If a notification-permission dialog appears | "後で" ≈ `310 2180` | dismiss |

## Two caption fields on the publish screen (observed 2026-08-09)
The publish screen exposes **two** EditTexts, not one. `ui_dump` and pick by placeholder —
never by y-coordinate alone:

| field | placeholder | limit | center |
|---|---|---|---|
| title | `キャッチーなタイトルを追加しよう` | **90 chars** (`0/90` counter) | `540 596` |
| description | `長い説明を書くと、視聴数が平均で3倍増える可能性があります。` | long | `540 831` |

The title field is **single-line**: `\n` in the typed text is silently converted to a space,
so compose for that rather than expecting line breaks. The description field is untested by
this skill — the flow below fills the title only.

## Caption (90-char limit)
Full body won't fit. Compose title + a hook + all hashtags within 90 chars, e.g. for post3:
```
“いいね”のいらない日記、つくりました
SNSじゃない、あなただけの動画日記📔
#日記アプリ #ライフログ #1年前の今日 #プライバシー #おすすめアプリ
```
Input it with ADBKeyboard (handles Japanese + emoji + newline):
```bash
kb_type $'“いいね”のいらない日記、つくりました\nSNSじゃない、あなただけの動画日記📔\n#日記アプリ #ライフログ #1年前の今日 #プライバシー #おすすめアプリ'
```

## Verify success (do NOT trust burned-in numbers)
The Hioto images have a slide counter like `02 / 06` **burned into the picture** — this is NOT
proof of carousel size. To verify:
- After publishing, the feed/profile post shows **TikTok's own dots** above the caption — count
  them (6 dots = 6 images). `scripts/crop.py <shot> 350 1820 730 1880 dots.png 3` to read them.
- Or the pre-publish プレビュー shows a real `1/6` counter (top-right) + 6 dots.
- **暗い表紙はドットが背景に埋もれて数えにくい→第一確認はプロフィールグリッドの ▶ 表示**（dots crop はフォールバック）。
Confirm banner "写真が投稿されました！すべてのユーザーに表示されます。"

## Teardown
```bash
kb_off          # restore the user's normal keyboard (Gboard)
keep_awake_off  # restore screen timeout
```

## Self-recovery — solve irregularities yourself, don't bail to the user
The goal is **a correct post lands**. Irregularities are expected; recover from them in-flow
instead of stopping. After every step that matters, **verify before continuing**, and if it's
wrong, back out to the previous known screen and retry. Concrete recipe:

1. **Verify, don't assume.** After a tap, screenshot (or `ui_dump` on picker/edit screens —
   uiautomator works there, just not on the camera surface). Confirm the expected state:
   badge count after a selection ○, `次へ(N)` incremented, `1/6` counter, `0/90` caption field,
   "カバー" thumbnail = 01. If it doesn't match, **do not proceed** — recover.
2. **Recover to a known state.** `back` to the previous screen (or force-stop + `fresh_launch`
   and re-enter), then redo the step. Re-measure coords from a fresh screenshot each retry —
   never reuse a coordinate from before a transition.
3. **If taps are non-deterministic** (same coord hits different UI, toggles don't register,
   1 tap selects many) → that's **memory thrash**. Run `mem_reclaim`, wait ~3s, and retry the
   step. Prefer `tap_node`/`ui_center` (locate the node, tap its center) over blind coords on
   the picker — relocating each time survives lag.
4. **Bounded retries.** Retry a step up to ~3×, and the whole post up to ~2× (force-stop →
   fresh_launch → restart flow). The schedule entry stays `queued` until success, so a fully
   abandoned attempt is safely retried on the next run — losing an attempt is fine, a **wrong
   post is not**.
5. **Hard stop only to avoid a wrong post.** The one thing worse than not posting is posting
   the wrong thing. If after retries you cannot reach a verified-correct publish screen, stop
   BEFORE 投稿, leave the schedule `queued`, and notify (below). Never tap 投稿 on an unverified state.

### Known failure modes & in-flow fix
- **Only 1 image posts** → tapped image centers, not the ○. Redo with circles + badge check (`tap_node` the cell's selection node).
- **Wrong cover** → editor showed a different image at 次へ. Swipe to 01 first, verify, then 次へ.
- **ANR ("応答していません") storms** → `free_cpu` + `mem_reclaim` (bg dexopt/low RAM); tap 待機, wait, retry.
- **Back to launcher mid-flow** → edge tap (x<70) or nav-bar (y>2300) fired a gesture. Re-launch into the flow; keep taps to element centers.
- **Picker shows stale/wrong frame, toggles dead** → memory thrash: `mem_reclaim`, `ui_settle`, retry with `tap_node`.

## harness report (Slack on success, LINE on exception)
- **On success** — including a post that needed in-flow recovery — send ONE **Slack** completion
  report (llms.txt routine-report channel):
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sns-daily-pipeline/scripts/harness.py slack --text "[<app>] TikTok 公開: <title/what>"`.
- **On hard failure** — retries exhausted and you stopped to avoid a wrong post, or adb/device is
  gone — send ONE **LINE** alert (not Slack):
  `python3 ${CLAUDE_PLUGIN_ROOT}/skills/sns-daily-pipeline/scripts/harness.py push --text "[<app>] <what failed, after N retries>"`.
Token in `sns-daily-pipeline/.harness.env`.
