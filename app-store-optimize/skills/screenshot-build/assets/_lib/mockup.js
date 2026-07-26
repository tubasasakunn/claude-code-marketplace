/**
 * スクリーンショットを端末モックアップの画面に流し込む。
 *
 * 仕組みは Canva の Smart Mockup と同じで、モック側が持っている画面の四隅へ
 * 画像を射影変換（ホモグラフィ）するだけ。違いは四隅を人が仕込むか、
 * tools/prep_mockup.py が検出するか。
 *
 * フレーム画像は画面が抜いてある PNG で、スクリーンショットより手前に重ねる。
 * だから変形が数 px ずれても角丸やベゼルの内側で吸収され、境界が汚くならない。
 */
(() => {
  /** ガウス消去（部分ピボット選択）。A x = b を解く。 */
  function solve(A, b) {
    const n = b.length;
    const m = A.map((row, i) => [...row, b[i]]);
    for (let col = 0; col < n; col++) {
      let pivot = col;
      for (let r = col + 1; r < n; r++) {
        if (Math.abs(m[r][col]) > Math.abs(m[pivot][col])) pivot = r;
      }
      if (Math.abs(m[pivot][col]) < 1e-12) return null;   // 退化した四角形
      [m[col], m[pivot]] = [m[pivot], m[col]];
      for (let r = 0; r < n; r++) {
        if (r === col) continue;
        const f = m[r][col] / m[col][col];
        for (let c = col; c <= n; c++) m[r][c] -= f * m[col][c];
      }
    }
    return m.map((row, i) => row[n] / row[i]);   // 対角化済みなので割るだけ
  }

  /**
   * src の 4 点を dst の 4 点へ写す 3x3 ホモグラフィを解く（h8 = 1 に固定）。
   * 点はいずれも [左上, 右上, 右下, 左下] の順。
   */
  function homography(src, dst) {
    const A = [];
    const b = [];
    for (let i = 0; i < 4; i++) {
      const [x, y] = src[i];
      const [u, v] = dst[i];
      A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
      A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
    }
    return solve(A, b);
  }

  /** 3x3 ホモグラフィを CSS の matrix3d（列優先の 4x4）に詰め替える。 */
  function toMatrix3d(h) {
    const [a, b, c, d, e, f, g, i] = h;
    return `matrix3d(${[a, d, 0, g, b, e, 0, i, 0, 0, 1, 0, c, f, 0, 1].join(',')})`;
  }

  const settled = (img) => (img.complete && img.naturalWidth)
    ? Promise.resolve()
    : new Promise((res) => { img.onload = img.onerror = res; });

  async function applyMockups(root = document) {
    const nodes = [...root.querySelectorAll('[data-mockup]')];
    await Promise.all(nodes.flatMap((n) => [...n.querySelectorAll('img')].map(settled)));

    for (const node of nodes) {
      const name = node.dataset.mockup;
      const meta = (window.MOCKUPS || {})[name];
      if (!meta) throw new Error(`モックアップ '${name}' が mockup/index.js に無い`);

      const shot = node.querySelector('.mock-shot');
      if (!shot || !shot.naturalWidth) throw new Error(`'${name}' のスクリーンショットが読めない`);

      // フレームの表示サイズに合わせて四隅を拡縮する。
      // offsetWidth を使うのは、プレビューの zoom に影響されない CSS px が欲しいため
      // （getBoundingClientRect は zoom 後の実寸を返すので、変形が二重に縮む）。
      const sx = node.offsetWidth / meta.size[0];
      const sy = node.offsetHeight / meta.size[1];

      // 四隅をわずかに外へ広げる。ぴったりに合わせると、丸め誤差の 1px 分だけ
      // 画面の縁から背景が透けて見える（オレンジの地に細い輪郭が出た）。
      // はみ出した分はフレームのベゼルが隠すので、広げる側に倒すのが安全。
      const over = Number(node.dataset.overscan || 1.006);
      const cx = meta.corners.reduce((s, p) => s + p[0], 0) / 4;
      const cy = meta.corners.reduce((s, p) => s + p[1], 0) / 4;
      const dst = meta.corners.map(([x, y]) => [
        (cx + (x - cx) * over) * sx,
        (cy + (y - cy) * over) * sy,
      ]);

      const w = shot.naturalWidth;
      const h = shot.naturalHeight;
      shot.style.width = `${w}px`;
      shot.style.height = `${h}px`;

      const m = homography([[0, 0], [w, 0], [w, h], [0, h]], dst);
      if (!m) throw new Error(`'${name}' の四隅が退化している`);
      shot.style.transform = toMatrix3d(m);
    }
  }

  window.applyMockups = applyMockups;
})();
