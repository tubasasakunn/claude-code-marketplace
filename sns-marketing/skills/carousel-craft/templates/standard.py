#!/usr/bin/env python3
"""雛形『standard』— エディトリアル・ミニマルのカルーセル一式（全アプリ共通の基準）。

スライド型: cover(7 variant) / photo / shot(見切れ) / info / cta。
各レンダラは (spec, W, H, brand) を受け取り、brand（material/manifest.json）で色・
ワードマーク・素材・見出しフォントを差し替える。投稿ごとにこれをコピーして新しいエンジンを作る前提。

設計方針（[[DESIGN_NOTES]]）:
- 見出しは **太い丸/角ゴシック**（Noto明朝の"AIっぽさ"を避ける。brand.head=maru/kaku/antique/mincho）。
- **chrome を載せない**（左上ワードマーク・右上ページ番号・「ポイント」等の汎用ラベルは削除）。
- **余白を大きく・情報は最小限・小さい文字は書かない**。アイコン(SVGバンク)で直感的に。
- 背景は「暗幕＋文字」の一辺倒にしない（cover_card 等のクリーン表現も使う）。
"""
import math
import os
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
import brand as B  # noqa: E402

WHITE = (255, 255, 255)
SOFT_W = (255, 255, 255, 235)


def _repo_root():
    """リポジトリルート（target/ と CLAUDE.md を持つ階層）。spec の bg は repo 相対(material/...)で書けるようにする。

    このスキルは plugin cache（~/.claude/plugins/cache/...）に配られるので、__file__ から
    上へ辿るだけでは見つからない（cache はリポジトリの外）。呼び出し側の gen.py が
    SNS_ROOT を立てて渡すのでそれを最優先で使い、無ければ上方探索 → $HOME 候補の順に落ちる。
    ここで "/" に落ちると bg が解決できず、全スライドが無地になる。
    """
    def ok(d):
        d = Path(d)
        return d.is_dir() and (d / "target").is_dir() and (d / "CLAUDE.md").exists()

    env = os.environ.get("SNS_ROOT")
    if env and ok(env):
        return Path(env).resolve()
    for d in Path(__file__).resolve().parents:
        if ok(d):
            return d
    home = Path.home()
    for d in [home / "workspace" / "marketing", home / "workspace_tmp" / "marketing",
              home / "marketing", *sorted(home.glob("*/marketing"))]:
        if ok(d):
            return d.resolve()
    return Path("/")   # 見つからない＝素材が引けない。gen.py 側の素材チェックで落ちる


REPO_ROOT = _repo_root()


def margin(W):
    return round(W * 0.085)


def H_(brand, size):
    return B.head_font(round(size), brand.head)


def _path(brand, val):
    """bg/footage/shot を解決: 絶対パス or **リポジトリルート相対(material/images/..)** or
    app material/(footage|screenshots)/<名> or 拡張子補完。素材バンクは repo 相対で書ける（自己完結）。"""
    if not val:
        return None
    p = Path(str(val))
    if p.is_absolute() and p.exists():
        return p
    # リポジトリルート基準（CWD 非依存）。spec の bg に "material/images/<uuid>.jpg" と書ける。
    rr = REPO_ROOT / val
    if rr.exists():
        return rr
    mat = brand.material
    if mat and val in getattr(brand, "footage", {}):
        cand = mat / brand.footage[val]
        if cand.exists():
            return cand
    if mat:
        # screens/ は hanasu 系の置き場（hioto=material/直下, anki/connect=screenshots/）
        for cand in (mat / val, mat / "screens" / val, mat / "screenshots" / val, mat / "footage" / val):
            if cand.exists():
                return cand
        for ext in ("jpg", "png", "jpeg", "webp"):
            c = mat / "footage" / f"{val}.{ext}"
            if c.exists():
                return c
    return p if p.exists() else None


def _fit(d, text, kind, brand, max_w, start_px):
    """max_w に収まる最大の head_font サイズを返す。"""
    px = start_px
    while px > 24 and d.textlength(text, font=H_(brand, px)) > max_w:
        px -= 4
    return H_(brand, px)


def _swipe(canvas, x, y, s, color=SOFT_W):
    d = ImageDraw.Draw(canvas)
    ax = B.draw_tracked(d, "SWIPE", B.mono_font(round(26 * s), "medium"), color, x, y, 8)
    B.arrow(canvas, ax + round(16 * s), y + round(13 * s), round(28 * s), color)


def _tall(W, H):
    """9:16（TikTok/Reels）か。3:4（Lemon8/IG）と UI 被りの重さが桁で違う。"""
    return H / W > 1.55


def _anchor(W, H, base, tall_ratio):
    """テキスト群の**下端アンカー**比率を返す。

    9:16 は下 810px がUI（キャプション＋操作）に食われ、使えるのは y=270〜1110 ＝
    フレームの44%しかない（[[LAYOUTS]] §2・実測）。従来の下寄せ（0.76〜0.82H）は
    そのUI帯のど真ん中で、**表紙のフックが実機で読めない**。9:16 だけ可視帯へ引き上げる。
    3:4 は下 173px だけなので従来の下寄せを保つ（構図としてはこちらが本来）。"""
    return round(H * (tall_ratio if _tall(W, H) else base))


def _swipe_bottom(canvas, M, W, H, s):
    _swipe(canvas, M, round(H * 0.565) if _tall(W, H) else H - round(116 * s), s)


def _cover_base(spec, W, H, brand, dark=0.42, scrim_start=0.30, scrim_bot=215):
    s = W / 1080
    bgp = _path(brand, spec.get("bg"))
    dark = spec.get("dark", dark)      # spec 側で明度を上書き（時間帯の階調・明るい素材の救済）
    if bgp:
        canvas = B.darken(B.cover_crop(Image.open(bgp), W, H), dark).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (W, H), brand.ink + (255,))
        B.soft_blob(canvas, brand.accent(spec["accent"]), W // 2, round(H * 0.3), r=round(680 * s), alpha=90)
    canvas.alpha_composite(B.vgrad_alpha(W, H, 70, 0))
    canvas.alpha_composite(B.bottom_scrim(W, H, start=scrim_start, bot_a=scrim_bot))
    B.frame_ticks(canvas, WHITE, alpha=90, margin=round(52 * s), length=round(40 * s), width=3)
    return canvas


def _hl(canvas, head, hf, accent, M, top, lead, hl):
    if not hl:
        return
    d = ImageDraw.Draw(canvas)
    for li, line in enumerate(head):
        j = line.find(hl)
        if j >= 0:
            d.text((M + d.textlength(line[:j], font=hf), top + li * lead), hl, font=hf, fill=accent)


# MARK: - カバー variant

def cover_editorial(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.42)
    head = spec["headline"].split("\n")
    hf = H_(brand, 112 * s)
    lead = round(136 * s)
    top = _anchor(W, H, 0.82, 0.50) - len(head) * lead
    if spec.get("kicker"):
        B.tick_label(canvas, spec["kicker"], M, top - round(74 * s), WHITE, accent, size=round(30 * s))
    B.draw_shadowed(canvas, head, hf, WHITE, M, top, lead, align="left", shadow_a=130, blur=9)
    _hl(canvas, head, hf, accent, M, top, lead, spec.get("hl"))
    end = top + len(head) * lead
    d = ImageDraw.Draw(canvas)
    d.line([(M, end + round(20 * s)), (M + round(110 * s), end + round(20 * s))], fill=accent, width=round(8 * s))
    _swipe(canvas, M, end + round(46 * s), s)
    return canvas


def cover_card(spec, W, H, brand):
    """写真をほぼ暗くせず、クリーンな角丸パネルに見出しを載せる（暗幕パターンから脱却）。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    bgp = _path(brand, spec.get("bg"))
    if bgp:
        canvas = B.darken(B.cover_crop(Image.open(bgp), W, H), 0.14).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (W, H), accent + (255,))
        B.soft_blob(canvas, brand.ink, W // 2, round(H * 0.7), r=round(720 * s), alpha=60)
    head = spec["headline"].split("\n")
    hf = H_(brand, 92 * s)
    lead = round(118 * s)
    pad = round(56 * s)
    # SWIPE 行のぶん(56s)を必ず確保する。入れないとパネル下端＝見出し最終行の下端と一致し、
    # SWIPE が見出しに**重なって**描かれる（実測バグ）。
    panel_h = len(head) * lead + pad * 2 + round(56 * s) + (round(56 * s) if spec.get("kicker") else 0)
    # パネル**下端**がUI帯に入らないよう上限を掛ける（9:16=下810px / 3:4=下173px）
    py = min(round(H * 0.64), H - (round(H * 0.42) if _tall(W, H) else round(H * 0.12)) - panel_h)
    B.rounded_plate(canvas, [M, py, W - M, py + panel_h], round(48 * s), brand.bg + (250,))
    d = ImageDraw.Draw(canvas)
    ty = py + pad
    if spec.get("kicker"):
        B.tick_label(canvas, spec["kicker"], M + pad, ty, brand.sub_ink, accent, size=round(28 * s))
        ty += round(56 * s)
    B.draw_lines(d, head, hf, brand.ink, M + pad, ty, lead, align="left")
    _hl(canvas, head, hf, accent, M + pad, ty, lead, spec.get("hl"))
    _swipe(canvas, M + pad, py + panel_h - pad - round(8 * s), s, color=brand.sub_ink + (255,))
    return canvas


def cover_question(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.50, scrim_start=0.22, scrim_bot=228)
    q = spec["question"].split("\n")
    qf = H_(brand, 100 * s)
    lead = round(124 * s)
    ans = spec.get("answer")
    top = _anchor(W, H, 0.76, 0.50) - len(q) * lead - (round(108 * s) if ans else 0)
    d = ImageDraw.Draw(canvas)
    B.draw_tracked(d, "Q.", B.mono_font(round(70 * s), "light"), accent + (255,), M, top - round(96 * s), 2)
    end = B.draw_shadowed(canvas, q, qf, WHITE, M, top, lead, align="left", shadow_a=140, blur=9)
    if ans:
        ay = end + round(40 * s)
        ax = B.draw_tracked(d, "A.", B.mono_font(round(36 * s), "medium"), accent + (255,), M, ay, 2)
        d.text((ax + round(16 * s), ay - round(6 * s)), spec["answer"], font=H_(brand, 48 * s), fill=SOFT_W)
    _swipe_bottom(canvas, M, W, H, s)
    return canvas


def cover_quote(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.52, scrim_start=0.24, scrim_bot=224)
    q = spec["quote"].split("\n")
    qf = H_(brand, 100 * s)
    lead = round(128 * s)
    top = _anchor(W, H, 0.78, 0.52) - len(q) * lead
    if B.has_svg("quote"):
        B.paste_svg(canvas, "quote", M, top - round(120 * s), round(82 * s), accent)
    B.draw_shadowed(canvas, q, qf, WHITE, M, top, lead, align="left", shadow_a=140, blur=10)
    _swipe_bottom(canvas, M, W, H, s)
    return canvas


def cover_split(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.54, scrim_start=0.16, scrim_bot=232)
    d = ImageDraw.Draw(canvas)
    y = _anchor(W, H, 0.42, 0.30)
    B.draw_tracked(d, "BEFORE", B.mono_font(round(28 * s), "medium"), (255, 255, 255, 140), M, y, 6)
    y += round(54 * s)
    y = B.draw_shadowed(canvas, spec["before"].split("\n"), H_(brand, 66 * s),
                        (255, 255, 255, 210), M, y, round(86 * s), align="left", shadow_a=110, blur=7)
    y += round(36 * s)
    B.hairline(canvas, M, y, W - M, color=(255, 255, 255), alpha=70, width=2)
    y += round(42 * s)
    B.draw_tracked(d, "AFTER", B.mono_font(round(28 * s), "medium"), accent + (255,), M, y, 6)
    y += round(58 * s)
    B.draw_shadowed(canvas, spec["after"].split("\n"), H_(brand, 100 * s),
                    accent + (255,), M, y, round(116 * s), align="left", shadow_a=120, blur=8)
    _swipe_bottom(canvas, M, W, H, s)
    return canvas


def cover_versus(spec, W, H, brand):
    s, cx, M, accent = W / 1080, W // 2, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.56, scrim_start=0.5, scrim_bot=120)
    f1 = H_(brand, 74 * s)
    B.draw_shadowed(canvas, [spec["a"]], f1, WHITE, cx, _anchor(W, H, 0.34, 0.22), round(92 * s), align="center", shadow_a=120, blur=9)
    B.draw_shadowed(canvas, ["VS"], H_(brand, 124 * s), accent + (255,), cx, _anchor(W, H, 0.45, 0.32),
                    round(124 * s), align="center", shadow_a=120, blur=10)
    B.draw_shadowed(canvas, [spec["b"]], f1, WHITE, cx, _anchor(W, H, 0.61, 0.43), round(92 * s), align="center", shadow_a=120, blur=9)
    B.draw_shadowed(canvas, [spec["question"]], B.font(round(42 * s), 600), SOFT_W, cx, _anchor(W, H, 0.73, 0.53),
                    round(58 * s), align="center", shadow_a=110, blur=6)
    _swipe(canvas, cx - round(58 * s), round(H * 0.565) if _tall(W, H) else H - round(116 * s), s)
    return canvas


def cover_numeric(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.46, scrim_start=0.30, scrim_bot=218)
    big = spec["big"].split("\n")
    bf = H_(brand, 132 * s)
    lead = round(150 * s)
    teaser = spec.get("teaser")
    top = _anchor(W, H, 0.78, 0.52) - len(big) * lead - (round(70 * s) if teaser else 0)
    if spec.get("kicker"):
        B.tick_label(canvas, spec["kicker"], M, top - round(78 * s), WHITE, accent, size=round(30 * s))
    end = B.draw_shadowed(canvas, big, bf, WHITE, M, top, lead, align="left", shadow_a=120, blur=9)
    if teaser:
        d = ImageDraw.Draw(canvas)
        d.line([(M, end + round(26 * s)), (M + round(110 * s), end + round(26 * s))], fill=accent, width=round(8 * s))
        B.draw_shadowed(canvas, [teaser], B.font(round(36 * s), 500), SOFT_W, M, end + round(46 * s),
                        round(48 * s), align="left", shadow_a=110, blur=5)
    _swipe_bottom(canvas, M, W, H, s)
    return canvas


def cover_giant(spec, W, H, brand):
    """巨大数字。**数字そのものが主役**で、言葉は数字の脇役に落とす（numeric との違いはそこ）。

    数字を画面高の 20〜24% で置く＝ジャンプ率4.0超。日本のカルーセル運用の実務記事も
    「数字は大きく太く、スマホで一瞬で理解できるサイズ」を最初に挙げる。→ [[LAYOUTS]] §7-1。
    `big`(数字) ＋ `unit`(単位・小さくアクセント色) ＋ `kicker` / `teaser`(各1行)。"""
    s, M, cx = W / 1080, margin(W), W // 2
    accent = brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=spec.get("dark", 0.56), scrim_start=0.20, scrim_bot=196)
    d = ImageDraw.Draw(canvas)
    big, unit = str(spec["big"]), spec.get("unit", "")
    gf = H_(brand, round(H * (0.225 if _tall(W, H) else 0.185)))
    uf = H_(brand, round(H * 0.052))
    bw, uw = d.textlength(big, font=gf), (d.textlength(unit, font=uf) if unit else 0)
    gap = round(16 * s) if unit else 0
    x0 = cx - (bw + gap + uw) / 2
    top = _anchor(W, H, 0.70, 0.47) - round(gf.size * 1.06)
    if spec.get("kicker"):
        B.tick_label(canvas, spec["kicker"], M, top - round(88 * s), WHITE, accent, size=round(30 * s))
    B.draw_shadowed(canvas, [big], gf, WHITE, x0, top, gf.size, align="left", shadow_a=150, blur=16)
    if unit:
        d.text((x0 + bw + gap, top + gf.size * 0.62), unit, font=uf, fill=accent + (255,))
    y = top + round(gf.size * 1.06)
    d.line([(cx - round(70 * s), y + round(20 * s)), (cx + round(70 * s), y + round(20 * s))],
           fill=accent, width=round(8 * s))
    if spec.get("teaser"):
        B.draw_shadowed(canvas, [spec["teaser"]], H_(brand, 52 * s), SOFT_W, cx, y + round(52 * s),
                        round(66 * s), align="center", shadow_a=130, blur=8)
    _swipe(canvas, cx - round(58 * s), round(H * 0.565) if _tall(W, H) else H - round(116 * s), s)
    return canvas


def cover_magazine(spec, W, H, brand):
    """雑誌の表紙。**柱（英字ロゴ＋号数）→ 太罫 → 写真 → 日本語キャッチ → 英字の小見出し**。

    誌面設計の語彙（版面・柱・ノンブル・見出し階層）をそのまま縦1080に持ち込む型。
    英字を添えると情報量を増やさずに格が上がるので、日本語の大見出しと組でだけ使う。
    → [[LAYOUTS]] §7-2。`headline`(日本語) ＋ `en`(英字サブ) ＋ `issue`(柱の右)。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=spec.get("dark", 0.44), scrim_start=0.26, scrim_bot=210)
    d = ImageDraw.Draw(canvas)
    # 柱: 英字ワードマーク（左）と号数（右）を1本の罫線で締める
    top = round(H * (0.150 if _tall(W, H) else 0.105))
    lf = B.mono_font(round(40 * s), "medium")
    B.draw_tracked(d, brand.wordmark.upper(), lf, WHITE, M, top, round(14 * s))
    if spec.get("issue"):
        B.draw_tracked(d, spec["issue"], B.mono_font(round(30 * s), "light"), (255, 255, 255, 190),
                       W - M, top + round(8 * s), 6, anchor="r")
    rule_y = top + round(64 * s)
    d.line([(M, rule_y), (W - M, rule_y)], fill=WHITE + (230,), width=round(6 * s))

    head = spec["headline"].split("\n")
    hf = H_(brand, 104 * s)
    lead = round(128 * s)
    hy = _anchor(W, H, 0.74, 0.485) - len(head) * lead
    B.draw_shadowed(canvas, head, hf, WHITE, M, hy, lead, align="left", shadow_a=140, blur=10)
    _hl(canvas, head, hf, accent, M, hy, lead, spec.get("hl"))
    end = hy + len(head) * lead
    B.hairline(canvas, M, end + round(22 * s), W - M, color=(255, 255, 255), alpha=120, width=2)
    if spec.get("en"):
        B.draw_tracked(d, spec["en"].upper(), B.mono_font(round(28 * s), "regular"),
                       accent + (255,), M, end + round(44 * s), round(10 * s))
    _swipe_bottom(canvas, M, W, H, s)
    return canvas


COVER_VARIANTS = {
    "editorial": cover_editorial, "card": cover_card, "question": cover_question,
    "quote": cover_quote, "split": cover_split, "versus": cover_versus, "numeric": cover_numeric,
    # ★2026-07-27 追加（[[LAYOUTS]] §7 の「高」優先候補をようやく実装）
    "giant": cover_giant, "magazine": cover_magazine,
}


def slide_cover(spec, W, H, brand):
    return COVER_VARIANTS[spec.get("variant", "editorial")](spec, W, H, brand)


def slide_photo(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    bgp = _path(brand, spec.get("bg"))
    # dark は spec で上書き可。連投する photo に階調を付けると「時間が流れている」ことが
    # 写真そのもので伝わる（一律に暗幕を掛けると朝も夜も同じ暗さになり、変化が消える）。
    if bgp:
        canvas = B.darken(B.cover_crop(Image.open(bgp), W, H), spec.get("dark", 0.46)).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (W, H), brand.ink + (255,))
        B.soft_blob(canvas, accent, W // 2, round(H * 0.3), r=round(700 * s), alpha=90)
    canvas.alpha_composite(B.bottom_scrim(W, H, start=0.30, bot_a=222))
    cap = spec["caption"].split("\n")
    cf = H_(brand, 84 * s)
    lead = round(116 * s)
    note_lines = spec["note"].split("\n") if spec.get("note") else []
    top = _anchor(W, H, 0.80, 0.54) - len(cap) * lead - len(note_lines) * round(52 * s)
    d = ImageDraw.Draw(canvas)
    d.line([(M, top - round(36 * s)), (M + round(64 * s), top - round(36 * s))], fill=accent, width=round(7 * s))
    end = B.draw_shadowed(canvas, cap, cf, WHITE, M, top, lead, align="left", shadow_a=140, blur=10)
    if note_lines:
        B.draw_shadowed(canvas, note_lines, B.font(round(40 * s), 500), (255, 255, 255, 235), M,
                        end + round(24 * s), round(52 * s), align="left", shadow_a=110, blur=6)
    return canvas


def app_shot(spec, brand):
    shot = Image.open(_path(brand, spec["shot"]))
    fp = _path(brand, spec.get("footage"))
    return B.key_out_green(shot, B.footage_scene(fp)) if fp else shot.convert("RGB")


def slide_shot(spec, W, H, brand):
    # 実画面: 見出し特大(上)＋端末を大きく下端から見切れ。bgあり=素材ブリード白文字／無し=クリーン濃文字。
    s, M, cx = W / 1080, margin(W), W // 2
    accent = brand.accent(spec["accent"])
    tall = H / W > 1.55
    th_f, top_f = (0.84, 0.36) if tall else (0.92, 0.30)
    bgp = _path(brand, spec.get("bg"))
    if bgp:
        canvas = B.cover_crop(Image.open(bgp), W, H).convert("RGBA")
        canvas.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
        canvas.alpha_composite(B.vgrad_alpha(W, H, 150, 0))
        ink, sub_ink = WHITE, (228, 228, 228)
    else:
        canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
        B.soft_blob(canvas, accent, round(W * 0.85), round(H * 0.2), r=round(560 * s), alpha=58)
        ink, sub_ink = brand.ink, brand.sub_ink
    y = round(H * 0.075)
    title = spec.get("title") or spec.get("caption", "")
    y = B.draw_lines(ImageDraw.Draw(canvas), title.split("\n"), H_(brand, 100 * s), ink, M, y, round(120 * s), align="left")
    if spec.get("sub"):
        y += round(16 * s)
        B.draw_lines(ImageDraw.Draw(canvas), spec["sub"].split("\n"), B.font(round(44 * s), 500), sub_ink, M, y, round(58 * s), align="left")
    if bgp:
        canvas.alpha_composite(B.bottom_scrim(W, H, start=0.72, bot_a=120))
    B.paste_phone_shadow(canvas, B.phone_mockup(app_shot(spec, brand)), cx, round(H * top_f), round(H * th_f))
    if bgp:        # grain は写真背景の質感用にだけ薄く。クリーン(flat)背景には載せない
        B.grain(canvas, seed=spec["idx"], amount=7)
    return canvas


def slide_info(spec, W, H, brand):
    # 余白を大きく・項目を絞り・大きな文字。番号 or SVGアイコンで直感的に。chrome無し。
    # 余白規範([[SPACING]]): 行は均等リズムで帯に中央寄せ＝項目間に孤立余白(間延び)を作らない。
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.86), round(H * 0.12), r=round(560 * s), alpha=46)
    d = ImageDraw.Draw(canvas)
    title_lines = spec["title"].split("\n")
    title_lead = round(108 * s)
    title_h = len(title_lines) * title_lead
    bullets = spec["bullets"][:4]      # 詰め込みすぎない
    lead_b = round(62 * s)
    # 番号/アイコン列幅を実測し、本文を block(32) 段で近接配置（番号が浮く=近接の弱さを解消）
    nf0 = H_(brand, 76 * s)
    has_icon = any(isinstance(b, dict) and b.get("icon") and B.has_svg(b["icon"]) for b in bullets)
    marker_w = round(76 * s) if has_icon else d.textlength(str(len(bullets)), font=nf0)
    text_x = M + round(marker_w) + B.sp("block", W)

    def _bh(b):
        text = b.get("text", "") if isinstance(b, dict) else b
        return len(text.split("\n")) * lead_b
    row_h = max(max(_bh(b) for b in bullets), round(96 * s))   # 等高（最も高い項目＋最小行高）
    bullet_gap = B.sp("group", W)                              # 項目間は一定（間延びさせない）
    block_h = len(bullets) * row_h + (len(bullets) - 1) * bullet_gap
    # 見出し＋本文を1つの塊にし、**下UIで隠れる帯を除いた可視帯に中央寄せ**（[[SPACING]] §7）。
    # raw画像では下が空くが、実機では下UI(TikTok≈下16%)が覆う＝視聴者の見る範囲で重心が中央に来る。
    group_h = title_h + B.sp("section", W) + block_h
    tall = H / W > 1.55
    band_top = round(H * 0.12)
    band_bot = H - (round(H * 0.16) if tall else round(H * 0.10))   # 下UI/余白ぶんを除く
    top = band_top + max(0, (band_bot - band_top - group_h) / 2)
    B.draw_lines(d, title_lines, H_(brand, 86 * s), brand.ink, M, top, title_lead, align="left")
    list_top = top + title_h + B.sp("section", W)
    ys = [list_top + i * (row_h + bullet_gap) for i in range(len(bullets))]
    for i, (b, ry) in enumerate(zip(bullets, ys)):
        icon = b.get("icon") if isinstance(b, dict) else None
        text = b.get("text", "") if isinstance(b, dict) else b
        cy = ry + row_h / 2
        if icon and B.has_svg(icon):
            ih = round(76 * s)
            B.paste_svg(canvas, icon, M, round(cy - ih / 2), ih, accent)
        else:
            nf = H_(brand, 76 * s)
            d.text((M, cy - nf.size * 0.62), f"{i + 1}", font=nf, fill=accent)
        lines = text.split("\n")
        bf = B.font(round(50 * s), 600)
        B.draw_lines(d, lines, bf, brand.ink, text_x, cy - len(lines) * lead_b / 2, lead_b, align="left")
    return canvas      # フラット面: grain は載せない（文字/平面が荒れる。[[SPACING]] §11）


def _search_bar(canvas, brand, cx, y, w, h, label, accent):
    """検索バー: 白ピル＋枠＋アプリ名＋右端に塗りボタン(虫眼鏡白)。"""
    d = ImageDraw.Draw(canvas)
    bx = cx - w // 2
    B.rounded_plate(canvas, [bx, y, bx + w, y + h], h // 2, WHITE + (255,))
    d.rounded_rectangle([bx, y, bx + w, y + h], radius=h // 2, outline=brand.ink + (255,), width=max(3, round(h * 0.035)))
    # 右端 塗りボタン＋白虫眼鏡
    br = round(h * 0.40)
    bcx, bcy = bx + w - round(h * 0.52), y + h // 2
    d.ellipse([bcx - br, bcy - br, bcx + br, bcy + br], fill=brand.ink + (255,))
    if B.has_svg("magnifier"):
        m = round(br * 1.05)
        B.paste_svg(canvas, "magnifier", bcx - m // 2, bcy - m // 2, m, WHITE)
    # アプリ名(収まるサイズに)
    pad = round(h * 0.42)
    maxw = w - (h) - pad
    nf = _fit(d, label, brand.head, brand, maxw, round(h * 0.36))
    d.text((bx + pad, bcy - nf.size * 0.62), label, font=nf, fill=brand.ink)


def slide_cta(spec, W, H, brand):
    # インストール誘導(理想形): 検索バー(名前+塗り虫眼鏡)→大アイコン→「今すぐダウンロード」の3要素だけ。
    # 小さい見出し・ラベルは載せない。余白たっぷり・装飾なし（[[DESIGN_NOTES]]）。
    # 余白規範([[SPACING]]): 3要素を一定の段差(gap)で1つの島にまとめ光学中央へ。
    # 等間隔にすることで「アイコン→DLテキスト間に巨大な死に空間」「下UIへ侵入」を防ぐ。
    s, cx = W / 1080, W // 2
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, cx, round(H * 0.50), r=round(860 * s), alpha=42)
    d = ImageDraw.Draw(canvas)
    sb_w, sb_h = round(W * 0.84), round(156 * s)
    icon_h = round(424 * s)
    dtxt = spec.get("cta_foot", "今すぐダウンロード")
    df = _fit(d, dtxt, brand.head, brand, round(W * 0.88), round(104 * s))
    txt_h = round(df.size)
    gap = B.sp("hero", W) + round(16 * s)            # 3要素の等間隔（≈80px）
    total = sb_h + gap + icon_h + gap + txt_h
    y = round(H * 0.46) - total / 2                  # 光学中央（真ん中よりわずか上）
    _search_bar(canvas, brand, cx, round(y), sb_w, sb_h, brand.wordmark, accent)
    y += sb_h + gap
    if brand.icon and Path(brand.icon).exists():
        ic = B._icon_rounded(brand.icon, icon_h)
        canvas.alpha_composite(ic, (cx - ic.width // 2, round(y)))
    y += icon_h + gap
    d.text((cx - d.textlength(dtxt, font=df) / 2, round(y)), dtxt, font=df, fill=brand.ink)
    return canvas      # フラット面: grain は載せない（[[SPACING]] §11）


def slide_showcase(spec, W, H, brand):
    """D型＝成果物ショーケース。**そのアプリで作れたもの**を全面で見せるだけのスライド。

    実物（「【カメラアプリ】激おすすめ old Roll」1,647いいね/7枚）の構造は
    「説明2枚 → 作例5枚（文字ゼロ）」。説明を尽くすより、出力の魅力だけで見せる型。
    紙面・画像・動画を生成するアプリではこれが主砲になる。→ [[PATTERNS]] §1b D型

    `label` を書かなければ**文字ゼロ**（それが既定＝連続配置で作例が並ぶリズムを作る）。
    書く場合だけスクリムを敷き、上セーフ帯の内側に小さく置く。"""
    s, M = W / 1080, margin(W)
    src = _path(brand, spec.get("bg")) or _path(brand, spec.get("shot"))
    if src:
        canvas = B.cover_crop(Image.open(src), W, H).convert("RGBA")
    else:                      # 素材未指定は qa.py が NO-MATERIAL で弾く（保険の地色）
        canvas = Image.new("RGBA", (W, H), brand.ink + (255,))
    label = spec.get("label") or spec.get("caption")
    if label:
        canvas.alpha_composite(B.vgrad_alpha(W, H, 140, 0))
        B.draw_shadowed(canvas, label.split("\n"), H_(brand, 62 * s), WHITE, M,
                        round(H * 0.155), round(82 * s), align="left", shadow_a=140, blur=10)
    return canvas


def slide_feature(spec, W, H, brand):
    """C型＝1機能1スライド。角丸ラベルの機能名を**全スライド同位置**＋端末＋説明3行。

    実物（「鬼集中するとき専用アプリ」2,210いいね/10枚）の構造。ラベル位置が1pxもぶれないことが
    素人との差になっている。→ [[PATTERNS]] §1b C型

    ★セーフゾーン順守（[[LAYOUTS]] §2）: TikTok 9:16 は下810pxがUIに食われ、**使えるのは
    y=270〜1110＝フレームの44%**しかない。よって tall では端末を小さくして全要素を安全域に収める。
    Lemon8/IG 3:4 は下173pxだけなので端末を大きく取れる。ここを比率一律にすると、9:16 で
    説明文がUIの下に消える（旧セーフゾーン値のままだと気づけなかった事故）。"""
    s, M, cx = W / 1080, margin(W), W // 2
    accent = brand.accent(spec["accent"])
    tall = H / W > 1.55
    bgp = _path(brand, spec.get("bg"))
    if bgp:
        canvas = B.darken(B.cover_crop(Image.open(bgp), W, H), 0.34).convert("RGBA")
        ink, sub_ink = WHITE, (232, 232, 232)
    else:
        canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
        B.soft_blob(canvas, accent, round(W * 0.2), round(H * 0.12), r=round(560 * s), alpha=52)
        ink, sub_ink = brand.ink, brand.sub_ink
    d = ImageDraw.Draw(canvas)

    # 1) 機能名ラベル（角丸ピル）— 全スライド同じ y。ここが揃うとコレクションに見える
    lab = spec.get("label", "")
    # 3:4 の 0.085 は上セーフ(130px)の外に出る（1440×0.085=122）。0.105 で内側に収める
    lab_y = round(H * (0.150 if tall else 0.105))
    if lab:
        lf = H_(brand, 54 * s)
        tw_ = d.textlength(lab, font=lf)
        px, py = B.sp("pill_x", W), B.sp("pill_y", W)
        d.rounded_rectangle([M, lab_y, M + tw_ + px * 2, lab_y + lf.size + py * 2],
                            radius=round((lf.size + py * 2) / 2), fill=accent + (255,))
        d.text((M + px, lab_y + py), lab, font=lf, fill=WHITE)
        lab_y += lf.size + py * 2

    body = spec.get("sub") or spec.get("caption") or ""
    lines = body.split("\n") if body else []
    lead = round(58 * s)
    bf = B.font(round(42 * s), 500)

    if tall:
        # ★9:16 は ラベル → 説明 → 端末(下端から見切れ) の順にする。
        # 実物C型の「端末を中央、説明を下」を 9:16 でそのままやると、可視帯が y270–1110 の
        # 44% しかないため端末と説明文が**物理的に重なる**（旧実装の実害。端末下端1014 に対し
        # 説明が959から始まっていた）。端末を縮めて回避すると今度は実画面が読めない。
        # → 文字を可視帯の上半分にまとめ、端末は下端から見切れさせて大きさを保つ
        #   （[[DESIGN_NOTES]] 2026-06-26「実画面は下端から見切れ・死に空間ゼロ」と同じ扱い）。
        y = lab_y
        if lines:
            y += B.sp("group", W)
            B.draw_lines(d, lines, bf, sub_ink, M, y, lead, align="left")
            y += len(lines) * lead
        if spec.get("shot"):
            B.paste_phone_shadow(canvas, B.phone_mockup(app_shot(spec, brand)), cx,
                                 y + B.sp("section", W), round(H * 0.84))
    else:
        # 3:4 は下UIが 173px だけ＝実物C型どおり ラベル → 端末 → 説明
        ph_top = lab_y + B.sp("group", W)
        ph_h = round(H * 0.46)
        if spec.get("shot"):
            B.paste_phone_shadow(canvas, B.phone_mockup(app_shot(spec, brand)), cx, ph_top, ph_h)
        if lines:
            by = min(ph_top + ph_h + B.sp("group", W), round(H * 0.845) - len(lines) * lead)
            B.draw_lines(d, lines, bf, sub_ink, M, by, lead, align="left")
    if bgp:
        B.grain(canvas, seed=spec["idx"], amount=7)
    return canvas


# MARK: - 手仕事の質感まわり（scrap 用のプリミティブ）

def _print_card(img, w, pad, foot, tilt, shadow=True, ratio=None):
    """白フチのプリント風カード（下フチだけ広い＝チェキ/ポラロイドの比率）にして傾ける。

    ratio=h/w を渡すとその比でセンタークロップする（縦長素材を横位置のコマに使うときに要る）。"""
    if ratio:
        img = B.cover_crop(img, 1200, round(1200 * ratio))
    iw, ih = img.size
    h = round(w * ih / iw)
    card = Image.new("RGBA", (w + pad * 2, h + pad + foot), (255, 255, 255, 255))
    card.paste(img.convert("RGB").resize((w, h), Image.LANCZOS), (pad, pad))
    d = ImageDraw.Draw(card)
    d.rectangle([0, 0, card.width - 1, card.height - 1], outline=(226, 219, 210, 255), width=2)
    if shadow:
        pad2 = round(w * 0.12)
        lay = Image.new("RGBA", (card.width + pad2 * 2, card.height + pad2 * 2), (0, 0, 0, 0))
        sh = Image.new("RGBA", card.size, (54, 42, 33, 92))
        lay.paste(sh, (pad2 + round(w * 0.012), pad2 + round(w * 0.02)))
        lay = lay.filter(ImageFilter.GaussianBlur(round(w * 0.035)))
        lay.alpha_composite(card, (pad2, pad2))
        card = lay
    return card.rotate(tilt, resample=Image.BICUBIC, expand=True)


def _hand_ellipse(canvas, cx, cy, rx, ry, color, width, seed=0):
    """ラクガキの丸。1周より少し多く回して始点を追い越させ、半径を微妙に揺らす。"""
    rnd = random.Random(seed)
    pts, n = [], 96
    start, span = rnd.uniform(0, math.tau), math.tau * 1.07
    for i in range(n + 1):
        a = start + span * i / n
        wob = 1 + 0.038 * math.sin(a * 3 + seed) + rnd.uniform(-0.010, 0.010)
        pts.append((cx + rx * wob * math.cos(a), cy + ry * wob * math.sin(a)))
    ImageDraw.Draw(canvas).line(pts, fill=color, width=width, joint="curve")


def _marker(canvas, x, y, w, h, color, alpha=105, seed=0):
    """蛍光ペンの帯。上下の辺をわずかに傾け、端を丸めない＝手で引いた線に見せる。"""
    rnd = random.Random(seed)
    j = h * 0.10
    lay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).polygon(
        [(x, y + rnd.uniform(-j, j)), (x + w, y + rnd.uniform(-j, j)),
         (x + w, y + h + rnd.uniform(-j, j)), (x, y + h + rnd.uniform(-j, j))],
        fill=tuple(color) + (alpha,))
    canvas.alpha_composite(lay.filter(ImageFilter.GaussianBlur(2)))


def _hgrad(w, h, stops):
    """色の列を横方向に線形補間した帯（パノラマの地）。"""
    a = np.array(stops, np.float32)
    xs = np.linspace(0, len(stops) - 1, w)
    i0 = np.floor(xs).astype(int).clip(0, len(stops) - 1)
    i1 = np.minimum(i0 + 1, len(stops) - 1)
    t = (xs - i0)[:, None]
    col = a[i0] * (1 - t) + a[i1] * t
    return Image.fromarray(np.repeat(col[None, :, :], h, 0).astype(np.uint8), "RGB")


# MARK: - 中面の新しい型

def slide_grid(spec, W, H, brand):
    """カードを2列に並べる中面。比較・○選・バリエーションを1枚に収める唯一の型。

    [[LAYOUTS]] §4「カード3〜4分割グリッド」。複数要素を置ける代わりに詰め込みやすいので、
    **1セル＝ラベル1語＋本文1〜2行**に絞る（守らないと info の劣化版になる）。
    `cells`: [{"label":"…","text":"…","icon":"<SVG名>"}] を2〜4個。"""
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.12), round(H * 0.10), r=round(560 * s), alpha=44)
    d = ImageDraw.Draw(canvas)
    cells = spec["cells"][:4]
    title_lines = spec["title"].split("\n") if spec.get("title") else []
    tlead = round(104 * s)
    cols = 2 if len(cells) > 1 else 1
    rows = (len(cells) + cols - 1) // cols
    gap = B.sp("block", W)
    cw = (W - M * 2 - gap * (cols - 1)) // cols
    pad0 = B.sp("pad", W)

    def _cell_h(c):     # カード高は中身の実測から決める（固定比だと下に死に空間ができる）
        h = pad0 * 2
        if c.get("icon") and B.has_svg(c["icon"]):
            h += round(62 * s) + B.sp("hd_body", W)
        if c.get("label"):
            h += round(62 * s) + B.sp("hd_body", W)
        if c.get("text"):
            h += len(c["text"].split("\n")) * round(50 * s)
        return h
    ch = max(_cell_h(c) for c in cells)
    block_h = rows * ch + (rows - 1) * gap
    group_h = len(title_lines) * tlead + (B.sp("section", W) if title_lines else 0) + block_h
    # 格子は info より背が高くなりやすい。9:16 は**可視帯の下限(y=1110≒0.578H)**で切る
    # ——ここを info と同じ「下16%を除く」にすると、下の段がまるごとUIの下に沈む
    band_top = round(H * 0.12)
    band_bot = round(H * 0.578) if _tall(W, H) else H - round(H * 0.10)
    top = band_top + max(0, (band_bot - band_top - group_h) / 2)
    if title_lines:
        B.draw_lines(d, title_lines, H_(brand, 86 * s), brand.ink, M, top, tlead, align="left")
        top += len(title_lines) * tlead + B.sp("section", W)
    pad = B.sp("pad", W)
    for i, c in enumerate(cells):
        x = M + (i % cols) * (cw + gap)
        y = top + (i // cols) * (ch + gap)
        B.rounded_plate(canvas, [x, y, x + cw, y + ch], round(28 * s), brand.card + (255,))
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=round(28 * s),
                            outline=accent + (70,), width=2)
        cy = y + pad
        icon = c.get("icon")
        if icon and B.has_svg(icon):
            B.paste_svg(canvas, icon, x + pad, cy, round(62 * s), accent)
            cy += round(62 * s) + B.sp("hd_body", W)
        if c.get("label"):
            B.draw_lines(d, [c["label"]], H_(brand, 52 * s), brand.ink, x + pad, cy, round(62 * s), align="left")
            cy += round(62 * s) + B.sp("hd_body", W)
        if c.get("text"):
            lines = c["text"].split("\n")
            B.draw_lines(d, lines, B.font(round(38 * s), 500), brand.sub_ink, x + pad, cy,
                         round(50 * s), align="left")
    return canvas


def slide_callout(spec, W, H, brand):
    """実画面の**1点だけ**を丸で囲み、周囲を落とす。

    ハイライトは注目を集める一方で周辺への注意を抑制し、キューを重ねると効果が反転する
    （視覚キュー g=0.261 に対し複合キュー g=−0.635。40研究・N=5,049）。だからこの型は
    **`spot` を1つしか受け取らない**＝複合キューを実装として作れないようにしてある。
    → [[PATTERNS]] §3。`spot`:[x,y]（端末画面内の相対座標）, `spot_r`（画面幅比）。"""
    s, M, cx = W / 1080, margin(W), W // 2
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.86), round(H * 0.14), r=round(560 * s), alpha=50)
    d = ImageDraw.Draw(canvas)
    y = round(H * 0.075)
    tl = spec["title"].split("\n")
    tf = _fit(d, max(tl, key=len), brand.head, brand, W - M * 2, round(92 * s))   # 幅に合わせて自動縮小
    y = B.draw_lines(d, tl, tf, brand.ink, M, y, round(tf.size * 1.22), align="left")
    if spec.get("sub"):
        y += round(14 * s)
        B.draw_lines(d, spec["sub"].split("\n"), B.font(round(42 * s), 500), brand.sub_ink, M, y,
                     round(56 * s), align="left")

    phone = B.phone_mockup(app_shot(spec, brand))
    ph_h = round(H * (0.72 if _tall(W, H) else 0.62))
    ph_top = round(H * (0.30 if _tall(W, H) else 0.34))
    B.paste_phone_shadow(canvas, phone, cx, ph_top, ph_h)
    pw = round(phone.width * ph_h / phone.height)

    fx, fy = spec.get("spot", [0.5, 0.62])
    r = round(pw * spec.get("spot_r", 0.30))
    sx, sy = cx - pw / 2 + pw * fx, ph_top + ph_h * fy
    # 円の外だけを落とす（マスクのふちはぼかして"スポットライト"に）
    veil = Image.new("RGBA", (W, H), (26, 20, 15, 128))
    hole = Image.new("L", (W, H), 255)
    ImageDraw.Draw(hole).ellipse([sx - r, sy - r, sx + r, sy + r], fill=0)
    veil.putalpha(ImageChops.multiply(veil.getchannel("A"),
                                      hole.filter(ImageFilter.GaussianBlur(round(26 * s)))))
    canvas.alpha_composite(veil)
    _hand_ellipse(canvas, sx, sy, r * 1.02, r * 1.02, accent + (255,), round(9 * s),
                  seed=spec["idx"])
    if spec.get("spot_label"):
        lf = H_(brand, 44 * s)
        tw = d.textlength(spec["spot_label"], font=lf)
        px, py = B.sp("pill_x", W), B.sp("pill_y", W)
        lx = min(max(M, sx - (tw + px * 2) / 2), W - M - tw - px * 2)
        ly = sy + r + round(24 * s)
        d.rounded_rectangle([lx, ly, lx + tw + px * 2, ly + lf.size + py * 2],
                            radius=round((lf.size + py * 2) / 2), fill=accent + (255,))
        d.text((lx + px, ly + py), spec["spot_label"], font=lf, fill=WHITE)
    return canvas


def slide_scrap(spec, W, H, brand):
    """スクラップブック。白フチのプリントを傾けて重ね、手描きの丸か蛍光帯を**1つだけ**足す。

    2026 のグラフィックトレンド調査が揃って「手書き・ステッカー・切り貼り＝AI生成の均質さへの
    反動」を指しており、[[PATTERNS]] §1b D型の実測（iOSマークアップ風のラクガキが効く／
    作り込むと逆に弱くなりうる）と独立に一致した。**エディトリアル路線とは混ぜない**
    ——どちらかに振り切る型。`prints`:[{"src","at":[x,y],"w","rot"}]、`memo`、`mark`(circle|band)。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.18), round(H * 0.80), r=round(680 * s), alpha=30)
    d = ImageDraw.Draw(canvas)
    band_bot = round(H * (0.560 if _tall(W, H) else 0.88))

    if spec.get("title"):
        lines = spec["title"].split("\n")
        tf = _fit(d, max(lines, key=len), brand.head, brand, W - M * 2 - round(24 * s), round(80 * s))
        lead = round(tf.size * 1.26)
        y = round(H * 0.085)
        if spec.get("mark") == "band":
            # 蛍光帯は**最終行だけ**（強調は1点）。文字より先に敷く＝ペンの上から書いた見え方にしない
            ln = lines[-1]
            _marker(canvas, M - round(10 * s), y + (len(lines) - 1) * lead + round(tf.size * 0.42),
                    d.textlength(ln, font=tf) + round(26 * s), round(tf.size * 0.66),
                    accent, alpha=120, seed=spec["idx"])
        B.draw_lines(d, lines, tf, brand.ink, M, y, lead, align="left")

    prints = spec.get("prints", [])[:3]
    for i, p in enumerate(prints):
        src = _path(brand, p.get("src"))
        if not src:
            continue
        w = round(W * p.get("w", 0.52))
        # ratio 既定 0.78（横位置のプリント）。縦長素材をそのまま貼ると可視帯を突き抜ける
        card = _print_card(Image.open(src), w, round(w * 0.055), round(w * 0.16), p.get("rot", -3),
                           ratio=p.get("ratio", 0.78))
        ax, ay = p.get("at", [0.5, 0.55])
        canvas.alpha_composite(card, (round(W * ax - card.width / 2), round(H * ay - card.height / 2)))
        if p.get("memo"):
            # プリントの白い下フチ（手書きのキャプションを書く場所）に載せる
            mf = H_(brand, 36 * s)
            mx = round(W * ax - card.width / 2) + round(card.width * 0.14)
            my = round(H * ay - card.height / 2) + card.height - round(w * 0.175)
            d.text((mx, my), p["memo"], font=mf, fill=(122, 112, 103))

    if spec.get("mark") == "circle" and prints:
        p = prints[0]
        ax, ay = p.get("at", [0.5, 0.55])
        pw = W * p.get("w", 0.52)
        _hand_ellipse(canvas, W * ax, H * ay - pw * 0.06, pw * 0.56, pw * 0.62,
                      accent + (255,), round(9 * s), seed=spec["idx"])

    if spec.get("memo"):
        lines = spec["memo"].split("\n")
        lead = round(60 * s)
        B.draw_lines(d, lines, B.font(round(46 * s), 600), brand.ink, M,
                     band_bot - len(lines) * lead, lead, align="left")
    B.grain(canvas, seed=spec["idx"], amount=6)      # 紙の粒子。写真ではなく地に薄く
    return canvas


def slide_panorama(spec, W, H, brand):
    """連続キャンバス（パノラマ）。N枚を貫く1枚の絵を作り、自分の担当区間だけを切り出す。

    **横スワイプでしか成立しない表現**で、絵が次のスライドへ続くこと自体がスワイプの動機になる。
    Instagram の分割投稿として日本でも定着した手法（横長1枚を N 分割）。ここでは hioto の
    アクセント（morning→midnight）を横一直線のグラデにし、その上に時刻のコマを置く
    ＝**ブランドのトークンがそのまま時間の経過になる**。
    `pano`:[i,n]（1始まり）、`stops`:[accent名…]、`frames`:[{"src","at","w","rot"}]（at は全体幅比）。
    ⚠️ 全スライドで `stops`/`frames` を同じ内容にすること（1枚の絵を切り出すため）。"""
    s, M = W / 1080, margin(W)
    i, n = spec["pano"]
    accent = brand.accent(spec["accent"])
    stops = [brand.accent(k) for k in spec.get("stops", ["morning", "evening", "midnight"])]
    full_w = W * n
    canvas = _hgrad(full_w, H, stops).convert("RGBA")
    canvas.alpha_composite(B.vgrad_alpha(full_w, H, 40, 150))       # 上明るく下を締める
    fd = ImageDraw.Draw(canvas)
    rail_y = round(H * spec.get("rail_y", 0.475))
    if spec.get("rail"):
        # 全幅を貫く1本の軸。**これが境界をまたいで連続する**＝次のスライドがあることを絵で示す。
        fd.line([(0, rail_y), (full_w, rail_y)], fill=(255, 255, 255, 140), width=max(3, round(4 * s)))
        step = full_w / (n * 6)
        for k in range(n * 6 + 1):
            x = round(k * step)
            long = (k % 6 == 0)
            t = round((14 if long else 7) * s)
            fd.line([(x, rail_y - t), (x, rail_y + t)],
                    fill=(255, 255, 255, 170 if long else 90), width=2)
    for f in spec.get("frames", []):
        src = _path(brand, f.get("src"))
        if not src:
            continue
        w = round(W * f.get("w", 0.30))
        card = _print_card(Image.open(src), w, round(w * 0.05), round(w * 0.05), f.get("rot", 0),
                           ratio=f.get("ratio"))
        cxf = full_w * f.get("at", 0.5)
        # rail があればカード下端を軸に載せる（写真が時間の上に立っているように見せる）
        cyf = (rail_y - card.height - round(12 * s)) if spec.get("rail") \
            else (H * f.get("y", 0.42) - card.height / 2)
        canvas.alpha_composite(card, (round(cxf - card.width / 2), round(cyf)))
        if f.get("at_label"):
            lf = B.mono_font(round(30 * s), "medium")
            B.draw_tracked(fd, f["at_label"], lf, (255, 255, 255, 235),
                           round(cxf), rail_y + round(34 * s), 4, anchor="c")
    canvas = canvas.crop(((i - 1) * W, 0, i * W, H))
    canvas.alpha_composite(B.bottom_scrim(W, H, start=0.42, bot_a=150))
    d = ImageDraw.Draw(canvas)
    if spec.get("caption"):
        lines = spec["caption"].split("\n")
        lead = round(96 * s)
        # rail があるときは軸の下に置く（軸の上だと線が文字を横切る）
        top = (rail_y + round(112 * s)) if spec.get("rail") \
            else _anchor(W, H, 0.80, 0.545) - len(lines) * lead
        B.draw_shadowed(canvas, lines, H_(brand, 74 * s), WHITE, M, top, lead, align="left",
                        shadow_a=150, blur=10)
    if spec.get("clock"):
        B.draw_tracked(d, spec["clock"], B.mono_font(round(34 * s), "medium"), (255, 255, 255, 225),
                       M, round(H * (0.155 if _tall(W, H) else 0.11)), 6)
    return canvas


# MARK: - 写真×文字（暗幕を使わない解法）★2026-07-27
#
# 「黒いオーバーレイに白文字」は写真の上に文字を置く最も簡単な解だが、**それしか使わないと
# 何案作っても同じ見え方になる**（実際に指摘を受けた）。[[LAYOUTS]] §6 が本来言っているのは
#   ① 重ねないのが基本（写真の余白側に置く）
#   ② 重ねる時の手は5つ（下スクリム／半透明帯／縁取り／不透明塗り30–50%／背景ぼかし）
# で、②の1番目だけを常用していたことになる。以下は ① と ②の残りを型にしたもの。

def _duotone(img, dark_rgb, light_rgb):
    """写真を2色の間に写し込む（暗部→dark / 明部→light）。黒幕とは別の統一のかけ方。"""
    g = np.asarray(img.convert("L"), np.float32)[..., None] / 255.0
    a, b = np.array(dark_rgb, np.float32), np.array(light_rgb, np.float32)
    return Image.fromarray((a * (1 - g) + b * g).astype(np.uint8), "RGB")


def _text_mask_photo(canvas, img, lines, f, x, y, lead, dark=0.26):
    """文字の形に写真を抜く（cutout）。地は紙のまま＝暗幕の逆で、明るいまま強い。

    抜いた文字は**紙地とのコントラストだけ**で読ませるので、明るい写真をそのまま使うと消える。
    darken を一段かけて字面を確保する（写真そのものは全面に出ないので暗さが目立たない）。"""
    mask = Image.new("L", canvas.size, 0)
    B.draw_lines(ImageDraw.Draw(mask), lines, f, 255, x, y, lead, align="left")
    photo = B.darken(B.cover_crop(img, canvas.width, canvas.height), dark).convert("RGBA")
    photo.putalpha(mask)
    canvas.alpha_composite(photo)


LAYOUT_MODES = ("margin", "band", "frame", "light", "duotone", "cutout", "stripe", "edge")


def slide_layout(spec, W, H, brand):
    """写真と文字の関係を `mode` で切り替える汎用スライド。**暗幕（黒＋白文字）を使わない**ための型。

    mode:
      `margin`  上に写真 / 下は紙地に濃文字（重ねない・最も汎用）
      `band`    写真全面＋中央に**紙の帯**（黒幕ではなく白い面を敷く）
      `frame`   額装。写真を小さく置き、周囲の紙地に文字
      `light`   **白**幕（明るいオーバーレイ）＋濃文字
      `duotone` ブランド色で写真を染める＋白文字（黒ではない統一）
      `cutout`  特大文字の形に写真を抜く。地は紙
      `stripe`  写真を横帯に切り、間の紙地に文字
      `edge`    幕なし。写真の余白側（空・床）へ直接置く ※明るい面のある写真を選ぶこと
    フィールド: `bg` `title` `sub` `kicker` `hl` `big`(true で見出しを表紙サイズ) `at`(edge の上下)。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    tall = _tall(W, H)
    mode = spec.get("mode", "margin")
    bgp = _path(brand, spec.get("bg"))
    img = Image.open(bgp) if bgp else None
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    ink, sub_ink = brand.ink, brand.sub_ink
    lines = spec["title"].split("\n") if spec.get("title") else []
    hs = (104 if spec.get("big") else 78) * s
    tx, ty = M, round(H * 0.30)
    ky = None                                    # kicker を別位置に置く mode 用（cutout）

    if img is None:
        B.soft_blob(canvas, accent, W // 2, round(H * 0.3), r=round(700 * s), alpha=80)

    elif mode == "margin":
        ph = round(H * (0.38 if tall else 0.56))
        canvas.alpha_composite(B.cover_crop(img, W, ph).convert("RGBA"), (0, 0))
        ty = ph + B.sp("section", W)

    elif mode == "band":
        canvas = B.cover_crop(img, W, H).convert("RGBA")
        bh = round(hs * 1.34) * max(len(lines), 1) + B.sp("pad", W) * 2 + \
            (round(58 * s) * len(spec["sub"].split("\n")) if spec.get("sub") else 0)
        by = round(H * (0.28 if tall else 0.40))
        B.rounded_plate(canvas, [0, by, W, by + bh], 0, brand.bg + (252,))
        ty = by + B.sp("pad", W)

    elif mode == "frame":
        fw, fh = round(W * 0.76), round(H * (0.30 if tall else 0.46))
        fx, fy = (W - fw) // 2, round(H * (0.145 if tall else 0.10))
        sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh_).rectangle([fx + 8, fy + 18, fx + fw + 8, fy + fh + 18], fill=(60, 46, 36, 60))
        canvas.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(round(26 * s))))
        canvas.alpha_composite(B.cover_crop(img, fw, fh).convert("RGBA"), (fx, fy))
        ty = fy + fh + B.sp("section", W)

    elif mode == "light":
        canvas = B.cover_crop(img, W, H).convert("RGBA")
        canvas.alpha_composite(Image.new("RGBA", (W, H), brand.bg + (166,)))
        ty = round(H * (0.27 if tall else 0.20))

    elif mode == "duotone":
        # 明部は accent をそのまま使わず白寄りに振る。濃いアクセント(night など)だと
        # 明部まで沈んで写真の階調が消えるため
        hi = tuple(round(c * 0.42 + 255 * 0.58) for c in accent)
        canvas = _duotone(B.cover_crop(img, W, H), brand.ink, hi).convert("RGBA")
        ink, sub_ink = WHITE, (245, 240, 236)
        ty = _anchor(W, H, 0.78, 0.48) - len(lines) * round(hs * 1.3)

    elif mode == "cutout":
        cf = H_(brand, (150 if spec.get("big") else 116) * s)
        lead = round(cf.size * 1.14)
        ty0 = round(H * (0.20 if tall else 0.16)) + (round(64 * s) if spec.get("kicker") else 0)
        ky = ty0 - round(64 * s)                 # 抜き文字の上に置く（下に回ると順序が崩れる）
        _text_mask_photo(canvas, img, lines, cf, M, ty0, lead, dark=spec.get("dark", 0.26))
        ty = ty0 + len(lines) * lead + B.sp("group", W)
        lines = []                               # 見出しは写真で描いたので、以降は本文だけ

    elif mode == "stripe":
        n, gap = 3, B.sp("group", W)
        top = round(H * (0.135 if tall else 0.10))
        sh_ = round((H * (0.40 if tall else 0.58) - gap * (n - 1)) / n)
        full = B.cover_crop(img, W, sh_ * n + gap * (n - 1))
        for i in range(n):
            y0 = i * (sh_ + gap)
            canvas.alpha_composite(full.crop((0, y0, W, y0 + sh_)).convert("RGBA"), (0, top + y0))
        ty = top + n * sh_ + (n - 1) * gap + B.sp("section", W)

    else:                                        # edge — 幕なし。写真の余白側へ直接置く
        canvas = B.cover_crop(img, W, H).convert("RGBA")
        ty = (round(H * 0.155) if spec.get("at", "top") == "top"
              else _anchor(W, H, 0.80, 0.48) - len(lines) * round(hs * 1.3))
        if spec.get("on_dark"):
            ink, sub_ink = WHITE, (240, 236, 232)

    d = ImageDraw.Draw(canvas)
    shadow = mode in ("duotone", "edge")         # 写真に直接載る場合だけ影を足す
    if spec.get("kicker"):
        B.tick_label(canvas, spec["kicker"], tx, ty if ky is None else ky, ink, accent, size=round(30 * s))
        if ky is None:
            ty += round(64 * s)
    if lines:
        hf = _fit(d, max(lines, key=len), brand.head, brand, W - M * 2, round(hs))
        lead = round(hf.size * 1.3)
        top0 = ty
        ty = (B.draw_shadowed(canvas, lines, hf, ink, tx, ty, lead, align="left", shadow_a=130, blur=9)
              if shadow else B.draw_lines(d, lines, hf, ink, tx, ty, lead, align="left"))
        _hl(canvas, lines, hf, accent, tx, top0, lead, spec.get("hl"))
    if spec.get("sub"):
        ty += B.sp("hd_body", W)
        sl, sf = spec["sub"].split("\n"), B.font(round(42 * s), 500)
        if shadow:
            B.draw_shadowed(canvas, sl, sf, sub_ink, tx, ty, round(58 * s), align="left", shadow_a=110, blur=6)
        else:
            B.draw_lines(d, sl, sf, sub_ink, tx, ty, round(58 * s), align="left")
    if img is not None and mode in ("band", "duotone", "edge", "light"):
        B.grain(canvas, seed=spec["idx"], amount=6)
    return canvas


# MARK: - アプリ紹介の定番型（2026-07-27 調査：〇選 / ランキング / 比較 / ステップ / 実数 / まとめ）

def _band_top_bot(W, H):
    """9:16 は可視帯 y270–1110、3:4 は下UIが軽いので広く取る。中面の共通レンジ。"""
    return round(H * 0.12), (round(H * 0.578) if _tall(W, H) else H - round(H * 0.10))


def slide_rank(spec, W, H, brand):
    """巨大順位 ＋ 対象 ＋ 実画面。**1位を最後に置く**ためのランキング用スライド。

    実物B型（「有能アプリランキング」3,974いいね）は巨大順位数字・名前・罫線・定型行を
    10枚すべてで同位置に反復していた。**様式が信頼を作る**型なので、位置は絶対に動かさない。
    単一アプリでは「アプリの順位」ではなく**機能／理由の順位**に読み替えて使う。
    `rank`(順位) `label`(見出し) `sub` `shot`/`bg`。"""
    s, M, cx = W / 1080, margin(W), W // 2
    accent = brand.accent(spec["accent"])
    bgp = _path(brand, spec.get("bg"))
    if bgp:
        canvas = B.darken(B.cover_crop(Image.open(bgp), W, H), spec.get("dark", 0.5)).convert("RGBA")
        ink, sub_ink = WHITE, (230, 230, 230)
    else:
        canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
        B.soft_blob(canvas, accent, round(W * 0.86), round(H * 0.12), r=round(520 * s), alpha=48)
        ink, sub_ink = brand.ink, brand.sub_ink
    d = ImageDraw.Draw(canvas)
    y = round(H * 0.115)
    nf = H_(brand, 132 * s)                      # 巨大順位（全スライド同じ位置・同じ大きさ）
    num = str(spec.get("rank", ""))
    d.text((M, y), num, font=nf, fill=accent + (255,))
    lx = M + d.textlength(num, font=nf) + B.sp("block", W)
    lf = _fit(d, spec.get("label", ""), brand.head, brand, W - lx - M, round(76 * s))
    d.text((lx, y + round(nf.size * 0.30)), spec.get("label", ""), font=lf, fill=ink)
    ry = y + round(nf.size * 1.02)
    d.line([(M, ry), (W - M, ry)], fill=accent + (200,), width=round(5 * s))
    if spec.get("sub"):
        B.draw_lines(d, spec["sub"].split("\n"), B.font(round(42 * s), 500), sub_ink, M,
                     ry + B.sp("block", W), round(56 * s), align="left")
    if spec.get("shot"):
        ph_top = round(H * (0.34 if _tall(W, H) else 0.38))
        B.paste_phone_shadow(canvas, B.phone_mockup(app_shot(spec, brand)), cx, ph_top,
                             round(H * (0.84 if _tall(W, H) else 0.72)))
    if bgp:
        B.grain(canvas, seed=spec["idx"], amount=7)
    return canvas


def slide_table(spec, W, H, brand):
    """2列の比較表。「〇〇 vs 〇〇」「NG vs OK」＝運用テンプレの3系統のひとつ。

    ⚠️ **他社製品との比較には使わない**（景表法。合理的根拠と調査条件の併記が要る）。
    比較するのは**行為・状態**（書く日記／撮る日記、before／after）に限る。→ [[PATTERNS]] §5。
    `title` `cols`[2] `rows`[{label,a,b}] `mark_col`(0|1 強調する側)。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.14), round(H * 0.10), r=round(520 * s), alpha=42)
    d = ImageDraw.Draw(canvas)
    cols, rows = spec["cols"][:2], spec["rows"][:5]
    title_lines = spec["title"].split("\n") if spec.get("title") else []
    tlead = round(104 * s)
    lab_w = round((W - M * 2) * 0.34)
    col_w = (W - M * 2 - lab_w) // 2
    row_h = round(112 * s)
    head_h = round(96 * s)
    group_h = len(title_lines) * tlead + (B.sp("section", W) if title_lines else 0) + head_h + len(rows) * row_h
    band_top, band_bot = _band_top_bot(W, H)
    top = band_top + max(0, (band_bot - band_top - group_h) / 2)
    if title_lines:
        B.draw_lines(d, title_lines, H_(brand, 84 * s), brand.ink, M, top, tlead, align="left")
        top += len(title_lines) * tlead + B.sp("section", W)
    mark = spec.get("mark_col", 1)
    # 強調する側の列だけ地を敷く（強調は1点）
    B.rounded_plate(canvas, [M + lab_w + mark * col_w, top,
                             M + lab_w + (mark + 1) * col_w, top + head_h + len(rows) * row_h],
                    round(24 * s), accent + (30,))
    hf = H_(brand, 46 * s)
    for i, c in enumerate(cols):
        cxx = M + lab_w + i * col_w + col_w / 2
        col = accent + (255,) if i == mark else brand.sub_ink + (255,)
        B.draw_lines(d, [c], hf, col, cxx, top + round(24 * s), round(56 * s), align="center")
    d.line([(M, top + head_h), (W - M, top + head_h)], fill=brand.ink + (60,), width=2)
    for r, row in enumerate(rows):
        ry = top + head_h + r * row_h
        B.draw_lines(d, [row["label"]], B.font(round(38 * s), 600), brand.sub_ink, M,
                     ry + round(row_h * 0.30), round(46 * s), align="left")
        for i, key in enumerate(("a", "b")):
            cxx = M + lab_w + i * col_w + col_w / 2
            val = str(row.get(key, ""))
            vf = _fit(d, val, brand.head, brand, col_w - round(24 * s), round(52 * s))
            col = brand.ink if i == mark else brand.sub_ink
            B.draw_lines(d, [val], vf, col, cxx, ry + round(row_h * 0.26), round(58 * s), align="center")
        if r < len(rows) - 1:
            B.hairline(canvas, M, ry + row_h, W - M, color=brand.ink, alpha=30, width=2)
    return canvas


def slide_bleed(spec, W, H, brand):
    """実画面を**端末枠なしで全面ブリード**し、白の角丸カードを浮かせる（A型）。

    実物（「激推し神アプリ」6,899いいね・9枚）の中面。端末モックを外すぶん画面が大きく写り、
    白カードが「あとから貼った付箋」に見えて可読性も上がる。番号・見出し・カード位置を
    **全スライドで固定**するのがこの型の肝。→ [[PATTERNS]] §1b A型。
    `num` `title` `shot`(+`footage`) `card`(白カードの本文) `card_label`。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    shot = app_shot(spec, brand)
    canvas = B.cover_crop(shot, W, H).convert("RGBA")
    # 上だけ締める。実画面は白基調のことが多く、190 では白文字が沈むので強めに取る
    canvas.alpha_composite(B.vgrad_alpha(W, H, 232, 0))
    d = ImageDraw.Draw(canvas)
    y = round(H * 0.115)
    if spec.get("num"):
        nf = B.mono_font(round(40 * s), "medium")
        r = round(38 * s)
        d.ellipse([M, y + round(6 * s), M + r * 2, y + r * 2 + round(6 * s)], fill=accent + (255,))
        B.draw_tracked(d, str(spec["num"]), nf, WHITE, M + r, y + round(20 * s), 0, anchor="c")
        tx = M + r * 2 + B.sp("block", W)
    else:
        tx = M
    if spec.get("title"):
        tf = _fit(d, spec["title"], brand.head, brand, W - tx - M, round(70 * s))
        B.draw_shadowed(canvas, [spec["title"]], tf, WHITE, tx, y, round(tf.size * 1.2),
                        align="left", shadow_a=150, blur=10)
    # 白カード（見出し＋本文）を可視帯の下寄りに浮かせる
    if spec.get("card"):
        lines = spec["card"].split("\n")
        lab = spec.get("card_label")
        pad = B.sp("pad", W)
        lead = round(52 * s)
        h = pad * 2 + len(lines) * lead + (round(62 * s) if lab else 0)
        cy = (round(H * 0.578) if _tall(W, H) else round(H * 0.86)) - h
        B.rounded_plate(canvas, [M, cy, W - M, cy + h], round(28 * s), (255, 255, 255, 246))
        ty = cy + pad
        if lab:
            B.draw_lines(d, [lab], H_(brand, 50 * s), brand.ink, M + pad, ty, round(62 * s), align="left")
            ty += round(62 * s)
        B.draw_lines(d, lines, B.font(round(40 * s), 500), (96, 88, 80), M + pad, ty, lead, align="left")
    B.grain(canvas, seed=spec["idx"], amount=6)
    return canvas


def slide_spec(spec, W, H, brand):
    """アイコン主役 ＋ 定型スペック行（B型）。**中身より「揃っていること」が効く**型。

    実物（ランキング10枚）は投稿独自の定型フィールド（使用頻度｜毎日 ／ 暗記度｜★★★★★）を
    全スライドで反復していた。単一アプリでは**機能ごとのスペック**に読み替える。
    `num` `name` `icon`(SVG名) `specs`[{k,v}] `caption`。アイコンを省くとアプリアイコンを使う。"""
    s, M, cx = W / 1080, margin(W), W // 2
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, cx, round(H * 0.30), r=round(620 * s), alpha=40)
    d = ImageDraw.Draw(canvas)
    nf = _fit(d, spec.get("name", ""), brand.head, brand, W - M * 2 - round(140 * s), round(78 * s))
    ih = round(H * (0.16 if _tall(W, H) else 0.20))
    n_specs = len(spec.get("specs", [])[:4])
    cap_lines = len(spec["caption"].split("\n")) if spec.get("caption") else 0
    group_h = (round(nf.size * 1.5) + ih + B.sp("group", W) + n_specs * round(64 * s)
               + (B.sp("block", W) + cap_lines * round(54 * s) if cap_lines else 0))
    band_top, band_bot = _band_top_bot(W, H)
    y = band_top + max(0, (band_bot - band_top - group_h) / 2)   # 可視帯へ中央寄せ
    if spec.get("num"):
        B.draw_tracked(d, str(spec["num"]), B.mono_font(round(38 * s), "medium"), accent + (255,),
                       M, y + round(nf.size * 0.26), 6)
    d.text((M + round(104 * s), y), spec.get("name", ""), font=nf, fill=brand.ink)
    y += round(nf.size * 1.5)

    icon = spec.get("icon")
    if icon and B.has_svg(icon):
        B.paste_svg(canvas, icon, cx - ih // 2, y, ih, accent)
    elif brand.icon and Path(brand.icon).exists():
        ic = B._icon_rounded(brand.icon, ih)
        canvas.alpha_composite(ic, (cx - ic.width // 2, y))
    y += ih + B.sp("group", W)

    kf, vf = B.font(round(36 * s), 500), H_(brand, 44 * s)
    for row in spec.get("specs", [])[:4]:
        d.text((M, y), row["k"], font=kf, fill=brand.sub_ink)
        d.text((M + round((W - M * 2) * 0.42), y - round(6 * s)), str(row["v"]), font=vf, fill=brand.ink)
        y += round(64 * s)
        B.hairline(canvas, M, y - round(14 * s), W - M, color=brand.ink, alpha=26, width=2)
    if spec.get("caption"):
        y += B.sp("block", W)
        B.draw_lines(d, spec["caption"].split("\n"), B.font(round(40 * s), 600), brand.ink, M, y,
                     round(54 * s), align="left")
    return canvas


def slide_steps(spec, W, H, brand):
    """縦のステップ図（番号バッジを線で連結）。運用テンプレ3系統の「ステップ型」。

    手順そのものが少ないことを見せる型なので、**3〜4手に必ず収める**。
    `title` `steps`[{label,text}]。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.88), round(H * 0.12), r=round(520 * s), alpha=44)
    d = ImageDraw.Draw(canvas)
    steps = spec["steps"][:4]
    title_lines = spec["title"].split("\n") if spec.get("title") else []
    tlead = round(104 * s)
    r = round(42 * s)
    step_h = round(178 * s)
    group_h = len(title_lines) * tlead + (B.sp("section", W) if title_lines else 0) + len(steps) * step_h
    band_top, band_bot = _band_top_bot(W, H)
    top = band_top + max(0, (band_bot - band_top - group_h) / 2)
    if title_lines:
        B.draw_lines(d, title_lines, H_(brand, 84 * s), brand.ink, M, top, tlead, align="left")
        top += len(title_lines) * tlead + B.sp("section", W)
    cxn = M + r
    for i, st in enumerate(steps):
        cy = top + i * step_h + r
        if i < len(steps) - 1:                       # 次の番号へ伸びる縦線
            d.line([(cxn, cy + r), (cxn, cy + step_h - r)], fill=accent + (110,), width=round(4 * s))
        d.ellipse([cxn - r, cy - r, cxn + r, cy + r], fill=accent + (255,))
        B.draw_tracked(d, str(i + 1), B.mono_font(round(38 * s), "medium"), WHITE, cxn, cy - round(20 * s), 0, anchor="c")
        tx = cxn + r + B.sp("block", W)
        B.draw_lines(d, [st["label"]], H_(brand, 62 * s), brand.ink, tx, cy - round(52 * s), round(72 * s), align="left")
        if st.get("text"):
            B.draw_lines(d, st["text"].split("\n"), B.font(round(42 * s), 500), brand.sub_ink, tx,
                         cy + round(22 * s), round(54 * s), align="left")
    return canvas


def slide_stats(spec, W, H, brand):
    """実数を2〜3個並べる（proof）。「一般的な主張より、実数のほうがスクロールを止めにくい」。

    ⚠️ 出せるのは**アプリの仕様から言い切れる数**だけ（実績・DL数・No.1 は §5 の対象）。
    `title` `stats`[{n,unit,label}] `note`。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.16), round(H * 0.12), r=round(560 * s), alpha=44)
    d = ImageDraw.Draw(canvas)
    stats = spec["stats"][:3]
    title_lines = spec["title"].split("\n") if spec.get("title") else []
    tlead = round(104 * s)
    row_h = round(206 * s)
    group_h = len(title_lines) * tlead + (B.sp("section", W) if title_lines else 0) + len(stats) * row_h
    band_top, band_bot = _band_top_bot(W, H)
    top = band_top + max(0, (band_bot - band_top - group_h) / 2)
    if title_lines:
        B.draw_lines(d, title_lines, H_(brand, 84 * s), brand.ink, M, top, tlead, align="left")
        top += len(title_lines) * tlead + B.sp("section", W)
    nf, uf, lf = H_(brand, 132 * s), H_(brand, 46 * s), B.font(round(40 * s), 500)
    for i, st in enumerate(stats):
        y = top + i * row_h
        num = str(st["n"])
        d.text((M, y), num, font=nf, fill=brand.ink)
        x = M + d.textlength(num, font=nf) + round(12 * s)
        if st.get("unit"):
            d.text((x, y + round(nf.size * 0.56)), st["unit"], font=uf, fill=accent + (255,))
        d.text((M, y + round(nf.size * 1.06)), st["label"], font=lf, fill=brand.sub_ink)
        if i < len(stats) - 1:
            B.hairline(canvas, M, y + row_h - round(30 * s), W - M, color=brand.ink, alpha=26, width=2)
    if spec.get("note"):
        B.draw_lines(d, [spec["note"]], B.font(round(32 * s), 500), brand.sub_ink, M,
                     band_bot - round(48 * s), round(42 * s), align="left")
    return canvas


def slide_recap(spec, W, H, brand):
    """まとめ（番号リストで全再掲）。**最終スライドの前に置く**のが実物デッキの定石。

    保存を promote するのではなく、**保存に値する中身をここで一望させる**。項目は短句のみ。
    `title` `items`[]（5〜7個）。"""
    s, M = W / 1080, margin(W)
    accent = brand.accent(spec["accent"])
    canvas = Image.new("RGBA", (W, H), brand.bg + (255,))
    B.soft_blob(canvas, accent, round(W * 0.9), round(H * 0.9), r=round(600 * s), alpha=36)
    d = ImageDraw.Draw(canvas)
    items = spec["items"][:7]
    title_lines = spec["title"].split("\n") if spec.get("title") else []
    tlead = round(104 * s)
    row_h = round(86 * s)
    group_h = len(title_lines) * tlead + (B.sp("section", W) if title_lines else 0) + len(items) * row_h
    band_top, band_bot = _band_top_bot(W, H)
    top = band_top + max(0, (band_bot - band_top - group_h) / 2)
    if title_lines:
        B.draw_lines(d, title_lines, H_(brand, 84 * s), brand.ink, M, top, tlead, align="left")
        top += len(title_lines) * tlead + B.sp("section", W)
    nf, tf = B.mono_font(round(34 * s), "medium"), H_(brand, 50 * s)
    for i, it in enumerate(items):
        y = top + i * row_h
        B.draw_tracked(d, f"{i + 1:02d}", nf, accent + (255,), M, y + round(12 * s), 3)
        d.text((M + round(92 * s), y), it, font=tf, fill=brand.ink)
    return canvas


RENDERERS = {
    "cover": slide_cover, "photo": slide_photo, "shot": slide_shot,
    "info": slide_info, "cta": slide_cta,
    # ★2026-07-25 実物デッキの分解から追加。単一アプリを売るときの本命2種 → [[PATTERNS]] §1b
    "showcase": slide_showcase, "feature": slide_feature,
    # ★2026-07-27 追加。カルーセル固有の表現(panorama)・手仕事の質感(scrap)・
    #   1点強調(callout)・多要素の格子(grid) → [[LAYOUTS]] §4,§7 / [[PATTERNS]] §6
    "grid": slide_grid, "callout": slide_callout, "scrap": slide_scrap, "panorama": slide_panorama,
    # ★2026-07-27 追加(2)。アプリ紹介の定番型（〇選/ランキング/比較/ステップ/実数/まとめ）
    "rank": slide_rank, "table": slide_table, "bleed": slide_bleed, "spec": slide_spec,
    "steps": slide_steps, "stats": slide_stats, "recap": slide_recap,
    # ★2026-07-27 追加(3)。**暗幕＋白文字からの脱却**。mode で8通りの写真×文字を切り替える
    "layout": slide_layout,
}
