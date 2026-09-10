#!/usr/bin/env python3
"""ストア画像を組むための描画部品。

make_pattern_samples.py（構図カタログ）と、将来の本番画像生成が共有する。
ブランド（色・ワードマーク・書体）は appstore.config.json が正本。

構図の型そのものはここには置かない。ここにあるのは「端末を傾ける」「影で浮かせる」
「蛍光マーカーを敷く」といった、型を組むための語彙だけ。
"""

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _config import get  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCREENS = ROOT / "material" / "screens"
LAYOUTS = ROOT / "material" / "layouts"

# MARK: - ブランド

BG = tuple(get("brand", "bg", default=[247, 244, 240]))
INK = tuple(get("brand", "ink", default=[31, 27, 22]))
SUB = tuple(get("brand", "sub_ink", default=[111, 106, 99]))
CARD = tuple(get("brand", "card", default=[255, 255, 255]))
A = {k: tuple(v) for k, v in get("brand", "accents", default={}).items()}
WORDMARK = get("brand", "wordmark", default="話す日記帳")

# 6.9" は縦 1320x2868 / 横 2868x1320。ASC は解像度でシェルフを判定するので変えない。
PORTRAIT = (1320, 2868)
LANDSCAPE = (2868, 1320)

FONTS = {
    "sans": (Path("/tmp/NotoSansJP.ttf"),
             get("fonts", "jp_sans_url", default="https://raw.githubusercontent.com/"
                 "google/fonts/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf")),
    "serif": (Path("/tmp/NotoSerifJP.ttf"),
              get("fonts", "jp_serif_url", default="https://raw.githubusercontent.com/"
                  "google/fonts/main/ofl/notoserifjp/NotoSerifJP%5Bwght%5D.ttf")),
}

FORCE_FRAME: bool | None = None   # CLI から全型のフレーム有無を上書きする


def ensure_fonts() -> None:
    for path, url in FONTS.values():
        if not path.exists():
            subprocess.run(["curl", "-sL", "--max-time", "90", "-o", str(path), url], check=True)


def font(size: int, weight: int = 700, family: str = "sans") -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS[family][0]), size)
    try:
        f.set_variation_by_axes([weight])
    except OSError:
        pass
    return f


# MARK: - キャンバスと素材

def screen(name: str) -> Image.Image:
    return Image.open(SCREENS / name).convert("RGB")


def layout(name: str) -> Image.Image:
    return Image.open(LAYOUTS / name).convert("RGB")


def canvas(size, bg) -> Image.Image:
    return Image.new("RGBA", size, tuple(bg) + (255,) if len(bg) == 3 else tuple(bg))


def paste(base: Image.Image, layer: Image.Image, xy) -> None:
    base.alpha_composite(layer.convert("RGBA"), (round(xy[0]), round(xy[1])))


def round_mask(size, r: int) -> Image.Image:
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], r, fill=255)
    return m


def rounded(img: Image.Image, r: int) -> Image.Image:
    out = img.convert("RGBA")
    out.putalpha(round_mask(img.size, r))
    return out


def cover(img: Image.Image, w: int, h: int, *, top: float = 0.0) -> Image.Image:
    """(w, h) を埋めるよう拡縮して切り抜く。material/layouts は高さが 1441〜4744px と
    ばらつくため、単純な crop では黒帯が出る。top=0 で上端基準、0.5 で中央基準。"""
    s = max(w / img.width, h / img.height)
    r = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    return r.crop(((r.width - w) // 2, round((r.height - h) * top),
                   (r.width - w) // 2 + w, round((r.height - h) * top) + h))


def vgrad(size, stops) -> Image.Image:
    return _grad(size, stops, vertical=True)


def hgrad(size, stops) -> Image.Image:
    return _grad(size, stops, vertical=False)


def _grad(size, stops, *, vertical: bool) -> Image.Image:
    """1px の帯を作って伸ばす。全画素を1度で埋めるので塗り漏れが出ない。"""
    n = size[1] if vertical else size[0]
    strip = Image.new("RGB", (1, n) if vertical else (n, 1))
    px = strip.load()
    for i in range(n):
        t = i / max(n - 1, 1)
        for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
            if p0 <= t <= p1:
                f = (t - p0) / max(p1 - p0, 1e-6)
                col = tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
                px[(0, i) if vertical else (i, 0)] = col
                break
    return strip.resize(size, Image.BILINEAR)


# MARK: - 端末

def phone(src: Image.Image, width: int, *, framed: bool = True,
          bezel_ratio: float = 0.034, buttons: bool = True) -> Image.Image:
    """端末モックアップ。返す画像の幅は必ず引数の width（側面ボタンもその内側）。

    AIDEV-NOTE: ダイナミックアイランドを描いてはいけない。material/screens/ の
    スクショは実機のステータスバーごと写っており、島を重ねると二重の黒い塊になる
    （2026-07 に実際に発生）。「フレームなのに島が無い」と思って足すと再発する。

    影・反射・ノッチの捏造は足さない（Apple Marketing Guidelines が端末画像の改変
    として禁じている）。傾けと浮遊の影は構図の型として rot() / floated() で別に扱うが、
    ストア提出前にその2つは審査観点で見直すこと。
    """
    if FORCE_FRAME is not None:
        framed = FORCE_FRAME
    if not framed:
        h = round(width * src.height / src.width)
        return rounded(src.resize((width, h), Image.LANCZOS), round(width * 0.075))

    pad = round(width * 0.017) if buttons else 0
    body_w = width - pad * 2
    bez = max(5, round(body_w * bezel_ratio))
    inner_w = body_w - bez * 2
    inner_h = round(inner_w * src.height / src.width)
    H = inner_h + bez * 2
    r_out = round(body_w * 0.125)
    r_in = max(2, r_out - bez)

    body = Image.new("RGBA", (width, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    if buttons:
        bw, col = pad + round(bez * 0.30), (58, 58, 64, 255)
        for y0, y1 in ((0.150, 0.196), (0.238, 0.318), (0.334, 0.414)):
            d.rounded_rectangle([0, H * y0, bw, H * y1], bw * 0.42, fill=col)
        d.rounded_rectangle([width - bw, H * 0.246, width, H * 0.366], bw * 0.42, fill=col)
    d.rounded_rectangle([pad, 0, pad + body_w - 1, H - 1], r_out, fill=(20, 20, 23, 255))
    body.alpha_composite(rounded(src.resize((inner_w, inner_h), Image.LANCZOS), r_in),
                         (pad + bez, bez))
    return body


def rot(img: Image.Image, deg: float) -> Image.Image:
    """反時計回りに回転。expand=True なので返る寸法は元より大きい。"""
    return img.convert("RGBA").rotate(deg, expand=True, resample=Image.BICUBIC)


def floated(img: Image.Image, *, blur: int = 34, dx: int = 0, dy: int = 26,
            alpha: int = 115):
    """影付きの浮遊オブジェクト。返り値は (合成画像, オフセット)。
    元と同じ位置 (x, y) に見せたいなら (x - off, y - off) に貼る。"""
    pad = blur * 3
    src = img.convert("RGBA")
    out = Image.new("RGBA", (src.width + pad * 2, src.height + pad * 2), (0, 0, 0, 0))
    sh = Image.new("RGBA", src.size, (0, 0, 0, 0))
    sh.putalpha(src.split()[3].point(lambda v: v * alpha // 255))
    tmp = Image.new("RGBA", out.size, (0, 0, 0, 0))
    tmp.alpha_composite(sh, (pad + dx, pad + dy))
    out.alpha_composite(tmp.filter(ImageFilter.GaussianBlur(blur)))
    out.alpha_composite(src, (pad, pad))
    return out, pad


def place(base: Image.Image, obj: Image.Image, center, *, deg: float = 0.0,
          float_: bool = False, **fkw) -> None:
    """obj を center を中心に置く。deg で回転、float_ で影を付ける。"""
    if deg:
        obj = rot(obj, deg)
    off = 0
    if float_:
        obj, off = floated(obj, **fkw)
    paste(base, obj, (center[0] - obj.width / 2, center[1] - obj.height / 2))


# MARK: - 文字

def text_block(d, xy, lines, f, fill, *, leading=1.28, align="left", width=None,
               tracking=0.0):
    """行ごとに描く。改行は呼び出し側で決める（禁則を自分で握るため）。"""
    x, y = xy
    step = round(f.size * leading)
    for ln in lines:
        w = d.textlength(ln, font=f) + tracking * max(len(ln) - 1, 0)
        px = x if align == "left" else (x + (width - w) / 2 if align == "center"
                                        else x + width - w)
        if tracking:
            cx = px
            for ch in ln:
                d.text((cx, y), ch, font=f, fill=fill)
                cx += d.textlength(ch, font=f) + tracking
        else:
            d.text((px, y), ln, font=f, fill=fill)
        y += step
    return y


def text_layer(lines, f, fill, *, leading=1.28, tracking=0.0, pad=20):
    """回転させたい文字は、透明レイヤーに描いてから rot() に渡す。"""
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = max(probe.textlength(ln, font=f) + tracking * max(len(ln) - 1, 0) for ln in lines)
    h = round(f.size * leading) * len(lines)
    lay = Image.new("RGBA", (round(w) + pad * 2, h + pad * 2), (0, 0, 0, 0))
    text_block(ImageDraw.Draw(lay), (pad, pad), lines, f, fill,
               leading=leading, tracking=tracking)
    return lay


def marker(d, xy, text, f, ink, hl, *, pad=14, ratio=0.52, tracking=0.0):
    """蛍光マーカー風の色帯を文字の下半分に敷く（日本のストア画像の定番）。"""
    x, y = xy
    w = d.textlength(text, font=f) + tracking * max(len(text) - 1, 0)
    top = y + f.size * (1.0 - ratio)
    d.rounded_rectangle([x - pad, top, x + w + pad, y + f.size * 1.06],
                        round(f.size * 0.08), fill=hl)
    if tracking:
        cx = x
        for ch in text:
            d.text((cx, y), ch, font=f, fill=ink)
            cx += d.textlength(ch, font=f) + tracking
    else:
        d.text((x, y), text, font=f, fill=ink)
    return w


def rule(d, x, y, w, color, h=10):
    d.rounded_rectangle([x, y, x + w, y + h], h // 2, fill=color)


def dots(d, cx, y, r=13, gap=44, colors=None, center=True):
    cols = colors or list(A.values())
    x = cx - gap * (len(cols) - 1) / 2 if center else cx
    for i, c in enumerate(cols):
        d.ellipse([x + i * gap - r, y - r, x + i * gap + r, y + r], fill=c)


def wordmark(d, x, y, size, fill, family="sans", weight=700):
    """角丸の「話」グリフ + アプリ名。アイコンの語彙をそのまま流用する。"""
    d.rounded_rectangle([x, y, x + size, y + size], round(size * 0.24), fill=A["bengara"])
    gf = font(round(size * 0.62), 700)
    bb = d.textbbox((0, 0), "話", font=gf)
    d.text((x + (size - (bb[2] - bb[0])) / 2 - bb[0],
            y + (size - (bb[3] - bb[1])) / 2 - bb[1]), "話", font=gf, fill=(255, 255, 255))
    nf = font(round(size * 0.74), weight, family)
    nb = d.textbbox((0, 0), WORDMARK, font=nf)
    d.text((x + size + round(size * 0.30), y + (size - (nb[3] + nb[1])) / 2),
           WORDMARK, font=nf, fill=fill)


def wordmark_width(d, size, family="sans", weight=700) -> float:
    return (size + round(size * 0.30)
            + d.textlength(WORDMARK, font=font(round(size * 0.74), weight, family)))


def checklist(d, xy, items, f, ink, accent, *, gap=1.9, box=None):
    """✓ 付きの箇条書き。日本のストア画像で「特徴3点」を並べる定番。"""
    x, y = xy
    b = box or round(f.size * 0.86)
    for it in items:
        d.rounded_rectangle([x, y + f.size * 0.10, x + b, y + f.size * 0.10 + b],
                            round(b * 0.24), outline=accent, width=max(3, b // 12))
        d.line([x + b * 0.24, y + f.size * 0.10 + b * 0.52,
                x + b * 0.44, y + f.size * 0.10 + b * 0.74], fill=accent,
               width=max(3, b // 10))
        d.line([x + b * 0.44, y + f.size * 0.10 + b * 0.74,
                x + b * 0.80, y + f.size * 0.10 + b * 0.24], fill=accent,
               width=max(3, b // 10))
        d.text((x + b * 1.55, y), it, font=f, fill=ink)
        y += f.size * gap
    return y


# MARK: - 注釈

def badge(lines, color, size, f, *, ink=(255, 255, 255)):
    """円形の注釈バッジ（Otter.ai の緑丸の型）。"""
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([0, 0, size - 1, size - 1], fill=color)
    h = round(f.size * 1.3) * len(lines)
    text_block(d, (0, (size - h) / 2), lines, f, ink, leading=1.3,
               align="center", width=size)
    return im


def curve_arrow(im, p0, p1, *, color, width=10, bow=0.28, head=46, steps=64):
    """手描き風のカーブ矢印。before→after を結ぶのに使う。"""
    d = ImageDraw.Draw(im)
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    dx, dy = x1 - x0, y1 - y0
    cx, cy = mx - dy * bow, my + dx * bow          # 制御点は線分の法線方向へ
    pts = []
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        pts.append((u * u * x0 + 2 * u * t * cx + t * t * x1,
                    u * u * y0 + 2 * u * t * cy + t * t * y1))
    d.line(pts, fill=color, width=width, joint="curve")
    ang = math.atan2(pts[-1][1] - pts[-2][1], pts[-1][0] - pts[-2][0])
    for s in (2.7, -2.7):
        d.line([pts[-1], (pts[-1][0] + head * math.cos(ang + s),
                          pts[-1][1] + head * math.sin(ang + s))],
               fill=color, width=width)


def burst(d, cx, cy, r_in, r_out, *, color, n=18, width=8):
    """集中線。長短を交互に振ると手描きに近づく。"""
    for i in range(n):
        a = 2 * math.pi * i / n
        ro = r_out * (1.0 if i % 2 == 0 else 0.72)
        d.line([cx + r_in * math.cos(a), cy + r_in * math.sin(a),
                cx + ro * math.cos(a), cy + ro * math.sin(a)], fill=color, width=width)


def loupe(base, src, *, at, src_center, src_r, size, ring=(255, 255, 255, 245),
          k=1.0, origin=None):
    """src の一部を円形に拡大して base に置き、元位置に輪と引き出し線を描く。

    at: 拡大円の左上 / src_center・src_r: 素材上の中心と半径 / k: 素材→画面の縮尺
    origin: 画面上の元位置（省略時は描かない）
    """
    d = ImageDraw.Draw(base)
    if origin:
        ox, oy = origin
        d.line([at[0] + size * 0.18, at[1] + size * 0.94,
                ox + src_r * k * 0.72, oy - src_r * k * 0.72], fill=(255, 255, 255, 170),
               width=6)
        d.ellipse([ox - src_r * k, oy - src_r * k, ox + src_r * k, oy + src_r * k],
                  outline=(255, 255, 255, 210), width=6)
    cx, cy = src_center
    crop = src.crop((cx - src_r, cy - src_r, cx + src_r, cy + src_r)) \
              .resize((size, size), Image.LANCZOS)
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255)
    crop.putalpha(m)
    paste(base, crop, at)
    d.ellipse([at[0], at[1], at[0] + size, at[1] + size], outline=ring, width=10)


# MARK: - ピクトグラム（利用シーンを絵で示す。単純図形のみ）

def pict(kind: str, size: int, color) -> Image.Image:
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s, w = size, max(4, size // 18)
    if kind == "moon":                                   # 三日月
        d.ellipse([s * 0.10, s * 0.10, s * 0.90, s * 0.90], fill=color)
        d.ellipse([s * 0.34, s * 0.02, s * 1.14, s * 0.82], fill=(0, 0, 0, 0))
    elif kind == "bed":                                  # 布団
        d.rounded_rectangle([s * 0.06, s * 0.46, s * 0.94, s * 0.74], s * 0.06, fill=color)
        d.rounded_rectangle([s * 0.12, s * 0.32, s * 0.42, s * 0.48], s * 0.06, fill=color)
        d.line([s * 0.10, s * 0.74, s * 0.10, s * 0.88], fill=color, width=w * 2)
        d.line([s * 0.90, s * 0.74, s * 0.90, s * 0.88], fill=color, width=w * 2)
    elif kind == "train":                                # 電車
        d.rounded_rectangle([s * 0.20, s * 0.10, s * 0.80, s * 0.78], s * 0.14,
                            outline=color, width=w * 2)
        d.rounded_rectangle([s * 0.30, s * 0.22, s * 0.70, s * 0.44], s * 0.05, fill=color)
        d.ellipse([s * 0.30, s * 0.54, s * 0.42, s * 0.66], fill=color)
        d.ellipse([s * 0.58, s * 0.54, s * 0.70, s * 0.66], fill=color)
        d.line([s * 0.26, s * 0.80, s * 0.14, s * 0.94], fill=color, width=w)
        d.line([s * 0.74, s * 0.80, s * 0.86, s * 0.94], fill=color, width=w)
    elif kind == "mic":                                  # マイク
        d.rounded_rectangle([s * 0.40, s * 0.12, s * 0.60, s * 0.56], s * 0.10, fill=color)
        d.arc([s * 0.28, s * 0.30, s * 0.72, s * 0.72], 0, 180, fill=color, width=w * 2)
        d.line([s * 0.50, s * 0.72, s * 0.50, s * 0.86], fill=color, width=w * 2)
        d.line([s * 0.34, s * 0.88, s * 0.66, s * 0.88], fill=color, width=w * 2)
    elif kind == "clock":                                # 時計
        d.ellipse([s * 0.10, s * 0.10, s * 0.90, s * 0.90], outline=color, width=w * 2)
        d.line([s * 0.50, s * 0.50, s * 0.50, s * 0.26], fill=color, width=w * 2)
        d.line([s * 0.50, s * 0.50, s * 0.68, s * 0.60], fill=color, width=w * 2)
    elif kind == "book":                                 # 本
        d.line([s * 0.50, s * 0.22, s * 0.50, s * 0.86], fill=color, width=w)
        for sx in (-1, 1):
            d.polygon([(s * 0.50, s * 0.22), (s * (0.50 + sx * 0.38), s * 0.30),
                       (s * (0.50 + sx * 0.38), s * 0.86), (s * 0.50, s * 0.78)],
                      outline=color, width=w * 2)
    return im
