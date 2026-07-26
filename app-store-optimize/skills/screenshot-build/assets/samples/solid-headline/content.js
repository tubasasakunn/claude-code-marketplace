/**
 * solid-headline — 淡い地に濃い文字。端末は正面のまま素直に見せる。
 *
 * またぎも飛び出しも使わない代わりに、1 枚ずつが独立して成立する。
 * 検索結果でどの 3 枚が並んでも崩れないので、迷ったらこの型が安全。
 */
window.CONTENT = {
  meta: {
    app: 'Hioto',
    size: { w: 1320, h: 2868 },
  },

  theme: {
    paper: '#F7F4F0',
    paperDeep: '#EFE8E0',
    ink: '#2A2520',
    sub: '#7C6F65',
    accent: '#C25A33',
    badgeBg: '#2A2520',
    badgeInk: '#F7F4F0',
  },

  wordmark: {
    icon: '../../apps/hioto/material/app_icon_1024.png',
    text: 'Hioto',
  },

  shots: [
    {
      variant: 'hero',
      headline: ['撮るだけで、', '<em>1日</em>がのこる。'],
      sub: '長押ししている間だけ録る、動画の日記',
      wordmark: true,
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/03_shorts.png',
        w: 2200, x: -450, y: 1080, rotate: -4,
      },
    },

    {
      variant: 'flat',
      headline: ['長押しするだけ。', '編集はいらない'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/01_camera.png',
        w: 2300, x: -505, y: 640,
      },
      badge: { lines: ['1日', '3秒で'], x: '84%', y: '30%', rotate: -7 },
    },

    {
      variant: 'flat',
      headline: ['その日が、勝手に', '1本の動画になる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/05_insights.png',
        w: 2300, x: -505, y: 640,
      },
    },

    {
      variant: 'flat',
      headline: ['カレンダーに、', '日々が積もる'],
      mock: {
        name: 'iphone-flat',
        shot: '../../apps/hioto/material/note/04_calendar.png',
        w: 2300, x: -505, y: 640,
      },
      badge: { lines: ['ぜんぶ', '端末の中'], x: '85%', y: '28%', rotate: 7 },
    },
  ],
};
