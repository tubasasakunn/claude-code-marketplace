#!/usr/bin/env python3
"""promo-video レンダラ（app 非依存・manifest 駆動）。

target/<app>/material/manifest.json から Brand（色/ワードマーク/アイコン/モチーフ/素材）を読み、
spec(JSON) の storyboard を carousel-craft の描画ツールキットで動画化する。
ルートは target 配下の具体を知らない＝material/manifest.json を持つ repo を置くだけで対象に。

Usage:
  render.py --app hioto                          # 既定 spec = templates/hioto.json
  render.py --app hioto path/to/spec.json        # spec を指定
  render.py --app hioto --probe                  # エンコードせず各シーン代表フレームを probe.png に
  render.py --app hioto --out /tmp/out.mp4 --raw /tmp/out_raw.mp4
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "engine"))
sys.path.insert(0, str(SKILL / "templates"))
import video as V          # noqa: E402
import importlib            # noqa: E402


def _repo_root():
    for d in Path(__file__).resolve().parents:
        if (d / "target").is_dir() and (d / "CLAUDE.md").exists():
            return d
    return Path(__file__).resolve().parents[-1]


def find_material(app_id, target):
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
    sys.exit(f"render: app '{app_id}' の material/manifest.json が target に見つからない")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("spec", nargs="?", default=None, help="storyboard spec.json（既定 templates/<app>.json）")
    ap.add_argument("--template", default="standard")
    ap.add_argument("--target", default=str(_repo_root() / "target"))
    ap.add_argument("--out", default=None, help="共有用 mp4（既定 ./<app>_promo.mp4）")
    ap.add_argument("--raw", default=None, help="高品質の生 mp4（既定 <out>.raw.mp4）")
    ap.add_argument("--crf", type=int, default=19)
    ap.add_argument("--no-share", action="store_true", help="生のみ。トランスコードしない")
    ap.add_argument("--probe", action="store_true", help="エンコードせず代表フレームを probe.png に")
    a = ap.parse_args()

    V.ensure_fonts()
    MAT = find_material(a.app, a.target)
    brand = V.B.Brand.from_manifest(MAT)

    spec_path = Path(a.spec) if a.spec else (SKILL / "templates" / f"{a.app}.json")
    if not spec_path.exists():
        sys.exit(f"render: spec が無い: {spec_path}（templates/<app>.json を作るか spec を指定）")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    w, h = spec.get("size", [1080, 1920])
    fps = spec.get("fps", 30)
    V.set_size(w, h, fps)

    tmpl = importlib.import_module(a.template)
    clips = tmpl.build_clips(spec, brand, MAT)

    out = Path(a.out) if a.out else Path.cwd() / f"{a.app}_promo.mp4"
    if a.probe:
        p = V.probe_sheet(clips, out.with_name(f"{a.app}_probe.png"))
        print("probe ->", p)
        return

    raw = Path(a.raw) if a.raw else out.with_suffix(".raw.mp4")
    print(f"rendering {a.app}: {len(clips)} scenes -> {raw}", flush=True)
    total = V.render_video(clips, str(raw), fps=fps)
    print(f"raw done: {raw}  frames={total}  ~{total/fps:.1f}s", flush=True)
    if a.no_share:
        return
    V.transcode_share(str(raw), str(out), crf=a.crf)
    sz = out.stat().st_size / 1e6
    print(f"share done: {out}  {sz:.1f}MB  (crf {a.crf})")


if __name__ == "__main__":
    main()
