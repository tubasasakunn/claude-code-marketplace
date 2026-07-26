#!/usr/bin/env python3
"""standard 雛形：宣伝動画のシーン型カタログ（spec 駆動・app 非依存）。

各シーンは spec の 1 エントリ（dict）＋ Brand（material/manifest.json）＋ material/ から組む。
文言・素材・アクセントはすべて spec / manifest から来る＝アプリ固有をハードコードしない。
新しい動画は spec(JSON) を書くだけ。新しい見せ方が要るときだけここに型を足す。

シーン型（spec の "type"）:
  cold_open     表紙：ブランドモチーフが咲く＋ワードマーク＋タグライン
  hook          フック：footage を Ken Burns、見出し＋サブを立ち上げ
  day_cycle     時間が流れる：複数 footage を連続フェーズでクロスフェード＋時間帯アクセント循環
  app_magic     実機の瞬間：緑ビューファインダを footage 差し替え＋タップ波紋
  proof_gallery 証拠：実画面 3 台のパララックス・ギャラリー
  privacy       メッセージ：暗い footage＋モチーフ svg＋見出し
  cta           締め：モチーフ＋ワードマーク＋タグライン＋誘導＋アクセントドット
共通フィールド: frames(必須), accent(アクセント名), kicker, head[], sub[], foot[]
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

import video as V
B = V.B


# ------------------------------------------------------------------ helpers
def _edge():
    return B.sp("edge")


def _ft(MAT, name):
    return Path(MAT) / "footage" / f"{name}.jpg"


def _acc(brand, name, default="evening"):
    if name and name in brand.accents:
        return brand.accents[name]
    return brand.accent(default)


# ------------------------------------------------------------------ cold_open
class ColdOpen(V.Clip):
    def __init__(self, s, brand, MAT):
        super().__init__(s["frames"]); self.s = s; self.br = brand
        self.acc = _acc(brand, s.get("accent"))

    def render(self, i):
        s, br = self.s, self.br
        t = i / (self.n - 1)
        c = Image.new("RGBA", (V.W, V.H), tuple(br.bg) + (255,))
        ta = int(130 * V.eo_cubic(V.seg(t, 0.05, 0.5)))
        if ta:
            V.frame_ticks(c, self.acc, alpha=ta)
        sb = V.seg(t, 0.10, 0.72)
        if sb > 0 and br.motif and Path(br.motif).exists():
            hgt = int(V.lerp(150, 300, V.eo_quint(sb)))
            ang = V.lerp(-35, 0, V.eo_quint(sb))
            mot = B.svg_image(str(br.motif), self.acc, hgt).rotate(
                ang, resample=Image.BICUBIC, expand=True)
            a = int(255 * V.eo_cubic(V.seg(t, 0.10, 0.55)))
            mot.putalpha(mot.getchannel("A").point(lambda v: v * a // 255))
            c.alpha_composite(mot, (V.W // 2 - mot.width // 2, 600 - mot.height // 2))
        V.anim_layer(c, lambda L: B.wordmark(L, br, V.W // 2, 880, 78, anchor="c"),
                     V.seg(t, 0.45, 0.85), dy=40)

        def w2(L):
            V.head_lines(L, [s["tagline"]], 50, V.W // 2, 1010, tuple(br.ink),
                         kind=br.head, align="c")
            if s.get("kicker"):
                V.mono_label(L, s["kicker"], V.W // 2 - 86, 1110, tuple(br.sub_ink),
                             size=28, tracking=8)
        V.anim_layer(c, w2, V.seg(t, 0.58, 0.95), dy=34)
        fi = V.eo_cubic(V.seg(t, 0.0, 0.12))
        if fi < 1:
            c = Image.blend(Image.new("RGBA", (V.W, V.H), tuple(br.bg) + (255,)), c, fi)
        return c.convert("RGB")


# ------------------------------------------------------------------ hook
class Hook(V.Clip):
    def __init__(self, s, brand, MAT):
        super().__init__(s["frames"]); self.s = s; self.br = brand
        self.acc = _acc(brand, s.get("accent"))
        self.base = V.kb_base(_ft(MAT, s["footage"]))

    def render(self, i):
        s, br = self.s, self.br
        t = i / (self.n - 1)
        c = V.kb_frame(self.base, t, z0=1.0, z1=1.12,
                       pan0=(-0.02, -0.03), pan1=(0.02, 0.02)).convert("RGBA")
        V.grain(c, seed=11)
        V.scrim(c, start=0.30, bot_a=225); V.topscrim(c, h=430, a=120)
        V.small_wordmark(c, br, on_dark=True)
        V.frame_ticks(c, self.acc, alpha=120)
        if s.get("kicker"):
            V.anim_layer(c, lambda L: V.mono_label(L, s["kicker"], _edge(), 1170,
                         (235, 228, 220), accent=self.acc, size=30, tracking=7),
                         V.seg(t, 0.12, 0.45), dy=30)
        V.anim_layer(c, lambda L: V.head_lines(L, s["head"], 96, _edge(), 1230,
                     B.WHITE, kind=br.head), V.seg(t, 0.22, 0.62), dy=56)
        if s.get("sub"):
            V.anim_layer(c, lambda L: V.head_lines(L, s["sub"], 58, _edge(), 1380,
                         (236, 214, 198), kind=br.head), V.seg(t, 0.45, 0.85), dy=44)
        return c.convert("RGB")


# ------------------------------------------------------------------ day_cycle
class DayCycle(V.Clip):
    XF = 0.30  # クロスフェード幅（セグメント単位）

    def __init__(self, s, brand, MAT):
        super().__init__(s["frames"]); self.s = s; self.br = brand
        self.steps = s["steps"]
        self.bases = [V.kb_base(_ft(MAT, st["footage"])) for st in self.steps]
        self.accs = [_acc(brand, st.get("accent")) for st in self.steps]

    def _phase(self, fpos, k):
        span = 1.0 + 2.0 * self.XF
        return V.clamp01((fpos - (k - self.XF)) / span)

    def _kb(self, k, fpos):
        return V.kb_frame(self.bases[k], self._phase(fpos, k),
                          z0=1.05, z1=1.13, pan0=(-0.012, 0), pan1=(0.012, 0))

    def _clock(self, c, k, alpha, accent):
        if alpha <= 0.01:
            return
        st = self.steps[k]
        def draw(L):
            V.mono_label(L, st["clock"], _edge(), 1490, B.WHITE,
                         accent=accent, size=46, tracking=4, rule=52)
            V.head_lines(L, [st["word"]], 40, _edge(), 1556, (236, 230, 222),
                         kind=self.br.head)
        V.fade_layer(c, draw, alpha)

    def render(self, i):
        br = self.br
        t = i / (self.n - 1)
        N = len(self.steps)
        fpos = t * N
        idx = min(N - 1, int(fpos)); local = fpos - idx
        cur = self._kb(idx, fpos)
        in_xf = local > 1 - self.XF and idx < N - 1
        if in_xf:
            a = V.smooth((local - (1 - self.XF)) / self.XF)
            cur = Image.blend(cur, self._kb(idx + 1, fpos), a)
            accent = V.lerp_col(self.accs[idx], self.accs[idx + 1], a)
        else:
            a = 0.0; accent = self.accs[idx]
        c = cur.convert("RGBA")
        V.grain(c, seed=20)  # 固定シード＝グレイン静止
        V.scrim(c, start=0.46, bot_a=215); V.topscrim(c, h=420, a=130)
        V.small_wordmark(c, br, on_dark=True)
        V.frame_ticks(c, accent, alpha=120)
        # 時間帯バー（連続）
        barw = V.W - 2 * _edge(); bx = _edge(); by = 1640
        lay = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        dd.line([(bx, by), (bx + barw, by)], fill=(255, 255, 255, 60), width=3)
        dd.line([(bx, by), (bx + int(barw * V.clamp01(t)), by)], fill=accent + (255,), width=5)
        for k in range(N):
            dotx = bx + barw * (k + 0.5) / N
            lit = V.clamp01(fpos - k + 0.5)
            col = V.lerp_col((255, 255, 255), self.accs[k], lit); r = 7 + 2 * lit
            dd.ellipse([dotx - r, by - r, dotx + r, by + r],
                       fill=col + (int(90 + 165 * lit),))
        c.alpha_composite(lay)
        self._clock(c, idx, 1.0 - a, accent)
        if in_xf:
            self._clock(c, idx + 1, a, self.accs[idx + 1])
        if self.s.get("head"):
            V.anim_layer(c, lambda L: V.head_lines(L, self.s["head"], 62, _edge(), 250,
                         B.WHITE, kind=br.head, leading=82), V.seg(t, 0.04, 0.26), dy=40)
        return c.convert("RGB")


# ------------------------------------------------------------------ app_magic
class AppMagic(V.Clip):
    def __init__(self, s, brand, MAT):
        super().__init__(s["frames"]); self.s = s; self.br = brand
        self.acc = _acc(brand, s.get("accent"))
        self.base = V.kb_base(_ft(MAT, s.get("footage_bg", s.get("footage"))))
        vf = _ft(MAT, s["viewfinder"]) if s.get("viewfinder") else None
        self.phone = V.keyed_phone(MAT, s["shot"], vf)

    def render(self, i):
        s, br = self.s, self.br
        t = i / (self.n - 1)
        c = V.kb_frame(self.base, t, z0=1.06, z1=1.16).convert("RGBA")
        V.grain(c, seed=40)
        c.alpha_composite(B.vgrad_alpha(V.W, V.H, 120, 30))
        V.scrim(c, start=0.55, bot_a=170)
        V.small_wordmark(c, br, on_dark=True)
        V.frame_ticks(c, self.acc, alpha=120)
        rise = V.eo_quint(V.seg(t, 0.0, 0.5))
        top = V.lerp(V.H + 60, 360, rise)
        px, py, pw, ph = V.phone_place(c, self.phone, V.W // 2, top, 1180)
        rip = V.seg(t, 0.52, 0.92)
        if rip > 0:
            V.ripple(c, px + pw * 0.5, py + ph * 0.715, rip, self.acc, rmax=150)

        def cap(L):
            if s.get("kicker"):
                V.mono_label(L, s["kicker"], _edge(), 150, (240, 234, 226),
                             accent=self.acc, size=30, tracking=7)
            V.head_lines(L, s["head"], 70, _edge(), 200, B.WHITE, kind=br.head, leading=92)
        V.anim_layer(c, cap, V.seg(t, 0.18, 0.55), dy=40)
        return c.convert("RGB")


# ------------------------------------------------------------------ proof_gallery
class ProofGallery(V.Clip):
    def __init__(self, s, brand, MAT):
        super().__init__(s["frames"]); self.s = s; self.br = brand
        self.acc = _acc(brand, s.get("accent"))
        def mk(d):
            vf = _ft(MAT, d["key"]) if d.get("key") else None
            return V.keyed_phone(MAT, d["shot"], vf)
        sides = s.get("sides", [])
        # [left, hero, right]
        self.phones = [mk(sides[0]) if len(sides) > 0 else mk(s["hero"]),
                       mk(s["hero"]),
                       mk(sides[1]) if len(sides) > 1 else mk(s["hero"])]

    def render(self, i):
        s, br = self.s, self.br
        t = i / (self.n - 1)
        c = Image.new("RGBA", (V.W, V.H), tuple(br.bg) + (255,))
        B.soft_blob(c, self.acc, V.W * 0.5, 720, r=720, alpha=46)
        V.frame_ticks(c, self.acc, alpha=120)
        V.small_wordmark(c, br, on_dark=False)
        drift = V.eo_cubic(t) * 150
        th = 1080
        centers = [V.W * 0.5 + 470, V.W * 0.5 - 40, V.W * 0.5 - 560]
        depth = [0.6, 1.0, 0.6]
        for k in (0, 2, 1):   # far first, hero last
            ph = self.phones[k]
            cx = centers[k] - drift * depth[k]
            tt = th if k == 1 else int(th * 0.82)
            top = 470 if k == 1 else 560
            ap = 255 if k == 1 else 180
            ratio = tt / ph.height
            p = ph.resize((round(ph.width * ratio), tt), Image.LANCZOS)
            if ap < 255:
                p.putalpha(p.getchannel("A").point(lambda v: v * ap // 255))
            sh = Image.new("RGBA", c.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle(
                [cx - p.width / 2 + 12, top + 30, cx + p.width / 2 + 12, top + p.height + 30],
                radius=120, fill=(60, 50, 40, 70))
            c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(34)))
            c.alpha_composite(p, (round(cx - p.width / 2), top))

        def cap(L):
            if s.get("kicker"):
                V.mono_label(L, s["kicker"], _edge(), 150, tuple(br.sub_ink),
                             accent=self.acc, size=30, tracking=7)
            V.head_lines(L, s["head"], 64, _edge(), 200, tuple(br.ink),
                         kind=br.head, leading=84)
        V.anim_layer(c, cap, V.seg(t, 0.12, 0.5), dy=40)
        if s.get("foot"):
            V.anim_layer(c, lambda L: V.head_lines(L, [s["foot"]], 38, _edge(), 1660,
                         tuple(br.sub_ink), kind=br.head), V.seg(t, 0.4, 0.8), dy=30)
        return c.convert("RGB")


# ------------------------------------------------------------------ privacy
class Privacy(V.Clip):
    def __init__(self, s, brand, MAT):
        super().__init__(s["frames"]); self.s = s; self.br = brand
        self.acc = _acc(brand, s.get("accent"), default="midnight")
        self.base = V.kb_base(_ft(MAT, s["footage"]))

    def render(self, i):
        s, br = self.s, self.br
        t = i / (self.n - 1)
        bg = B.darken(V.kb_frame(self.base, t, z0=1.05, z1=1.14), 0.30)
        c = bg.convert("RGBA")
        V.grain(c, seed=60)
        c.alpha_composite(B.vgrad_alpha(V.W, V.H, 90, 120))
        V.frame_ticks(c, self.acc, alpha=130)
        V.small_wordmark(c, br, on_dark=True)
        sb = V.seg(t, 0.1, 0.6)
        if sb > 0 and s.get("motif") and B.has_svg(s["motif"]):
            sh = B.svg_image(s["motif"], self.acc, int(V.lerp(120, 188, V.eo_quint(sb))))
            a = int(255 * V.eo_cubic(sb))
            sh.putalpha(sh.getchannel("A").point(lambda v: v * a // 255))
            c.alpha_composite(sh, (V.W // 2 - sh.width // 2, 560 - sh.height // 2))
        if s.get("kicker"):
            V.anim_layer(c, lambda L: V.mono_label(L, s["kicker"], V.W // 2 - 150, 760,
                         (220, 214, 230), size=28, tracking=6), V.seg(t, 0.2, 0.55), dy=26)

        def t2(L):
            V.head_lines(L, s["head"], 84, V.W // 2, 830, B.WHITE, kind=br.head, align="c")
            if s.get("sub"):
                V.head_lines(L, s["sub"], 56, V.W // 2, 950, (214, 206, 226),
                             kind=br.head, align="c")
        V.anim_layer(c, t2, V.seg(t, 0.3, 0.7), dy=46)
        if s.get("foot"):
            V.anim_layer(c, lambda L: V.head_lines(L, s["foot"], 36, V.W // 2, 1080,
                         (190, 184, 206), kind=br.head, align="c"), V.seg(t, 0.5, 0.9), dy=30)
        return c.convert("RGB")


# ------------------------------------------------------------------ cta
class CTA(V.Clip):
    def __init__(self, s, brand, MAT):
        super().__init__(s["frames"]); self.s = s; self.br = brand
        self.acc = _acc(brand, s.get("accent"))

    def render(self, i):
        s, br = self.s, self.br
        t = i / (self.n - 1)
        c = Image.new("RGBA", (V.W, V.H), tuple(br.bg) + (255,))
        B.soft_blob(c, self.acc, V.W * 0.5, 640, r=620, alpha=50)
        V.frame_ticks(c, self.acc, alpha=130)
        if br.motif and Path(br.motif).exists():
            pulse = 1 + 0.03 * math.sin(t * math.pi * 2)
            mot = B.svg_image(str(br.motif), self.acc, int(216 * pulse))
            a = int(255 * V.eo_cubic(V.seg(t, 0.0, 0.3)))
            mot.putalpha(mot.getchannel("A").point(lambda v: v * a // 255))
            c.alpha_composite(mot, (V.W // 2 - mot.width // 2, 560 - mot.height // 2))
        V.anim_layer(c, lambda L: B.wordmark(L, br, V.W // 2, 820, 96, anchor="c"),
                     V.seg(t, 0.18, 0.5), dy=36)
        V.anim_layer(c, lambda L: V.head_lines(L, [s["tagline"]], 54, V.W // 2, 980,
                     tuple(br.ink), kind=br.head, align="c"), V.seg(t, 0.3, 0.62), dy=34)
        if s.get("cta"):
            V.anim_layer(c, lambda L: V.mono_label(L, s["cta"], V.W // 2 - 150, 1110,
                         tuple(br.sub_ink), size=34, tracking=4), V.seg(t, 0.45, 0.78), dy=28)
        da = V.eo_cubic(V.seg(t, 0.55, 0.9))
        if da > 0:
            dl = Image.new("RGBA", (V.W, V.H), (0, 0, 0, 0))
            B.accent_dots(dl, br, V.W // 2, 1230, r=11, gap=46)
            dl.putalpha(dl.getchannel("A").point(lambda v: int(v * da)))
            c.alpha_composite(dl)
        return c.convert("RGB")


# ------------------------------------------------------------------ registry / builder
TYPES = {
    "cold_open": ColdOpen, "hook": Hook, "day_cycle": DayCycle,
    "app_magic": AppMagic, "proof_gallery": ProofGallery,
    "privacy": Privacy, "cta": CTA,
}


def build_clips(spec, brand, MAT):
    clips = []
    for ent in spec["scenes"]:
        cls = TYPES.get(ent["type"])
        if cls is None:
            raise SystemExit(f"standard: 未知のシーン型 '{ent['type']}'（{list(TYPES)}）")
        clips.append(cls(ent, brand, MAT))
    return clips
