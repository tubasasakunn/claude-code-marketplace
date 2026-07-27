#!/usr/bin/env python3
"""スクリーンショットの「何も無い横帯」を洗い出す。

    python3 tools/measure_bands.py <画像.png>
    python3 tools/measure_bands.py <画像.png> --min-h 24 --ratio      # 0..1 で出す
    python3 tools/measure_bands.py a.png b.png c.png --common         # 全画像に共通の帯

## 何に使うか

端末やパネルの縁を**どこに落とすか**は、これで先に決める。目分量で置くと必ず
「ボタンが半分だけ残る」「文字が途中で切れる」に当たる。

- **端末の切り口** — 下端をどこで抜くか。全画面で位置を揃えるなら `--common`
- **切り出した板の上下端** — 板は元の矩形より上下へ広がる。その縁も帯に落とす
- **つなぎの切れ目** — 縦の帯を見るときは `--axis x`

## 平坦さは輝度だけで測らない

左右いっぱいに広がる CTA ボタン（赤い塗り）は、その行の中では色が一定なので
**輝度の分散では「空き帯」と判定されてしまう**。実際にそれで板の縁をボタンに
落とし、赤いにじみが覗いた。

そこで行ごとに「輝度のばらつき」と「彩度のばらつき＋彩度の高さ」の両方を見る。
地の色から離れた行は、平坦でも帯とみなさない。
"""
import argparse
import sys

import numpy as np
from PIL import Image


def bands(path, axis='y', min_h=16, tol=6.0, sat_tol=10.0):
    """帯（何も無い連続した行/列）を [(開始, 終了), ...] で返す。"""
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
    if axis == 'x':
        a = a.transpose(1, 0, 2)

    lum = a @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    sat = a.max(axis=2) - a.min(axis=2)          # 彩度の代わり（0 = 無彩色）

    # 行ごとのばらつき。UI があると必ずどちらかが立つ。
    flat = (lum.std(axis=1) < tol) & (sat.std(axis=1) < tol)

    # 平坦でも「地の色から離れている」行は帯にしない（全幅の CTA ボタンなど）。
    base = np.median(sat[flat].mean(axis=1)) if flat.any() else 0.0
    plain = flat & (np.abs(sat.mean(axis=1) - base) < sat_tol)

    out, start = [], None
    for i, ok in enumerate(plain):
        if ok and start is None:
            start = i
        elif not ok and start is not None:
            if i - start >= min_h:
                out.append((start, i))
            start = None
    if start is not None and len(plain) - start >= min_h:
        out.append((start, len(plain)))
    return out, a.shape[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src', nargs='+')
    ap.add_argument('--axis', choices=['y', 'x'], default='y',
                    help='y=横帯（既定、切り口の探索）／x=縦帯（つなぎの切れ目）')
    ap.add_argument('--min-h', type=int, default=16, help='これより薄い帯は捨てる')
    ap.add_argument('--tol', type=float, default=6.0, help='平坦とみなすばらつきの上限')
    ap.add_argument('--ratio', action='store_true', help='px ではなく 0..1 で出す')
    ap.add_argument('--common', action='store_true',
                    help='全画像に共通する帯だけを出す（端末位置を全枚で揃えるとき）')
    args = ap.parse_args()

    per = {}
    size = None
    for p in args.src:
        b, n = bands(p, args.axis, args.min_h, args.tol)
        per[p] = b
        if size is None:
            size = n
        elif size != n:
            print(f'⚠ 画像の大きさが揃っていない（{size} と {n}）。--common は信用できない',
                  file=sys.stderr)

    def fmt(v):
        return f'{v / size:.4f}' if args.ratio else str(v)

    if args.common:
        mask = np.ones(size, dtype=bool)
        for b in per.values():
            m = np.zeros(size, dtype=bool)
            for s, e in b:
                m[s:e] = True
            mask &= m
        runs, start = [], None
        for i, ok in enumerate(mask):
            if ok and start is None:
                start = i
            elif not ok and start is not None:
                if i - start >= args.min_h:
                    runs.append((start, i))
                start = None
        if start is not None and size - start >= args.min_h:
            runs.append((start, size))
        print(f'全 {len(args.src)} 枚に共通する帯（{args.axis} 軸 / 全長 {size}）')
        if not runs:
            print('  無し。--min-h を下げるか、揃える画面を減らす')
        for s, e in runs:
            print(f'  {fmt(s)} 〜 {fmt(e)}   幅 {e - s}px')
        return

    for p, b in per.items():
        print(f'{p}  （{args.axis} 軸 / 全長 {size}）')
        for s, e in b:
            print(f'  {fmt(s)} 〜 {fmt(e)}   幅 {e - s}px')


if __name__ == '__main__':
    main()
