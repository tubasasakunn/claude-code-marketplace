#!/usr/bin/env python3
"""promo-video 共通ツールキット（全アプリ共通＝ルート集約）。

宣伝動画（無音・縦9:16・~30s）を **PIL でフレームを1枚ずつ合成 → ffmpeg でエンコード** する
ための再利用プリミティブ。デザインの正本は carousel-craft（`engine/brand.py`）で、ここは
その描画ツールキットを **動かす（時間軸を与える）** 層。色・ワードマーク・モチーフ・素材は
`Brand`（各 target/<app>/material/manifest.json）から来る＝アプリ固有を一切ハードコードしない。

設計の肝（SKILL.md §トラブルと教訓 が正本）:
- 連続フェーズ Ken Burns：クロスフェード中に「入ってくる映像」を固定値で描くと 0.3 秒
  フリーズ→急発進して **カクつく**。各素材を “出現〜退出まで途切れず進むフェーズ” で駆動する。
- テキストは rise+fade+blur の `anim_layer` で立ち上げ、切替はブラー無しのクロスフェード。
- グレインは **固定シード**（毎フレーム振り直すと切替でチラつく）。写真背景にだけ薄く。
- ストリーミング・クロスフェード assemble（全フレームをメモリに持たない）。
- 仕上げは libx264/CRF で共有サイズへトランスコード（quality最大の生は数百Mbになる）。

依存: Pillow, numpy, imageio, imageio-ffmpeg（sudo 不要の静的 ffmpeg 同梱）。
"""
import importlib.util as _ilu
import math
import os
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont  # noqa: F401

# ------------------------------------------------------------------ carousel-craft engine
# このファイルは skills/promo-video/engine/video.py。carousel-craft は skills/ の兄弟。
_CC_CANDS = [
    Path(__file__).resolve().parents[2] / "carousel-craft" / "engine",   # in-repo（正本・兄弟スキル）
]
CC_ENGINE = next((p for p in _CC_CANDS if (p / "brand.py").exists()), _CC_CANDS[0])
_spec = _ilu.spec_from_file_location("cc_brand", CC_ENGINE / "brand.py")
B = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(B)          # carousel-craft の brand toolkit を B として公開

# ------------------------------------------------------------------ fonts（/tmp に用意）
FONTS = {
    "/tmp/NotoSansJP.ttf":  ("https://raw.githubusercontent.com/google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf", 100000),
    "/tmp/NotoSerifJP.ttf": ("https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifjp/NotoSerifJP%5Bwght%5D.ttf", 100000),
    "/tmp/DMMono-Light.ttf":   ("https://raw.githubusercontent.com/google/fonts/main/ofl/dmmono/DMMono-Light.ttf", 10000),
    "/tmp/DMMono-Regular.ttf": ("https://raw.githubusercontent.com/google/fonts/main/ofl/dmmono/DMMono-Regular.ttf", 10000),
    "/tmp/DMMono-Medium.ttf":  ("https://raw.githubusercontent.com/google/fonts/main/ofl/dmmono/DMMono-Medium.ttf", 10000),
}


def ensure_fonts():
    for path, (url, min_bytes) in FONTS.items():
        if not os.path.exists(path) or os.path.getsize(path) < min_bytes:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as fp:
                fp.write(r.read())


# ------------------------------------------------------------------ canvas size
W, H, FPS = 1080, 1920, 30   # 既定（render.py が spec で上書き可）


def set_size(w, h, fps):
    global W, H, FPS
    W, H, FPS = w, h, fps


# ------------------------------------------------------------------ easing
def clamp01(t): return 0.0 if t < 0 else (1.0 if t > 1 else t)
def eo_cubic(t): t = clamp01(t); return 1 - (1 - t) ** 3
def eo_quint(t): t = clamp01(t); return 1 - (1 - t) ** 5
def smooth(t): t = clamp01(t); return t * t * (3 - 2 * t)
def ei_cubic(t): t = clamp01(t); return t ** 3
def lerp(a, b, t): return a + (b - a) * t
def lerp_col(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def seg(t, a, b):
    """[a,b] 窓内の進行度 0..1（窓外は 0/1）。立ち上げのタイミング制御に。"""
    if t <= a: return 0.0
    if t >= b: return 1.0
    return (t - a) / (b - a)


# ------------------------------------------------------------------ footage / ken burns
_src_cache = {}


def src(path):
    p = str(path)
    if p not in _src_cache:
        _src_cache[p] = Image.open(p).convert("RGB")
    return _src_cache[p]


def kb_base(path, over=1.22):
    """高解像のカバー画像（後で窓を切り出してズーム/パン）。over=余白率。"""
    return B.cover_crop(src(path), int(W * over), int(H * over))


def kb_frame(base, t, z0=1.0, z1=1.10, pan0=(0, 0), pan1=(0, 0)):
    """base の中をズーム/パンして 1 フレーム切り出す。t は 0..1 の連続値で渡すこと。"""
    BW, BH = base.size
    z = lerp(z0, z1, t)
    ww, wh = BW / z, BH / z
    px = lerp(pan0[0], pan1[0], t); py = lerp(pan0[1], pan1[1], t)
    cx = BW / 2 + px * BW; cy = BH / 2 + py * BH
    x0 = max(0, min(BW - ww, cx - ww / 2)); y0 = max(0, min(BH - wh, cy - wh / 2))
    crop = base.crop((round(x0), round(y0), round(x0 + ww), round(y0 + wh)))
    return crop.resize((W, H), Image.LANCZOS)


# ------------------------------------------------------------------ scrim / grain
def scrim(canvas, start=0.40, bot_a=210, top_a=0):
    canvas.alpha_composite(B.bottom_scrim(W, H, start=start, top_a=top_a, bot_a=bot_a))


def topscrim(canvas, h=560, a=150):
    g = np.zeros((H, W, 4), np.uint8)
    col = np.zeros(H, np.uint8)
    col[:h] = np.linspace(a, 0, h).astype(np.uint8)
    g[..., 3] = np.repeat(col[:, None], W, axis=1)
    canvas.alpha_composite(Image.fromarray(g, "RGBA"))


def grain(canvas, seed, amount=6):
    """写真背景にだけ薄く。seed は固定で（毎フレーム振り直すとチラつく）。"""
    B.grain(canvas, seed=seed, amount=amount)


# ------------------------------------------------------------------ animated text
def anim_layer(canvas, draw_fn, t, dy=52, blur=8, ease=eo_quint):
    """draw_fn(layer) が最終位置に描いた RGBA レイヤを rise+fade+blur で出す。t=0..1。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(layer)
    e = ease(t)
    off = int((1 - e) * dy)
    if off:
        layer = ImageChops.offset(layer, 0, off)
    if t < 1 and blur:
        r = (1 - smooth(t)) * blur
        if r > 0.3:
            layer = layer.filter(ImageFilter.GaussianBlur(r))
    a = layer.getchannel("A").point(lambda v: int(v * e))
    layer.putalpha(a)
    canvas.alpha_composite(layer)


def head_lines(layer, lines, size, x, top, fill, leading=None, kind="kaku",
               tracking=0, align="l"):
    """見出し（carousel-craft の head フォント＝丸ゴ/角ゴ等）。align: l/c/r。"""
    f = B.head_font(size, kind)
    d = ImageDraw.Draw(layer)
    lead = leading or int(size * 1.28)
    y = top
    for ln in lines:
        if tracking:
            B.draw_tracked(d, ln, f, fill, x, y, tracking, anchor=align)
        else:
            w = d.textlength(ln, font=f)
            xx = x if align == "l" else (x - w if align == "r" else x - w / 2)
            d.text((xx, y), ln, font=f, fill=fill)
        y += lead
    return y


def mono_label(layer, text, x, y, fill, accent=None, size=30, tracking=5, rule=40,
               anchor="l"):
    """DM Mono のラベル。accent を渡すと頭にアクセントの罫を引く（エディトリアル定石）。
    anchor: l=左基準 / c=中心 / r=右基準（罫を含めた全幅で揃える）。"""
    d = ImageDraw.Draw(layer)
    # DM Mono に和文グリフは無い（□ 豆腐）。和文を含むラベルは Noto Sans JP で組む。
    f = (B.mono_font(size, "medium") if all(ord(ch) < 128 for ch in text)
         else B.font(size, 600))
    total = B.tracked_width(d, text, f, tracking) + (
        (rule + size * 0.55) if accent is not None else 0)
    x = x - total / 2 if anchor == "c" else (x - total if anchor == "r" else x)
    if accent is not None:
        cy = y + size * 0.62
        d.line([(x, cy), (x + rule, cy)], fill=accent, width=3)
        x = x + rule + size * 0.55
    B.draw_tracked(d, text, f, fill, x, y, tracking)


def fade_layer(canvas, draw_fn, alpha):
    """draw_fn が描いたレイヤを一定 alpha(0..1) で重ねる（ブラー無しクロスフェード用）。"""
    if alpha <= 0.01:
        return
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_fn(layer)
    a = layer.getchannel("A").point(lambda v: int(v * alpha))
    layer.putalpha(a)
    canvas.alpha_composite(layer)


# ------------------------------------------------------------------ brand bits
def small_wordmark(canvas, brand, on_dark, x=None, y=92, size=46):
    B.wordmark(canvas, brand, B.sp("edge") if x is None else x, y, size,
               anchor="l", on_dark=on_dark)


def frame_ticks(canvas, accent, alpha=130):
    B.frame_ticks(canvas, accent, alpha=alpha, margin=70, length=44, width=4)


# ------------------------------------------------------------------ phone helpers
def phone_place(canvas, phone, cx, top, target_h, shadow=True):
    """phone モック画像を target_h にして配置。戻り値=(px,py,pw,ph)。"""
    ratio = target_h / phone.height
    p = phone.resize((round(phone.width * ratio), target_h), Image.LANCZOS)
    px, py = round(cx - p.width / 2), round(top)
    if shadow:
        sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle(
            [px + 12, py + 30, px + p.width + 12, py + p.height + 30],
            radius=130, fill=(50, 38, 30, 95))
        canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(38)))
    canvas.alpha_composite(p, (px, py))
    return px, py, p.width, p.height


def keyed_phone(material_dir, shot_name, footage_path=None):
    """アプリ実画面 png をクロマキー緑(#00FF00)だけ footage に差し替えて phone モック化。
    footage_path=None なら緑が無い画面としてそのまま使う。"""
    shot = Image.open(Path(material_dir) / f"{shot_name}.png").convert("RGBA")
    if footage_path is not None:
        scene = B.footage_scene(str(footage_path))
        shot = B.key_out_green(shot, scene)
    elif shot.mode == "RGBA":
        shot = shot.convert("RGB")
    return B.phone_mockup(shot)


def ripple(canvas, cx, cy, t, accent, rmax=190):
    """タップ波紋（t=0..1 で広がりつつ消える）。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for k in range(3):
        tt = clamp01(t * 1.4 - k * 0.22)
        if tt <= 0 or tt >= 1:
            continue
        r = eo_cubic(tt) * rmax
        a = int(200 * (1 - tt))
        d.ellipse([cx - r, cy - r, cx + r, cy + r],
                  outline=accent + (a,), width=max(2, int(6 * (1 - tt))))
    canvas.alpha_composite(layer)


# ------------------------------------------------------------------ Clip base
class Clip:
    """1 シーン。n フレーム。render(i)->RGB Image を実装する。"""
    def __init__(self, n):
        self.n = n

    def render(self, i):
        raise NotImplementedError


# ------------------------------------------------------------------ assemble（ストリーミング・クロスフェード）
def assemble(writer, clips, D=9, verbose=True):
    """clips を順に再生し、隣接シーン境界で D フレームのクロスディゾルブ。
    全フレームをメモリに持たず writer へ流す（前シーン末尾 D 枚だけ保持）。"""
    prev_tail = []
    total = 0
    for ci, clip in enumerate(clips):
        n = clip.n
        tail = []
        for i in range(n):
            img = clip.render(i)
            if i < D and prev_tail:
                a = (i + 1) / (D + 1)
                img = Image.blend(prev_tail[i], img, a)
                writer.append_data(np.asarray(img)); total += 1
            elif i >= n - D and ci < len(clips) - 1:
                tail.append(img)
            else:
                writer.append_data(np.asarray(img)); total += 1
        prev_tail = tail
        if verbose:
            print(f"  clip {ci+1}/{len(clips)} {clip.__class__.__name__} ({n}f) done", flush=True)
    for img in prev_tail:
        writer.append_data(np.asarray(img)); total += 1
    return total


# ------------------------------------------------------------------ encode
def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def render_video(clips, raw_out, fps=None, D=9):
    """clips を高品質の生 mp4 に書き出す。戻り値=フレーム数。"""
    import imageio
    fps = fps or FPS
    writer = imageio.get_writer(
        raw_out, fps=fps, codec="libx264", quality=9, macro_block_size=1,
        ffmpeg_log_level="error",
        output_params=["-pix_fmt", "yuv420p", "-profile:v", "high",
                       "-preset", "slow", "-movflags", "+faststart"])
    total = assemble(writer, clips, D=D)
    writer.close()
    return total


def transcode_share(raw_out, share_out, crf=19):
    """生 mp4 を共有サイズ(CRF)へトランスコード（無音）。"""
    import subprocess
    subprocess.run([ffmpeg_exe(), "-loglevel", "error", "-y", "-i", str(raw_out),
                    "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
                    "-crf", str(crf), "-preset", "slow",
                    "-movflags", "+faststart", "-an", str(share_out)], check=True)


# ------------------------------------------------------------------ QA
def probe_sheet(clips, out, cols=2, cw=300, fracs=(0.5, 0.85)):
    """各シーンの代表フレームを 1 枚のコンタクトシートに（目視レビュー用）。"""
    cells = []
    for cl in clips:
        for fr in fracs:
            cells.append(cl.render(min(cl.n - 1, int(cl.n * fr))))
    ch = int(cw * H / W)
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw, rows * ch), (20, 20, 22))
    for k, im in enumerate(cells):
        sheet.paste(im.resize((cw, ch), Image.LANCZOS), ((k % cols) * cw, (k // cols) * ch))
    sheet.save(out)
    return out


def strip_consecutive(clip, frames, out, cw=300):
    """1 シーンの連続フレームを横並びに（カクつき＝フリーズの有無を目で確認）。"""
    ch = int(cw * H / W)
    sheet = Image.new("RGB", (len(frames) * cw, ch), (20, 20, 22))
    d = ImageDraw.Draw(sheet); f = ImageFont.load_default()
    for i, fr in enumerate(frames):
        sheet.paste(clip.render(fr).resize((cw, ch)), (i * cw, 0))
        d.text((i * cw + 4, 4), f"f{fr}", fill=(255, 240, 120), font=f)
    sheet.save(out)
    return out
