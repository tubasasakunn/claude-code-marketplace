#!/usr/bin/env python3
"""App-agnostic carousel generator.

target/<app>/material/manifest.json から Brand（色・ワードマーク・アイコン・素材）を読み、
carousel-craft の共通ツールキット（engine/brand.py）＋雛形（templates/<t>.py）で
TikTok(1080x1920)/Lemon8(1080x1440) のカルーセル画像を生成する。

ルートは target 配下の具体を知らない＝target/ に material/manifest.json を持つ repo を
置くだけで対象に加わる。エンジンコードは repo 側に持たない（毎回 root の雛形から組む）。

Spec JSON: { id, accent, template?, slides[], copy:{tiktok,lemon8:{title,body,hashtags}} }
  slides は雛形のレンダラが読む形（standard: cover/photo/shot/info/cta）。

Usage: gen.py --app <id> <spec.json> <outdir> [--template standard] [--target <dir>]
"""
import argparse, json, os, sys, importlib.util, urllib.request
from pathlib import Path


from appmeta import ROOT as _REPO_ROOT   # ルート解決は appmeta.py が唯一の正本（SNS_ROOT 対応）

# carousel-craft 側（templates/standard.py）は appmeta を持たないので、解決済みのルートを
# 環境変数で渡す。これが無いと plugin cache から動かしたとき bg が引けず全スライドが無地になる。
os.environ.setdefault("SNS_ROOT", str(_REPO_ROOT))

# carousel-craft は同じ skills/ の兄弟（このファイルから2つ上が skills/）。移設しても不変。
CC = Path(__file__).resolve().parents[2] / "carousel-craft"
DEFAULT_TARGET = _REPO_ROOT / "target"
SIZES = {"tiktok": (1080, 1920), "lemon8": (1080, 1440)}

# 共通フォント（/tmp に用意）。path -> (url, min_bytes)
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


def find_material(app_id, target):
    """target/*/material/manifest.json を走査し、id か dir名が一致する material/ を返す。"""
    target = Path(target)
    direct = target / app_id / "material"
    if (direct / "manifest.json").exists():
        return direct
    for mani in target.glob("*/material/manifest.json"):
        try:
            if json.loads(mani.read_text(encoding="utf-8")).get("id") == app_id:
                return mani.parent
        except Exception:
            continue
    sys.exit(f"gen: app '{app_id}' の material/manifest.json が target に見つからない")


def load_template(name):
    path = CC / "templates" / f"{name}.py"
    if not path.exists():
        sys.exit(f"gen: 雛形 templates/{name}.py が無い")
    spec = importlib.util.spec_from_file_location(f"tmpl_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("spec")
    ap.add_argument("outdir")
    ap.add_argument("--template", default=None)
    ap.add_argument("--target", default=str(DEFAULT_TARGET))
    ap.add_argument("--allow-flat", action="store_true",
                    help="cover/photo の bg(実素材) 省略を許可（素材ファースト違反を承知で）")
    a = ap.parse_args()

    ensure_fonts()
    sys.path.insert(0, str(CC / "engine"))
    import brand as B  # noqa: E402

    material = find_material(a.app, a.target)
    brand = B.Brand.from_manifest(material)
    spec = json.load(open(a.spec, encoding="utf-8"))
    template = a.template or spec.get("template", "standard")
    tmpl = load_template(template)

    accent_name = spec.get("accent", next(iter(brand.accents)))
    slides = spec["slides"]
    total = len(slides)
    # 素材ファーストの強制: cover/photo は実素材 bg 必須（灰色/ベタ背景を素通りさせない）。
    flat = [i for i, sl in enumerate(slides, 1)
            if sl.get("type") in ("cover", "photo") and not (sl.get("bg") or sl.get("bg_options"))]
    if flat and not a.allow_flat:
        sys.exit(f"gen: 素材ファースト違反 — cover/photo に bg(実素材) が無い slide {flat}。"
                 f"ルート素材バンクの repo相対パス(material/images/<name>.jpg)を bg に指定するか、承知の上なら --allow-flat。")
    for platform, (W, H) in SIZES.items():
        out = os.path.join(a.outdir, platform)
        os.makedirs(out, exist_ok=True)
        names = []
        for i, sl in enumerate(slides, 1):
            s = {**sl, "accent": sl.get("accent", accent_name), "idx": i, "total": total}
            img = tmpl.RENDERERS[s["type"]](s, W, H, brand).convert("RGB")
            n = f"{i:02d}_{s['type']}.png"
            img.save(os.path.join(out, n))
            names.append(n)
        cp = spec.get("copy", {}).get(platform, {})
        idx = {"post": spec.get("id", os.path.basename(a.outdir.rstrip("/"))),
               "platform": platform, "size": f"{W}x{H}",
               "title": cp.get("title", ""), "body": cp.get("body", ""),
               "hashtags": cp.get("hashtags", []), "images": names}
        json.dump(idx, open(os.path.join(out, "index.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        warn = "" if (cp.get("title") or cp.get("body") or cp.get("hashtags")) else \
            "  ⚠️ 文言/タグ空: spec に copy:{%s:{title,body,hashtags}} を入れる（投稿キャプションに使う）" % platform
        print(f"  [{a.app}/{template}] {platform}: {len(names)} slides -> {out}{warn}")
    print("done")


if __name__ == "__main__":
    main()
