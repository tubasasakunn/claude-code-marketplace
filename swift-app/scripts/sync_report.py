#!/usr/bin/env python3
"""swift-base の雛形資産が各アプリでどれだけズレているかを表にする。

使い方:
    python3 sync_report.py --base <swift-base> --apps <apps dir> [--resultkit <ResultKit dir>]
    python3 sync_report.py --base ... --apps ... --only ci_post_clone   # 1資産だけ
    python3 sync_report.py --base ... --apps ... --diff <app> <asset>   # 実差分を見る

記号: =  正本と同一 / !=  差分あり / -  そのアプリに無い
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

# 正本（swift-base）からの相対パス。glob 可。
FILE_ASSETS = [
    ".claude/rules/*.md",
    ".github/workflows/*.yml",
    "fastlane/Fastfile",
    "ci_scripts/ci_post_clone.sh",
    "scripts/*.py",
    "scripts/*.sh",
]
# ディレクトリ単位で見るもの（中のファイル数と差分数を数える）
DIR_ASSETS = ["post"]


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def collect_assets(base: Path) -> list[str]:
    out = []
    for pat in FILE_ASSETS:
        if "*" in pat:
            parent, name = pat.rsplit("/", 1)
            out.extend(
                f"{parent}/{f.name}" for f in sorted((base / parent).glob(name))
            )
        elif (base / pat).is_file():
            out.append(pat)
    return out


def app_dirs(apps: Path) -> list[Path]:
    return [d for d in sorted(apps.iterdir()) if d.is_dir() and not d.name.startswith(".")]


def dir_state(base_dir: Path, app_dir: Path) -> str:
    """ディレクトリ資産の状態。中のファイルを比べて差分数を返す。"""
    if not app_dir.is_dir():
        return "-"
    diff = 0
    total = 0
    for f in sorted(base_dir.rglob("*")):
        if not f.is_file() or "__pycache__" in f.parts or f.name == ".DS_Store":
            continue
        total += 1
        counterpart = app_dir / f.relative_to(base_dir)
        if not counterpart.is_file() or md5(counterpart) != md5(f):
            diff += 1
    return "=" if diff == 0 else f"!={diff}/{total}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, type=Path, help="swift-base のパス")
    ap.add_argument("--apps", required=True, type=Path, help="アプリを並べたディレクトリ")
    ap.add_argument("--resultkit", type=Path, help="ResultKit 正本のパス（図鑑アプリ向け）")
    ap.add_argument("--only", help="資産名の部分一致で絞る")
    ap.add_argument("--diff", nargs=2, metavar=("APP", "ASSET"), help="実差分を表示して終了")
    args = ap.parse_args()

    base = args.base.expanduser().resolve()
    apps = args.apps.expanduser().resolve()

    if args.diff:
        app, asset = args.diff
        a, b = base / asset, apps / app / asset
        if not b.is_file():
            print(f"{app} に {asset} は無い")
            return 1
        subprocess.run(["diff", "-u", str(a), str(b)])
        return 0

    assets = collect_assets(base)
    if args.only:
        assets = [a for a in assets if args.only in a]
    targets = app_dirs(apps)

    # 資産 × アプリのマトリクス
    rows = []
    for asset in assets:
        src = base / asset
        h = md5(src)
        cells = []
        for app in targets:
            f = app / asset
            if not f.is_file():
                cells.append("-")
            else:
                cells.append("=" if md5(f) == h else "!=")
        rows.append((asset, cells))
    for d in DIR_ASSETS:
        if (base / d).is_dir():
            rows.append((d + "/", [dir_state(base / d, app / d) for app in targets]))
    if args.resultkit:
        rk = args.resultkit.expanduser().resolve()
        cells = []
        for app in targets:
            # <app>/<AppName>/ResultKit/ を探す（AppName はアプリごとに違う）
            found = next((p for p in app.glob("*/ResultKit") if p.is_dir()), None)
            cells.append(dir_state(rk, found) if found else "-")
        rows.append(("ResultKit/", cells))

    # 出力（Markdown 表）
    width = max(len(a) for a, _ in rows) + 1
    print(f"# swift-base 同期レポート\n")
    print(f"正本: `{base}`  対象: {len(targets)} アプリ\n")
    print("記号: `=` 同一 / `!=` 差分 / `-` 欠落\n")
    hdr = "| " + "資産".ljust(width) + " | " + " | ".join(a.name for a in targets) + " |"
    print(hdr)
    print("|" + "---|" * (len(targets) + 1))
    for asset, cells in rows:
        print("| " + asset.ljust(width) + " | " + " | ".join(cells) + " |")

    print("\n## サマリ（要対処の多い順）\n")
    print("| 資産 | 同一 | 差分 | 欠落 | 差分のあるアプリ |")
    print("|---|---|---|---|---|")
    summary = []
    for asset, cells in rows:
        same = sum(1 for c in cells if c == "=")
        diff = sum(1 for c in cells if c.startswith("!="))
        miss = sum(1 for c in cells if c == "-")
        who = " ".join(a.name for a, c in zip(targets, cells) if c.startswith("!="))
        summary.append((diff + miss, asset, same, diff, miss, who))
    for _, asset, same, diff, miss, who in sorted(summary, reverse=True):
        print(f"| {asset} | {same} | {diff} | {miss} | {who} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
