// Мультфильм «Тимофей в 90-х»: рисует кадр в момент t (сек) на canvas 1080x1920.
// Используется и в живом плеере (index.html), и при рендере видео (scripts/render_anim.js).
(function () {
  const W = 1080, H = 1920, FONT = '"Russo One", sans-serif';
  const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const seg = (t, a, b) => clamp((t - a) / (b - a));
  const lerp = (a, b, k) => a + (b - a) * k;
  const ease = k => (k < 0.5 ? 2 * k * k : 1 - Math.pow(-2 * k + 2, 2) / 2);
  const inT = (t, a, b) => t >= a && t < b;

  // ---------- персонажи ----------
  const CAST = {
    tim: { skin: '#f2c49b', shirt: '#2f6fdc', pants: '#2b3a55', shoes: '#222', hair: '#5a3418', style: 'boy' },
    mom: { skin: '#f0bf96', shirt: '#9b3d8f', pants: '#f0bf96', shoes: '#5b1f3a', hair: '#7a3b12', style: 'mom' },
    f1: { skin: '#e9b48a', shirt: '#1f7a3a', pants: '#1f7a3a', shoes: '#eee', hair: '#222', style: 'boy', stripes: true },
    f2: { skin: '#f4caa5', shirt: '#f2b705', pants: '#3b5bdb', shoes: '#c92a2a', hair: '#d9a441', style: 'girl' },
    f3: { skin: '#d9a27a', shirt: '#e8590c', pants: '#495057', shoes: '#333', hair: '#3b2412', style: 'boy' },
  };

  function limb(ctx, x, y, a1, l1, a2, l2, w, col) {
    const kx = x + Math.sin(a1) * l1, ky = y + Math.cos(a1) * l1;
    const fx = kx + Math.sin(a2) * l2, fy = ky + Math.cos(a2) * l2;
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(kx, ky); ctx.lineTo(fx, fy); ctx.stroke();
    return [fx, fy];
  }

  // o: {who,x,y,s,dir,walk(фаза|null),sit,arm,armB,talk,shock,sleep,lift,t,alpha}
  function person(ctx, o) {
    const c = CAST[o.who], t = o.t;
    ctx.save();
    ctx.globalAlpha = o.alpha ?? 1;
    ctx.translate(o.x, o.y - (o.lift || 0));
    ctx.scale((o.s || 1) * (o.dir || 1), o.s || 1);
    // тень
    if (!o.sit) {
      ctx.fillStyle = 'rgba(0,0,0,.18)';
      ctx.beginPath(); ctx.ellipse(0, (o.lift || 0) / (o.s || 1), 90 - Math.min(40, (o.lift || 0) / 5), 16, 0, 0, Math.PI * 2); ctx.fill();
    }
    const ph = o.walk, sw = ph == null ? 0 : Math.sin(ph) * 0.6;
    if (ph != null) ctx.translate(0, -Math.abs(Math.cos(ph)) * 14);

    const hipY = -195, dark = shade(c.pants, -25);
    const leg = (a, col) => {
      let a1 = a, a2 = a < 0 ? a * 1.4 : a;
      if (o.sit) { a1 = 1.45; a2 = 0; }
      const w = c.style === 'mom' ? 30 : 44;
      const [fx, fy] = limb(ctx, 0, hipY, a1, 100, a2, 98, w, col);
      ctx.fillStyle = c.shoes;
      ctx.beginPath(); ctx.ellipse(fx + 14, fy + 4, 34, 17, 0, 0, Math.PI * 2); ctx.fill();
    };
    // рука: угол от вертикали вниз, + = вперёд
    const armAngle = (pose, back) => {
      switch (pose) {
        case 'wave': return back ? -sw * 0.8 : 2.7 + Math.sin(t * 14) * 0.35;
        case 'point': return back ? 0.1 : 1.5;
        case 'up': return back ? -2.6 : 2.6;
        case 'thumb': return back ? 0.1 : 1.0;
        case 'type': return 1.15 + Math.sin(t * 22 + (back ? 1.5 : 0)) * 0.08;
        case 'give': return back ? 0.1 : 1.35;
        default: return back ? sw * 0.9 : -sw * 0.9;
      }
    };
    const arm = (back) => {
      const pose = back ? (o.armB || o.arm) : o.arm;
      const a = armAngle(pose, back);
      const col = back ? shade(c.shirt, -30) : c.shirt;
      const bend = pose === 'type' ? 0.6 : pose === 'thumb' ? 1.8 : 0.15;
      const [hx, hy] = limb(ctx, 0, -360, a, 85, a + bend, 80, 34, col);
      ctx.fillStyle = c.skin; ctx.beginPath(); ctx.arc(hx, hy, 21, 0, Math.PI * 2); ctx.fill();
      if (!back && pose === 'thumb') { ctx.fillRect(hx - 6, hy - 40, 12, 30); }
      if (!back && o.hold === 'bread') bread(ctx, hx + 10, hy + 10, 0.7);
      if (!back && o.hold === 'coin') coin(ctx, hx + 18, hy - 8, 0.8);
    };

    leg(o.sit ? 1.45 : -sw, dark);
    arm(true);
    leg(o.sit ? 1.45 : sw, c.pants);
    // туловище
    ctx.fillStyle = c.shirt;
    if (c.style === 'mom') {
      ctx.beginPath(); ctx.moveTo(-60, -390); ctx.lineTo(60, -390); ctx.lineTo(95, -120); ctx.lineTo(-95, -120); ctx.closePath(); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,.85)';
      ctx.beginPath(); ctx.roundRect(-45, -300, 90, 170, 18); ctx.fill(); // фартук
    } else {
      ctx.beginPath(); ctx.roundRect(-62, -395, 124, 215, 42); ctx.fill();
      if (c.stripes) { ctx.fillStyle = '#fff'; for (const dx of [-8, 6, 20]) ctx.fillRect(dx - 3, -385, 6, 195); }
    }
    // голова
    ctx.fillStyle = c.skin; ctx.fillRect(-16, -420, 32, 40);
    ctx.beginPath(); ctx.arc(0, -475, 84, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = c.hair;
    if (c.style === 'mom') {
      ctx.beginPath(); ctx.arc(-10, -500, 88, Math.PI * 0.95, Math.PI * 2.05); ctx.fill();
      ctx.beginPath(); ctx.arc(-70, -555, 42, 0, Math.PI * 2); ctx.fill();
    } else if (c.style === 'girl') {
      ctx.beginPath(); ctx.arc(-6, -495, 90, Math.PI * 0.9, Math.PI * 2.05); ctx.fill();
      ctx.beginPath(); ctx.ellipse(-92, -450, 22, 48, 0.3, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#e03131'; ctx.beginPath(); ctx.arc(-84, -495, 14, 0, Math.PI * 2); ctx.fill();
    } else {
      ctx.beginPath(); ctx.arc(-8, -495, 88, Math.PI * 0.92, Math.PI * 1.98); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-20, -575); ctx.lineTo(70, -545); ctx.lineTo(40, -520); ctx.lineTo(0, -540); ctx.fill();
    }
    // лицо (смотрит в +x)
    const ey = -485, big = o.shock ? 1.6 : 1;
    if (o.sleep) {
      ctx.strokeStyle = '#333'; ctx.lineWidth = 5;
      for (const ex of [22, 56]) { ctx.beginPath(); ctx.arc(ex, ey, 10, 0.2, Math.PI - 0.2); ctx.stroke(); }
    } else {
      const blink = (Math.sin(t * 1.7 + (o.x || 0)) > 0.985) ? 0.15 : 1;
      for (const ex of [22, 58]) {
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(ex, ey, 13 * big, 17 * big * blink, 0, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#1b1b1b'; ctx.beginPath(); ctx.arc(ex + 4, ey + 2, 7 * Math.min(big, 1.2) * blink, 0, Math.PI * 2); ctx.fill();
      }
      ctx.strokeStyle = shade(c.hair, -10); ctx.lineWidth = 6; ctx.lineCap = 'round';
      const br = o.shock ? -14 : 0;
      ctx.beginPath(); ctx.moveTo(10, ey - 28 + br); ctx.lineTo(32, ey - 31 + br); ctx.moveTo(46, ey - 31 + br); ctx.lineTo(70, ey - 28 + br); ctx.stroke();
    }
    ctx.fillStyle = shade(c.skin, -18); ctx.beginPath(); ctx.ellipse(80, -465, 10, 13, 0, 0, Math.PI * 2); ctx.fill();
    // рот
    ctx.fillStyle = '#7a1f1f'; ctx.strokeStyle = '#7a1f1f'; ctx.lineWidth = 6;
    if (o.shock) { ctx.beginPath(); ctx.ellipse(46, -430, 14, 20, 0, 0, Math.PI * 2); ctx.fill(); }
    else if (o.talk) { const m = 4 + Math.abs(Math.sin(t * 17)) * 13; ctx.beginPath(); ctx.ellipse(46, -432, 16, m, 0, 0, Math.PI * 2); ctx.fill(); }
    else if (!o.sleep) { ctx.beginPath(); ctx.arc(46, -445, 20, 0.35, Math.PI - 0.35); ctx.stroke(); }
    // щёки
    ctx.fillStyle = 'rgba(255,90,90,.22)'; ctx.beginPath(); ctx.arc(66, -450, 13, 0, Math.PI * 2); ctx.fill();
    arm(false);
    ctx.restore();
  }

  function shade(hex, p) {
    const n = parseInt(hex.slice(1), 16);
    const f = v => clamp(Math.round(v + (p / 100) * 255), 0, 255);
    return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`;
  }

  // ---------- предметы ----------
  function bread(ctx, x, y, s = 1) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    ctx.fillStyle = '#c47a2c'; ctx.beginPath(); ctx.roundRect(-60, -30, 120, 60, 26); ctx.fill();
    ctx.fillStyle = '#e09a46'; ctx.beginPath(); ctx.roundRect(-55, -30, 110, 32, 20); ctx.fill();
    ctx.strokeStyle = '#8a4f14'; ctx.lineWidth = 5;
    for (const dx of [-30, 0, 30]) { ctx.beginPath(); ctx.moveTo(dx - 10, -22); ctx.lineTo(dx + 10, -4); ctx.stroke(); }
    ctx.restore();
  }
  function coin(ctx, x, y, s = 1, spin = 1) {
    ctx.save(); ctx.translate(x, y); ctx.scale(s * spin, s);
    ctx.fillStyle = '#f5c542'; ctx.strokeStyle = '#b8860b'; ctx.lineWidth = 5;
    ctx.beginPath(); ctx.arc(0, 0, 24, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#b8860b'; ctx.font = `bold 24px ${FONT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('1', 0, 1);
    ctx.restore();
  }
  function bubble(ctx, x, y, text, k = 1, opt = {}) {
    if (k <= 0) return;
    ctx.save(); ctx.translate(x, y);
    const s = 0.6 + 0.4 * Math.min(1, k * 1.4) + Math.sin(Math.min(1, k) * Math.PI) * 0.08;
    ctx.scale(s, s); ctx.globalAlpha = Math.min(1, k * 3);
    const fs = opt.size || 70;
    ctx.font = `${fs}px ${FONT}`;
    const w = Math.max(opt.icon ? 170 : 0, ctx.measureText(text).width + 60), h = opt.icon ? 140 : fs + 50;
    ctx.fillStyle = '#fff'; ctx.strokeStyle = '#1b1b1b'; ctx.lineWidth = 7;
    ctx.beginPath(); ctx.roundRect(-w / 2, -h, w, h, 34);
    ctx.moveTo(-18, -2); ctx.lineTo(opt.tail || -10, 40); ctx.lineTo(24, -2);
    ctx.fill(); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.fillRect(-14, -12, 34, 14);
    if (opt.icon === 'bread') bread(ctx, 0, -h / 2, 0.85);
    else { ctx.fillStyle = opt.color || '#1b1b1b'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(text, 0, -h / 2 + 4); }
    ctx.restore();
  }
  function cloud(ctx, x, y, s) {
    ctx.fillStyle = 'rgba(255,255,255,.9)';
    for (const [dx, dy, r] of [[0, 0, 50], [50, -20, 60], [110, 0, 48], [55, 15, 50]]) { ctx.beginPath(); ctx.arc(x + dx * s, y + dy * s, r * s, 0, Math.PI * 2); ctx.fill(); }
  }
  function portal(ctx, x, y, r, t, alpha = 1) {
    if (r <= 1) return;
    ctx.save(); ctx.globalAlpha = alpha; ctx.translate(x, y);
    const g = ctx.createRadialGradient(0, 0, 0, 0, 0, r);
    g.addColorStop(0, '#ffffff'); g.addColorStop(0.25, '#b388ff'); g.addColorStop(0.6, '#4c2bd6'); g.addColorStop(1, 'rgba(40,0,120,0)');
    ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(0, 0, r, r * 1.25, 0, 0, Math.PI * 2); ctx.fill();
    ctx.lineWidth = 8; ctx.lineCap = 'round';
    for (let i = 0; i < 5; i++) {
      ctx.strokeStyle = i % 2 ? 'rgba(0,255,230,.8)' : 'rgba(255,255,255,.85)';
      ctx.beginPath();
      for (let a = 0; a < 4.5; a += 0.08) {
        const rr = r * 0.95 * (a / 4.5), ang = a * 1.6 + t * 5 + i * (Math.PI * 2 / 5);
        const px = Math.cos(ang) * rr, py = Math.sin(ang) * rr * 1.25;
        a === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.stroke();
    }
    ctx.restore();
  }

  // ---------- фоны ----------
  function apartment(ctx, t) {
    ctx.fillStyle = '#e9d6a6'; ctx.fillRect(0, 0, W, 1300);
    for (let x = 0; x < W; x += 72) { ctx.fillStyle = 'rgba(160,110,50,.12)'; ctx.fillRect(x, 0, 30, 1300); }
    ctx.fillStyle = 'rgba(150,80,40,.25)';
    for (let y = 40; y < 1300; y += 90) for (let x = (y / 90 % 2) * 36 + 15; x < W; x += 72) { ctx.beginPath(); ctx.arc(x, y, 7, 0, Math.PI * 2); ctx.fill(); }
    // ковёр на стене
    ctx.fillStyle = '#8f1d1d'; ctx.fillRect(110, 250, 520, 620);
    ctx.strokeStyle = '#e8b04b'; ctx.lineWidth = 10; ctx.strokeRect(135, 275, 470, 570);
    ctx.strokeStyle = '#1d3b6e'; ctx.lineWidth = 14; ctx.strokeRect(165, 305, 410, 510);
    for (const [s, col] of [[200, '#e8b04b'], [140, '#1d3b6e'], [80, '#e8b04b'], [30, '#f3e3b5']]) {
      ctx.fillStyle = col; ctx.beginPath(); ctx.moveTo(370, 560 - s * 1.2); ctx.lineTo(370 + s, 560); ctx.lineTo(370, 560 + s * 1.2); ctx.lineTo(370 - s, 560); ctx.fill();
    }
    ctx.fillStyle = '#e8b04b'; for (let x = 115; x < 630; x += 14) { ctx.fillRect(x, 870, 5, 22); ctx.fillRect(x, 228, 5, 22); }
    // окно
    ctx.fillStyle = '#9fd3ff'; ctx.fillRect(720, 240, 260, 500);
    cloud(ctx, 760 + (t * 10) % 200, 360, 0.5);
    ctx.strokeStyle = '#f8f8f8'; ctx.lineWidth = 18; ctx.strokeRect(720, 240, 260, 500);
    ctx.beginPath(); ctx.moveTo(850, 240); ctx.lineTo(850, 740); ctx.moveTo(720, 430); ctx.lineTo(980, 430); ctx.stroke();
    ctx.fillStyle = '#e07b39';
    ctx.beginPath(); ctx.moveTo(690, 210); ctx.quadraticCurveTo(760, 500, 700, 800); ctx.lineTo(680, 800); ctx.lineTo(680, 210); ctx.fill();
    ctx.beginPath(); ctx.moveTo(1010, 210); ctx.quadraticCurveTo(940, 500, 1000, 800); ctx.lineTo(1030, 800); ctx.lineTo(1030, 210); ctx.fill();
    ctx.fillStyle = '#6b4a2b'; ctx.fillRect(670, 200, 380, 16);
    // пол
    ctx.fillStyle = '#8a5a2b'; ctx.fillRect(0, 1300, W, 620);
    ctx.strokeStyle = 'rgba(60,30,10,.35)'; ctx.lineWidth = 4;
    for (let y = 1300; y < H; y += 60) for (let x = (y / 60 % 2) * 60; x < W; x += 120) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + 60, y + 60); ctx.stroke(); }
    ctx.fillStyle = '#5c3a1c'; ctx.fillRect(0, 1290, W, 22);
    // тумба с телевизором
    ctx.fillStyle = '#6e4423'; ctx.fillRect(60, 1020, 330, 280);
    ctx.fillStyle = '#7f532d'; ctx.fillRect(80, 1040, 140, 240); ctx.fillRect(230, 1040, 140, 240);
    ctx.fillStyle = '#3d3d3d'; ctx.beginPath(); ctx.roundRect(80, 760, 290, 260, 20); ctx.fill();
    ctx.fillStyle = `hsl(200,30%,${35 + Math.sin(t * 9) * 4}%)`; ctx.beginPath(); ctx.roundRect(105, 785, 200, 175, 30); ctx.fill();
    ctx.fillStyle = '#999'; for (const yy of [810, 860, 910]) { ctx.beginPath(); ctx.arc(335, yy, 12, 0, Math.PI * 2); ctx.fill(); }
    ctx.strokeStyle = '#555'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(225, 760); ctx.lineTo(180, 680); ctx.moveTo(225, 760); ctx.lineTo(280, 690); ctx.stroke();
  }

  function sky(ctx, t, top = '#78b7ff', bot = '#dff0ff') {
    const g = ctx.createLinearGradient(0, 0, 0, 1300); g.addColorStop(0, top); g.addColorStop(1, bot);
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, 1300);
    cloud(ctx, ((t * 18) % 1400) - 250, 220, 1); cloud(ctx, ((t * 12 + 700) % 1400) - 250, 380, 0.7);
  }
  function panelHouse(ctx, x, y, w, h, t, tint = '#c3bdb3') {
    ctx.fillStyle = tint; ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = 'rgba(0,0,0,.12)'; ctx.lineWidth = 3;
    for (let yy = y; yy < y + h; yy += 80) { ctx.beginPath(); ctx.moveTo(x, yy); ctx.lineTo(x + w, yy); ctx.stroke(); }
    let i = 0;
    for (let yy = y + 22; yy < y + h - 60; yy += 80) for (let xx = x + 22; xx < x + w - 40; xx += 70) {
      const lit = ((i++ * 7919) % 11) < 2;
      ctx.fillStyle = lit ? '#ffe9a3' : '#5d7a99'; ctx.fillRect(xx, yy, 40, 46);
    }
  }
  function yardBase(ctx, t) {
    sky(ctx, t);
    panelHouse(ctx, -40, 420, 460, 900, t);
    panelHouse(ctx, 640, 520, 480, 800, t, '#b8b2a6');
    ctx.fillStyle = '#5e9e3d'; ctx.fillRect(0, 1250, W, 90);
    ctx.fillStyle = '#7a7a7a'; ctx.fillRect(0, 1330, W, 590);
    ctx.strokeStyle = 'rgba(0,0,0,.25)'; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.moveTo(150, 1500); ctx.lineTo(240, 1540); ctx.lineTo(260, 1610); ctx.moveTo(820, 1420); ctx.lineTo(760, 1470); ctx.stroke();
    // дерево
    ctx.fillStyle = '#6b4423'; ctx.fillRect(470, 980, 40, 300);
    ctx.fillStyle = '#3f8f2f'; for (const [dx, dy, r] of [[0, 0, 110], [-80, 50, 80], [80, 50, 80], [0, -80, 80]]) { ctx.beginPath(); ctx.arc(490 + dx, 960 + dy, r, 0, Math.PI * 2); ctx.fill(); }
  }
  function kioskScene(ctx, t) {
    sky(ctx, t, '#8cc8ff', '#f4f9ff');
    panelHouse(ctx, -60, 600, 420, 700, t);
    ctx.fillStyle = '#7a7a7a'; ctx.fillRect(0, 1300, W, 620);
    ctx.fillStyle = '#9a9a9a'; ctx.fillRect(0, 1300, W, 40);
    // ларёк
    ctx.fillStyle = '#2f62b8'; ctx.fillRect(560, 820, 440, 500);
    ctx.fillStyle = '#c92a2a'; ctx.fillRect(540, 700, 480, 130);
    ctx.fillStyle = '#ffd43b'; ctx.font = `100px ${FONT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('ХЛЕБ', 780, 768);
    ctx.fillStyle = '#cfe8ff'; ctx.fillRect(600, 880, 360, 230);
    ctx.strokeStyle = '#e9ecef'; ctx.lineWidth = 10; ctx.strokeRect(600, 880, 360, 230);
    ctx.fillStyle = '#ffd8a8'; ctx.beginPath(); ctx.arc(780, 990, 55, 0, Math.PI * 2); ctx.fill(); // продавщица
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(780, 950, 58, Math.PI, 0); ctx.fill();
    ctx.fillStyle = '#222'; ctx.beginPath(); ctx.arc(762, 990, 6, 0, 7); ctx.arc(798, 990, 6, 0, 7); ctx.fill();
    ctx.fillStyle = '#8b5a2b'; ctx.fillRect(590, 1110, 380, 30);
    bread(ctx, 680, 1090, 0.6); bread(ctx, 880, 1090, 0.6);
    ctx.fillStyle = '#fff'; ctx.font = `46px ${FONT}`; ctx.fillText('1993', 780, 1220);
  }
  function photoScene(ctx, t, k) {
    ctx.fillStyle = '#e9d6a6'; ctx.fillRect(0, 0, W, H);
    for (let x = 0; x < W; x += 72) { ctx.fillStyle = 'rgba(160,110,50,.12)'; ctx.fillRect(x, 0, 30, H); }
    ctx.save();
    const s = lerp(1, 1.12, k); ctx.translate(540, 760); ctx.scale(s, s); ctx.translate(-540, -760);
    ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.fillRect(250, 300, 600, 820);
    ctx.fillStyle = '#7b4a1e'; ctx.fillRect(230, 280, 600, 820);
    ctx.fillStyle = '#d4a056'; ctx.fillRect(255, 305, 550, 770);
    ctx.fillStyle = '#3a6fb0'; ctx.fillRect(285, 335, 490, 600);
    // триколор
    ctx.fillStyle = '#fff'; ctx.fillRect(620, 360, 120, 40); ctx.fillStyle = '#1c4fd1'; ctx.fillRect(620, 400, 120, 40); ctx.fillStyle = '#d62828'; ctx.fillRect(620, 440, 120, 40);
    // мультяшный портрет
    ctx.fillStyle = '#2b2f3a'; ctx.beginPath(); ctx.moveTo(330, 935); ctx.quadraticCurveTo(340, 740, 530, 730); ctx.quadraticCurveTo(720, 740, 730, 935); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.moveTo(490, 735); ctx.lineTo(570, 735); ctx.lineTo(530, 860); ctx.fill();
    ctx.fillStyle = '#7a1f1f'; ctx.beginPath(); ctx.moveTo(518, 760); ctx.lineTo(542, 760); ctx.lineTo(548, 860); ctx.lineTo(530, 880); ctx.lineTo(512, 860); ctx.fill();
    ctx.fillStyle = '#efbf9a'; ctx.beginPath(); ctx.ellipse(530, 600, 120, 145, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#e8e8e8'; ctx.beginPath(); ctx.ellipse(520, 480, 130, 60, -0.1, Math.PI, 0); ctx.fill();
    ctx.beginPath(); ctx.ellipse(470, 485, 90, 40, -0.3, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#222'; ctx.beginPath(); ctx.ellipse(485, 590, 9, 6, 0, 0, 7); ctx.ellipse(575, 590, 9, 6, 0, 0, 7); ctx.fill();
    ctx.strokeStyle = '#555'; ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(460, 562); ctx.lineTo(505, 565); ctx.moveTo(555, 565); ctx.lineTo(600, 562); ctx.stroke();
    ctx.fillStyle = '#d99e7a'; ctx.beginPath(); ctx.ellipse(530, 630, 22, 32, 0, 0, 7); ctx.fill();
    ctx.strokeStyle = '#8a3b2b'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(490, 690); ctx.quadraticCurveTo(530, 700, 570, 690); ctx.stroke();
    ctx.fillStyle = '#f3e3b5'; ctx.fillRect(285, 950, 490, 105);
    ctx.fillStyle = '#3b2412'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.font = `48px ${FONT}`; ctx.fillText('ПРЕЗИДЕНТ', 530, 985);
    ctx.font = `36px ${FONT}`; ctx.fillText('Б. Н. ЕЛЬЦИН', 530, 1030);
    ctx.restore();
  }
  function computerScene(ctx, t, t0) {
    ctx.fillStyle = '#9fb89a'; ctx.fillRect(0, 0, W, 1350);
    for (let x = 0; x < W; x += 80) { ctx.fillStyle = 'rgba(40,70,40,.10)'; ctx.fillRect(x, 0, 36, 1350); }
    ctx.fillStyle = '#7a5130'; ctx.fillRect(0, 1350, W, 570);
    // плакат
    ctx.fillStyle = '#fff'; ctx.fillRect(90, 220, 260, 340); ctx.fillStyle = '#1c7ed6'; ctx.fillRect(110, 240, 220, 240);
    ctx.fillStyle = '#ffd43b'; ctx.font = `44px ${FONT}`; ctx.textAlign = 'center'; ctx.fillText('ДЕНДИ', 220, 525);
    ctx.fillStyle = '#fab005'; ctx.beginPath(); ctx.arc(220, 360, 70, 0, 7); ctx.fill();
    // стол
    ctx.fillStyle = '#a0703f'; ctx.fillRect(380, 1100, 700, 40); ctx.fillStyle = '#86592f'; ctx.fillRect(400, 1140, 30, 320); ctx.fillRect(1020, 1140, 30, 320);
    // системник
    ctx.fillStyle = '#e3dccb'; ctx.fillRect(900, 760, 150, 340); ctx.fillStyle = '#bdb5a2'; ctx.fillRect(920, 800, 110, 26); ctx.fillRect(920, 840, 110, 26);
    ctx.fillStyle = '#2f9e44'; ctx.beginPath(); ctx.arc(1010, 1050, 9, 0, 7); ctx.fill();
    // монитор
    ctx.fillStyle = '#d8d0bd'; ctx.beginPath(); ctx.roundRect(440, 600, 440, 420, 24); ctx.fill();
    ctx.fillStyle = '#c9c0ab'; ctx.fillRect(590, 1020, 140, 50); ctx.fillRect(540, 1065, 240, 35);
    const sx = 475, sy = 635, cw = 20, cols = 19, rows = 17;
    ctx.fillStyle = '#071a07'; ctx.fillRect(sx, sy, cols * cw, rows * cw);
    // змейка
    const path = [];
    for (let x = 1; x < cols - 2; x++) path.push([x, 2]);
    for (let y = 2; y < rows - 2; y++) path.push([cols - 2, y]);
    for (let x = cols - 2; x > 1; x--) path.push([x, rows - 2]);
    for (let y = rows - 2; y > 5; y--) path.push([2, y]);
    for (let x = 2; x < cols - 5; x++) path.push([x, 6]);
    for (let y = 6; y < rows - 5; y++) path.push([cols - 5, y]);
    for (let x = cols - 5; x > 1; x--) path.push([x, rows - 5]);
    for (let y = rows - 5; y > 2; y--) path.push([1, y]);
    const P = path.length, h = Math.floor(Math.max(0, t - t0) * 9), eaten = Math.floor(h / 11);
    const len = 4 + eaten;
    const apple = path[((eaten + 1) * 11) % P];
    ctx.fillStyle = '#ff3b3b'; ctx.fillRect(sx + apple[0] * cw + 3, sy + apple[1] * cw + 3, cw - 6, cw - 6);
    for (let i = 0; i < len; i++) {
      const [x, y] = path[((h - i) % P + P) % P];
      ctx.fillStyle = i === 0 ? '#b2ff59' : '#4caf50'; ctx.fillRect(sx + x * cw + 1, sy + y * cw + 1, cw - 2, cw - 2);
    }
    ctx.fillStyle = '#b2ff59'; ctx.font = `22px ${FONT}`; ctx.textAlign = 'left'; ctx.fillText('ОЧКИ: ' + eaten * 10, sx + 8, sy + 16);
    ctx.fillStyle = 'rgba(255,255,255,.06)'; for (let y = sy; y < sy + rows * cw; y += 6) ctx.fillRect(sx, y, cols * cw, 2);
    // клавиатура
    ctx.fillStyle = '#e3dccb'; ctx.beginPath(); ctx.roundRect(470, 1070, 380, 34, 8); ctx.fill();
    // стул
    ctx.fillStyle = '#4a3020'; ctx.fillRect(140, 1270, 260, 26); ctx.fillRect(160, 1296, 22, 200); ctx.fillRect(360, 1296, 22, 200); ctx.fillRect(140, 900, 26, 380);
  }
  function nightScene(ctx, t, t0) {
    ctx.fillStyle = '#1b2440'; ctx.fillRect(0, 0, W, 1350);
    ctx.fillStyle = '#2a2018'; ctx.fillRect(0, 1350, W, 570);
    // окно с луной
    ctx.fillStyle = '#0b1026'; ctx.fillRect(640, 180, 340, 440);
    for (let i = 0; i < 18; i++) { const x = 660 + (i * 97) % 300, y = 200 + (i * 53) % 400; ctx.fillStyle = `rgba(255,255,255,${0.4 + 0.6 * Math.abs(Math.sin(t * 2 + i))})`; ctx.fillRect(x, y, 4, 4); }
    ctx.fillStyle = '#fff6c9'; ctx.beginPath(); ctx.arc(890, 280, 50, 0, 7); ctx.fill();
    ctx.fillStyle = '#0b1026'; ctx.beginPath(); ctx.arc(870, 265, 46, 0, 7); ctx.fill();
    ctx.strokeStyle = '#d7dbe8'; ctx.lineWidth = 16; ctx.strokeRect(640, 180, 340, 440);
    ctx.beginPath(); ctx.moveTo(810, 180); ctx.lineTo(810, 620); ctx.stroke();
    // флаг СССР — распадается
    const k = seg(t, t0 + 0.9, t0 + 2.4);
    const fx = 90, fy = 220, fw = 460, fh = 300, n = 6, m = 4;
    for (let i = 0; i < n; i++) for (let j = 0; j < m; j++) {
      const r = ((i * 7 + j * 13) % 10) / 10, kk = clamp(k * 1.4 - r * 0.4);
      ctx.save();
      const px = fx + i * fw / n, py = fy + j * fh / m;
      ctx.translate(px + fw / n / 2 + (r - 0.5) * 200 * kk, py + fh / m / 2 + 900 * kk * kk);
      ctx.rotate((r - 0.5) * 4 * kk); ctx.globalAlpha = 1 - clamp(kk * 1.2 - 0.2);
      ctx.beginPath(); ctx.rect(-fw / n / 2, -fh / m / 2, fw / n + 1, fh / m + 1); ctx.clip();
      ctx.translate(-(px + fw / n / 2), -(py + fh / m / 2));
      ctx.fillStyle = '#c40000'; ctx.fillRect(fx, fy, fw, fh);
      ctx.fillStyle = '#ffd700'; star(ctx, fx + 80, fy + 70, 30); ctx.font = `64px ${FONT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('СССР', fx + 280, fy + 160);
      ctx.restore();
    }
    // кровать
    ctx.fillStyle = '#5c3a1c'; ctx.fillRect(70, 1120, 60, 420); ctx.fillRect(950, 1220, 50, 320);
    ctx.fillStyle = '#e9ecef'; ctx.beginPath(); ctx.roundRect(130, 1260, 820, 140, 30); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.ellipse(250, 1230, 120, 55, 0, 0, 7); ctx.fill();
  }
  function star(ctx, x, y, r) {
    ctx.beginPath();
    for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * 0.45 : r; ctx.lineTo(x + Math.cos(a) * rr, y + Math.sin(a) * rr); }
    ctx.fill();
  }
  function calendar(ctx, x, y, day, flip, alpha) {
    if (alpha <= 0) return;
    ctx.save(); ctx.globalAlpha = alpha; ctx.translate(x, y);
    ctx.fillStyle = '#c92a2a'; ctx.beginPath(); ctx.roundRect(-130, -170, 260, 70, 14); ctx.fill();
    ctx.fillStyle = '#fff'; ctx.font = `38px ${FONT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('ДЕНЬ', 0, -135);
    ctx.scale(1, 1 - Math.sin(flip * Math.PI) * 0.9);
    ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.roundRect(-130, -100, 260, 220, 14); ctx.fill();
    ctx.fillStyle = day === 3 ? '#c92a2a' : '#1b1b1b'; ctx.font = `170px ${FONT}`; ctx.fillText(String(day), 0, 15);
    ctx.restore();
  }

  // ---------- сцены по таймингу озвучки ----------
  const CUTS = [13.9, 16.1, 19.0, 24.3, 30.05, 33.95, 38.85];

  function scene(ctx, t) {
    if (t < 13.9) {
      apartment(ctx, t);
      const app = seg(t, 0.1, 1.0);
      if (t < 1.6) portal(ctx, 330, 1150, 260 * Math.sin(seg(t, 0, 1.6) * Math.PI), t);
      const wk = seg(t, 1.2, 2.9), out = seg(t, 13.35, 13.9);
      let tx = lerp(330, 430, ease(wk)) + out * 500;
      let dir = 1;
      if (inT(t, 4.3, 5.4) || inT(t, 6.0, 6.6)) dir = -1;
      const shock = inT(t, 11.38, 13.0), jump = shock ? Math.sin(seg(t, 11.38, 11.9) * Math.PI) * 90 : 0;
      person(ctx, {
        who: 'tim', x: tx, y: 1460, s: 1, dir, t, alpha: app,
        walk: (wk > 0 && wk < 1) || out > 0 ? t * 9 : null,
        talk: inT(t, 4.36, 6.9) || inT(t, 12.2, 12.8),
        shock, lift: jump, arm: inT(t, 13.3, 13.9) ? 'thumb' : inT(t, 4.4, 5.9) ? 'point' : null,
      });
      bubble(ctx, tx + 40, 840, '?', seg(t, 6.0, 6.3) * (t < 7.0 ? 1 : 0), { size: 110 });
      bubble(ctx, tx + 40, 840, '?!', seg(t, 11.4, 11.6) * (t < 13.0 ? 1 : 0), { size: 110, color: '#c92a2a' });
      bubble(ctx, tx + 40, 840, 'ОК!', seg(t, 13.3, 13.45), { size: 80 });
      // мама
      const mk = seg(t, 7.0, 8.6);
      if (t > 6.9) {
        person(ctx, {
          who: 'mom', x: lerp(1200, 790, ease(mk)), y: 1470, s: 1.12, dir: -1, t,
          walk: mk > 0 && mk < 1 ? t * 8 : null, talk: inT(t, 8.77, 10.5),
          arm: inT(t, 8.77, 9.4) ? 'wave' : inT(t, 9.5, 10.7) ? 'point' : null,
        });
        bubble(ctx, 760, 760, '', seg(t, 9.6, 9.9) * (t < 11.2 ? 1 : 0), { icon: 'bread', tail: 30 });
      }
    } else if (t < 16.1) {
      yardBase(ctx, t);
      const wave = t > 14.3 ? 'wave' : null;
      person(ctx, { who: 'f2', x: 650, y: 1520, s: 0.9, dir: -1, t, arm: wave });
      person(ctx, { who: 'f1', x: 810, y: 1540, s: 0.95, dir: -1, t, arm: t > 14.6 ? 'wave' : null });
      person(ctx, { who: 'f3', x: 960, y: 1520, s: 0.92, dir: -1, t, arm: wave });
      const wk = seg(t, 13.9, 15.2);
      person(ctx, { who: 'tim', x: lerp(-120, 360, ease(wk)), y: 1560, s: 1, dir: 1, t, walk: wk < 1 ? t * 9 : null, arm: t > 15.3 ? 'wave' : null });
      bubble(ctx, 810, 930, 'Привет!', seg(t, 14.6, 14.9), { size: 60 });
    } else if (t < 19.0) {
      photoScene(ctx, t, seg(t, 16.1, 19.0));
      person(ctx, { who: 'tim', x: 170, y: 1580, s: 0.85, dir: 1, t, shock: t > 17.8 });
    } else if (t < 24.3) {
      kioskScene(ctx, t);
      const wk = seg(t, 19.0, 20.3), turn = t > 21.7;
      const tx = lerp(-100, 400, ease(wk));
      const give = inT(t, 20.3, 21.2);
      person(ctx, {
        who: 'tim', x: tx, y: 1560, s: 1, dir: turn && inT(t, 22.6, 23.4) ? -1 : 1, t,
        walk: wk < 1 ? t * 9 : null, arm: give ? 'give' : turn && t > 23.3 ? 'up' : null,
        hold: t > 21.4 ? 'bread' : t > 20.0 && t < 20.4 ? 'coin' : null,
        talk: inT(t, 22.7, 24.1), shock: inT(t, 23.3, 24.2),
      });
      const ck = seg(t, 20.4, 21.2);
      if (ck > 0 && ck < 1) coin(ctx, lerp(560, 700, ck), 1110 - Math.sin(ck * Math.PI) * 220, 1.2, Math.cos(t * 20));
      bubble(ctx, tx + 40, 870, 'Где я?', seg(t, 22.7, 22.95) * (t < 23.3 ? 1 : 0), { size: 64 });
      bubble(ctx, tx + 40, 870, '90-е?!', seg(t, 23.3, 23.5), { size: 70, color: '#c92a2a' });
    } else if (t < 30.05) {
      yardBase(ctx, t);
      // мяч
      const bx = 540 + Math.sin(t * 1.6) * 380, by = 1680 - Math.abs(Math.sin(t * 5)) * 240;
      ctx.fillStyle = 'rgba(0,0,0,.2)'; ctx.beginPath(); ctx.ellipse(bx, 1690, 30, 8, 0, 0, 7); ctx.fill();
      ctx.fillStyle = '#e03131'; ctx.beginPath(); ctx.arc(bx, by - 10, 34, 0, 7); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.fillRect(bx - 34, by - 16, 68, 10);
      const kids = [['f1', 0], ['f2', 2.1], ['f3', 4.2]];
      for (const [w, p] of kids) {
        const a = t * 1.4 + p, x = 540 + Math.cos(a) * 330, y = 1520 + Math.sin(a) * 70;
        person(ctx, { who: w, x, y, s: 0.85 + Math.sin(a) * 0.05, dir: -Math.sin(a) > 0 ? 1 : -1, t, walk: t * 13 + p, arm: inT(t, 28.4, 29.9) ? 'up' : null });
      }
      const rk = seg(t, 24.5, 25.6), yay = inT(t, 28.4, 29.3);
      person(ctx, {
        who: 'tim', x: lerp(-150, 540, ease(rk)), y: 1700, s: 1.05, dir: 1, t,
        walk: rk < 1 ? t * 13 : null, lift: yay ? Math.sin(seg(t, 28.4, 29.3) * Math.PI) * 200 : 0,
        arm: yay ? 'up' : null, talk: inT(t, 27.5, 29.8),
      });
      bubble(ctx, 600, 980, 'Я-ху!', seg(t, 28.4, 28.6) * (t < 29.4 ? 1 : 0), { size: 80, color: '#c92a2a' });
      bubble(ctx, 600, 980, 'Классно!', seg(t, 29.15, 29.35), { size: 66 });
    } else if (t < 33.95) {
      yardBase(ctx, t);
      const pk = seg(t, 32.85, 33.6);
      portal(ctx, 540, 1040, 240 * ease(pk), t);
      calendar(ctx, 540, 420, t < 31.24 ? 1 : t < 32.09 ? 2 : 3, Math.max(seg(t, 31.1, 31.4) * (t < 31.4 ? 1 : 0), seg(t, 31.95, 32.25) * (t < 32.25 ? 1 : 0)), seg(t, 30.6, 30.9) * (1 - seg(t, 33.5, 33.8)));
      person(ctx, { who: 'f1', x: 700, y: 1560, s: 0.95, dir: -1, t, talk: inT(t, 30.1, 33.7), arm: inT(t, 32.9, 33.9) ? 'point' : null });
      person(ctx, { who: 'f2', x: 880, y: 1600, s: 0.9, dir: -1, t, talk: inT(t, 31.2, 32.0) });
      person(ctx, { who: 'tim', x: 330, y: 1600, s: 1, dir: 1, t, shock: t > 32.9 });
    } else if (t < 38.85) {
      computerScene(ctx, t, 34.4);
      const wk = seg(t, 33.95, 34.6);
      if (wk < 1) person(ctx, { who: 'tim', x: lerp(-100, 300, wk), y: 1460, s: 1, dir: 1, t, walk: t * 9 });
      else person(ctx, { who: 'tim', x: 300, y: 1455, s: 1, dir: 1, t, sit: true, arm: 'type', talk: false });
      bubble(ctx, 310, 760, '♥', seg(t, 37.1, 37.4), { size: 90, color: '#e03131' });
    } else {
      nightScene(ctx, t, 38.85);
      // Тимофей под одеялом
      ctx.save(); ctx.translate(250, 1190); ctx.rotate(-1.5);
      person(ctx, { who: 'tim', x: 0, y: 356, s: 0.75, dir: 1, t, sleep: t > 40.9 });
      ctx.restore();
      ctx.fillStyle = '#3b5bdb'; ctx.beginPath(); ctx.roundRect(330, 1180, 640, 200, 40); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,.15)'; for (let x = 360; x < 950; x += 70) ctx.fillRect(x, 1190, 30, 180);
      if (t > 40.9) for (let i = 0; i < 3; i++) {
        const k = ((t - 40.9) * 0.8 + i / 3) % 1;
        ctx.globalAlpha = Math.sin(k * Math.PI); ctx.fillStyle = '#fff'; ctx.font = `${50 + i * 14}px ${FONT}`; ctx.textAlign = 'center';
        ctx.fillText('Z', 320 + k * 120 + i * 20, 1050 - k * 260); ctx.globalAlpha = 1;
      }
    }
  }

  // ---------- субтитры (караоке) ----------
  function subtitles(ctx, t, lines) {
    const g = ctx.createLinearGradient(0, 1560, 0, H); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(0.35, 'rgba(0,0,0,.55)'); g.addColorStop(1, 'rgba(0,0,0,.75)');
    ctx.fillStyle = g; ctx.fillRect(0, 1560, W, H - 1560);
    const line = lines.find(l => t >= l.start && t < l.end);
    if (!line) return;
    const fs = 76; ctx.font = `${fs}px ${FONT}`; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
    const space = ctx.measureText(' ').width, maxW = 960;
    const rows = [[]]; let rw = 0;
    for (const w of line.words) {
      const ww = ctx.measureText(w.text).width;
      if (rw > 0 && rw + space + ww > maxW) { rows.push([]); rw = 0; }
      rows[rows.length - 1].push({ ...w, ww }); rw += (rw ? space : 0) + ww;
    }
    let cur = -1; line.words.forEach((w, i) => { if (t >= w.start) cur = i; });
    const appear = seg(t, line.start, line.start + 0.15);
    let idx = 0;
    rows.forEach((row, ri) => {
      const total = row.reduce((s, w) => s + w.ww, 0) + space * (row.length - 1);
      let x = (W - total) / 2; const y = 1740 + (ri - (rows.length - 1) / 2) * (fs * 1.2) + (1 - appear) * 30;
      for (const w of row) {
        const on = idx === cur;
        const pop = on ? 1.08 + 0.1 * (1 - seg(t, line.words[idx].start, line.words[idx].start + 0.12)) : 1;
        ctx.save(); ctx.globalAlpha = appear; ctx.translate(x + w.ww / 2, y); ctx.scale(pop, pop);
        ctx.lineWidth = 12; ctx.strokeStyle = '#000'; ctx.lineJoin = 'round'; ctx.strokeText(w.text, -w.ww / 2, 0);
        if (on) { ctx.shadowColor = 'rgba(255,40,40,.8)'; ctx.shadowBlur = 24; }
        ctx.fillStyle = on ? '#ff2a2a' : '#fff'; ctx.fillText(w.text, -w.ww / 2, 0);
        ctx.restore();
        x += w.ww + space; idx++;
      }
    });
  }

  window.drawFrame = function (ctx, t, lines) {
    ctx.save();
    ctx.clearRect(0, 0, W, H);
    scene(ctx, t);
    let f = 0; for (const c of CUTS) f = Math.max(f, 1 - Math.abs(t - c) / 0.2);
    if (t < 0.25) f = Math.max(f, 1 - t / 0.25);
    if (f > 0) { ctx.fillStyle = `rgba(0,0,0,${f})`; ctx.fillRect(0, 0, W, H); }
    subtitles(ctx, t, lines);
    ctx.restore();
  };
})();
