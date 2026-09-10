#!/usr/bin/env python3
"""promo-video QA：客観チェック＋目視用シート。**数値で満足せず raw を等倍で見る**前提の補助。

  qa.py --app hioto sheet                       # 各シーン代表フレームのコンタクトシート
  qa.py --app hioto strip --scene 2 --around 40 # 指定シーンの連続フレーム（フリーズ/カクつき確認）
  qa.py --app hioto check out.mp4               # 尺/解像度/fps/ビットレートを表示

strip は「クロスフェード中に映像が止まっていないか」を連続フレームで目視するためのもの
（day_cycle のカクつきはこれで発見・修正した）。--scene は spec の 0 始まり index。
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(SKILL / "engine"))
sys.path.insert(0, str(SKILL / "templates"))
import video as V          # noqa: E402
import importlib            # noqa: E402
from render import find_material, _repo_root   # noqa: E402


def _load(app, spec_arg, template, target):
    V.ensure_fonts()
    MAT = find_material(app, target)
    brand = V.B.Brand.from_manifest(MAT)
    spec_path = Path(spec_arg) if spec_arg else (SKILL / "templates" / f"{app}.json")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    w, h = spec.get("size", [1080, 1920]); V.set_size(w, h, spec.get("fps", 30))
    clips = importlib.import_module(template).build_clips(spec, brand, MAT)
    return clips


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("mode", choices=["sheet", "strip", "check"])
    ap.add_argument("file", nargs="?", default=None, help="check 用 mp4")
    ap.add_argument("--spec", default=None)
    ap.add_argument("--template", default="standard")
    ap.add_argument("--target", default=str(_repo_root() / "target"))
    ap.add_argument("--scene", type=int, default=0)
    ap.add_argument("--around", type=int, default=None, help="strip の中心フレーム（既定=シーン中央）")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.mode == "check":
        f = a.file or f"{a.app}_promo.mp4"
        subprocess.run([V.ffmpeg_exe(), "-i", f, "-hide_banner"])
        return

    clips = _load(a.app, a.spec, a.template, a.target)
    if a.mode == "sheet":
        out = a.out or f"{a.app}_probe.png"
        print("sheet ->", V.probe_sheet(clips, out))
    else:  # strip
        cl = clips[a.scene]
        ctr = a.around if a.around is not None else cl.n // 2
        frames = [max(0, min(cl.n - 1, ctr + d)) for d in (-4, -2, 0, 2, 4, 6)]
        out = a.out or f"{a.app}_strip_s{a.scene}.png"
        print("strip ->", V.strip_consecutive(cl, frames, out))


if __name__ == "__main__":
    main()
