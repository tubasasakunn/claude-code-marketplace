/**
 * スクリーンショットの一部を切り出して、端末の外へ飛び出させる。
 *
 * ASO のストア画像でよく使われる表現で、伝えたい UI をアプリ画面から抜き出し、
 * 実際より大きく、端末のベゼルをまたいで浮かせる。切り出しは背景画像のずらしで
 * やっているので、元のスクリーンショットを差し替えれば中身も自動で入れ替わる。
 *
 * data-rect は元画像のピクセル座標で [x, y, w, h]。tools/measure_cards.py で測れる。
 */
(() => {
  const loaded = new Map();

  function load(src) {
    if (!loaded.has(src)) {
      loaded.set(src, new Promise((res, rej) => {
        const im = new Image();
        im.onload = () => res(im);
        im.onerror = () => rej(new Error(`breakout の画像が読めない: ${src}`));
        im.src = src;
      }));
    }
    return loaded.get(src);
  }

  async function applyBreakouts(root = document) {
    const nodes = [...root.querySelectorAll('.breakout[data-src]')];
    await Promise.all(nodes.map(async (el) => {
      const src = el.dataset.src;
      const im = await load(src);
      const [rx, ry, rw] = el.dataset.rect.split(',').map(Number);

      // 指定した表示幅に合わせて、元画像ごと拡大してから位置をずらす。
      // offsetWidth なのはプレビューの zoom に引きずられないため（mockup.js と同じ理由）。
      const scale = el.offsetWidth / rw;
      el.style.backgroundImage = `url("${src}")`;
      el.style.backgroundSize = `${im.naturalWidth * scale}px auto`;
      el.style.backgroundPosition = `${-rx * scale}px ${-ry * scale}px`;
    }));
  }

  window.applyBreakouts = applyBreakouts;
})();
