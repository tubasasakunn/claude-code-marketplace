# PILLOW.md — Pillow/numpy 描画テクニック

依存前提: Pillow + numpy のみ（外部バイナリなし）。コードは要点のみの断片。

---

## 1. タイポグラフィ

### anchor（配置の基準点）
2文字コード: 1文字目=水平(`l`/`m`/`r`)、2文字目=垂直(`a`=アセンダー/`t`/`m`/`s`=ベースライン/`b`/`d`=ディセンダー)。
TrueType/OpenType のみ対応。

```python
draw.text((cx, cy), "見出し", font=font, anchor="mm")  # 中央基準
```

### 縁取り・影
- 縁取り: `stroke_width=4, stroke_fill=(0,0,0)` を**必ず両方**指定（stroke_fill 省略は fill 色になる）。
- 影: 黒テキストを別 RGBA レイヤに描き `GaussianBlur(blur)` + オフセットして先に合成、上に本体。

### グラデーション文字（マスク合成）
ImageDraw は文字へのグラデ塗り非対応。定石は「文字=マスク」:

```python
mask = Image.new("L", size, 0)
ImageDraw.Draw(mask).text(xy, s, font=font, fill=255, anchor="mm")
canvas.paste(gradient_img, (0, 0), mask=mask)
```

### フォントメトリクス
- `font.getbbox(s)` / `draw.textbbox(xy, s)` … anchor/stroke 込みの実描画 bbox。はみ出し検証はこれ。
- `draw.textlength(s)` / `font.getlength(s)` … 字送り量（1/64px 精度）。カーソル計算・字間実装用。
- `font.getmetrics()` → `(ascent, descent)` … **行送りはこれ基準**。描画高さの積み上げは
  行ごとにアセンダー/ディセンダーが違い行間が不揃いになる（Pillow #1540）。

### 自動折返し（日本語）
Pillow にネイティブ機能なし。`textwrap` は等幅換算で日本語に不正確。
`getlength()` で実測しながら1文字/1トークンずつ追加するループが確実:

```python
lines, cur = [], ""
for ch in text:
    if font.getlength(cur + ch) > max_w:
        lines.append(cur); cur = ch
    else:
        cur += ch
lines.append(cur)
```

新しめの Pillow には `PIL.ImageText` モジュールがあり、`Text.wrap()`（`grow`/`shrink` で枠に収める
自動スケール付き）、`stroke()`、`embed_color()`、anchor 対応の `get_bbox()` が1オブジェクトに統合
されている。使えるバージョンならこちらが簡潔。

### 枠に収める（fit）
「折返し→それでも溢れたらサイズを段階的に縮小」の複合最適化にする。
1行前提のサイズ縮小だけだと長文で破綻する。

### 字間（letter-spacing）
1文字ずつ `draw.text()` する単純実装はカーニング・合字と干渉しうる。
精密にやるなら「通常描画 → 1文字ずつ crop → 文字幅+spacing で再配置」パターン。
（簡易実装で十分な場面が多い。ズレが見えたらこのパターンに切替）

### 複数行
`draw.multiline_text(xy, s, spacing=N, align="left|center|right|justify")`。
`justify`（両端揃え）は Pillow 11.2.1+。

### カラー絵文字
- ネイティブ: `draw.text(..., embedded_color=True)`（Pillow 8.0+）+ COLR/CBDT/SBIX 形式の
  カラー絵文字フォント（Noto Color Emoji 等）。
- 柔軟にやるなら `pilmoji`（絵文字を画像として貼り込み。Twemoji/Apple/Google ソース切替可）。
- **絵文字フォントをロードしていないエンジンに絵文字入りテキストを渡すと豆腐(□)になる**。
  spec 側でガードするか対応フォントを足す。

---

## 2. 描画品質（アンチエイリアス）

### スーパーサンプリング（定石）
`ImageDraw` の塗り（fill）は AA されない — 円・角丸・斜め線はジャギる（Pillow #5577。
`rounded_rectangle` は形状対応のみで縁の AA は無い）。**2〜4倍で描いて LANCZOS 縮小**:

```python
SS = 4
big = Image.new("RGBA", (w*SS, h*SS), (0,0,0,0))
ImageDraw.Draw(big).rounded_rectangle([...], radius=r*SS, fill=col)
out = big.resize((w, h), Image.LANCZOS)
```

適用漏れが起きやすい場所: **テキスト本体**（PIL のフォントラスタライザ任せにしがち）、
角丸プレート、小さい円・ドット、モックアップの枠。SVG やアイコンだけ SS して
テキストが非 SS、という不均一を作らない。

### aggdraw
真の AA 描画が要るなら AGG ラッパの `aggdraw`（Pillow Image と相互運用可）。

### ぼかし半径は解像度比例で
`GaussianBlur(1.2)` のような固定値は基準解像度前提になる。キャンバス幅に比例させる
（例: `blur = w / 900`）と解像度を変えても見た目が保たれる。

---

## 3. 合成・エフェクト

### グラデーション（numpy）
```python
# 縦の alpha グラデ（scrim 用）
alpha = np.linspace(0, 160, h).astype(np.uint8)          # 上→下で濃く
layer = np.zeros((h, w, 4), np.uint8); layer[..., 3] = alpha[:, None]
canvas.alpha_composite(Image.fromarray(layer))
# 放射状: np.meshgrid で中心からの距離を使う
```

### scrim（写真上の文字の可読性）
下端（or 上端）を「40%黒 → 完全透明」の縦グラデでフェード。画像全体を暗くせず
コントラストだけ確保する。Netflix/Apple 等でも常用のパターン。

### ノイズ / grain
```python
arr = np.asarray(img).astype(np.int16)
out = np.clip(arr + np.random.normal(0, std, arr.shape), 0, 255).astype(np.uint8)
```
運用規範: 写真背景にだけ薄く。フラット面に載せると汚れて見える。
動画では**シード固定**しないとフレーム間でノイズが踊る。

### ドロップシャドウ
黒塗り図形/テキストマスクを `GaussianBlur(radius)` → オフセット位置に `alpha_composite` → 本体を重ねる。

### ブレンドモード
- 組込み `ImageChops`: `multiply` / `screen` / `overlay` / `soft_light` / `hard_light` など。追加ライブラリ不要。
- 不透明度付き・多モードは `blend_modes` パッケージ（numpy float RGBA）。
- numpy 自前: multiply=`a*b`, screen=`1-(1-a)*(1-b)`, overlay=`where(a<.5, 2ab, 1-2(1-a)(1-b))`。
- **注意**: `Image.blend` / 単純 lerp はガンマ補正なしの線形 RGB 補間で暗部が濁る。
  こだわる場面では sRGB→リニア化してから合成して戻す。

### duotone
グレースケール化 → `Image.point()` の LUT か numpy で
`gray/255 * (colB - colA) + colA` の線形補間。

### クロマキー抜き
「緑が赤・青より支配的な画素」を numpy で閾値判定して alpha=0:

```python
r, g, b = arr[...,0], arr[...,1], arr[...,2]
mask = (g > r * 1.15) & (g > b * 1.15) & (g > 100)
```
併せて: 緑スピル除去（`g = min(g, max(r,b)+k)`）、マスクの軽い GaussianBlur でエッジ馴染ませ。
閾値は照明で変わるのでハードコードせず引数化しておく。

---

## 4. SVG ラスタライズ

| 手段 | 特徴 |
|------|------|
| 自前パーサ（正規表現+ベジェ分割） | 依存ゼロ。fill-rule / transform / gradient 非対応、固定分割だと拡大でカクつく |
| `cairosvg` | 高速・簡潔。壊れた SVG に弱い |
| `resvg-py` | Rust製 resvg。高精度・高速・pip で入る。**複雑な SVG を使うならこれが本命** |

自前でやる場合でも**ラスタ結果をキャッシュ**する（同じアイコンを毎回パース・再ラスタライズしない）。

---

## 5. パフォーマンス

- Pillow→numpy は `np.asarray(img)`（`np.array` よりコピー節約）、復路は `Image.fromarray`。
- `putpixel`/`getpixel` の Python ループは禁止。numpy / `Image.point()` / `ImageChops` / `ImageFilter` に寄せる。
- フルサイズ RGBA レイヤの乱造に注意（レイヤごとに `Image.new("RGBA", canvas.size)` →
  `alpha_composite` はメモリと時間を食う）。部分矩形で描いて貼る、レイヤを使い回す。
- バッチ生成（カルーセル複数枚）は `multiprocessing` でコア数スケール（描画は CPU バウンド）。
- さらに速く: `Pillow-SIMD`（リサイズ・フィルタで 4〜8 倍報告。ドロップイン代替）。

---

## 6. レイアウトをコードで表す

- マージン・グリッド・セーフゾーンは**キャンバスサイズ比の定数**で宣言（絶対 px ハードコードしない）。
- 余白は基準スケール（例: 8 の倍数）に snap させると間延び・詰まりすぎを機械的に防げる。
- ジャンプ率（見出し/本文サイズ比）はテーマ定数で比率管理（例: `H1 = BASE*3.2`）。
- 定数・配置関数は1ファイルに集約し、テンプレート側から呼ぶ（このリポジトリでは
  carousel-craft の `engine/brand.py` + `LAYOUTS.md` がその役割）。

---

## 主要ソース

- Pillow 公式: Text Anchors / ImageFont / ImageText / ImageFilter / ImageCms / release notes
- Pillow #5577（塗りの AA なし）/ #1540（行送りとベースライン）
- pilmoji, resvg-py, Pillow-SIMD, blend_modes（各 GitHub/PyPI）
- Smashing Magazine "Designing Accessible Text Over Images"
