/**
 * ストア画像の位置合わせを、画面上で直接やるためのエディタ。
 *
 *   node tools/edit.mjs template/bold-breakout      ← サーバーごと開く（保存できる）
 *   open 'template/bold-breakout/index.html?edit=1' ← file:// でも動く（コピーのみ）
 *
 * 触れるのは端末モック・飛び出す UI 片・円形バッジ。掴んで動かし、ホイールで大きさを
 * 変え、選んだ状態で矢印キーを押せば 1px ずつ動く。値は右のパネルに出るので、
 * 直接入力してもよい。
 *
 * 結果は content.js のキー（`spreads.0.mock` のような形）ごとの上書きとして
 * layout.js に書き出す。content.js を直に書き換えないのは、あちらに「なぜその数字か」
 * を書いたコメントが載っているため。位置が固まったら値を content.js へ写して
 * layout.js を消す。
 */
(() => {
  if (!new URLSearchParams(location.search).has('edit')) return;

  const overrides = JSON.parse(JSON.stringify(window.LAYOUT || {}));
  let selected = null;

  const css = `
    body.editing { padding: 0 !important; background: #14100e; }
    body.editing #sheet {
      flex-direction: row !important; align-items: flex-start !important;
      gap: 0 !important; zoom: .26; padding: 40px;
    }
    body.editing .shot { outline: 1px solid rgba(255,255,255,.25); }
    body.editing [data-edit] { cursor: grab; }
    body.editing [data-edit].sel { outline: 3px dashed #4ADE80; outline-offset: 4px; }
    /* ハンドルは左上に置く。端末モックは 2500px 級でキャンバスの外まで伸びるので、
       右下だと画面の外へ出てしまって掴めない。 */
    body.editing .eh {
      position: absolute; left: -16px; top: -16px; width: 44px; height: 44px;
      background: #4ADE80; border: 3px solid #14100e; border-radius: 50%;
      cursor: nwse-resize; z-index: 99;
    }
    #ed {
      position: fixed; top: 0; right: 0; bottom: 0; width: 320px; z-index: 9999;
      background: #1c1714; color: #F1EAE3; border-left: 1px solid #332b26;
      font: 13px/1.6 ui-monospace, "SF Mono", Menlo, monospace;
      display: flex; flex-direction: column; overflow: hidden;
    }
    #ed h2 { margin: 0; padding: 14px 16px; font-size: 12px; letter-spacing: .12em;
             color: #E68A5E; border-bottom: 1px solid #332b26; font-weight: 700; }
    #ed .body { padding: 14px 16px; display: flex; flex-direction: column; gap: 12px;
                overflow-y: auto; flex: 1; }
    #ed .k { color: #4ADE80; word-break: break-all; font-size: 12px; }
    #ed .hint { color: #8b7d73; font-size: 11.5px; line-height: 1.7; }
    /* 要素は重なるので（バッジが端末の上に乗るなど）、クリックだけでは奥を選べない。
       一覧から直接選べるようにしておく。 */
    #ed .list { display: flex; flex-direction: column; gap: 2px; }
    #ed .list button {
      all: unset; padding: 5px 8px; border-radius: 5px; cursor: pointer;
      font: inherit; font-size: 11.5px; color: #cbbfb5; background: #14100e;
    }
    #ed .list button:hover { background: #2a231f; }
    #ed .list button.on { background: #4ADE80; color: #14100e; font-weight: 700; }
    #ed .list button:focus-visible { outline: 2px solid #4ADE80; }
    #ed .row { display: grid; grid-template-columns: 26px 1fr; align-items: center; gap: 8px; }
    #ed label { color: #8b7d73; }
    #ed input {
      width: 100%; padding: 6px 8px; border-radius: 6px; border: 1px solid #3a312b;
      background: #14100e; color: #F1EAE3; font: inherit;
    }
    #ed input:focus { outline: 2px solid #4ADE80; outline-offset: -1px; }
    #ed .btns { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #332b26; }
    #ed button.act {
      flex: 1; padding: 9px; border: 0; border-radius: 7px; cursor: pointer;
      background: #4ADE80; color: #14100e; font: inherit; font-weight: 700;
    }
    #ed button.act.alt { background: #332b26; color: #F1EAE3; }
    #ed pre {
      margin: 0; padding: 12px 16px; max-height: 34vh; overflow: auto;
      background: #14100e; border-top: 1px solid #332b26;
      font-size: 11.5px; line-height: 1.55; color: #cbbfb5; white-space: pre-wrap;
    }
    #ed .msg { padding: 0 16px 10px; color: #4ADE80; font-size: 11.5px; min-height: 18px; }
  `;

  const panel = () => {
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);

    const d = document.createElement('div');
    d.id = 'ed';
    d.innerHTML = `
      <h2>LAYOUT EDITOR</h2>
      <div class="body">
        <div class="list" id="ed-list"></div>
        <div class="k" id="ed-key">要素を選ぶ</div>
        <div class="hint">ドラッグで移動、矢印キーで 1px（Shift で 10px）。
          大きさは左上の丸を引くか、ホイール（選択中に上下）で変える。</div>
        <div class="row"><label>x</label><input id="ed-x" disabled></div>
        <div class="row"><label>y</label><input id="ed-y" disabled></div>
        <div class="row"><label>w</label><input id="ed-w" disabled></div>
        <div class="row"><label>rot</label><input id="ed-r" disabled></div>
      </div>
      <div class="msg" id="ed-msg"></div>
      <pre id="ed-out">まだ動かしていない</pre>
      <div class="btns">
        <button id="ed-save" class="act">保存</button>
        <button id="ed-copy" class="act alt">コピー</button>
      </div>`;
    document.body.appendChild(d);
    return d;
  };

  const pageW = () => window.CONTENT.meta.size.w;
  const pageH = () => window.CONTENT.meta.size.h;
  const zoom = () => parseFloat(getComputedStyle(document.getElementById('sheet')).zoom) || 1;
  const nodesFor = (key) => [...document.querySelectorAll(`[data-edit="${CSS.escape(key)}"]`)];
  const num = (v) => Math.round(v * 100) / 100;

  /** その要素のいまの値を、content.js と同じ座標系で読む。 */
  function read(node) {
    const dx = Number(node.dataset.dx || 0);
    const rotate = Number(node.dataset.rotate || 0);
    if (node.dataset.kind === 'badge') {
      return { x: node.style.left, y: node.style.top, rotate };   // % のまま持つ
    }
    return {
      x: num(parseFloat(node.style.left) - dx),   // またぎのずらし分を戻す
      y: num(parseFloat(node.style.top)),
      w: num(parseFloat(node.style.width)),
      rotate,
    };
  }

  /** 同じキーを持つ要素すべてに値を書く（またぎは 2 枚に出ているため）。 */
  function write(key, vals) {
    for (const node of nodesFor(key)) {
      const kind = node.dataset.kind;
      const dx = Number(node.dataset.dx || 0);

      if (vals.rotate != null) {          // モックも傾けて使う（正面フレームを斜めに、など）
        node.dataset.rotate = vals.rotate;
        if (kind === 'badge') node.style.setProperty('--rot', `${vals.rotate}deg`);
        else node.style.transform = vals.rotate ? `rotate(${vals.rotate}deg)` : '';
      }

      if (kind === 'badge') {
        if (vals.x != null) node.style.left = vals.x;
        if (vals.y != null) node.style.top = vals.y;
        continue;
      }
      if (vals.x != null) node.style.left = `${vals.x + dx}px`;
      if (vals.y != null) node.style.top = `${vals.y}px`;
      if (vals.w != null) {
        node.style.width = `${vals.w}px`;
        if (kind === 'breakout') {
          const [, , rw, rh] = node.dataset.rect.split(',').map(Number);
          node.style.height = `${Math.round(vals.w * rh / rw)}px`;
        }
      }
    }
    overrides[key] = { ...(overrides[key] || {}), ...vals };
    refresh();
  }

  let reapplyTimer = null;
  function reapply() {
    clearTimeout(reapplyTimer);
    reapplyTimer = setTimeout(async () => {
      await window.applyMockups(document);
      await window.applyBreakouts(document);
    }, 50);
  }

  function refresh() {
    const out = document.getElementById('ed-out');
    out.textContent = Object.keys(overrides).length
      ? JSON.stringify(overrides, null, 2)
      : 'まだ動かしていない';
    if (selected) {
      const v = read(selected);
      document.getElementById('ed-x').value = v.x ?? '';
      document.getElementById('ed-y').value = v.y ?? '';
      document.getElementById('ed-w').value = v.w ?? '';
      document.getElementById('ed-r').value = v.rotate ?? '';
    }
  }

  /** パネルの一覧を作る。重なって掴めない要素はここから選ぶ。 */
  function buildList() {
    const list = document.getElementById('ed-list');
    const seen = new Set();
    list.innerHTML = '';
    for (const n of document.querySelectorAll('[data-edit]')) {
      const key = n.dataset.edit;
      if (seen.has(key)) continue;          // またぎは 2 枚に出るので 1 行にまとめる
      seen.add(key);
      const b = document.createElement('button');
      b.type = 'button';
      b.dataset.for = key;
      b.textContent = key;
      b.addEventListener('click', () => select(n));
      list.appendChild(b);
    }
  }

  function select(node) {
    document.querySelectorAll('[data-edit].sel').forEach((n) => {
      n.classList.remove('sel');
      n.querySelector('.eh')?.remove();
    });
    document.querySelectorAll('#ed-list button').forEach((b) => b.classList.remove('on'));
    selected = node;
    if (!node) {
      document.getElementById('ed-key').textContent = '要素を選ぶ';
      ['x', 'y', 'w', 'r'].forEach((k) => { document.getElementById(`ed-${k}`).disabled = true; });
      return;
    }
    document.querySelector(`#ed-list button[data-for="${CSS.escape(node.dataset.edit)}"]`)
      ?.classList.add('on');
    nodesFor(node.dataset.edit).forEach((n) => n.classList.add('sel'));
    document.getElementById('ed-key').textContent = node.dataset.edit;

    const kind = node.dataset.kind;
    document.getElementById('ed-x').disabled = false;
    document.getElementById('ed-y').disabled = false;
    document.getElementById('ed-w').disabled = kind === 'badge';
    document.getElementById('ed-r').disabled = false;
    if (kind !== 'badge') {
      const h = document.createElement('div');
      h.className = 'eh';
      node.appendChild(h);
    }
    refresh();
  }

  function start() {
    document.body.classList.add('editing');
    panel();
    buildList();

    let drag = null;

    // ホイールで大きさを変える。端末モックは画面外まで伸びるので、
    // ハンドルを掴むよりこちらの方が速い。
    document.addEventListener('wheel', (e) => {
      if (!selected || selected.dataset.kind === 'badge' || e.target.closest('#ed')) return;
      e.preventDefault();
      const v = read(selected);
      const step = e.shiftKey ? 50 : 10;
      write(selected.dataset.edit, { w: Math.max(40, Math.round(v.w - Math.sign(e.deltaY) * step)) });
      reapply();
    }, { passive: false });

    document.addEventListener('mousedown', (e) => {
      if (e.target.closest('#ed')) return;
      const handle = e.target.classList?.contains('eh');
      const node = handle ? selected : e.target.closest('[data-edit]');
      if (!node) { select(null); return; }
      if (!handle) select(node);
      const v = read(node);
      drag = {
        node, handle, startX: e.clientX, startY: e.clientY,
        x: v.x, y: v.y, w: v.w,
        pct: node.dataset.kind === 'badge',
      };
      e.preventDefault();
    });

    document.addEventListener('mousemove', (e) => {
      if (!drag) return;
      const z = zoom();
      const dx = (e.clientX - drag.startX) / z;
      const dy = (e.clientY - drag.startY) / z;
      const key = drag.node.dataset.edit;

      if (drag.handle) {
        write(key, { w: Math.max(40, Math.round(drag.w + dx * 2)) });
        reapply();
      } else if (drag.pct) {
        write(key, {
          x: `${num(parseFloat(drag.x) + (dx / pageW()) * 100)}%`,
          y: `${num(parseFloat(drag.y) + (dy / pageH()) * 100)}%`,
        });
      } else {
        write(key, { x: Math.round(drag.x + dx), y: Math.round(drag.y + dy) });
      }
    });

    document.addEventListener('mouseup', () => {
      if (drag && !drag.handle) reapply();
      drag = null;
    });

    document.addEventListener('keydown', (e) => {
      if (!selected || e.target.tagName === 'INPUT') return;
      const step = e.shiftKey ? 10 : 1;
      const map = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
      if (!map[e.key]) return;
      e.preventDefault();
      const [ddx, ddy] = map[e.key];
      const v = read(selected);
      const key = selected.dataset.edit;
      if (selected.dataset.kind === 'badge') {
        write(key, {
          x: `${num(parseFloat(v.x) + (ddx / pageW()) * 100)}%`,
          y: `${num(parseFloat(v.y) + (ddy / pageH()) * 100)}%`,
        });
      } else {
        write(key, { x: v.x + ddx, y: v.y + ddy });
        reapply();
      }
    });

    for (const [id, field] of [['ed-x', 'x'], ['ed-y', 'y'], ['ed-w', 'w'], ['ed-r', 'rotate']]) {
      document.getElementById(id).addEventListener('change', (e) => {
        if (!selected) return;
        const raw = e.target.value.trim();
        const isPct = selected.dataset.kind === 'badge' && (field === 'x' || field === 'y');
        write(selected.dataset.edit, { [field]: isPct ? raw : Number(raw) });
        reapply();
      });
    }

    const msg = (t) => { document.getElementById('ed-msg').textContent = t; };

    document.getElementById('ed-save').addEventListener('click', async () => {
      try {
        const res = await fetch('__save', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify(overrides),
        });
        if (!res.ok) throw new Error(await res.text());
        msg('layout.js に保存した');
      } catch (err) {
        msg('保存できない（file:// で開いている）。コピーを使う');
      }
    });

    document.getElementById('ed-copy').addEventListener('click', async () => {
      await navigator.clipboard.writeText(JSON.stringify(overrides, null, 2));
      msg('クリップボードにコピーした');
    });

    refresh();
  }

  (window.__ready || Promise.resolve()).then(start);
})();
