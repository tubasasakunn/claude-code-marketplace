/**
 * content.js の shots[] / spreads[] を DOM に展開する。全テンプレート共通。
 *
 * テンプレートごとの違いは style.css と content.js だけで、組み立ての手順は同じ。
 * だからここに一本化してある。index.html でこれを読めば build.js は要らない。
 *
 * 端末モックへの流し込みは _lib/mockup.js、切り出しは _lib/breakout.js が担当する。
 *
 * フレーム画像の置き場は既定で `../mockup`。別の場所に置くなら index.html で
 * window.MOCKUP_DIR を先に定義する。
 */
window.__ready = (async () => {
  const C = window.CONTENT;
  const sheet = document.getElementById('sheet');

  /**
   * layout.js（エディタが書き出す位置の上書き）を content.js の値に被せる。
   *
   * content.js を直に書き換えないのは、あちらに「なぜその数字なのか」を書いた
   * コメントが載っているから。機械が書き戻すと消えてしまう。
   * 位置が固まったら layout.js の値を content.js へ写して、layout.js は消す。
   */
  const LAYOUT = window.LAYOUT || {};
  const withLayout = (key, obj) => (LAYOUT[key] ? { ...obj, ...LAYOUT[key] } : obj);

  const root = document.documentElement.style;
  root.setProperty('--w', `${C.meta.size.w}px`);
  root.setProperty('--h', `${C.meta.size.h}px`);
  for (const [k, v] of Object.entries(C.theme || {})) {
    root.setProperty(`--${k.replace(/[A-Z]/g, (m) => '-' + m.toLowerCase())}`, v);
  }

  const el = (tag, cls, parent) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (parent) parent.appendChild(n);
    return n;
  };

  const img = (src, cls, parent) => {
    const n = el('img', cls, parent);
    n.src = src;
    n.alt = '';
    return n;
  };

  const head = (shot, box) => {
    if (!shot.headline || !shot.headline.length) return;   // 見出しを置かない枚もある
    const h = el('header', 'head', box);
    el('h1', null, h).innerHTML = shot.headline.map((l) => `<span>${l}</span>`).join('');
    if (shot.sub) el('p', 'sub', h).textContent = shot.sub;
  };

  const wordmark = (parent) => {
    if (!C.wordmark) return;
    const w = el('div', 'wordmark', parent);
    if (C.wordmark.icon) img(C.wordmark.icon, 'mark', w);
    el('span', null, w).textContent = C.wordmark.text;
  };

  /** 端末モックアップ。中身の変形は applyMockups がやる。 */
  const mock = (m, parent, key, dx = 0) => {
    const meta = (window.MOCKUPS || {})[m.name];
    if (!meta) throw new Error(`モックアップ '${m.name}' が mockup/index.js に無い`);
    const n = el('div', 'mock', parent);
    n.dataset.mockup = m.name;
    n.dataset.edit = key;          // エディタが掴む識別子
    n.dataset.dx = dx;             // またぎで左へずらした分。編集時に引き戻す
    n.dataset.kind = 'mock';
    n.dataset.rotate = m.rotate || 0;
    n.style.left = `${m.x + dx}px`;
    n.style.top = `${m.y}px`;
    n.style.width = `${m.w}px`;
    n.style.aspectRatio = `${meta.size[0]} / ${meta.size[1]}`;
    // 正面のモックを傾けて使うときはここが効く。3D のパースではなく単純な回転なので、
    // 画面の中身は歪まない。
    if (m.rotate) n.style.transform = `rotate(${m.rotate}deg)`;
    img(m.shot, 'mock-shot', n);
    img(`${window.MOCKUP_DIR || '../mockup'}/${m.name}.png`, 'mock-frame', n);
  };

  /** 端末から飛び出す UI 片。実寸は applyBreakouts が背景として貼る。 */
  const breakout = (b, parent, key, dx = 0) => {
    const n = el('div', 'breakout', parent);
    n.dataset.src = b.src;
    n.dataset.rect = b.rect.join(',');
    n.dataset.edit = key;
    n.dataset.dx = dx;
    n.dataset.kind = 'breakout';
    n.dataset.rotate = b.rotate || 0;
    n.style.left = `${b.x + dx}px`;
    n.style.top = `${b.y}px`;
    n.style.width = `${b.w}px`;
    n.style.height = `${Math.round(b.w * b.rect[3] / b.rect[2])}px`;
    if (b.rotate) n.style.transform = `rotate(${b.rotate}deg)`;
  };

  /** ☑ 付きの箇条書き。機能を 3 行くらいで畳んで見せたいときに使う。 */
  const checklist = (items, parent) => {
    const ul = el('ul', 'checklist', parent);
    for (const t of items) el('li', null, ul).innerHTML = t;
  };

  /**
   * 手描き風の矢印。2 台の端末をつないで「こうすると、こうなる」を示す。
   *
   * 二次ベジェ 1 本で描き、`bend` で曲がり具合を決める（正で右手側へ膨らむ）。
   * 頭は別 path の三角。SVG は枚の全面に敷いて viewBox をキャンバスに合わせるので、
   * from / to はそのままキャンバス座標で書ける。
   */
  const arrow = (a, parent, key) => {
    const NS = 'http://www.w3.org/2000/svg';
    const [x1, y1] = a.from;
    const [x2, y2] = a.to;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const bend = a.bend ?? 0.3;
    // 制御点は中点から法線方向へ。曲率は距離に比例させる。
    const cx = (x1 + x2) / 2 - (dy / len) * bend * len;
    const cy = (y1 + y2) / 2 + (dx / len) * bend * len;

    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('class', 'arrow');
    svg.setAttribute('viewBox', `0 0 ${C.meta.size.w} ${C.meta.size.h}`);
    svg.dataset.edit = key;
    svg.dataset.kind = 'arrow';

    // 線と頭でクラスを分ける。まとめて fill を当てると、曲線とその弦で囲まれた面が
    // 塗り潰されて黒い塊になる。
    const line = document.createElementNS(NS, 'path');
    line.setAttribute('class', 'line');
    line.setAttribute('d', `M${x1},${y1} Q${cx},${cy} ${x2},${y2}`);
    line.setAttribute('stroke-width', a.width ?? 14);
    line.setAttribute('stroke-linecap', 'round');
    svg.appendChild(line);

    // 頭は終点での接線（制御点 → 終点）の向きに合わせる
    const ang = Math.atan2(y2 - cy, x2 - cx);
    const h = a.head ?? 46;
    const pt = (r, t) => `${x2 + r * Math.cos(ang + t)},${y2 + r * Math.sin(ang + t)}`;
    const tip = document.createElementNS(NS, 'path');
    tip.setAttribute('class', 'tip');
    tip.setAttribute('d', `M${x2},${y2} L${pt(h, 2.6)} L${pt(h * 0.62, Math.PI)} L${pt(h, -2.6)} Z`);
    svg.appendChild(tip);

    parent.appendChild(svg);
  };

  const badge = (b, parent, key) => {
    const n = el('div', 'badge', parent);
    n.dataset.edit = key;
    n.dataset.kind = 'badge';
    n.dataset.rotate = b.rotate ?? 0;
    n.style.left = b.x;
    n.style.top = b.y;
    n.style.setProperty('--rot', `${b.rotate ?? 0}deg`);
    n.innerHTML = b.lines.map((l) => `<span>${l}</span>`).join('');
  };

  const compose = (shot, box, si) => {
    head(shot, box);
    if (shot.checklist) checklist(shot.checklist, box);
    if (shot.wordmark) wordmark(box);
    if (shot.mock) mock(withLayout(`shots.${si}.mock`, shot.mock), box, `shots.${si}.mock`);
    // 1 枚に複数台を置く型（Before → After など）
    (shot.mocks || []).forEach((m, mi) => {
      const key = `shots.${si}.mocks.${mi}`;
      mock(withLayout(key, m), box, key);
    });
    (shot.breakouts || []).forEach((b, bi) => {
      const key = `shots.${si}.breakouts.${bi}`;
      breakout(withLayout(key, b), box, key);
    });
    (shot.arrows || []).forEach((a, ai) => arrow(a, box, `shots.${si}.arrows.${ai}`));
    if (shot.badge) {
      const key = `shots.${si}.badge`;
      badge(withLayout(key, shot.badge), box, key);
    }
  };

  const sections = C.shots.map((shot, i) => {
    const box = el('section', `shot v-${shot.variant || 'plain'}`, sheet);
    box.dataset.n = i + 1;
    compose(shot, box, i);
    return box;
  });

  /**
   * 複数の枚にまたがって置くもの。
   *
   * 座標は「またぎキャンバス」（幅 = 1 枚の幅 × pages の数）で指定する。
   * 同じものを各枚に描き、枚の順番ぶんだけ左へずらすと、切れ目で continue する。
   * .shot が overflow:hidden なので、はみ出した分は各枚で自然に切れる。
   *
   * ただし App Store では枚と枚の間に余白が入り、スクロールで並ぶ組も変わる。
   * つながって見えるのは検索結果に 3 枚並んだときだけなので、**各枚が単体でも
   * 成立していること**を優先し、またぎはあくまで加点として使う。
   */
  (C.spreads || []).forEach((sp, si) => {
    sp.pages.forEach((page, i) => {
      const box = sections[page];
      if (!box) throw new Error(`spreads[${si}].pages に無い枚がある: ${page}`);
      const dx = -i * C.meta.size.w;
      if (sp.mock) {
        const key = `spreads.${si}.mock`;
        mock(withLayout(key, sp.mock), box, key, dx);
      }
      (sp.breakouts || []).forEach((b, bi) => {
        const key = `spreads.${si}.breakouts.${bi}`;
        breakout(withLayout(key, b), box, key, dx);
      });
    });
  });

  if (new URLSearchParams(location.search).has('preview')) {
    document.body.classList.add('preview');
  }

  // 変形と切り出しは画像の実寸が要るので、ここまで来てから当てる。
  await window.applyMockups(document);
  await window.applyBreakouts(document);
})();
