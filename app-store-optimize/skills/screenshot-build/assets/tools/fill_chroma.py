#!/usr/bin/env python3
"""スクリーンショットのクロマキー領域に、別の画像を流し込む。

    python3 tools/fill_chroma.py <スクショ.png> <差し込む画像> -o <出力.png>
    python3 tools/fill_chroma.py shorts-feed.png footage/shorts.jpg -o screens/shorts.png

## なぜ要るか

動画・カメラを扱うアプリは、シミュレータで実際の映像を撮れない。そこでデモ用の
スクリーンショットでは映像領域を**単色で塗って**書き出しておき、あとから素材を
流し込む運用になっていることがある（swift-base 系は純緑 #00FF00）。

原寸のスクリーンショットが単色だからといって、LP 用に縮小した完成版を使うと
端末モックの画面に引き伸ばしたとき UI の細線が潰れる。**原寸のまま中身を入れる**
のが正解で、そのための道具。

## 半透明の UI を潰さない

素朴にマスクで置き換えると、単色の上に乗っている半透明の UI（シャッターリング、
タブバー、フォーカスの照準など）が一緒に消える。

そこで置き換えではなく**アンコンポジット**する。単色の残り具合から背景の寄与率を
求め、その分だけ引いてから素材を足す。

    bg  = clip((G - max(R,B)) / 255, 0, 1)     背景（単色）の寄与率 ≒ 1-α
    out = (C - bg * key) + bg * scene

`bg=1`（純粋な単色）なら丸ごと素材に、`bg=0`（不透明な UI）ならそのまま、
半透明ならその割合だけ差し替わる。
"""
import argparse
import pathlib
import sys

import numpy as np
from PIL import Image


# クロマキーは「純色」であることが前提。チャンネル差がこれ未満の色は、
# UI に使われている普通の色（グラフの青など）とみなして拾わない。
# 60 まで緩めたら、緑が 1 つも無い画面でグラフの青 #5C7CA4 を拾って
# 2.9% を書き換えてしまった。
PURE = 150


def detect_key(rgb):
    """塗りつぶしに使われている純色を推定する。見つからなければ None。"""
    q = (rgb.reshape(-1, 3) // 8).astype(np.int32)
    keys = q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]
    vals, cnt = np.unique(keys, return_counts=True)
    for i in np.argsort(-cnt):
        k = int(vals[i])
        c = np.array([(k // 1024) % 32, (k // 32) % 32, k % 32]) * 8 + 4
        if int(c.max()) - int(c.min()) >= PURE:
            return c.astype(np.float32)
    return None


def coverage(rgb, key):
    """各画素で「単色がどれだけ残っているか」を 0..1 で返す。

    支配チャンネル（緑なら G）が他をどれだけ上回るかで見る。純色との距離で測ると、
    上に半透明の白が乗った箇所で急に 0 になってしまう。
    """
    ch = int(np.argmax(key))
    others = [i for i in range(3) if i != ch]
    strength = rgb[..., ch] - np.maximum(rgb[..., others[0]], rgb[..., others[1]])
    ref = float(key[ch] - max(key[others[0]], key[others[1]]))
    return np.clip(strength / max(ref, 1.0), 0.0, 1.0)


def fmt_key(key):
    return 'key #%02X%02X%02X' % tuple(int(v) for v in key)


def fill_crop(img, size):
    """アスペクトフィルで中央クロップ。"""
    w, h = size
    scale = max(w / img.width, h / img.height)
    im = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x0, y0 = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x0, y0, x0 + w, y0 + h))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('shot', help='クロマキー領域を含むスクリーンショット')
    ap.add_argument('scene', help='流し込む画像')
    ap.add_argument('-o', '--out', required=True)
    ap.add_argument('--key', help='塗りつぶしの色（例: 00FF00）。既定は自動判定')
    ap.add_argument('--floor', type=float, default=0.10,
                    help='これ以下の寄与率は 0 に丸める。UI のわずかな色かぶりを守る（既定 0.10）')
    ap.add_argument('--min-area', type=float, default=0.5,
                    help='塗りつぶし領域がこの%%未満なら対象外とみなす（既定 0.5）')
    args = ap.parse_args()

    shot = Image.open(args.shot).convert('RGB')
    rgb = np.asarray(shot).astype(np.float32)

    key = (np.array([int(args.key.lstrip('#')[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)
           if args.key else detect_key(np.asarray(shot)))
    if key is None:
        print(f'{args.shot}: クロマキー領域が無い。この画面は原寸のまま使える', file=sys.stderr)
        sys.exit(2)

    bg = coverage(rgb, key)
    bg[bg < args.floor] = 0.0
    if bg.max() <= 0:
        print(f'{args.shot}: 塗りつぶし領域が見つからない。--key で色を指定する', file=sys.stderr)
        sys.exit(2)

    # 純度だけでは分離しきれない。アイコンのオレンジ #FCAC1C（差 224）のような色は
    # 純色判定を通ってしまうので、**占める面積**でも切る。クロマキーは画面の一部を
    # まとまって占めるが、アイコンは散在するので率が桁違いに低い
    # （実測: 緑のサムネイル 1.9% に対し、誤検知したアイコン 0.2%）。
    area = float((bg > 0.5).mean()) * 100
    if not args.key and area < args.min_area:
        print(f'{args.shot}: クロマキー領域が無い（{fmt_key(key)} が {area:.2f}% だけ）。'
              f'この画面は原寸のまま使える', file=sys.stderr)
        sys.exit(2)

    scene = np.asarray(fill_crop(Image.open(args.scene).convert('RGB'), shot.size)).astype(np.float32)

    a = bg[..., None]
    out = np.clip((rgb - a * key) + a * scene, 0, 255).astype(np.uint8)

    dst = pathlib.Path(args.out)
    dst.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(dst)

    print(f'{dst}  {shot.width}×{shot.height}  {fmt_key(key)}  差し替え {area:.1f}%')


if __name__ == '__main__':
    main()
