#!/usr/bin/env python3
"""直近投稿の**サムネ（表紙）**を並べ、次に使うべき treat を出す。

なぜ要るか: 表紙は全員が見る唯一のスライドで、フィードでの見え方は
`variant`（文字組）ではなく **`treat`（写真の扱い）** でほぼ決まる。
2026-08-02 まで treat という軸自体が無く、28投稿すべての表紙が
「暗い写真＋白文字」だった。企画（spec を書く前）にこれを叩いて、
**直近と違う treat を選ぶ**。書いたあとの検算は qa.py の COVER-REPEAT。

Usage:
  cover_history.py <posts_dir>            # 例: marketing/anki_posts
  cover_history.py <posts_dir> -n 12
  cover_history.py <posts_dir> --json     # パイプライン用
"""
import argparse, glob, json, os, sys

# 表紙の見え方の全カード。standard.py の COVER_TREATS ＋ 自前で紙パネルを敷く variant=card。
ALL_KEYS = ("dark", "light", "duotone", "paper", "frame", "band", "edge", "card")
LOOKBACK = 3          # qa.py の COVER_LOOKBACK と揃える


def cover_key(sl):
    return "card" if sl.get("variant") == "card" else sl.get("treat", "dark")


def scan(posts_dir, limit):
    rows = []
    for p in sorted(glob.glob(os.path.join(posts_dir, "*", "spec.json")), reverse=True):
        try:
            spec = json.load(open(p, encoding="utf-8"))
        except Exception:
            continue
        for sl in spec.get("slides", []):
            if sl.get("type") == "cover":
                rows.append({"post": os.path.basename(os.path.dirname(p)),
                             "variant": sl.get("variant", "editorial"),
                             "treat": cover_key(sl),
                             "bg": os.path.basename(sl.get("bg", "")) or "-"})
                break
        if len(rows) >= limit:
            break
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("posts_dir")
    ap.add_argument("-n", type=int, default=8)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(a.posts_dir):
        sys.exit(f"cover_history: {a.posts_dir} が無い")

    rows = scan(a.posts_dir, a.n)
    recent = [r["treat"] for r in rows[:LOOKBACK]]
    fresh = [k for k in ALL_KEYS if k not in recent]
    used = {}
    for r in rows:
        used[r["treat"]] = used.get(r["treat"], 0) + 1
    never = [k for k in ALL_KEYS if k not in used]

    if a.json:
        print(json.dumps({"recent": rows, "blocked": recent, "available": fresh,
                          "never_used": never}, ensure_ascii=False, indent=2))
        return

    print(f"直近の表紙（{os.path.basename(a.posts_dir.rstrip('/'))}・新しい順）")
    print(f"{'post':<10} {'treat':<9} {'variant':<10} bg")
    for r in rows:
        print(f"{r['post']:<10} {r['treat']:<9} {r['variant']:<10} {r['bg']}")
    print()
    print(f"使用回数: " + "  ".join(f"{k}={used.get(k, 0)}" for k in ALL_KEYS))
    print(f"★直近{LOOKBACK}投稿で使用済み（選ぶな）: {'/'.join(recent) or '-'}")
    print(f"★選べる treat: {'/'.join(fresh)}")
    if never:
        print(f"★一度も使っていない: {'/'.join(never)}  ← ここから選ぶのが最優先")
    print("\n表紙の写真も直近と被らせない（qa.py が COVER-REPEAT:bg で弾く）")


if __name__ == "__main__":
    main()
