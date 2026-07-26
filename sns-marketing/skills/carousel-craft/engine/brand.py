#!/usr/bin/env python3
"""carousel-craft 共通描画ツールキット（全アプリ共通＝ルート集約）。

各アプリ repo にあった post/_brand.py（ほぼ同一）をここに1本化した。プリミティブ
（SVGレンダラ / grain / scrim / phone_mockup / draw_lines / key_out_green …）は色を
引数で受けるブランド非依存。アプリ固有の色・ワードマーク・アクセントは `Brand`
（各 repo の material/manifest.json から読む）に分離した。

雛形（templates/*.py）はこの toolkit と Brand を受け取り、投稿ごとに新しいエンジンを
組む。フォントは共通（/tmp に gen.py が DL する Noto + DM Mono）。

依存: Pillow, numpy
"""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
SVG_DIR = HERE / "assets" / "svg"
FONTS_DIR = HERE.parent / "fonts"   # 高インパクト和文(fonts.pyで取得済)

# 共通フォント（gen.py の ensure_fonts が /tmp に用意する）
SANS = Path("/tmp/NotoSansJP.ttf")
SERIF = Path("/tmp/NotoSerifJP.ttf")
DM_MONO = {
    "light": Path("/tmp/DMMono-Light.ttf"),
    "regular": Path("/tmp/DMMono-Regular.ttf"),
    "medium": Path("/tmp/DMMono-Medium.ttf"),
}
# 見出し用ディスプレイフォント（Noto明朝の"AIっぽさ"を避け、太い丸/ジオメトリックゴシックに）
HEAD_FONTS = {
    "maru": FONTS_DIR / "ZenMaruGothic-Black.ttf",       # 丸ゴシック・親しみ(暮らし/勉強/日記)
    "kaku": FONTS_DIR / "ZenKakuGothicNew-Black.ttf",    # 角ゴ・骨太クリーン(情報/信頼)
    "antique": FONTS_DIR / "ZenAntique-Regular.ttf",      # アンティーク明朝(美容/上品)
    "mincho": FONTS_DIR / "ShipporiMincho-Bold.ttf",      # 太明朝
}
WHITE = (255, 255, 255)
_font_cache = {}


# MARK: - スペーシング（余白）システム — [[SPACING]] の実装正本
# 1080基準・8の倍数スケール（4は密所のみ半ステップ）。余白は原則この離散値へ snap する
# ＝孤立余白(trapped whitespace)・リズム不統一を構造的に防ぐ。templates は数値を直書きせず
# sp("token")/snap() を使う。不変則: 内側の余白 < 外側の余白 / 左右マージンは対称。
SP_SCALE = (8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 96, 112, 128, 160)
SP_TOKENS = {            # 意味づけ余白（1080基準px）
    "edge":      88,     # 外周マージン W×8.1%（margin() と一致）
    "edge_tight": 72,    # 詰めた外周（Lemon8/帯）
    "hd_body":   16,     # 見出し→直下本文（近接でグループ化）
    "block":     32,     # 同一群のブロック間
    "group":     64,     # 別の視覚的島の間
    "section":   96,     # 大きな段
    "pad":       32,     # カード/パネル内側パディング
    "pill_y":    16, "pill_x": 24,   # 帯/ピル内側
    "hero":      64,     # 主役まわりの強制クリアスペース
}


def snap(v, scale=SP_SCALE):
    """任意px を最も近いスケール値へ。段差を2〜3種に収束させ間延び/不揃いを消す。"""
    return min(scale, key=lambda s: abs(s - v))


def sp(name, W=1080):
    """意味づけ余白トークンを幅Wへスケール。templates はこれを使い数値を直書きしない。"""
    return round(SP_TOKENS[name] * W / 1080)


def stack_centered(band_top, band_bot, n, row_h, gap_min, gap_max):
    """n個の等高ブロックを帯[band_top,band_bot]に均等リズムで中央寄せ配置し、各先頭yを返す。
    gap=(band-n*row_h)/(n-1) を [gap_min,gap_max] にクランプ＝間延び(trapped)を上限で止め、
    余りは上下へ均等＝中央寄せ（孤立した内部余白を作らず、上下を対称な breathing room にする）。"""
    band = band_bot - band_top
    if n <= 1:
        return [band_top + (band - row_h) / 2]
    gap = max(gap_min, min(gap_max, (band - n * row_h) / (n - 1)))
    stack_h = n * row_h + (n - 1) * gap
    start = band_top + (band - stack_h) / 2
    return [start + i * (row_h + gap) for i in range(n)]


# MARK: - Brand（アプリ固有トークン＝material/manifest.json から）

@dataclass
class Brand:
    bg: tuple = (247, 244, 240)
    ink: tuple = (42, 37, 32)
    sub_ink: tuple = (111, 103, 96)
    card: tuple = (255, 255, 255)
    accents: dict = field(default_factory=lambda: {"evening": (224, 123, 84)})
    wordmark: str = "App"
    icon: Path = None        # material 内のアプリアイコン（wordmark のグリフ＝全アプリ必須）
    motif: Path = None       # material 内のアプリ固有シンボル svg（任意・装飾）
    icon_color: tuple = None
    material: Path = None     # material/ ディレクトリ（shot/footage/icon/motif 解決用）
    footage: dict = field(default_factory=dict)  # 任意: 名前 -> material相対パス
    head: str = "kaku"        # 見出しフォント種別 maru/kaku/antique/mincho

    @classmethod
    def from_manifest(cls, material_dir):
        material_dir = Path(material_dir)
        data = json.loads((material_dir / "manifest.json").read_text(encoding="utf-8"))
        b = data.get("brand", {})
        wm = b.get("wordmark", {})
        if isinstance(wm, str):
            wm = {"text": wm}
        # アイコンは material 内に必ずある前提（無ければ既定名を探す）
        icon = wm.get("icon") or b.get("icon")
        icon_path = (material_dir / icon) if icon else None
        if not (icon_path and icon_path.exists()):
            for cand in ("app_icon_1024.png", "app_icon.png", "icon_1024.png"):
                if (material_dir / cand).exists():
                    icon_path = material_dir / cand
                    break
        motif = b.get("motif")
        return cls(
            bg=tuple(b.get("bg", [247, 244, 240])),
            ink=tuple(b.get("ink", [42, 37, 32])),
            sub_ink=tuple(b.get("sub_ink", [111, 103, 96])),
            card=tuple(b.get("card", [255, 255, 255])),
            accents={k: tuple(v) for k, v in b.get("accents", {}).items()} or {"evening": (224, 123, 84)},
            wordmark=wm.get("text", data.get("name", "App")),
            icon=icon_path,
            motif=(material_dir / motif) if motif else None,
            icon_color=tuple(b["icon_color"]) if b.get("icon_color") else None,
            material=material_dir,
            footage=data.get("footage", {}),
            head=b.get("head", "kaku"),
        )

    def accent(self, name):
        return self.accents.get(name) or next(iter(self.accents.values()))


# MARK: - フォント

def font(size, weight=600, serif=False):
    key = (size, weight, serif)
    if key in _font_cache:
        return _font_cache[key]
    f = ImageFont.truetype(str(SERIF if serif else SANS), size)
    try:
        f.set_variation_by_axes([weight])
    except OSError:
        pass
    _font_cache[key] = f
    return f


def serif_font(size, weight=600):
    return font(size, weight, serif=True)


def mono_font(size, weight="medium"):
    key = ("mono", size, weight)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(str(DM_MONO[weight]), size)
    return _font_cache[key]


def head_font(size, kind="kaku"):
    """見出し用ディスプレイフォント（既定=骨太角ゴ）。kind: maru/kaku/antique/mincho。
    無ければ Noto Serif にフォールバック。"""
    key = ("head", size, kind)
    if key not in _font_cache:
        path = HEAD_FONTS.get(kind)
        if not (path and path.exists()):
            return serif_font(size, 700)
        _font_cache[key] = ImageFont.truetype(str(path), size)
    return _font_cache[key]


# MARK: - エディトリアル部品（トラッキング / ヘアライン / グレイン / 枠ティック）

def tracked_width(draw, text, f, tracking):
    return sum(draw.textlength(c, font=f) for c in text) + tracking * max(len(text) - 1, 0)


def draw_tracked(draw, text, f, fill, x, y, tracking=0, anchor="l"):
    if anchor != "l":
        w = tracked_width(draw, text, f, tracking)
        x = x - w if anchor == "r" else x - w / 2
    for c in text:
        draw.text((x, y), c, font=f, fill=fill)
        x += draw.textlength(c, font=f) + tracking
    return x


def hairline(canvas, x0, y, x1, color=(42, 37, 32), alpha=46, width=2):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).line([(x0, y), (x1, y)], fill=color + (alpha,), width=width)
    canvas.alpha_composite(layer)


def grain(canvas, seed=0, amount=8, coarse=False):
    """フィルムグレイン。**写真背景にだけ薄く**載せる質感用。amount=不透明度(0で無効)。
    ⚠️ フラット面(info/cta やベタ/グラデ背景)には載せない＝ベクター文字・平面に乗ると
    2x2のNEARESTノイズが JPEG圧縮ノイズ状の『画質荒れ』に見える([[SPACING]] §11)。
    既定は full解像度の細かいグレイン（coarse=True で旧来の粗い 2x2 ブロック）。"""
    if amount <= 0:
        return
    rng = np.random.default_rng(seed)
    w, h = canvas.size
    step = 2 if coarse else 1
    n = rng.integers(0, 2, size=(max(1, h // step), max(1, w // step)), dtype=np.uint8) * 255
    noise = Image.fromarray(n, "L")
    if step > 1:
        noise = noise.resize((w, h), Image.NEAREST)
    layer = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    layer.putalpha(noise.point(lambda v: amount if v else 0))
    canvas.alpha_composite(layer)


def _ss_layer(size, scale=4):
    return Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0)), scale


def frame_ticks(canvas, color, alpha=150, margin=64, length=46, width=4, corners="all"):
    layer, ss = _ss_layer(canvas.size)
    d = ImageDraw.Draw(layer)
    W, H = canvas.size
    m, L, wd = margin * ss, length * ss, width * ss
    pts = {"tl": (m, m, 1, 1), "tr": (W * ss - m, m, -1, 1),
           "bl": (m, H * ss - m, 1, -1), "br": (W * ss - m, H * ss - m, -1, -1)}
    use = pts.keys() if corners == "all" else corners
    for k in use:
        x, y, sx, sy = pts[k]
        d.line([(x, y), (x + sx * L, y)], fill=color + (alpha,), width=wd)
        d.line([(x, y), (x, y + sy * L)], fill=color + (alpha,), width=wd)
    canvas.alpha_composite(layer.resize(canvas.size, Image.LANCZOS))


def tick_label(canvas, text, x, y, color, accent, tracking=4, size=30, rule=34):
    d = ImageDraw.Draw(canvas)
    cy = y + size * 0.60
    d.line([(x, cy), (x + rule, cy)], fill=accent, width=3)
    f = font(size, 600)
    draw_tracked(d, text, f, color, x + rule + size * 0.5, y, tracking)
    return x + rule + size * 0.5


# MARK: - SVG レンダラ（依存ゼロ・スーパーサンプリング）

def _path_subpaths(d):
    toks = re.findall(r"[MmLlHhVvCcQqZz]|-?\d*\.?\d+(?:e-?\d+)?", d)
    i, cmd = 0, None
    pos, start = [0.0, 0.0], [0.0, 0.0]
    subs, cur = [], []

    def n():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
        if cmd in ("M", "m"):
            x, y = n(), n()
            if cmd == "m":
                x += pos[0]; y += pos[1]
            if cur:
                subs.append((cur, False)); cur = []
            pos, start, cur = [x, y], [x, y], [(x, y)]
            cmd = "l" if cmd == "m" else "L"
        elif cmd in ("L", "l"):
            x, y = n(), n()
            if cmd == "l":
                x += pos[0]; y += pos[1]
            pos = [x, y]; cur.append((x, y))
        elif cmd in ("H", "h"):
            x = n() + (pos[0] if cmd == "h" else 0); pos = [x, pos[1]]; cur.append((x, pos[1]))
        elif cmd in ("V", "v"):
            y = n() + (pos[1] if cmd == "v" else 0); pos = [pos[0], y]; cur.append((pos[0], y))
        elif cmd in ("C", "c"):
            c = [n() for _ in range(6)]
            if cmd == "c":
                c = [c[k] + pos[k % 2] for k in range(6)]
            p0 = tuple(pos)
            for k in range(1, 19):
                t = k / 18; m = 1 - t
                cur.append((m**3 * p0[0] + 3 * m * m * t * c[0] + 3 * m * t * t * c[2] + t**3 * c[4],
                            m**3 * p0[1] + 3 * m * m * t * c[1] + 3 * m * t * t * c[3] + t**3 * c[5]))
            pos = [c[4], c[5]]
        elif cmd in ("Q", "q"):
            c = [n() for _ in range(4)]
            if cmd == "q":
                c = [c[k] + pos[k % 2] for k in range(4)]
            p0 = tuple(pos)
            for k in range(1, 19):
                t = k / 18; m = 1 - t
                cur.append((m * m * p0[0] + 2 * m * t * c[0] + t * t * c[2],
                            m * m * p0[1] + 2 * m * t * c[1] + t * t * c[3]))
            pos = [c[2], c[3]]
        elif cmd in ("Z", "z"):
            cur.append(tuple(start)); subs.append((cur, True)); cur = []
            pos = list(start)
        else:
            i += 1
    if cur:
        subs.append((cur, False))
    return subs


def _stroke_poly(d, pts, col, w):
    w = max(1, int(round(w)))
    if len(pts) >= 2:
        d.line(pts, fill=col, width=w, joint="curve")
    r = w / 2.0
    for x, y in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


_SVG_EL = re.compile(r"<(path|line|circle|polyline|polygon|rect)\b([^>]*?)/?>", re.S)
_SVG_ATTR = re.compile(r'([\w:-]+)\s*=\s*"([^"]*)"')


_NAMED = {"white": (255, 255, 255), "black": (26, 26, 30), "red": (227, 84, 84),
          "green": (44, 165, 108), "blue": (45, 110, 235), "gold": (240, 190, 78),
          "orange": (234, 142, 56), "yellow": (242, 201, 76), "pink": (231, 122, 138),
          "purple": (140, 92, 206), "teal": (36, 160, 156), "gray": (146, 146, 156),
          "grey": (146, 146, 156), "ink": (42, 37, 32)}


def _parse_color(s):
    """SVG の色文字列 -> RGBA。none/未対応(gradient等) は None。"""
    if not s:
        return None
    s = s.strip().lower()
    if s in ("none", "transparent"):
        return None
    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) >= 6:
            try:
                return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
            except ValueError:
                return None
    if s.startswith("rgb"):
        nums = re.findall(r"[\d.]+", s)
        if len(nums) >= 3:
            return (int(float(nums[0])), int(float(nums[1])), int(float(nums[2])), 255)
    if s in _NAMED:
        return _NAMED[s] + (255,)
    return None  # url(#grad) 等は非対応


def svg_image(name, color, height, ss=4):
    """SVG を height px にラスタライズ。color=None なら各要素の色を尊重(多色/リッチ)、
    色を渡せばその単色で塗る(tint・後方互換)。gradient は非対応(灰でフォールバック)。"""
    text = (SVG_DIR / (name if name.endswith(".svg") else name + ".svg")).read_text()
    m = re.search(r'viewBox\s*=\s*"([^"]+)"', text)
    if m:
        x0, y0, vw, vh = [float(v) for v in m.group(1).replace(",", " ").split()]
    else:
        x0 = y0 = 0.0
        vw = vh = 100.0
    sc = height * ss / vh
    img = Image.new("RGBA", (max(1, round(vw * sc)), max(1, round(vh * sc))), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    override = None if color is None else (color if len(color) == 4 else color + (255,))
    gm = re.search(r"<g\b([^>]*)>", text)
    gdef = dict(_SVG_ATTR.findall(gm.group(1))) if gm else {}
    FALLBACK = (180, 180, 186, 255)

    def T(px, py):
        return ((px - x0) * sc, (py - y0) * sc)

    def colors(a):
        fill = a.get("fill", gdef.get("fill", "black"))
        stroke = a.get("stroke", gdef.get("stroke", "none"))
        op = float(a.get("opacity", "1") or 1)
        fop = float(a.get("fill-opacity", "1") or 1) * op
        sop = float(a.get("stroke-opacity", "1") or 1) * op
        fcol = None if fill == "none" else (override or _parse_color(fill) or FALLBACK)
        scol = None if stroke == "none" else (override or _parse_color(stroke))
        if fcol and fop < 1:
            fcol = fcol[:3] + (int(fcol[3] * fop),)
        if scol and sop < 1:
            scol = scol[:3] + (int(scol[3] * sop),)
        return fcol, scol, float(a.get("stroke-width", gdef.get("stroke-width", 2))) * sc

    for tag, attrs in _SVG_EL.findall(text):
        a = dict(_SVG_ATTR.findall(attrs))
        fcol, scol, sw = colors(a)
        if tag == "path":
            for pts, _closed in _path_subpaths(a.get("d", "")):
                P = [T(*p) for p in pts]
                if fcol:
                    d.polygon(P, fill=fcol)
                if scol:
                    _stroke_poly(d, P, scol, sw if sw else 2 * ss)
        elif tag == "circle":
            c = T(float(a.get("cx", 0)), float(a.get("cy", 0))); r = float(a.get("r", 0)) * sc
            box = [c[0] - r, c[1] - r, c[0] + r, c[1] + r]
            if fcol:
                d.ellipse(box, fill=fcol)
            if scol:
                d.ellipse(box, outline=scol, width=max(1, int(sw)))
        elif tag == "line":
            if scol:
                _stroke_poly(d, [T(float(a["x1"]), float(a["y1"])),
                                 T(float(a["x2"]), float(a["y2"]))], scol, sw)
        elif tag in ("polyline", "polygon"):
            v = [float(t) for t in a.get("points", "").replace(",", " ").split()]
            P = [T(v[k], v[k + 1]) for k in range(0, len(v) - 1, 2)]
            if tag == "polygon" and fcol:
                d.polygon(P, fill=fcol)
            if scol:
                _stroke_poly(d, P, scol, sw if sw else 2 * ss)
        elif tag == "rect":
            x, y = T(float(a.get("x", 0)), float(a.get("y", 0)))
            w, h = float(a.get("width", 0)) * sc, float(a.get("height", 0)) * sc
            rr = float(a.get("rx", 0)) * sc
            box = [x, y, x + w, y + h]
            if fcol:
                d.rounded_rectangle(box, radius=rr, fill=fcol)
            if scol:
                d.rounded_rectangle(box, radius=rr, outline=scol, width=max(1, int(sw)))
    return img.resize((max(1, img.width // ss), max(1, img.height // ss)), Image.LANCZOS)


def has_svg(name):
    return (SVG_DIR / (name if name.endswith(".svg") else name + ".svg")).exists()


def paste_svg(canvas, name, x, y, height, color, anchor="l", alpha=255):
    im = svg_image(name, color, height)
    if alpha < 255:
        a = im.getchannel("A").point(lambda v: v * alpha // 255)
        im.putalpha(a)
    if anchor == "c":
        x -= im.width // 2
    elif anchor == "r":
        x -= im.width
    canvas.alpha_composite(im, (round(x), round(y)))
    return im.width


def arrow(canvas, x, y, length, color, width=3):
    if has_svg("arrow"):
        return paste_svg(canvas, "arrow", x, y, length, color if len(color) == 4 else color + (255,))
    layer, ss = _ss_layer(canvas.size)
    d = ImageDraw.Draw(layer)
    x0, y0 = x * ss, y * ss
    L, wd, hd = length * ss, width * ss, length * ss * 0.42
    d.line([(x0, y0), (x0 + L, y0)], fill=color, width=wd)
    d.line([(x0 + L - hd, y0 - hd), (x0 + L, y0)], fill=color, width=wd)
    d.line([(x0 + L - hd, y0 + hd), (x0 + L, y0)], fill=color, width=wd)
    canvas.alpha_composite(layer.resize(canvas.size, Image.LANCZOS))
    return x + length


def index_tag(canvas, idx, total, x, y, color, anchor="r", size=30):
    d = ImageDraw.Draw(canvas)
    txt = f"{idx:02d} / {total:02d}"
    f = mono_font(size, "regular")
    draw_tracked(d, txt, f, color, x, y, 3, anchor=anchor)


def bottom_scrim(w, h, start=0.42, top_a=0, bot_a=205):
    col = np.zeros(h, np.uint8)
    s0 = int(h * start)
    col[s0:] = np.linspace(top_a, bot_a, h - s0).astype(np.uint8)
    a = np.repeat(col[:, None], w, axis=1)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 3] = a
    return Image.fromarray(rgba, "RGBA")


# MARK: - 画像ユーティリティ

def cover_crop(img, w, h):
    img = img.convert("RGB")
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = round(iw * scale), round(ih * scale)
    img = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - w) // 2, (nh - h) // 2
    return img.crop((x, y, x + w, y + h))


def darken(img, amount):
    black = Image.new("RGB", img.size, (0, 0, 0))
    return Image.blend(img.convert("RGB"), black, amount)


def vgrad_alpha(w, h, top_a, bot_a):
    col = np.linspace(top_a, bot_a, h).astype(np.uint8)
    a = np.repeat(col[:, None], w, axis=1)
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 3] = a
    return Image.fromarray(rgba, "RGBA")


def footage_scene(path):
    src = Image.open(path)
    return lambda size: cover_crop(src, size[0], size[1])


def key_out_green(shot, scene_for_bbox):
    rgb = np.asarray(shot.convert("RGB")).astype(np.int16)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    strength = g - np.maximum(r, b)
    alpha = np.clip((strength - 26) * (255 / 50), 0, 255).astype(np.uint8)
    ys, xs = np.nonzero(alpha > 128)
    if len(xs) == 0:
        return shot.convert("RGB")
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    scene = scene_for_bbox((int(x1 - x0), int(y1 - y0)))
    despilled = rgb.copy()
    despilled[..., 1] = np.minimum(g, np.maximum(r, b) + 24)
    base = Image.fromarray(despilled.astype(np.uint8), "RGB")
    mask = Image.fromarray(alpha, "L").filter(ImageFilter.GaussianBlur(1.2))
    layer = Image.new("RGB", base.size)
    layer.paste(scene, (int(x0), int(y0)))
    base.paste(layer, (0, 0), mask)
    return base


# MARK: - テキストブロック

def draw_lines(draw, lines, f, fill, cx, top, leading, align="center", stroke=0, stroke_fill=None):
    # 行内の \n も安全に展開（PIL は複数行文字列の textlength で落ちるため）
    flat = []
    for ln in lines:
        flat.extend(str(ln).split("\n"))
    y = top
    for ln in flat:
        w = draw.textlength(ln, font=f)
        if align == "center":
            x = cx - w / 2
        elif align == "left":
            x = cx
        else:
            x = cx - w
        draw.text((x, y), ln, font=f, fill=fill, stroke_width=stroke, stroke_fill=stroke_fill)
        y += leading
    return y


def draw_shadowed(canvas, lines, f, fill, cx, top, leading, align="center",
                  shadow_a=170, blur=10, dy=4):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw_lines(ImageDraw.Draw(layer), lines, f, (0, 0, 0, shadow_a), cx, top + dy, leading, align)
    canvas.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))
    return draw_lines(ImageDraw.Draw(canvas), lines, f, fill, cx, top, leading, align)


def rounded_plate(canvas, box, radius, fill):
    plate = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle(box, radius=radius, fill=fill)
    canvas.alpha_composite(plate)


def soft_blob(canvas, accent, cx, cy, r=620, alpha=52):
    blob = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(blob).ellipse([cx - r, cy - r, cx + r, cy + r], fill=accent + (alpha,))
    canvas.alpha_composite(blob.filter(ImageFilter.GaussianBlur(150)))


# MARK: - iPhone モックアップ

def phone_mockup(shot, screen_r=150, bezel=26):
    sw, sh = shot.size
    pad = 14
    body_w, body_h = sw + bezel * 2, sh + bezel * 2
    img = Image.new("RGBA", (body_w + pad * 2, body_h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([pad, pad, pad + body_w, pad + body_h],
                        radius=screen_r + bezel, fill=(23, 23, 26, 255))
    d.rounded_rectangle([pad + 5, pad + 5, pad + body_w - 5, pad + body_h - 5],
                        radius=screen_r + bezel - 5, outline=(72, 70, 68, 255), width=3)
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, sw, sh], radius=screen_r, fill=255)
    img.paste(shot.convert("RGB"), (pad + bezel, pad + bezel), mask)
    return img


def paste_phone_shadow(canvas, phone, cx, top, target_h):
    ratio = target_h / phone.height
    p = phone.resize((round(phone.width * ratio), target_h), Image.LANCZOS)
    px, py = round(cx - p.width / 2), top
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        [px + 10, py + 26, px + p.width + 10, py + p.height + 26],
        radius=120, fill=(60, 45, 35, 80))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(34)))
    canvas.alpha_composite(p, (px, py))
    return p.width


# MARK: - ワードマーク / アイコン / モチーフ / アクセントドット

def _icon_rounded(path, height):
    """アプリアイコンを角丸マスクして返す（wordmark のグリフ＝app固有・material内）。"""
    src = Image.open(path).convert("RGBA")
    ss = 4; size = height * ss
    ic = src.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=int(size * 0.22), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0)); out.paste(ic, (0, 0), mask)
    return out.resize((height, height), Image.LANCZOS)


def wordmark(canvas, brand, x, y, size, anchor="l", on_dark=False):
    """ワードマーク = アプリアイコン（material内・app固有）+ テキスト。
    anchor: l=左基準 / c=中心 / r=右基準。"""
    ink = WHITE if on_dark else brand.ink
    d = ImageDraw.Draw(canvas)
    f = mono_font(int(size * 0.74), "medium")
    tw = d.textlength(brand.wordmark, font=f)
    glyph_img = _icon_rounded(brand.icon, size) if (brand.icon and Path(brand.icon).exists()) else None
    gap = int(size * 0.30)
    total = ((glyph_img.width + gap) if glyph_img else 0) + tw
    x0 = int(x - total / 2) if anchor == "c" else (int(x - total) if anchor == "r" else int(x))
    cx = x0
    if glyph_img is not None:
        canvas.alpha_composite(glyph_img, (cx, y)); cx += glyph_img.width + gap
    d.text((cx, y + size * 0.18), brand.wordmark, font=f, fill=ink)
    return total


def motif(canvas, brand, x, y, height, color, anchor="l", alpha=255):
    """アプリ固有の装飾モチーフ svg（material内・任意）。未設定なら何もしない。"""
    if not (brand.motif and Path(brand.motif).exists()):
        return 0
    im = svg_image(str(brand.motif), color, height)
    if alpha < 255:
        im.putalpha(im.getchannel("A").point(lambda v: v * alpha // 255))
    if anchor == "c":
        x -= im.width // 2
    elif anchor == "r":
        x -= im.width
    canvas.alpha_composite(im, (round(x), round(y)))
    return im.width


def accent_dots(canvas, brand, cx, y, r=11, gap=46):
    d = ImageDraw.Draw(canvas)
    cols = list(brand.accents.values())
    total = (len(cols) - 1) * gap
    x0 = cx - total / 2
    for i, c in enumerate(cols):
        x = x0 + i * gap
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
