#!/usr/bin/env python3
"""端末モックアップ PNG（画面が単色で塗られたもの）を、テンプレートで使える形に変換する。

    python3 tools/prep_mockup.py <入力.png> <出力名> [--debug]

やること:

  1. 画面の単色をアルファに落として「フレームだけ」の PNG を作る
  2. 抜いた境界に残る色かぶりを削る（デスピル）
  3. 画面領域の**四隅**を検出して JSON に書く

四隅は、角丸を無視した「元の長方形としての角」を出す。マスクの凸包から主要な 4 辺を
拾って直線を当て、その交点を取っているため。この 4 点にスクリーンショットを射影変換
（CSS の matrix3d）すれば、フレームの画面にぴったり収まる。

Canva 等で作ったモックアップなら、画面を単色で塗りつぶして PNG 書き出しするだけでよい。
色は自動で判定するので #00FF00 である必要はない（オリーブ緑でも通る）。
"""
import argparse
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw


# ── 画面の単色を拾う ────────────────────────────────────────

def detect_key(rgb, alpha):
    """画面を塗っている色を推定する。

    不透明画素の最頻色のうち、最初に見つかる「彩度のある色」を採る。グレー・黒・白は
    フレーム側の色なので飛ばす。緑と決め打たないので、Canva 側を何色で塗っても通る。
    """
    m = alpha > 200
    if not m.any():
        sys.exit('不透明な画素が無い')
    q = (rgb[m] // 8).astype(np.int32)
    keys = q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]
    vals, cnt = np.unique(keys, return_counts=True)
    for i in np.argsort(-cnt):
        k = int(vals[i])
        c = np.array([(k // 1024) % 32, (k // 32) % 32, k % 32]) * 8 + 4
        if int(c.max()) - int(c.min()) > 40:      # 彩度がある = 画面の塗り
            return c.astype(np.int16)
    sys.exit('画面の塗り色を判別できない。--key RRGGBB で指定する')


def screen_mask(rgb, key, lo=40, hi=110):
    """画面色との距離を 0..1 の抜き量に変換する。lo 以下は完全に抜く。"""
    d = np.linalg.norm(rgb.astype(np.float32) - key.astype(np.float32), axis=-1)
    return np.clip((hi - d) / (hi - lo), 0, 1)


def despill(rgb, soft, key):
    """抜いた縁に残る色かぶりを削る。画面色の支配チャンネルを他の上限まで引き下げる。"""
    ch = int(np.argmax(key))
    others = [i for i in range(3) if i != ch]
    out = rgb.astype(np.int16).copy()
    cap = np.maximum(out[..., others[0]], out[..., others[1]])
    out[..., ch] = np.where(soft > 0.08, np.minimum(out[..., ch], cap), out[..., ch])
    return np.clip(out, 0, 255).astype(np.uint8)


# ── 四隅を求める ────────────────────────────────────────────

def hull_of(mask):
    """マスクの凸包。行ごと・列ごとの端点だけ拾えば凸包には十分。"""
    pts = []
    rows = np.where(mask.any(axis=1))[0]
    for y in rows:
        xs = np.where(mask[y])[0]
        pts += [(int(xs[0]), int(y)), (int(xs[-1]), int(y))]
    cols = np.where(mask.any(axis=0))[0]
    for x in cols:
        ys = np.where(mask[:, x])[0]
        pts += [(int(x), int(ys[0])), (int(x), int(ys[-1]))]

    pts = sorted(set(pts))
    if len(pts) < 3:
        sys.exit('画面領域が見つからない。単色で塗られているか確認する')

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and cross(h[-2], h[-1], p) <= 0:
                h.pop()
            h.append(p)
        return h

    return half(pts)[:-1] + half(pts[::-1])[:-1]


def _angle_gap(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


def _fit_line(pts):
    """点群に直線を当てる（全最小二乗）。(a, b, c, 残差) を返す。直線は ax + by = c。"""
    p = np.asarray(pts, dtype=np.float64)
    centroid = p.mean(axis=0)
    _, _, vt = np.linalg.svd(p - centroid, full_matrices=False)
    direction = vt[0]
    normal = np.array([-direction[1], direction[0]])
    resid = float(np.sqrt((((p - centroid) @ normal) ** 2).mean()))
    return normal[0], normal[1], float(normal @ centroid), resid


def corners_from(hull, size, tol_deg=8.0, max_resid=2.5):
    """凸包から画面の 4 辺を選び、その交点を四隅として返す。

    素朴に「凸包の長い辺を 4 本」では通らない。書き出しのアンチエイリアスで輪郭が 1px
    揺れるため、まっすぐな 1 辺が凸包上では複数の短い辺に割れてしまう（実際、正面の
    モックで左辺が 3 本に分断された）。そうすると上位 4 本に対辺どうしが混ざり、
    平行な 2 直線の交点＝ほぼ無限遠を拾って壊れる。

    そこで連続する辺を向きでまとめてから選ぶ。角丸の弧も 1 つの塊にまとまるが、
    そちらは直線に乗らないので残差で弾ける。残った 4 つの塊に最小二乗で直線を当て、
    凸包上の順序（= 空間的に隣り合う順）で交点を取る。
    """
    n = len(hull)
    groups = []                      # [代表角, 総長, 点列, 最長辺長]
    for i in range(n):
        (x1, y1), (x2, y2) = hull[i], hull[(i + 1) % n]
        length = np.hypot(x2 - x1, y2 - y1)
        if length < 1e-9:
            continue
        angle = np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
        # 代表角はグループ内の最長辺のもの。平均だと角丸を辿るうちに向きが流れてしまう。
        if groups and _angle_gap(groups[-1][0], angle) <= tol_deg:
            g = groups[-1]
            if length > g[3]:
                g[0], g[3] = angle, length
            g[1] += length
            g[2] += [(x1, y1), (x2, y2)]
        else:
            groups.append([angle, length, [(x1, y1), (x2, y2)], length])

    # 凸包は環状なので、末尾と先頭が同じ向きならつなぐ
    if len(groups) > 1 and _angle_gap(groups[0][0], groups[-1][0]) <= tol_deg:
        tail = groups.pop()
        groups[0][1] += tail[1]
        groups[0][2] = tail[2] + groups[0][2]
        if tail[3] > groups[0][3]:
            groups[0][0], groups[0][3] = tail[0], tail[3]

    # 直線に乗っている塊だけを候補にする（角丸の弧をここで落とす）
    cand = []
    for idx, (_, total, pts, _) in enumerate(groups):
        a, b, c, resid = _fit_line(pts)
        if resid <= max_resid:
            cand.append((total, idx, (a, b, c)))
    if len(cand) < 4:
        sys.exit(f'画面の 4 辺を特定できない（直線とみなせた辺 {len(cand)} 本）')

    top = sorted(cand, reverse=True, key=lambda e: e[0])[:4]
    top.sort(key=lambda e: e[1])          # ← 凸包上の順序に戻す
    lines = [e[2] for e in top]

    pts = []
    for i in range(4):
        a1, b1, c1 = lines[i]
        a2, b2, c2 = lines[(i + 1) % 4]
        det = a1 * b2 - a2 * b1
        if abs(det) < 1e-9:
            sys.exit('隣り合う辺が平行になっている。4 辺の選択に失敗した')
        pts.append(((b2 * c1 - b1 * c2) / det, (a1 * c2 - a2 * c1) / det))

    # 画面の角が画像から大きく外れていたら、それは辺の取り違え。黙って通さない。
    w, h = size
    for x, y in pts:
        if not (-0.25 * w < x < 1.25 * w and -0.25 * h < y < 1.25 * h):
            sys.exit(f'四隅が画像の外に出た（{x:.0f}, {y:.0f}）。辺の選択に失敗している')

    # 左上 → 右上 → 右下 → 左下 の順に整える
    cx = sum(p[0] for p in pts) / 4
    cy = sum(p[1] for p in pts) / 4
    pts.sort(key=lambda p: np.arctan2(p[1] - cy, p[0] - cx))
    start = min(range(4), key=lambda i: pts[i][0] + pts[i][1])
    pts = pts[start:] + pts[:start]
    return [[round(x, 2), round(y, 2)] for x, y in pts]


def orient(corners, hard, size):
    """四隅を「画面の左上から時計回り」に並べ直す。

    画像座標の左上から始めるだけでは足りない。端末が寝ているモックでは、画像上の
    左上が画面の左上とは限らず、スクリーンショットの幅と高さが入れ替わって
    中身が 90 度倒れて入る（実際に lay で起きた）。

    画面は必ず縦長なので、まず短辺が幅（c0→c1）に来るよう巡回させる。残る 180 度の
    曖昧さは、ノッチ（画面の中でマスクが抜けている穴）が上辺の側に来る向きで決める。
    ノッチが見つからないモックでは判断できないので、そのまま返して警告する。
    """
    def edge(i, j):
        return np.hypot(corners[j][0] - corners[i][0], corners[j][1] - corners[i][1])

    if edge(0, 1) > edge(1, 2):          # 長辺が幅に来ている → 1 つ回す
        corners = corners[1:] + corners[:1]

    # 画面の内側にある「穴」＝ノッチを拾う
    ys, xs = np.where(~hard)
    if len(xs):
        poly = np.array(corners, dtype=np.float64)
        best = None
        for want in (1, -1):
            inside = np.ones(len(xs), dtype=bool)
            for i in range(4):
                x1, y1 = poly[i]
                x2, y2 = poly[(i + 1) % 4]
                cross = (x2 - x1) * (ys - y1) - (y2 - y1) * (xs - x1)
                inside &= (cross * want >= 0)
            if inside.sum() > 0 and (best is None or inside.sum() > best[1]):
                best = (inside, int(inside.sum()))
        if best and best[1] > 200:       # 小さすぎる穴はノイズ
            hole = best[0]
            gx, gy = xs[hole].mean(), ys[hole].mean()
            top = (poly[0] + poly[1]) / 2
            bottom = (poly[2] + poly[3]) / 2
            if np.hypot(gx - top[0], gy - top[1]) > np.hypot(gx - bottom[0], gy - bottom[1]):
                corners = corners[2:] + corners[:2]      # 上下が逆 → 180 度回す
            return corners, True

    return corners, False


def write_index(outdir):
    """mockup/*.json をまとめた index.js を作り直す。

    テンプレートは file:// で直接開けるようにしてあり、fetch は CORS で弾かれる。
    そこで <script> で読める形にしておく。
    """
    entries = {}
    for path in sorted(outdir.glob('*.json')):
        entries[path.stem] = json.loads(path.read_text(encoding='utf-8'))
    body = json.dumps(entries, ensure_ascii=False, indent=2)
    (outdir / 'index.js').write_text(
        '// prep_mockup.py が自動生成する。手で編集しない。\n'
        f'window.MOCKUPS = {body};\n', encoding='utf-8')


# ── 本体 ────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('name', help='出力名（例: iphone-tilt）')
    ap.add_argument('--out', default='mockup')
    ap.add_argument('--key', help='画面の塗り色を明示する（例: 7E9401）。既定は自動判定')
    ap.add_argument('--debug', action='store_true', help='検出した四隅を描いた確認用 PNG も出す')
    ap.add_argument('--rotate', type=int, choices=[0, 90, 180, 270], default=0,
                    help='自動判定した画面の向きをさらに回す（中身が倒れて入るときに使う）')
    args = ap.parse_args()

    im = Image.open(args.src).convert('RGBA')
    arr = np.array(im)
    rgb, alpha = arr[..., :3], arr[..., 3]

    if args.key:
        h = args.key.lstrip('#')
        key = np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.int16)
    else:
        key = detect_key(rgb, alpha)

    soft = screen_mask(rgb, key)
    hard = (soft > 0.5) & (alpha > 128)

    corners = corners_from(hull_of(hard), (im.width, im.height))
    corners, by_notch = orient(corners, hard, (im.width, im.height))
    if args.rotate:
        shift = args.rotate // 90
        corners = corners[shift:] + corners[:shift]

    out_rgb = despill(rgb, soft, key)
    out_alpha = (alpha.astype(np.float32) * (1 - soft)).astype(np.uint8)
    frame = np.dstack([out_rgb, out_alpha])

    outdir = pathlib.Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    png = outdir / f'{args.name}.png'
    Image.fromarray(frame, 'RGBA').save(png, optimize=True)

    meta = {
        'name': args.name,
        'src': str(pathlib.Path(args.src).name),
        'size': [im.width, im.height],
        'key': '#%02X%02X%02X' % tuple(int(v) for v in key),
        # 左上 → 右上 → 右下 → 左下。size の座標系。
        'corners': corners,
    }
    (outdir / f'{args.name}.json').write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_index(outdir)

    if args.debug:
        dbg = im.convert('RGB')
        d = ImageDraw.Draw(dbg)
        d.polygon([tuple(c) for c in corners], outline=(255, 0, 200), width=6)
        for i, (x, y) in enumerate(corners):
            d.ellipse([x - 14, y - 14, x + 14, y + 14], fill=(255, 0, 200))
            d.text((x + 20, y - 8), '↖↗↘↙'[i], fill=(255, 0, 200))
        dbg.save(outdir / f'{args.name}-debug.png')

    area = hard.sum()
    how = 'ノッチで上下を判定' if by_notch else '⚠ ノッチが見つからず上下は未確認'
    print(f'{png}  {im.width}×{im.height}  画面 {area:,}px  key {meta["key"]}  {how}')
    for label, (x, y) in zip(['左上', '右上', '右下', '左下'], corners):
        print(f'  {label}  {x:8.2f}, {y:8.2f}')


if __name__ == '__main__':
    main()
