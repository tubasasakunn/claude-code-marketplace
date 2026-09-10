#!/usr/bin/env python3
"""Render ONE carousel post for a *swift-base template* app (e.g. Tone /
mensmakeupadvisor) into an arbitrary output dir, reusing the repo's engine
(post/_brand.py + post/build_posts.py) WITHOUT polluting the repo.

Differs from the Hioto generator: the swift-base engine has a different API
  - RENDERERS[type](size, spec, accent, idx, total)
  - PLATFORMS[platform] = {"size": (w,h), "safe_bottom": ...}
  - brand/wordmark/accents come from <repo>/appstore.config.json (read by _brand)
  - cover/photo use footage_or_solid(): missing footage -> solid brand-accent bg
  - shot uses material/<shot> (real app screenshot), green-keyed only if footage given

Spec JSON:
{
  "id": "tone-001",
  "accent": "evening",                  # ACCENTS key from appstore.config brand
  "slides": [ { "type": "cover"|"photo"|"shot"|"info"|"cta", ... } ],
      # same shape as build_posts.POSTS[...]["slides"]
      #   cover: bg(footage key or omit->solid), kicker, headline
      #   photo: bg, caption, note?
      #   shot : shot("05_diagnosis_top.png" in material/), title, sub, footage?
      #   info : kicker?, title, bullets[3]
      #   cta  : headline, sub
  "copy": { "tiktok": {title,body,hashtags[]}, "lemon8": {title,body,hashtags[]} }
}

Usage: gen_post_swiftbase.py <spec.json> <outdir> --repo <path-to-app-repo>
Writes <outdir>/{tiktok,lemon8}/NN_type.png + index.json
"""
import argparse, json, os, sys, importlib.util, urllib.request
from pathlib import Path


def _repo_root():
    """リポジトリルート（target/ と CLAUDE.md を持つ階層）を __file__ から探す。絶対パス直書きをしない。"""
    for d in Path(__file__).resolve().parents:
        if (d / "target").is_dir() and (d / "CLAUDE.md").exists():
            return d
    return Path(__file__).resolve().parents[-1]


def ensure_fonts(repo):
    cfg = json.load(open(os.path.join(repo, "appstore.config.json")))
    urls = {"/tmp/NotoSansJP.ttf": cfg["fonts"]["jp_sans_url"],
            "/tmp/NotoSerifJP.ttf": cfg["fonts"]["jp_serif_url"]}
    for path, url in urls.items():
        if not os.path.exists(path) or os.path.getsize(path) < 100000:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
                f.write(r.read())

def load_engine(repo):
    post_dir = os.path.join(repo, "post")
    if post_dir not in sys.path:
        sys.path.insert(0, post_dir)
    spec = importlib.util.spec_from_file_location("build_posts", os.path.join(post_dir, "build_posts.py"))
    bp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bp)
    return bp

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("outdir")
    ap.add_argument("--repo", default=str(_repo_root() / "target" / "mensmakeupadvisor"))
    a = ap.parse_args()

    ensure_fonts(a.repo)
    bp = load_engine(a.repo)
    spec = json.load(open(a.spec, encoding="utf-8"))
    accent_name = spec.get("accent", "evening")
    slides = spec["slides"]
    total = len(slides)

    for platform, plat in bp.PLATFORMS.items():
        out = os.path.join(a.outdir, platform)
        os.makedirs(out, exist_ok=True)
        bp._CURRENT.clear(); bp._CURRENT.update(plat)      # renderers read platform cfg
        size = plat["size"]
        names = []
        for i, sl in enumerate(slides, 1):
            accent = bp.B.ACCENTS[sl.get("accent", accent_name)]
            img = bp.RENDERERS[sl["type"]](size, sl, accent, i, total).convert("RGB")
            name = f"{i:02d}_{sl['type']}.png"
            img.save(os.path.join(out, name)); names.append(name)
        cp = spec.get("copy", {}).get(platform, {})
        idx = {"post": spec.get("id", os.path.basename(a.outdir.rstrip("/"))),
               "platform": platform, "size": f"{size[0]}x{size[1]}",
               "title": cp.get("title", ""), "body": cp.get("body", ""),
               "hashtags": cp.get("hashtags", []), "images": names}
        with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as f:
            json.dump(idx, f, ensure_ascii=False, indent=2)
        print(f"  {platform}: {total} slides -> {out}")
    print("done")

if __name__ == "__main__":
    main()
