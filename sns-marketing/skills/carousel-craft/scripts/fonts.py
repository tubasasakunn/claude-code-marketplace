#!/usr/bin/env python3
"""Download a curated set of high-impact Japanese fonts for SNS carousels.

Research is consistent: thumbnail/cover headlines win with VERY heavy gothic
(塗りの面積で視線を止める); body stays on a clean readable sans; an elegant
serif/antique adds an editorial, premium mood. Noto Sans/Serif JP (variable,
up to Black 900) are already fetched by gen.py — this adds DISPLAY weapons the
default fonts can't match, into a shared cache so any engine can opt in.

All fonts are SIL OFL (free for commercial use) from the Google Fonts repo.

  cache: carousel-craft/fonts/<file>.ttf  （このファイルの2つ上＝skill直下を __file__ から解決）
  run:   python3 fonts.py            # download all (skip if present & big enough)
         python3 fonts.py --list     # just print the catalog + usage

Engines hardcode their font paths in <repo>/post/_brand.py. To upgrade a single
app's headline, point its serif/sans path at one of these files (see DESIGN_SPEC
『タイポグラフィ』). Default engine behaviour is untouched.
"""
import argparse, json, os, sys, urllib.request

CACHE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
RAW = "https://raw.githubusercontent.com/google/fonts/main/ofl/"

# file -> (url, min_bytes, role, when-to-use)
FONTS = {
    # ── Display / cover headline weapons (heavier / punchier than Noto) ──
    "DelaGothicOne-Regular.ttf": (
        RAW + "delagothicone/DelaGothicOne-Regular.ttf", 1_000_000,
        "超極太ディスプレイ", "表紙の短いフック1〜2語を画面いっぱいに。最も視線を止める。多用は重いので表紙限定"),
    "ZenKakuGothicNew-Black.ttf": (
        RAW + "zenkakugothicnew/ZenKakuGothicNew-Black.ttf", 1_000_000,
        "極太ジオメトリックゴシック", "見出し・強調語。Notoより骨太でクリーン。情報/勉強/ガジェット系の信頼感"),
    "ZenMaruGothic-Black.ttf": (
        RAW + "zenmarugothic/ZenMaruGothic-Black.ttf", 1_000_000,
        "極太丸ゴシック", "やわらかい・親近感のある見出し(暮らし/日記/主婦層)。Hioto/Connectの温度感"),
    # ── Editorial serif / antique (premium・大人の情緒) ──
    "ZenAntique-Regular.ttf": (
        RAW + "zenantique/ZenAntique-Regular.ttf", 1_000_000,
        "アンティーク明朝", "上品・レトロな見出し/引用。美容(Tone)や情緒カバーの格を上げる"),
    "ShipporiMincho-Bold.ttf": (
        RAW + "shipporimincho/ShipporiMincho-Bold.ttf", 1_000_000,
        "太明朝", "明朝で強さが要る見出し。Noto Serifより字面が大きく写真上でも負けない"),
    # ── Body / sans alternative ──
    "Murecho[wght].ttf": (
        RAW + "murecho/Murecho%5Bwght%5D.ttf", 200_000,
        "可変モダンサンス(〜900)", "本文・キャプションのNoto代替。やや現代的で詰まりが良い"),
}


def fetch(name, url, min_bytes):
    path = os.path.join(CACHE, name)
    if os.path.exists(path) and os.path.getsize(path) >= min_bytes:
        return path, "cached"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    if len(data) < min_bytes:
        return path, f"TOO-SMALL({len(data)}b)"
    with open(path, "wb") as fp:
        fp.write(data)
    return path, f"ok({len(data)//1024}KB)"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        print(json.dumps({n: {"role": v[2], "use": v[3]} for n, v in FONTS.items()},
                         ensure_ascii=False, indent=2))
        return
    os.makedirs(CACHE, exist_ok=True)
    out = {}
    for name, (url, mb, role, _use) in FONTS.items():
        try:
            path, status = fetch(name, url, mb)
        except Exception as e:
            path, status = os.path.join(CACHE, name), f"ERR:{e}"
        out[name] = status
        print(f"  {status:14s} {role:18s} {name}")
    bad = [k for k, v in out.items() if not v.startswith(("ok", "cached"))]
    print(f"\ncache: {CACHE}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
