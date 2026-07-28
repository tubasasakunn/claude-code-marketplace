#!/usr/bin/env python3
"""Visual QA for generated SNS carousels — enforce "use the real materials".

Two checks:
  A. MATERIAL (deterministic, spec-driven, hard-fail): with --spec spec.json, every
     slide that should carry a material — cover / photo (background image) and shot
     (app screenshot) — must declare one (`bg`/`bg_options`/`shot`/`footage`). A
     cover with no bg falls back to a flat gradient/solid → exactly the look we are
     killing. Pixel heuristics can't tell a dark photo from a gradient; the spec can.
  B. VISUAL (advisory): a contact sheet per platform with the platform UI SAFE ZONE
     drawn over every slide + a density number, so a human/agent Reads ONE image and
     judges hooks, legibility and safe-zone intrusions by eye.

Exit non-zero when a hard material flag fires, so the pipeline can loop
(fix spec → regenerate → re-QA) until clean.

Deps: Pillow + numpy (already used by the engines).

Usage:
  qa.py <imgs_dir> [--spec spec.json] [--strict]
     <imgs_dir> = .../<date>/imgs  (has tiktok/ lemon8/)  OR a single platform dir.
     --spec     = the gen.py spec; enables the deterministic material check.
     --strict   = also hard-fail on safe-zone intrusions (default: advisory).
"""
import argparse, json, os, sys, glob
from PIL import Image, ImageDraw
import numpy as np

# MARK: - プラットフォームUIセーフゾーン（px・正本）
#
# ★2026-07-25 実測に基づき全面改訂。旧値(top160/bottom480/right140)は出所不明の伝承で、
#   実際より 80〜330px 小さかった＝「安全」と判定した領域が実機ではUIに隠れていた。
#
# 根拠(独立2ソースが一致):
#   1) TikTok は**セーフゾーンを公式配布している**（散文ではなく DL 可能な ZIP テンプレート。
#      だからテキスト検索では見つからない）。その公式アートワークをピクセル実測した値が
#      @1080x1920 で top=240 / bottom=660(キャプション1行で810+) / right rail=180。
#   2) Meta 公式の 9:16 セーフゾーン(上14% / 下35% / 左右6%)を px 換算すると top=269 / bottom=672。
#      → 別プラットフォームの別文書が両バンドとも約4%以内で一致。伝承ではなく実体。
#
# よって全プラットフォーム共通の安全設計値として top=270 / bottom=810 / left,right=120 /
# 右レール=180 を採る（bottom は キャプション1行ぶんを見込んだ保守側）。
#
# ⚠ 出回っている "130/483/140/44" のセットは AI-SEO の捏造。再輸入しないこと
#   （Hootsuite/Sprout が他プラットフォームの数値は公開しつつ TikTok だけ空欄にしているのが傍証）。
#
# ⚠ 安全域は**矩形ではなく L 字**: 右のアクション列(いいね/コメント/シェア)は y=840 から下にしか
#   存在しない。つまり y<840 は全幅使え、y>=840 で右 180px が死ぬ。→ rail_top。
#
# 帰結: 使えるのは y=270〜1110 ＝ **フレームの44%**。「CTAは親指の届く下中央へ」という
# 定石は TikTok では成立しない（下は丸ごとUI）。CTA は中央帯かキャプション文へ置く。
SAFE = {
    # tiktok 9:16 — フルスクリーン。UI被りが最も重い
    (1080, 1920): {"top": 270, "bottom": 810, "left": 120, "right": 180, "rail_top": 840},
    # lemon8 / instagram 3:4 — フィードは全画面でないためUI被りは軽い。グリッド用の外周だけ確保
    (1080, 1440): {"top": 130, "bottom": 173, "left": 96,  "right": 96,  "rail_top": None},
}
BLOCK, BUSY_STD = 40, 12.0
# callout は実画面が主役、scrap は貼るプリントが主役＝どちらも素材が無ければ成立しない。
# grid / panorama は型ベースのグラフィック（panorama はブランド色のグラデだけでも成立する）。
MATERIAL_TYPES = ("cover", "photo", "shot", "callout", "scrap", "bleed", "layout")


def safe_for(w, h):
    if (w, h) in SAFE:
        return SAFE[(w, h)]
    base = SAFE[(1080, 1920)] if h / w > 1.5 else SAFE[(1080, 1440)]
    return {k: (round(v * w / 1080) if isinstance(v, (int, float)) else v)
            for k, v in base.items()}


def slide_type(name):
    stem = os.path.splitext(os.path.basename(name))[0]
    return stem.split("_", 1)[1] if "_" in stem else stem


def density(lum):
    h, w = lum.shape
    ny, nx = h // BLOCK, w // BLOCK
    if not (ny and nx):
        return 0.0
    crop = lum[: ny * BLOCK, : nx * BLOCK].reshape(ny, BLOCK, nx, BLOCK)
    return float((crop.std(axis=(1, 3)) > BUSY_STD).mean())


def dead_band(lum, typ):
    """グラフィックスライド(info/cta)の『縦の死に空間（間延び/trapped whitespace）』を検出。
    行ごとのインク有無(列方向std)を取り、内部(最初〜最後のインク行の間)の最長連続空白を H 比で返す。
    実素材スライド(cover/photo/shot)はテクスチャで埋まるため対象外（誤検知回避）。→ [[SPACING]]。"""
    if typ not in ("info", "cta"):
        return 0.0
    h = lum.shape[0]
    active = lum.std(axis=1) > 8.0          # フラット背景=低std / 文字・図=高std
    idx = np.nonzero(active)[0]
    if len(idx) < 2:
        return 0.0
    interior = active[idx[0]: idx[-1] + 1]
    best = run = 0
    for a in interior:
        run = 0 if a else run + 1
        best = max(best, run)
    return round(best / h, 3)


def edge_intrusion(lum, safe):
    """各セーフ帯のインク量を全体比で返す。
    右レールは**矩形ではなくL字**＝ y>=rail_top にしか存在しないので、その範囲だけを見る。
    全高で見ると、上部の見出しが右端まで届いているだけで誤検知していた（旧実装のバグ）。"""
    h, w = lum.shape
    base = float(lum.std()) + 1e-6
    rail_top = safe.get("rail_top")
    ry = min(int(rail_top * h / 1920), h) if rail_top else 0
    strips = {"top": lum[: safe["top"], :], "bottom": lum[h - safe["bottom"]:, :],
              "left": lum[:, : safe["left"]], "right": lum[ry:, w - safe["right"]:]}
    return {k: (round(float(s.std()) / base, 2) if s.size else 0.0)
            for k, s in strips.items()}


def slide_has_material(sl):
    """Does this source slide declare a real material? cover/photo need a background
    image (bg / bg_options); shot needs a screenshot (shot). footage counts as extra."""
    t = sl.get("type")
    if t in ("cover", "photo", "layout"):
        return bool(sl.get("bg") or sl.get("bg_options"))
    if t in ("shot", "callout", "bleed"):
        return bool(sl.get("shot"))
    if t == "scrap":
        return bool(sl.get("prints"))
    return True  # info / cta / grid は型ベースのグラフィック（素材を持たない設計）


# MARK: - 文言の法令・規約ガード（spec のテキストを機械的に弾く）
#
# 実アプリ宣伝で最も実害が出やすいのはレイアウトではなく**文言**。生成前の spec 段階で潰す。
# 出所: 消費者庁「打消し表示に関する報告書」(平成30年5月16日) / 景表法 No.1表示(令和5年度 措置命令13件) /
#       薬機法の効能効果標榜 / Meta Community Standards(engagement bait)。
LEGAL_NG = {
    # 薬機法: 医薬品的な効能効果と読まれる表現。日記・記録・メンタル系アプリが直撃する
    "薬機法": ["ストレスが減", "ストレス軽減", "メンタルが整", "メンタルケア", "自己肯定感が上",
             "うつ", "不安が消", "不眠", "睡眠の質が", "治る", "改善します", "予防でき",
             "セラピー", "カウンセリング効果", "心が軽くなり", "トラウマ"],
    # 景表法: No.1・最上級。合理的根拠と、国/期間/カテゴリ/調査時点の併記が無ければ書かない。
    # 小さな注記で「イメージ調査です」と添えても治癒しないと報告書が明記している
    "景表法": ["No.1", "NO.1", "no.1", "ナンバーワン", "日本一", "世界一", "業界初",
             "唯一の", "最も効果", "必ず痩せ", "誰でも必ず", "100%"],
    # Meta: 明示的なエンゲージメント要求は降格対象。「保存する理由」とセットなら可
    "規約": ["いいねして", "いいね押して", "シェアして", "フォローして", "拡散して"],
}
# 「保存」は禁止語ではない。裸の要求だけがベイトに寄るので、理由とセットかを見る
SAVE_BAIT = ("保存してね", "保存お願い", "保存推奨", "保存必須")


def _spec_texts(spec):
    """spec 内の全ユーザー可視テキストを (slide_idx, text) で列挙。"""
    out = []
    for i, sl in enumerate(spec.get("slides", []), 1):
        for k, v in sl.items():
            if isinstance(v, str) and k not in ("type", "bg", "shot", "footage", "accent", "icon"):
                out.append((i, v))
            elif isinstance(v, list):
                for b in v:
                    t = b.get("text", "") if isinstance(b, dict) else b
                    if isinstance(t, str):
                        out.append((i, t))
    return out


def legal_flags(spec):
    """法令・規約に触れる文言を検出。生成前に spec で弾くのが最も安い。"""
    flags = {}
    for idx, text in _spec_texts(spec):
        for law, words in LEGAL_NG.items():
            for w in words:
                if w in text:
                    flags.setdefault(idx, []).append(
                        f"LEGAL:{law} — 「{w}」は使わない（{text[:24]}…）")
        for w in SAVE_BAIT:
            if w in text:
                flags.setdefault(idx, []).append(
                    f"BAIT — 「{w}」は裸の要求。『次に〇〇する時のために保存』と理由を添える")
    return {k: " / ".join(v) for k, v in flags.items()}


def material_flags(spec):
    """Per-slide deterministic flags from the source spec (1-indexed to match NN_)."""
    flags = {}
    for i, sl in enumerate(spec.get("slides", []), 1):
        t = sl.get("type")
        if t in MATERIAL_TYPES and not slide_has_material(sl):
            need = {"shot": "shot(実app画面)", "callout": "shot(実app画面)",
                    "bleed": "shot(実app画面)",
                    "scrap": "prints[](貼るプリント)"}.get(t, "bg(実写真/実画面/素材バンク)")
            flags[i] = f"NO-MATERIAL:{t} — {need} を指定（フラット背景を排除）"
        elif t in ("cover", "photo") and not sl.get("footage") and t == "shot":
            pass
    # nudge: shot slides without footage are fine, but cover/photo with bg is the win
    return flags


def analyse(path, spec_flag=None):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    lum = np.asarray(im.convert("L"), dtype=np.float32)
    safe = safe_for(w, h)
    typ = slide_type(path)
    intr = edge_intrusion(lum, safe)
    flags = []
    if spec_flag:
        flags.append(spec_flag)
    if intr["right"] > 0.85:
        flags.append(f"RIGHT-RAIL({intr['right']}) — 右{safe['right']}pxに文字を置かない")
    if intr["bottom"] > 1.15:
        flags.append(f"BOTTOM-UI({intr['bottom']}) — 下{safe['bottom']}pxはUI被り")
    dead = dead_band(lum, typ)
    if dead > 0.20:
        flags.append(f"DEAD-BAND({dead}) — 縦に死に空間/間延び。要素を等間隔で中央寄せ([[SPACING]])")
    return {"file": os.path.basename(path), "type": typ, "size": [w, h],
            "coverage": round(density(lum), 3), "edges": intr, "dead_band": dead,
            "flags": flags, "hard": bool(spec_flag)}


def contact_sheet(paths, reports, out_png):
    if not paths:
        return
    tw = 300
    ims = []
    for p, r in zip(paths, reports):
        im = Image.open(p).convert("RGB")
        w, h = im.size
        im = im.resize((tw, round(tw * h / w)))
        th = im.height
        d = ImageDraw.Draw(im, "RGBA")
        sa = safe_for(w, h); sc = tw / w
        bad = bool(r["flags"])
        col = (255, 60, 60, 255) if bad else (80, 220, 120, 255)
        d.rectangle([sa["left"] * sc, sa["top"] * sc,
                     tw - sa["right"] * sc, th - sa["bottom"] * sc], outline=col, width=3)
        d.rectangle([0, 0, tw - 1, th - 1], outline=col, width=4)
        d.rectangle([0, 0, tw, 30], fill=(0, 0, 0, 170))
        d.text((6, 6), f"{r['file']}  cov={r['coverage']}", fill=(255, 255, 255))
        if bad:
            d.text((6, th - 22), "FLAGGED", fill=(255, 150, 150))
        ims.append(im)
    H = max(i.height for i in ims)
    sheet = Image.new("RGB", (sum(i.width for i in ims) + 10 * (len(ims) + 1), H + 20),
                      (28, 28, 30))
    x = 10
    for i in ims:
        sheet.paste(i, (x, 10)); x += i.width + 10
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    sheet.save(out_png)


def run_platform(pdir, platform, spec_flags):
    paths = sorted(glob.glob(os.path.join(pdir, "[0-9]*_*.png")))
    if not paths:
        return None
    reports = []
    for p in paths:
        idx = int(os.path.basename(p).split("_", 1)[0])
        reports.append(analyse(p, spec_flags.get(idx)))
    out_png = os.path.join(os.path.dirname(pdir.rstrip("/")), "_qa",
                           f"{platform}_contact.png")
    contact_sheet(paths, reports, out_png)
    return {"platform": platform, "dir": pdir, "slides": len(paths),
            "contact_sheet": out_png,
            "flagged": sum(1 for r in reports if r["flags"]),
            "hard_flags": sum(1 for r in reports if r["hard"]), "reports": reports}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("imgs_dir")
    ap.add_argument("--spec", help="gen.py spec.json — enables material check")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()

    spec_flags = {}
    if a.spec and os.path.exists(a.spec):
        spec = json.load(open(a.spec, encoding="utf-8"))
        spec_flags = material_flags(spec)
        for idx, msg in legal_flags(spec).items():   # 法令・規約は素材と同じく hard fail
            spec_flags[idx] = f"{spec_flags[idx]} / {msg}" if idx in spec_flags else msg
        n_slides = len(spec.get("slides", []))
        if 4 <= n_slides <= 5:                       # 実測: 4–5枚が最も弱い谷
            print(f"⚠️  SLIDE-COUNT({n_slides}) — 4〜5枚は実測で最弱の谷。"
                  f"3枚に絞るか6〜9枚まで積む（[[PATTERNS]] §4）", file=sys.stderr)

    results = []
    subs = [d for d in ("tiktok", "lemon8") if os.path.isdir(os.path.join(a.imgs_dir, d))]
    if subs:
        for plat in subs:
            r = run_platform(os.path.join(a.imgs_dir, plat), plat, spec_flags)
            if r:
                results.append(r)
    else:
        plat = os.path.basename(a.imgs_dir.rstrip("/")) or "slides"
        r = run_platform(a.imgs_dir, plat, spec_flags)
        if r:
            results.append(r)

    hard = sum(r["hard_flags"] for r in results)
    soft = sum(r["flagged"] for r in results) - hard
    print(json.dumps({
        "ok": (hard == 0) and (not a.strict or soft == 0),
        "hard_flags": hard, "soft_flags": soft,
        "note": "hard=素材未使用(spec必須)。soft=セーフゾーン侵犯(目視)。"
                "コンタクトシートを Read してフック/可読性/被りを確認。"
                + ("" if a.spec else "  ※--spec 未指定: 素材チェックは skip。"),
        "platforms": results}, ensure_ascii=False, indent=2))
    sys.exit(1 if (hard > 0 or (a.strict and soft > 0)) else 0)


if __name__ == "__main__":
    main()
