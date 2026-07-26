#!/usr/bin/env python3
"""スクリーンショットから、飛び出させたいカードの矩形を測る。

    python3 tools/measure_cards.py apps/hioto/material/note/04_calendar.png

明るい面（カード）が背景より白いことを利用して、行ごとの「ほぼ白」の割合から
帯を拾い、その帯の中で白い列の範囲を見る。出た数字はそのまま content.js の
`breakouts[].rect` に貼れる。

注意: 白の割合だけで切ると、カード下部の細い文字が並ぶ行で判定が落ち、**カードの
下端が実際より上に出る**。飛び出させたときに文字が切れるので、出た値はカードの
下端まで少し広げてから使う（04_calendar.png では y の終わりが 988 と出るが、
実際のカードは 1030 まである）。
"""
import argparse

import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('--white', type=int, default=246, help='「ほぼ白」とみなす下限（既定 246）')
    ap.add_argument('--row', type=float, default=0.55, help='帯とみなす行の白率（既定 0.55）')
    ap.add_argument('--min-h', type=int, default=40, help='これより低い帯は捨てる（既定 40）')
    args = ap.parse_args()

    a = np.array(Image.open(args.src).convert('RGB')).astype(int)
    h, w, _ = a.shape
    near_white = (a > args.white).all(axis=2)
    on = near_white.mean(axis=1) > args.row

    print(f'{args.src}  {w}×{h}')
    runs, start = [], None
    for y in range(h):
        if on[y] and start is None:
            start = y
        elif not on[y] and start is not None:
            if y - start >= args.min_h:
                runs.append((start, y))
            start = None
    if start is not None and h - start >= args.min_h:
        runs.append((start, h))

    if not runs:
        print('  カードらしい帯が見つからない。--row を下げてみる')
        return

    for y0, y1 in runs:
        cols = np.where(near_white[y0:y1].mean(axis=0) > 0.5)[0]
        if not len(cols):
            continue
        x0, x1 = int(cols[0]), int(cols[-1])
        print(f'  rect: [{x0}, {y0}, {x1 - x0}, {y1 - y0}],')


if __name__ == '__main__':
    main()
