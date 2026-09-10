#!/usr/bin/env python3
"""【参考実装】ストア画像の構図カタログ 44 型の組み方。

これは汎用の道具ではなく、あるアプリで実際に動かしたコードをそのまま置いたもの。
使い方は「該当する型の関数をコピーして、素材名・文言・色を差し替える」。
アプリごとにスクリプトを新しく書く前提で、ここは構図の実装例として参照する。

動かすには store_layout_kit.py と一緒に scripts/ へ置く
（kit の ROOT がリポジトリルートを指す必要がある）。

--- 以下、元のヘッダ ---

ストア画像の構図カタログを、material/ の実素材で1枚ずつ作る。

実在アプリのストア画像を採取して型に分解したもの（A〜J の10系統・44型）。
「どの構図がこのアプリで成立するか」を実物で比べ、選んだ型を
release/<version>/img/ の本番画像へ昇格させるための素材。

  使い方: python3 scripts/make_pattern_samples.py [P-01 P-23 ...]
          引数なしで全型。
          --frame / --bare で全型のフレーム有無を強制（別ディレクトリへ出力）
          --list で型の一覧だけ表示

描画部品は store_layout_kit.py、色・ワードマークは appstore.config.json、
画面は material/screens/、誌面は material/layouts/。

依存: Pillow
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import store_layout_kit as K  # noqa: E402
from store_layout_kit import (A, BG, INK, LANDSCAPE, PORTRAIT, SUB,  # noqa: E402
                              badge, burst, canvas, checklist, cover, curve_arrow,
                              dots, floated, font, hgrad, layout, loupe, marker,
                              paste, phone, pict, place, rot, rounded, rule,
                              screen, text_block, text_layer, vgrad, wordmark,
                              wordmark_width)

OUT = K.ROOT / "material" / "pattern_samples"


# MARK: - 共通の足場

def _lum(c) -> float:
    return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255


def base(ground, *, size=PORTRAIT, head=(), sub=(), ct=None, align="left",
         family="sans", hx=104, hy=250, hsize=112, ssize=46, leading=1.24,
         gap=70, tracking=-3, rule_col=None, subleading=1.5):
    """地 + 見出し（+ 補足）まで組んで (画像, Draw, 補足の下端 y) を返す。

    ground は色タプル、または貼り込む Image。文字色は地の明度から自動で決める。
    """
    if isinstance(ground, Image.Image):
        im = canvas(size, (0, 0, 0))
        im.paste(ground.convert("RGB"), (0, 0))
        probe = ground.convert("RGB").resize((1, 1)).getpixel((0, 0))
    else:
        im = canvas(size, ground)
        probe = tuple(ground)[:3]
    d = ImageDraw.Draw(im)
    ct = ct or ((255, 255, 255) if _lum(probe) < 0.55 else INK)
    W = size[0]
    x = 0 if align == "center" else hx
    y = hy
    if head:
        hf = font(hsize, 900 if family == "sans" else 700, family)
        text_block(d, (x, y), head, hf, ct, leading=leading, align=align,
                   width=W if align == "center" else None, tracking=tracking)
        y += round(hsize * leading) * len(head)
    if rule_col:
        rx = (W - 132) / 2 if align == "center" else hx + 4
        rule(d, rx, y + 18, 132, rule_col, 10)
        y += 52
    if sub:
        y += gap - 40
        sc = ct if _lum(probe) < 0.55 else SUB
        text_block(d, (x, y), sub, font(ssize, 500, family), sc, leading=subleading,
                   align=align, width=W if align == "center" else None)
        y += round(ssize * subleading) * len(sub)
    return im, d, y


def drop(im, scr, width, top, *, framed=True, cx=None):
    """端末を1台、上端 y = top に置く。cx 省略時はキャンバス中央。"""
    ph = phone(screen(scr) if isinstance(scr, str) else scr, width, framed=framed)
    paste(im, ph, ((im.width / 2 if cx is None else cx) - ph.width / 2, top))
    return ph


# MARK: - A 縦・接地（基本形）

def p01():
    """上見出し＋見切れ端末。最も普及した既定形。"""
    im, d, _ = base(A["bengara"], head=["話すだけで、", "今日が記事になる。"],
                    sub=["書かなくていい。声だけで続く日記。"],
                    rule_col=(255, 255, 255, 210))
    drop(im, "03_home.png", round(im.width * 0.80), 860)
    return im


def p02():
    """フルブリード素の実UI。加工ゼロ（Obsidian 型）。"""
    im = canvas(PORTRAIT, BG)
    paste(im, screen("09_paper.png").resize(PORTRAIT, Image.LANCZOS), (0, 0))
    return im


def p03():
    """下見出し＋全身フレーム端末。実測11本には例が無かった型（要検証）。"""
    im = canvas(PORTRAIT, A["ai"])
    ph = phone(screen("09_paper.png"), round(PORTRAIT[0] * 0.62))
    paste(im, ph, ((PORTRAIT[0] - ph.width) / 2, 200))
    d = ImageDraw.Draw(im)
    y = 200 + ph.height + 150
    text_block(d, (0, y), ["話した言葉だけで、", "できています。"], font(96, 900),
               (255, 255, 255), leading=1.26, align="center", width=PORTRAIT[0])
    text_block(d, (0, y + 290), ["AIが日記を創作することはありません。"], font(44, 500),
               (255, 255, 255, 200), align="center", width=PORTRAIT[0])
    return im


def p04():
    """紙面地＋2段見出し（明朝）。Stoic 型のエディトリアル。"""
    im = canvas(PORTRAIT, BG)
    d = ImageDraw.Draw(im)
    text_block(d, (110, 210), ["TALKING DIARY"], font(34, 600), SUB, tracking=7)
    text_block(d, (104, 300), ["あなたの一日を、", "刊行する。"], font(104, 700, "serif"),
               INK, leading=1.32, tracking=-2)
    rule(d, 110, 610, 118, A["bengara"], 8)
    text_block(d, (104, 676), ["AIとの会話が、雑誌のような1ページに。"],
               font(42, 400, "serif"), SUB)
    drop(im, "09_paper.png", round(im.width * 0.78), 830, framed=False)
    return im


def p05():
    """画面幅超え・両端見切れ。端末をキャンバスより広く取り左右を切る（Calm 型）。"""
    im, d, _ = base(A["seiji"], head=["誌面を、", "端から端まで。"], align="center", hy=230)
    drop(im, "09_paper.png", round(im.width * 1.24), 700, framed=False)
    return im


def p06():
    """見出しを画面に重ねる。実UIの余白の上に直接文字を置く。"""
    im = canvas(PORTRAIT, BG)
    paste(im, screen("01_onboarding_concept.png").resize(PORTRAIT, Image.LANCZOS), (0, 0))
    ov = Image.new("RGBA", PORTRAIT, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([0, PORTRAIT[1] * 0.52, PORTRAIT[0], PORTRAIT[1]],
                                fill=(247, 244, 240, 216))
    paste(im, ov, (0, 0))
    d = ImageDraw.Draw(im)
    text_block(d, (104, PORTRAIT[1] * 0.60), ["話すだけで、", "今日が記事になる。"],
               font(104, 900), INK, leading=1.26, tracking=-3)
    rule(d, 108, PORTRAIT[1] * 0.60 + 290, 120, A["bengara"], 9)
    return im


# MARK: - B 縦・傾斜

def p07():
    """微傾斜（5〜10°）。わずかに振るだけで「置かれた物」の質感が出る。"""
    im, d, _ = base(A["ai"], head=["毎日の電話が、", "習慣になる。"],
                    sub=["決めた時刻に、AIから今日を聞きます。"])
    place(im, phone(screen("03_home.png"), round(im.width * 0.76)),
          (im.width / 2, im.height * 0.72), deg=-7, float_=True, dy=34)
    return im


def p08():
    """中傾斜（約20°）。Calm 2枚目の型。可読性と動きが釣り合う角度。"""
    im, d, _ = base(vgrad(PORTRAIT, [(0, A["ai"]), (0.55, (110, 100, 150)),
                                     (1, A["ebizome"])]),
                    head=["よく眠るために、", "話しておく。"], align="center", hy=230,
                    sub=["寝る前の数分を、ふりかえる時間に。"])
    place(im, phone(screen("07_interview.png"), round(im.width * 0.82)),
          (im.width * 0.56, im.height * 0.70), deg=-20, float_=True, dy=40, blur=44)
    return im


def p09():
    """大傾斜（30°超）。UIはほぼ読めないので雰囲気を売る枚に限る。"""
    im, d, _ = base(A["ebizome"], head=["話したことが、", "誌面になる。"],
                    align="center", hy=220)
    place(im, phone(screen("09_paper.png"), round(im.width * 0.92)),
          (im.width * 0.58, im.height * 0.72), deg=-33, float_=True, dy=46, blur=50)
    return im


def p10():
    """隅差し。端末を隅から斜めに差し込み部分だけ見せる（Reflectly 1枚目の型）。"""
    im, d, _ = base(A["taisha"], head=["はじめまして、", "聞き手です。"], align="center",
                    hy=240, sub=["毎晩、あなたに取材します。"])
    place(im, phone(screen("07_interview.png"), round(im.width * 0.76)),
          (im.width * 0.84, im.height * 0.78), deg=-16, float_=True, dy=36)
    return im


def p11():
    """回転同調テキスト。見出しも端末と同じ角度に振る（Reflectly 2枚目の型）。"""
    deg = -13
    im = canvas(PORTRAIT, A["matsuba"])
    # 見出しは端末より上に完全に逃がす。白文字が白い画面に重なると読めない。
    place(im, phone(screen("07_interview.png"), round(im.width * 0.80)),
          (im.width * 0.55, im.height * 0.72), deg=deg, float_=True, dy=40, blur=44)
    lay = text_layer(["今日は、", "どんな一日", "でしたか。"], font(94, 900),
                     (255, 255, 255), leading=1.26, tracking=-3)
    place(im, lay, (im.width * 0.44, im.height * 0.165), deg=deg)
    return im


def p12():
    """2台斜め重ね。奥と手前で立体を作る（Upmind 1枚目の型）。"""
    im, d, _ = base(BG, head=["話す。すると、", "誌面になる。"], align="center", hy=230,
                    sub=["取材から組版までを、その場で。"])
    place(im, phone(screen("07_interview.png"), round(im.width * 0.60)),
          (im.width * 0.34, im.height * 0.66), deg=8, float_=True, dy=30, alpha=85)
    place(im, phone(screen("09_paper.png"), round(im.width * 0.64)),
          (im.width * 0.64, im.height * 0.74), deg=-6, float_=True, dy=36)
    return im


# MARK: - C 縦・浮遊

def p13():
    """単体浮遊。傾けず、影だけで支える。"""
    im, d, _ = base(A["karashi"], head=["ことばが、", "溜まっていく。"],
                    sub=["話した言葉が索引になります。"])
    place(im, phone(screen("05_vocabulary.png"), round(im.width * 0.74)),
          (im.width / 2, im.height * 0.72), float_=True, dy=44, blur=46, alpha=105)
    return im


def p14():
    """カード・カスケード。UIの帯を斜めに階段状へ（Otter.ai 1枚目の型）。"""
    im, d, _ = base(A["ai"], head=["聞いた言葉を、", "そのまま残す。"], hy=230)
    src = screen("09_paper.png")
    for i, (t0, t1) in enumerate([(0.16, 0.34), (0.32, 0.52), (0.50, 0.72)]):
        card = src.crop((60, round(src.height * t0), src.width - 60,
                         round(src.height * t1)))
        cw = round(im.width * 0.78)
        card = rounded(card.resize((cw, round(card.height * cw / card.width)),
                                   Image.LANCZOS), 22)
        place(im, card, (im.width * (0.40 + i * 0.10), im.height * (0.50 + i * 0.15)),
              deg=-12, float_=True, dy=26, blur=30)
    return im


def p15():
    """扇状フロート。3台を扇に開いて幅を示す。サムネイルでは読めない。"""
    im, d, _ = base(BG, head=["同じ誌面は、", "二度と出ない。"], align="center", hy=230,
                    hsize=104, sub=["その日の内容で、構成も余白も変わります。"])
    for name, deg, fx in (("genre_stats-day_long.png", -14, 0.22),
                          ("genre_timeline-detailed_long.png", 14, 0.78),
                          ("genre_quote-centered_short.png", 0, 0.50)):
        cw = round(im.width * 0.46)
        place(im, rounded(cover(layout(name), cw, round(cw * 1.36)), 22),
              (im.width * fx, im.height * 0.68), deg=deg, float_=True, dy=28, blur=32)
    return im


# MARK: - D 縦・注釈

def p16():
    """ルーペ拡大。見せたいUI部品を作り手が拡大する。"""
    im, d, _ = base(A["matsuba"], head=["押して、話すだけ。"], align="center", hy=250,
                    sub=["キーボードは、もう要りません。"])
    src, pw = screen("07_interview.png"), round(im.width * 0.70)
    px, py = (im.width - pw) / 2, 700
    paste(im, phone(src, pw), (px, py))
    k, cx, cy, rr = pw / src.width, 603, 1913, 205
    size = round(im.width * 0.40)
    loupe(im, src, at=(im.width - size - 70, py + cy * k - size - 150),
          src_center=(cx, cy), src_r=rr, size=size, k=k,
          origin=(px + cx * k, py + cy * k))
    return im


def p17():
    """円形バッジ注釈。丸い色面に短文を入れて重ねる（Otter.ai の緑丸）。"""
    im, d, _ = base(A["ai"], head=["声だけで、", "ここまで残る。"], hy=230)
    drop(im, "09_paper.png", round(im.width * 0.72), 820, framed=False)
    for lines, col, sz, at in ((["見出しも", "AIが付ける"], A["matsuba"], 300, (0.15, 0.47)),
                               (["特色は", "1日1色"], A["taisha"], 250, (0.85, 0.72))):
        place(im, badge(lines, col, sz, font(40, 800)),
              (im.width * at[0], im.height * at[1]), float_=True, dy=18, blur=24)
    return im


def p18():
    """フローティングUIカード。実UI由来の一部だけを拡大して浮かせる。"""
    im, d, _ = base(A["taisha"], head=["見出しは、", "AIが付ける。"],
                    sub=["その日の言葉から、アクセントは1色だけ。"])
    src, pw = screen("08_assembly.png"), round(im.width * 0.74)
    px, py = (im.width - pw) / 2, 860
    paste(im, phone(src, pw), (px, py))
    card = src.crop((40, 470, 1166, 760))
    cw = round(im.width * 0.90)
    card = rounded(card.resize((cw, round(card.height * cw / card.width)),
                               Image.LANCZOS), 26)
    place(im, card, (im.width / 2, py + 470 * (pw / src.width) + 340 + card.height / 2),
          float_=True, dy=30, blur=34)
    return im


def p19():
    """手描き矢印＋集中線。日本のストア画像の定番の強調（暗記カード型）。"""
    im, d, _ = base(BG, head=["話すだけで、", "ここまで書ける。"], align="center", hy=210,
                    hsize=104)
    a, b = round(im.width * 0.38), round(im.width * 0.30)
    paste(im, phone(screen("07_interview.png"), a), (60, 880))
    # 集中線の内径は端末の半対角より大きく取る。小さいと線が端末の脇から
    # 生えているように見える（端末を貫通した線の残りだけが見える状態）。
    bcx, bcy = im.width * 0.70, im.height * 0.695
    burst(d, bcx, bcy, round(im.width * 0.37), round(im.width * 0.46),
          color=A["karashi"], n=22, width=8)
    pb = phone(screen("09_paper.png"), b)
    paste(im, pb, (bcx - pb.width / 2, bcy - pb.height / 2))
    curve_arrow(im, (60 + a * 0.99, 1460), (bcx - pb.width / 2 - 40, 1760),
                color=A["bengara"], width=14, bow=0.32, head=52)
    text_block(d, (0, im.height - 290), ["取材 3分 → 誌面 1ページ"], font(52, 800), INK,
               align="center", width=im.width)
    return im


def p20():
    """蛍光マーカー見出し。キーワードだけ色帯で抜く（日本のストア画像の定番）。"""
    im = canvas(PORTRAIT, (255, 255, 255))
    d = ImageDraw.Draw(im)
    f = font(96, 900)
    w = marker(d, (104, 230), "話すだけ", f, INK, A["karashi"] + (120,), tracking=-3)
    text_block(d, (104 + w + 6, 230), ["で"], f, INK)
    text_block(d, (104, 230 + 124), ["日記が続く。"], f, INK, tracking=-3)
    checklist(d, (110, 500), ["書かなくていい", "毎日ちがう誌面", "話した言葉だけ"],
              font(46, 600), INK, A["bengara"])
    drop(im, "03_home.png", round(im.width * 0.74), 860)
    return im


def p21():
    """番号ステップ。手順を ①②③ で示す。"""
    im, d, _ = base(BG, head=["3分で、1ページ。"], align="center", hy=220,
                    sub=["やることは、話すだけ。"], tracking=-4)
    steps = [("①", "話す", "AIの質問に答える", "07_interview.png", A["matsuba"], 0.62),
             ("②", "組まれる", "その場で誌面になる", "08_assembly.png", A["karashi"], 0.14),
             ("③", "残る", "一冊に積み上がる", "09_paper.png", A["bengara"], 0.16)]
    y, pw = 620, round(im.width * 0.32)
    for numeral, title, note, scr, col, top in steps:
        paste(im, rounded(cover(screen(scr), pw, round(pw * 1.40), top=top), 20), (96, y))
        tx = 96 + pw + 70
        d.text((tx, y + 8), numeral, font=font(62, 900), fill=col)
        text_block(d, (tx + 92, y + 12), [title], font(60, 800), INK)
        text_block(d, (tx + 92, y + 108), [note], font(40, 500), SUB)
        rule(d, tx + 92, y + 190, 90, col, 7)
        y += round(pw * 1.40) + 80
    return im


def p22():
    """はみ出し図像。図像を実UIの外周から飛び出させる（Finch 型）。"""
    im, d, _ = base(A["seiji"], head=["夜のうちに、", "話しておく。"], hy=230)
    drop(im, "04_home_dark.png", round(im.width * 0.72), 900, framed=False)
    place(im, pict("moon", 300, (255, 255, 255, 235)), (im.width * 0.14, im.height * 0.36))
    place(im, pict("bed", 320, (255, 255, 255, 215)), (im.width * 0.87, im.height * 0.90))
    return im


# MARK: - E 縦・比較

def p23():
    """before→after（左右2端末＋矢印）。変化を1枚で示す（暗記カード型）。"""
    im, d, _ = base(BG, head=["話した声が、", "読み物になる。"], align="center", hy=200,
                    hsize=104)
    w = round(im.width * 0.40)
    ya, yb = 1000, 1240
    paste(im, phone(screen("07_interview.png"), w), (60, ya))
    paste(im, phone(screen("09_paper.png"), w), (im.width - w - 60, yb))
    for x, y, t, c in ((60 + w / 2, ya - 70, "取材", SUB),
                       (im.width - w / 2 - 60, yb - 70, "誌面", A["bengara"])):
        f = font(46, 800)
        d.text((x - d.textlength(t, font=f) / 2, y), t, font=f, fill=c)
    curve_arrow(im, (60 + w + 24, ya + w * 0.9), (im.width - w - 84, yb + w * 0.7),
                color=A["bengara"], width=13, bow=0.26, head=48)
    return im


def p24():
    """before→after（上下）。縦キャンバスと相性がよい並べ方。"""
    im, d, _ = base(A["ai"], head=["ただの独り言が、"], hy=190, hsize=88,
                    sub=["ひとつの記事になる。"], ssize=56)
    w = round(im.width * 0.56)
    paste(im, phone(screen("07_interview.png"), w), ((im.width - w) / 2, 600))
    cy = 600 + round(w * 2.10) + 40
    f = font(80, 900)
    d.text((im.width / 2 - d.textlength("↓", font=f) / 2, cy), "↓", font=f,
           fill=(255, 255, 255, 220))
    paste(im, phone(screen("09_paper.png"), w), ((im.width - w) / 2, cy + 140))
    return im


def p25():
    """斜め分割2状態。1枚を斜めに割り、左下と右上で状態を対置する。"""
    W, H = PORTRAIT
    im = canvas(PORTRAIT, BG)
    # 左上＝取材、右下＝誌面。どちらも白い画面なので色を被せないと斜めの境界が
    # 見えず、2つの本文が混ざって判読できなくなる。
    top = cover(screen("07_interview.png"), W, H, top=0.30).convert("RGBA")
    top.alpha_composite(Image.new("RGBA", (W, H), A["matsuba"] + (210,)))
    bot = cover(screen("09_paper.png"), W, H, top=0.10).convert("RGBA")
    bot.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 238, 96)))
    im.paste(top.convert("RGB"), (0, 0))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(W, 0), (W, H), (0, H)], fill=255)
    im.paste(bot.convert("RGB"), (0, 0), m)
    d = ImageDraw.Draw(im)
    d.line([(W, 0), (0, H)], fill=(255, 255, 255, 240), width=20)
    text_block(d, (90, 210), ["話す"], font(112, 900), (255, 255, 255), tracking=-4)
    text_block(d, (0, H - 430), ["読む"], font(112, 900), INK, align="right",
               width=W - 90, tracking=-4)
    return im


# MARK: - F 横向き

def p26():
    """横：テキスト左＋端末右。現行セットが採っている型。"""
    im = canvas(LANDSCAPE, BG)
    d = ImageDraw.Draw(im)
    wordmark(d, 150, 96, 62, INK)
    text_block(d, (150, 300), ["話し終えたら、", "その場で組版。"], font(150, 900), INK,
               leading=1.24, tracking=-5)
    rule(d, 154, 700, 130, A["karashi"], 12)
    text_block(d, (150, 790), ["見出しも本文も、", "あなたの言葉のまま一枚に。"],
               font(58, 500), SUB, leading=1.5)
    ph = phone(screen("08_assembly.png"), round(LANDSCAPE[1] * 0.44))
    paste(im, ph, (LANDSCAPE[0] - ph.width - 300, (LANDSCAPE[1] - ph.height) / 2))
    dots(d, 156, 1180, center=False)
    return im


def p27():
    """横：フルブリード。紙面を横位置いっぱいに使い、下帯に文字を置く。"""
    im = canvas(LANDSCAPE, BG)
    im.paste(cover(layout("genre_grand-spread_long.png"), *LANDSCAPE, top=0.08), (0, 0))
    ov = Image.new("RGBA", LANDSCAPE, (0, 0, 0, 0))
    ImageDraw.Draw(ov).rectangle([0, LANDSCAPE[1] * 0.68, LANDSCAPE[0], LANDSCAPE[1]],
                                fill=(20, 18, 16, 195))
    paste(im, ov, (0, 0))
    text_block(ImageDraw.Draw(im), (150, LANDSCAPE[1] * 0.755),
               ["毎日が、あなたの特集記事になる。"], font(104, 900), (255, 255, 255),
               tracking=-4)
    return im


def p28():
    """横：帯キャプション。上に色帯を敷き、下に端末を3台並べる。"""
    W, H = LANDSCAPE
    im = canvas(LANDSCAPE, BG)
    paste(im, Image.new("RGBA", (W, round(H * 0.30)), A["bengara"] + (255,)), (0, 0))
    d = ImageDraw.Draw(im)
    text_block(d, (0, H * 0.075), ["話すだけで、今日が記事になる。"], font(112, 900),
               (255, 255, 255), align="center", width=W, tracking=-4)
    for i, scr in enumerate(("07_interview.png", "08_assembly.png", "09_paper.png")):
        ph = phone(screen(scr), round(H * 0.40))
        paste(im, ph, (W * (0.20 + i * 0.30) - ph.width / 2, H * 0.36))
    return im


def p29():
    """横：2端末＋矢印の before→after。横位置は左右比較と相性がよい。"""
    W, H = LANDSCAPE
    im = canvas(LANDSCAPE, BG)
    d = ImageDraw.Draw(im)
    text_block(d, (0, 110), ["声が、そのまま誌面になる。"], font(104, 900), INK,
               align="center", width=W, tracking=-4)
    w = round(H * 0.42)
    paste(im, phone(screen("07_interview.png"), w), (W * 0.20 - w / 2, H * 0.30))
    paste(im, phone(screen("09_paper.png"), w), (W * 0.72 - w / 2, H * 0.30))
    curve_arrow(im, (W * 0.20 + w * 0.62, H * 0.62), (W * 0.72 - w * 0.66, H * 0.62),
                color=A["bengara"], width=15, bow=0.22, head=56)
    for x, t in ((0.20, "話す"), (0.72, "残る")):
        f = font(52, 800)
        d.text((W * x - d.textlength(t, font=f) / 2, H * 0.245), t, font=f, fill=SUB)
    return im


def p30():
    """横：ピクトグラム併置。使う場面を絵で添える（暗記カード型）。"""
    W, H = LANDSCAPE
    im = canvas(LANDSCAPE, BG)
    d = ImageDraw.Draw(im)
    f = font(104, 900)
    w = marker(d, (170, 190), "寝る前", f, INK, A["karashi"] + (120,), tracking=-4)
    text_block(d, (170 + w + 8, 190), ["の数分で"], f, INK)
    text_block(d, (170, 190 + 132), ["今日を残せる。"], f, INK, tracking=-4)
    text_block(d, (174, 480), ["布団の中でも、帰りの電車でも。"], font(56, 500), SUB)
    for i, k in enumerate(("bed", "train", "clock")):
        place(im, pict(k, 190, INK + (215,)), (260 + i * 250, H * 0.76))
    ph = phone(screen("07_interview.png"), round(H * 0.46))
    paste(im, ph, (W * 0.70 - ph.width / 2, (H - ph.height) / 2))
    return im


def p31():
    """横：傾斜端末。横位置で斜めに置くと動きが出る。"""
    W, H = LANDSCAPE
    im = canvas(LANDSCAPE, A["ebizome"])
    text_block(ImageDraw.Draw(im), (170, 300), ["聞き手は、", "毎晩ここにいる。"],
               font(140, 900), (255, 255, 255), leading=1.24, tracking=-5)
    place(im, phone(screen("07_interview.png"), round(H * 0.62)),
          (W * 0.74, H * 0.56), deg=-18, float_=True, dy=38, blur=46)
    return im


# MARK: - G セット単位（3枚組で1ファイル）

def _set_tile(accent, head, sub, scr):
    im, d, _ = base(accent, head=head, sub=[sub], hx=96, hy=230, hsize=100)
    drop(im, scr, round(im.width * 0.78), 800)
    return im


def _sheet(tiles, gap=56):
    sh = canvas((PORTRAIT[0] * len(tiles) + gap * (len(tiles) - 1), PORTRAIT[1]),
                (255, 255, 255))
    for i, t in enumerate(tiles):
        paste(sh, t, (i * (PORTRAIT[0] + gap), 0))
    return sh


def p32():
    """枚ごと色替え。構図を固定して地の色だけ回す（Spotify / Pinterest 型）。"""
    return _sheet([
        _set_tile(A["bengara"], ["話すだけで、", "1ページに。"], "書かなくていい日記。",
                  "03_home.png"),
        _set_tile(A["seiji"], ["毎日ちがう、", "誌面になる。"], "同じ構成は二度と出ません。",
                  "09_paper.png"),
        _set_tile(A["ebizome"], ["ことばが、", "溜まっていく。"], "話した言葉が索引に。",
                  "05_vocabulary.png")])


def p33():
    """パノラマ連結。地を3枚またぎで連続させる。設計時の隙間は 56px。"""
    gap = 56
    W3 = PORTRAIT[0] * 3 + gap * 2
    band = hgrad((W3, PORTRAIT[1]), [(0, A["ai"]), (0.5, A["ebizome"]), (1, A["taisha"])])
    tiles = []
    for i, (head, sub, scr) in enumerate(
            [(["話す。"], "取材に答えるだけ", "07_interview.png"),
             (["組まれる。"], "その場で誌面になる", "08_assembly.png"),
             (["残る。"], "一冊に積み上がる", "03_home.png")]):
        x0 = i * (PORTRAIT[0] + gap)
        t = canvas(PORTRAIT, (0, 0, 0))
        t.paste(band.crop((x0, 0, x0 + PORTRAIT[0], PORTRAIT[1])), (0, 0))
        d = ImageDraw.Draw(t)
        text_block(d, (96, 240), head, font(120, 900), (255, 255, 255), tracking=-4)
        text_block(d, (96, 420), [sub], font(44, 500), (255, 255, 255, 210))
        drop(t, scr, round(PORTRAIT[0] * 0.76), 780)
        tiles.append(t)
    return _sheet(tiles, gap)


def p34():
    """セット漸進グラデ。各枚は独立だが地の色が3枚で移り変わる（Calm 型）。"""
    cols = [(A["ai"], (86, 96, 140)), ((86, 96, 140), A["ebizome"]),
            (A["ebizome"], A["taisha"])]
    heads = [(["夜になったら、"], "AIから電話が鳴る"), (["話して、"], "その場で組版される"),
             (["朝には、"], "一枚の記事になっている")]
    tiles = []
    for (c0, c1), (head, sub) in zip(cols, heads):
        im, d, _ = base(vgrad(PORTRAIT, [(0, c0), (1, c1)]), head=head, sub=[sub],
                        hx=96, hy=230, hsize=104)
        drop(im, "03_home.png", round(PORTRAIT[0] * 0.76), 820)
        tiles.append(im)
    return _sheet(tiles)


# MARK: - H 実UIなし・信頼

def p35():
    """権威三点盛り（Upmind 型）。受賞が無い段階は検証できる事実で代替する。"""
    W = PORTRAIT[0]
    im = canvas(PORTRAIT, INK)
    d = ImageDraw.Draw(im)
    ws = 74
    wordmark(d, (W - wordmark_width(d, ws)) / 2, 210, ws, (255, 255, 255))
    text_block(d, (0, 380), ["毎日が、", "あなたの特集記事になる。"], font(88, 900),
               (255, 255, 255), leading=1.28, align="center", width=W)
    y = 700
    for label, col in (("広告なし", A["matsuba"]), ("誌面レイアウト 30種", A["karashi"]),
                       ("話した言葉だけ", A["seiji"])):
        f = font(48, 700)
        tw = d.textlength(label, font=f)
        x0 = (W - (tw + 150)) / 2
        d.rounded_rectangle([x0, y, x0 + tw + 150, y + 108], 54, outline=col + (255,),
                            width=5)
        d.ellipse([x0 + 46, y + 44, x0 + 66, y + 64], fill=col)
        d.text((x0 + 96, y + 26), label, font=f, fill=(255, 255, 255, 235))
        y += 140
    drop(im, "03_home.png", round(W * 0.62), 1240, framed=False)
    return im


def p36():
    """機能訴求リスト＋線画。実UIを出さず、できることを言葉と絵で並べる（Balance 型）。"""
    im, d, _ = base(BG, head=["書かない日記を、", "はじめる。"], align="center", hy=300,
                    hsize=100)
    checklist(d, (250, 720), ["声で今日をふりかえる", "雑誌のような誌面に編集",
                              "ことばを索引にして残す"], font(52, 600), INK,
              A["bengara"], gap=2.1)
    for i, k in enumerate(("mic", "book", "clock")):
        place(im, pict(k, 210, A[("matsuba", "bengara", "karashi")[i]] + (230,)),
              (PORTRAIT[0] * (0.24 + i * 0.26), PORTRAIT[1] * 0.74))
    return im


def p37():
    """ブランドパネル（明朝・実UIなし）。世界観だけを出す。"""
    W, H = PORTRAIT
    im = canvas(PORTRAIT, BG)
    d = ImageDraw.Draw(im)
    ws = 132
    wordmark(d, (W - wordmark_width(d, ws, "serif", 600)) / 2, H * 0.30, ws, INK,
             "serif", 600)
    text_block(d, (0, H * 0.30 + 260), ["あなたの一日を、", "刊行する。"],
               font(96, 600, "serif"), INK, leading=1.34, align="center", width=W)
    rule(d, (W - 130) / 2, H * 0.30 + 560, 130, A["bengara"], 8)
    text_block(d, (0, H * 0.30 + 640), ["AIとの音声取材で編集する、話す日記。"],
               font(40, 400, "serif"), SUB, align="center", width=W)
    dots(d, W / 2, H * 0.78, r=17, gap=62)
    return im


def p38():
    """報道ロゴ枚（Headspace / Otter.ai 型）。実績が出るまでは作れない枚。"""
    W, H = PORTRAIT
    im, d, _ = base(BG, head=["掲載実績"], align="center", hy=300, hsize=72,
                    sub=["※ 実績が出てから作る枚。現状は素材が無い。"], ssize=38)
    for i in range(6):
        bx, by = W * (0.28 + (i % 2) * 0.44), H * (0.46 + (i // 2) * 0.13)
        bw, bh = round(W * 0.32), round(H * 0.05)
        d.rounded_rectangle([bx - bw / 2, by - bh / 2, bx + bw / 2, by + bh / 2], 10,
                            fill=(0, 0, 0, 22))
    return im


# MARK: - I 一覧・特殊面

def p39():
    """見本市グリッド。バリエーションを面積で示す。"""
    im, d, _ = base(A["seiji"], head=["毎日ちがう、", "誌面レイアウト。"], align="center",
                    hy=230, hsize=104, sub=["30種の構成から、その日の内容に合わせて。"])
    names = ["genre_grand-spread_short.png", "genre_stats-day_short.png",
             "genre_quote-centered_short.png", "genre_timeline-detailed_short.png"]
    cols, gap, mx = 2, 46, 96
    cw = (PORTRAIT[0] - mx * 2 - gap) // cols
    ch = round(cw * 1.32)
    for i, name in enumerate(names):
        paste(im, rounded(cover(layout(name), cw, ch), 18),
              (mx + (i % cols) * (cw + gap), 760 + (i // cols) * (ch + gap)))
    return im


def p40():
    """カテゴリピクトグラム一覧。できることの幅を絵で並べる（Headspace 型）。"""
    im, d, _ = base(A["ai"], head=["話せることは、", "なんでもいい。"], align="center",
                    hy=230, hsize=104)
    labels = [("mic", "取材"), ("book", "誌面"), ("moon", "夜"),
              ("clock", "毎日の電話"), ("bed", "寝る前"), ("train", "移動中")]
    for i, (k, lab) in enumerate(labels):
        cx = PORTRAIT[0] * (0.24 + (i % 3) * 0.26)
        cy = PORTRAIT[1] * (0.52 + (i // 3) * 0.20)
        place(im, pict(k, 200, (255, 255, 255, 235)), (cx, cy))
        f = font(40, 700)
        d.text((cx - d.textlength(lab, font=f) / 2, cy + 135), lab, font=f,
               fill=(255, 255, 255, 220))
    return im


def p41():
    """ダークモード対比。Apple が公式に推奨している唯一の構図上の助言。"""
    # 地はダークだが端末の黒より明るくする。近黒の地に近黒のベゼルを置くと
    # 画面・端末・キャンバスが一塊の黒に潰れ、目的を果たさない。
    im, d, _ = base((46, 51, 60), head=["夜に馴染む、", "暗い誌面。"],
                    sub=["寝る前に読んでも、目に刺さりません。"], rule_col=A["karashi"])
    drop(im, "04_home_dark.png", round(im.width * 0.80), 860)
    return im


def p42():
    """ブロブ地。白地に有機的な色面を敷く（Awarefy 型・日本のAI系で多い）。"""
    W, H = PORTRAIT
    im = canvas(PORTRAIT, (255, 255, 255))
    blob = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blob)
    for cx, cy, rx, ry, al in ((0.18, 0.16, 0.42, 0.18, 46), (0.92, 0.30, 0.34, 0.22, 34),
                               (0.30, 0.94, 0.52, 0.20, 40)):
        bd.ellipse([W * (cx - rx), H * (cy - ry), W * (cx + rx), H * (cy + ry)],
                   fill=A["seiji"] + (al,))
    paste(im, blob.filter(ImageFilter.GaussianBlur(3)), (0, 0))
    d = ImageDraw.Draw(im)
    f = font(92, 900)
    w = marker(d, (104, 260), "モヤモヤ", f, INK, A["seiji"] + (110,), tracking=-3)
    text_block(d, (104 + w + 6, 260), ["を"], f, INK)
    text_block(d, (104, 260 + 120), ["ことばにする。"], f, INK, tracking=-3)
    text_block(d, (104, 490), ["AIが聞き手になって、今日を整えます。"], font(42, 500), SUB)
    drop(im, "05_vocabulary.png", round(W * 0.74), 820, framed=False)
    return im


def p43():
    """ウィジェット／OS文脈。合成UIなので提出前に実機で撮り直す前提の型。"""
    im, d, _ = base(vgrad(PORTRAIT, [(0, (18, 22, 30)), (0.55, (38, 44, 58)),
                                     (1, (22, 26, 34))]),
                    head=["決めた時刻に、", "AIから電話。"], align="center", hy=230,
                    hsize=104, sub=["通知をタップすれば、そのまま取材がはじまります。"],
                    ssize=40)
    W = PORTRAIT[0]
    bw, bh = W - 180, 300
    banner = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    bd = ImageDraw.Draw(banner)
    bd.rounded_rectangle([0, 0, bw - 1, bh - 1], 62, fill=(248, 246, 242, 240))
    wordmark(bd, 54, 52, 62, INK)
    bd.text((bw - 250, 66), "たった今", font=font(34, 500), fill=SUB)
    text_block(bd, (54, 150), ["今日はどんな一日でしたか？"], font(50, 700), INK)
    text_block(bd, (54, 218), ["3分のミニ取材をはじめましょう。"], font(40, 400), SUB)
    paste(im, banner, (90, 780))
    drop(im, "04_home_dark.png", round(W * 0.70), 1180)
    return im


# MARK: - J アンチパターン

def p44():
    """余白のみ／休符。1枚分の面積を情報ゼロで消費する（Pinterest 3枚目で実在）。"""
    W, H = PORTRAIT
    im = canvas(PORTRAIT, A["uguisu"])
    d = ImageDraw.Draw(im)
    ws = 150
    d.rounded_rectangle([(W - ws) / 2, (H - ws) / 2, (W + ws) / 2, (H + ws) / 2],
                        round(ws * 0.24), fill=(255, 255, 255, 235))
    gf = font(round(ws * 0.62), 700)
    bb = d.textbbox((0, 0), "話", font=gf)
    d.text(((W - (bb[2] - bb[0])) / 2 - bb[0], (H - (bb[3] - bb[1])) / 2 - bb[1]),
           "話", font=gf, fill=A["uguisu"])
    return im


# MARK: - カタログ

FAMILIES = {
    "A 縦・接地": ["P-01", "P-02", "P-03", "P-04", "P-05", "P-06"],
    "B 縦・傾斜": ["P-07", "P-08", "P-09", "P-10", "P-11", "P-12"],
    "C 縦・浮遊": ["P-13", "P-14", "P-15"],
    "D 縦・注釈": ["P-16", "P-17", "P-18", "P-19", "P-20", "P-21", "P-22"],
    "E 縦・比較": ["P-23", "P-24", "P-25"],
    "F 横向き": ["P-26", "P-27", "P-28", "P-29", "P-30", "P-31"],
    "G セット単位": ["P-32", "P-33", "P-34"],
    "H 実UIなし・信頼": ["P-35", "P-36", "P-37", "P-38"],
    "I 一覧・特殊面": ["P-39", "P-40", "P-41", "P-42", "P-43"],
    "J アンチパターン": ["P-44"],
}

PATTERNS = {
    "P-01": ("上見出し＋見切れ端末", p01), "P-02": ("フルブリード素の実UI", p02),
    "P-03": ("下見出し＋全身フレーム端末", p03), "P-04": ("紙面地＋2段見出し（明朝）", p04),
    "P-05": ("画面幅超え・両端見切れ", p05), "P-06": ("見出しを画面に重ねる", p06),
    "P-07": ("微傾斜", p07), "P-08": ("中傾斜（Calm型）", p08),
    "P-09": ("大傾斜", p09), "P-10": ("隅差し（Reflectly型）", p10),
    "P-11": ("回転同調テキスト（Reflectly型）", p11), "P-12": ("2台斜め重ね（Upmind型）", p12),
    "P-13": ("単体浮遊", p13), "P-14": ("カード・カスケード（Otter型）", p14),
    "P-15": ("扇状フロート", p15), "P-16": ("ルーペ拡大", p16),
    "P-17": ("円形バッジ注釈（Otter型）", p17), "P-18": ("フローティングUIカード", p18),
    "P-19": ("手描き矢印＋集中線", p19), "P-20": ("蛍光マーカー見出し", p20),
    "P-21": ("番号ステップ", p21), "P-22": ("はみ出し図像（Finch型）", p22),
    "P-23": ("before→after（左右）", p23), "P-24": ("before→after（上下）", p24),
    "P-25": ("斜め分割2状態", p25),
    "P-26": ("横：テキスト左＋端末右", p26), "P-27": ("横：フルブリード", p27),
    "P-28": ("横：帯キャプション", p28), "P-29": ("横：before→after", p29),
    "P-30": ("横：ピクトグラム併置", p30), "P-31": ("横：傾斜端末", p31),
    "P-32": ("枚ごと色替え（3枚組）", p32), "P-33": ("パノラマ連結（3枚組）", p33),
    "P-34": ("セット漸進グラデ（3枚組・Calm型）", p34),
    "P-35": ("権威三点盛り（Upmind型）", p35), "P-36": ("機能訴求リスト＋線画（Balance型）", p36),
    "P-37": ("ブランドパネル（明朝）", p37), "P-38": ("報道ロゴ枚", p38),
    "P-39": ("見本市グリッド", p39), "P-40": ("カテゴリピクトグラム一覧", p40),
    "P-41": ("ダークモード対比", p41), "P-42": ("ブロブ地（Awarefy型）", p42),
    "P-43": ("ウィジェット／OS文脈", p43), "P-44": ("余白のみ／休符", p44),
}


def main() -> None:
    args = list(sys.argv[1:])
    if "--list" in args:
        for fam, codes in FAMILIES.items():
            print(f"\n{fam}")
            for c in codes:
                print(f"  {c}  {PATTERNS[c][0]}")
        return
    K.ensure_fonts()
    out = OUT
    if "--frame" in args:
        args.remove("--frame")
        K.FORCE_FRAME, out = True, OUT.with_name(OUT.name + "_framed")
    elif "--bare" in args:
        args.remove("--bare")
        K.FORCE_FRAME, out = False, OUT.with_name(OUT.name + "_bare")
    out.mkdir(parents=True, exist_ok=True)
    want = [a.upper() for a in args] or list(PATTERNS)
    for code in want:
        if code not in PATTERNS:
            sys.exit(f"未知の型: {code}（--list で一覧）")
        label, fn = PATTERNS[code]
        img = fn().convert("RGB")
        img.save(out / f"{code}_{label}.png")
        print(f"{code} {img.size[0]}x{img.size[1]}  {label}")


if __name__ == "__main__":
    main()
