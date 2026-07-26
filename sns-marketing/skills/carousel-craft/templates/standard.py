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
from pathlib import Path

from PIL import Image, ImageDraw

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))
import brand as B  # noqa: E402

WHITE = (255, 255, 255)
SOFT_W = (255, 255, 255, 235)


def _repo_root():
    """リポジトリルート（target/ と CLAUDE.md を持つ階層）。spec の bg は repo 相対(material/...)で書けるようにする。"""
    for d in Path(__file__).resolve().parents:
        if (d / "target").is_dir() and (d / "CLAUDE.md").exists():
            return d
    return Path(__file__).resolve().parents[-1]


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
        for cand in (mat / val, mat / "screenshots" / val, mat / "footage" / val):
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


def _swipe_bottom(canvas, M, H, s):
    _swipe(canvas, M, H - round(116 * s), s)


def _cover_base(spec, W, H, brand, dark=0.42, scrim_start=0.30, scrim_bot=215):
    s = W / 1080
    bgp = _path(brand, spec.get("bg"))
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
    top = round(H * 0.82) - len(head) * lead
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
    panel_h = len(head) * lead + pad * 2 + (round(56 * s) if spec.get("kicker") else 0)
    py = round(H * 0.64)
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
    top = round(H * 0.76) - len(q) * lead - (round(108 * s) if ans else 0)
    d = ImageDraw.Draw(canvas)
    B.draw_tracked(d, "Q.", B.mono_font(round(70 * s), "light"), accent + (255,), M, top - round(96 * s), 2)
    end = B.draw_shadowed(canvas, q, qf, WHITE, M, top, lead, align="left", shadow_a=140, blur=9)
    if ans:
        ay = end + round(40 * s)
        ax = B.draw_tracked(d, "A.", B.mono_font(round(36 * s), "medium"), accent + (255,), M, ay, 2)
        d.text((ax + round(16 * s), ay - round(6 * s)), spec["answer"], font=H_(brand, 48 * s), fill=SOFT_W)
    _swipe_bottom(canvas, M, H, s)
    return canvas


def cover_quote(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.52, scrim_start=0.24, scrim_bot=224)
    q = spec["quote"].split("\n")
    qf = H_(brand, 100 * s)
    lead = round(128 * s)
    top = round(H * 0.78) - len(q) * lead
    if B.has_svg("quote"):
        B.paste_svg(canvas, "quote", M, top - round(120 * s), round(82 * s), accent)
    B.draw_shadowed(canvas, q, qf, WHITE, M, top, lead, align="left", shadow_a=140, blur=10)
    _swipe_bottom(canvas, M, H, s)
    return canvas


def cover_split(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.54, scrim_start=0.16, scrim_bot=232)
    d = ImageDraw.Draw(canvas)
    y = round(H * 0.42)
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
    _swipe_bottom(canvas, M, H, s)
    return canvas


def cover_versus(spec, W, H, brand):
    s, cx, M, accent = W / 1080, W // 2, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.56, scrim_start=0.5, scrim_bot=120)
    f1 = H_(brand, 74 * s)
    B.draw_shadowed(canvas, [spec["a"]], f1, WHITE, cx, round(H * 0.34), round(92 * s), align="center", shadow_a=120, blur=9)
    B.draw_shadowed(canvas, ["VS"], H_(brand, 124 * s), accent + (255,), cx, round(H * 0.45),
                    round(124 * s), align="center", shadow_a=120, blur=10)
    B.draw_shadowed(canvas, [spec["b"]], f1, WHITE, cx, round(H * 0.61), round(92 * s), align="center", shadow_a=120, blur=9)
    B.draw_shadowed(canvas, [spec["question"]], B.font(round(42 * s), 600), SOFT_W, cx, round(H * 0.73),
                    round(58 * s), align="center", shadow_a=110, blur=6)
    _swipe(canvas, cx - round(58 * s), H - round(116 * s), s)
    return canvas


def cover_numeric(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    canvas = _cover_base(spec, W, H, brand, dark=0.46, scrim_start=0.30, scrim_bot=218)
    big = spec["big"].split("\n")
    bf = H_(brand, 132 * s)
    lead = round(150 * s)
    teaser = spec.get("teaser")
    top = round(H * 0.78) - len(big) * lead - (round(70 * s) if teaser else 0)
    if spec.get("kicker"):
        B.tick_label(canvas, spec["kicker"], M, top - round(78 * s), WHITE, accent, size=round(30 * s))
    end = B.draw_shadowed(canvas, big, bf, WHITE, M, top, lead, align="left", shadow_a=120, blur=9)
    if teaser:
        d = ImageDraw.Draw(canvas)
        d.line([(M, end + round(26 * s)), (M + round(110 * s), end + round(26 * s))], fill=accent, width=round(8 * s))
        B.draw_shadowed(canvas, [teaser], B.font(round(36 * s), 500), SOFT_W, M, end + round(46 * s),
                        round(48 * s), align="left", shadow_a=110, blur=5)
    _swipe_bottom(canvas, M, H, s)
    return canvas


COVER_VARIANTS = {
    "editorial": cover_editorial, "card": cover_card, "question": cover_question,
    "quote": cover_quote, "split": cover_split, "versus": cover_versus, "numeric": cover_numeric,
}


def slide_cover(spec, W, H, brand):
    return COVER_VARIANTS[spec.get("variant", "editorial")](spec, W, H, brand)


def slide_photo(spec, W, H, brand):
    s, M, accent = W / 1080, margin(W), brand.accent(spec["accent"])
    bgp = _path(brand, spec.get("bg"))
    if bgp:
        canvas = B.darken(B.cover_crop(Image.open(bgp), W, H), 0.46).convert("RGBA")
    else:
        canvas = Image.new("RGBA", (W, H), brand.ink + (255,))
        B.soft_blob(canvas, accent, W // 2, round(H * 0.3), r=round(700 * s), alpha=90)
    canvas.alpha_composite(B.bottom_scrim(W, H, start=0.30, bot_a=222))
    cap = spec["caption"].split("\n")
    cf = H_(brand, 84 * s)
    lead = round(116 * s)
    note_lines = spec["note"].split("\n") if spec.get("note") else []
    top = round(H * 0.80) - len(cap) * lead - len(note_lines) * round(52 * s)
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

    # 2) 端末（安全域に収める。tall はUI帯が重いぶん小さく）
    ph_top = lab_y + B.sp("group", W)
    ph_h = round(H * (0.30 if tall else 0.46))
    if spec.get("shot"):
        B.paste_phone_shadow(canvas, B.phone_mockup(app_shot(spec, brand)), cx, ph_top, ph_h)

    # 3) 説明（安全域の下限 y=1110/1920≒0.578 を越えない）
    body = spec.get("sub") or spec.get("caption") or ""
    if body:
        by = ph_top + ph_h + B.sp("group", W)
        limit = round(H * (0.560 if tall else 0.845))
        lead = round(58 * s)
        by = min(by, limit - len(body.split("\n")) * lead)
        B.draw_lines(d, body.split("\n"), B.font(round(42 * s), 500), sub_ink, M, by, lead,
                     align="left")
    if bgp:
        B.grain(canvas, seed=spec["idx"], amount=7)
    return canvas


RENDERERS = {
    "cover": slide_cover, "photo": slide_photo, "shot": slide_shot,
    "info": slide_info, "cta": slide_cta,
    # ★2026-07-25 実物デッキの分解から追加。単一アプリを売るときの本命2種 → [[PATTERNS]] §1b
    "showcase": slide_showcase, "feature": slide_feature,
}
