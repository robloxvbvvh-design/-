// Симулятор Учителя 3D — сцена, анимации и ход урока.
(() => {
  'use strict';

  const $ = s => document.querySelector(s);
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const lerp = (a, b, k) => a + (b - a) * k;
  const easeIO = t => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);

  const LESSONS_PER_YEAR = 3;
  const SAVE_KEY = 'teacher-sim-3d-v1';

  // ======================================================================
  // Сохранение
  // ======================================================================
  let S = null;

  function makeStudents() {
    const boys = shuffle(NAMES.boys), girls = shuffle(NAMES.girls), last = shuffle(NAMES.last);
    const skins = ['#f2c9a5', '#e8b48f', '#d79f78', '#f5d6bd', '#c98d63'];
    const hairs = ['#3b2516', '#1e1612', '#6b3f1f', '#d9b25f', '#a8501f', '#4a2e1a'];
    const shirts = ['#e4574a', '#3f7fd1', '#45a36b', '#f0b43c', '#8b5cc4', '#ef7fa6', '#2fb3b3', '#f2f2f2', '#ff8c42'];
    const list = [];
    for (let i = 0; i < 18; i++) {
      const girl = i % 2 === 1;
      const ln = last[i % last.length];
      list.push({
        name: girl ? girls[i >> 1] : boys[i >> 1],
        last: girl ? (ln.endsWith('ий') ? ln.slice(0, -2) + 'ая' : ln + 'а') : ln,
        girl,
        skill: Math.round((0.25 + Math.random() * 0.6) * 100) / 100,
        skin: pick(skins), hair: pick(hairs), shirt: pick(shirts),
        pants: pick(['#2d3a5c', '#3b3b44', '#4b3a2f', '#2f4a3a']),
        marks: [],
      });
    }
    return shuffle(list);
  }

  function newState(name, gender) {
    return { teacher: name, gender, grade: 1, rep: 50, done: {}, lessons: 0, students: makeStudents(), stats: { five: 0, one: 0, fair: 0, unfair: 0 } };
  }
  function save() { try { localStorage.setItem(SAVE_KEY, JSON.stringify(S)); } catch (e) { /* без сохранения */ } }
  function load() { try { return JSON.parse(localStorage.getItem(SAVE_KEY)); } catch (e) { return null; } }

  // ======================================================================
  // Звук (WebAudio, без файлов)
  // ======================================================================
  let actx = null, muted = false;
  function audio() {
    if (!actx) { try { actx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { actx = null; } }
    if (actx && actx.state === 'suspended') actx.resume();
    return actx;
  }
  function tone(freq, dur, type = 'sine', vol = 0.15, when = 0) {
    const a = audio();
    if (!a || muted) return;
    const t = a.currentTime + when;
    const o = a.createOscillator(), g = a.createGain();
    o.type = type; o.frequency.setValueAtTime(freq, t);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(vol, t + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(a.destination);
    o.start(t); o.stop(t + dur + 0.05);
  }
  const SFX = {
    bell() { for (let i = 0; i < 12; i++) { tone(1318, 0.22, 'triangle', 0.07, i * 0.11); tone(1760, 0.16, 'sine', 0.04, i * 0.11 + 0.05); } },
    good() { tone(660, 0.15, 'sine', 0.14); tone(880, 0.15, 'sine', 0.14, 0.1); tone(1320, 0.3, 'sine', 0.12, 0.2); },
    bad() { tone(220, 0.3, 'sawtooth', 0.06); tone(150, 0.45, 'sawtooth', 0.06, 0.15); },
    click() { tone(900, 0.05, 'square', 0.03); },
    pop() { tone(520, 0.08, 'sine', 0.1); tone(780, 0.08, 'sine', 0.08, 0.06); },
    blip() { tone(380 + Math.random() * 160, 0.03, 'triangle', 0.025); },
    chalk() { tone(2400 + Math.random() * 800, 0.025, 'square', 0.012); },
    paper() { tone(300 + Math.random() * 200, 0.06, 'triangle', 0.04); },
    fanfare() { [523, 659, 784, 1047, 784, 1047].forEach((f, i) => tone(f, 0.35, 'triangle', 0.11, i * 0.14)); },
  };

  // ======================================================================
  // Three.js: сцена
  // ======================================================================
  THREE.ColorManagement.legacyMode = false;
  const canvas = $('#scene');
  if (typeof THREE === 'undefined') { window.__fatal('Не загрузилась библиотека 3D-графики (three.min.js).'); return; }
  let renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); }
  catch (e) { window.__fatal('Браузер не поддерживает WebGL (3D-графику).'); return; }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputEncoding = THREE.sRGBEncoding;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#a9cdea');
  const camera = new THREE.PerspectiveCamera(55, window.innerWidth / window.innerHeight, 0.05, 100);

  window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });

  const matCache = {};
  function M(color, opts) {
    const k = color + (opts ? JSON.stringify(opts) : '');
    return matCache[k] || (matCache[k] = new THREE.MeshStandardMaterial(Object.assign({ color, roughness: 0.85, metalness: 0 }, opts)));
  }
  function mesh(geo, mat, x, y, z, parent) {
    const m = new THREE.Mesh(geo, typeof mat === 'string' ? M(mat) : mat);
    m.position.set(x || 0, y || 0, z || 0);
    m.castShadow = true; m.receiveShadow = true;
    (parent || scene).add(m);
    return m;
  }
  const box = (w, h, d, mat, x, y, z, p) => mesh(new THREE.BoxGeometry(w, h, d), mat, x, y, z, p);
  const sph = (r, mat, x, y, z, p) => mesh(new THREE.SphereGeometry(r, 18, 14), mat, x, y, z, p);
  const cyl = (rt, rb, h, mat, x, y, z, p) => mesh(new THREE.CylinderGeometry(rt, rb, h, 18), mat, x, y, z, p);

  function canvasTex(w, h, draw) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    draw(ctx, w, h);
    const tex = new THREE.CanvasTexture(c);
    tex.encoding = THREE.sRGBEncoding;
    tex.anisotropy = 4;
    return { tex, canvas: c, ctx };
  }

  // ---------- Свет ----------
  scene.add(new THREE.HemisphereLight('#fff6e8', '#7a6048', 0.75));
  const sun = new THREE.DirectionalLight('#fff1d6', 1.25);
  sun.position.set(-11, 9, 1);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10, near: 1, far: 30 });
  sun.shadow.bias = -0.0005;
  scene.add(sun);
  const fill = new THREE.PointLight('#fff2dd', 0.35, 20);
  fill.position.set(1, 3.3, -1);
  scene.add(fill);

  // ---------- Комната ----------
  const ROOM = { x: 6, zf: -7, zb: 6.5, h: 3.6 };
  {
    const wood = canvasTex(512, 512, (c, w, h) => {
      for (let i = 0; i < 8; i++) {
        c.fillStyle = ['#b98a5a', '#c39563', '#ad7d4e', '#bf8f5d'][i % 4];
        c.fillRect(0, i * 64, w, 64);
        c.fillStyle = 'rgba(70,40,15,.35)';
        c.fillRect(0, i * 64, w, 2);
        c.fillRect((i * 173) % 512, i * 64, 2, 64);
        c.fillStyle = 'rgba(80,45,20,.12)';
        for (let j = 0; j < 6; j++) c.fillRect(0, i * 64 + 8 + j * 9 + (j % 2) * 3, w, 1);
      }
    });
    wood.tex.wrapS = wood.tex.wrapT = THREE.RepeatWrapping;
    wood.tex.repeat.set(3, 3.4);
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.x * 2, ROOM.zb - ROOM.zf),
      new THREE.MeshStandardMaterial({ map: wood.tex, roughness: 0.7 }));
    floor.rotation.x = -Math.PI / 2;
    floor.position.z = (ROOM.zb + ROOM.zf) / 2;
    floor.receiveShadow = true;
    scene.add(floor);

    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(ROOM.x * 2, ROOM.zb - ROOM.zf), M('#f4f1ea'));
    ceil.rotation.x = Math.PI / 2;
    ceil.position.set(0, ROOM.h, floor.position.z);
    scene.add(ceil);

    // стены — плоскости, видимые только изнутри (камера может стоять «за стеной»)
    const wall = (w, x, z, ry) => {
      const g = new THREE.Group();
      g.position.set(x, 0, z); g.rotation.y = ry;
      const up = new THREE.Mesh(new THREE.PlaneGeometry(w, ROOM.h), M('#efe5cf'));
      up.position.y = ROOM.h / 2; up.receiveShadow = true; g.add(up);
      const low = new THREE.Mesh(new THREE.PlaneGeometry(w, 1.05), M('#7fa68d'));
      low.position.set(0, 0.525, 0.005); low.receiveShadow = true; g.add(low);
      const strip = new THREE.Mesh(new THREE.PlaneGeometry(w, 0.05), M('#5d7f69'));
      strip.position.set(0, 1.07, 0.008); g.add(strip);
      scene.add(g);
      return g;
    };
    const depth = ROOM.zb - ROOM.zf, cz = (ROOM.zb + ROOM.zf) / 2;
    wall(ROOM.x * 2, 0, ROOM.zf, 0);
    wall(ROOM.x * 2, 0, ROOM.zb, Math.PI);
    wall(depth, -ROOM.x, cz, Math.PI / 2);
    wall(depth, ROOM.x, cz, -Math.PI / 2);

    // окна
    const sky = canvasTex(256, 256, (c, w, h) => {
      const gr = c.createLinearGradient(0, 0, 0, h);
      gr.addColorStop(0, '#6fb2ec'); gr.addColorStop(0.7, '#cfe7fb'); gr.addColorStop(1, '#cfe7fb');
      c.fillStyle = gr; c.fillRect(0, 0, w, h);
      c.fillStyle = 'rgba(255,255,255,.9)';
      [[60, 60, 30], [90, 55, 24], [180, 90, 26], [205, 92, 20]].forEach(([x, y, r]) => { c.beginPath(); c.arc(x, y, r, 0, 7); c.fill(); });
      c.fillStyle = '#4f8c4a';
      for (let i = 0; i < 9; i++) { c.beginPath(); c.arc(i * 32 + 10, 230 - (i % 3) * 14, 34, 0, 7); c.fill(); }
    });
    [-4.2, -0.6, 3].forEach(z => {
      const glass = new THREE.Mesh(new THREE.PlaneGeometry(2.1, 1.8), new THREE.MeshBasicMaterial({ map: sky.tex }));
      glass.rotation.y = Math.PI / 2; glass.position.set(-ROOM.x + 0.01, 2.05, z); scene.add(glass);
      const fr = '#f7f7f2';
      box(0.08, 0.08, 2.2, fr, -ROOM.x + 0.04, 2.98, z);
      box(0.08, 0.08, 2.2, fr, -ROOM.x + 0.04, 1.12, z);
      box(0.08, 1.9, 0.08, fr, -ROOM.x + 0.04, 2.05, z - 1.08);
      box(0.08, 1.9, 0.08, fr, -ROOM.x + 0.04, 2.05, z + 1.08);
      box(0.06, 1.8, 0.05, fr, -ROOM.x + 0.04, 2.05, z);
      box(0.06, 0.05, 2.1, fr, -ROOM.x + 0.04, 2.5, z);
      box(0.3, 0.05, 2.4, '#e9e6dc', -ROOM.x + 0.15, 1.08, z);
      // цветок на подоконнике
      cyl(0.09, 0.07, 0.16, '#c0643c', -ROOM.x + 0.17, 1.19, z + 0.6);
      for (let i = 0; i < 4; i++) sph(0.08, '#3f8f45', -ROOM.x + 0.17 + Math.sin(i * 2) * 0.05, 1.33 + i * 0.04, z + 0.6 + Math.cos(i * 2) * 0.05);
    });

    // лампы
    for (let x of [-2.8, 2.8]) for (let z of [-4.5, -0.5, 3.5]) {
      const l = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.06, 0.3), new THREE.MeshBasicMaterial({ color: '#fffbea' }));
      l.position.set(x, ROOM.h - 0.04, z); scene.add(l);
    }

    // дверь
    box(0.05, 2.2, 1.05, '#8a5a35', ROOM.x - 0.03, 1.1, 4.6);
    box(0.06, 2.3, 0.08, '#f2efe6', ROOM.x - 0.03, 1.15, 4.04);
    box(0.06, 2.3, 0.08, '#f2efe6', ROOM.x - 0.03, 1.15, 5.16);
    box(0.06, 0.08, 1.2, '#f2efe6', ROOM.x - 0.03, 2.28, 4.6);
    sph(0.04, '#d6b443', ROOM.x - 0.08, 1.05, 4.2);

    // шкафы у задней стены
    for (let i = 0; i < 4; i++) {
      const x = -4.5 + i * 1.5;
      box(1.4, 1.9, 0.45, '#c9a06c', x, 0.95, ROOM.zb - 0.25);
      box(1.3, 0.04, 0.42, '#a77f4f', x, 1.3, ROOM.zb - 0.27);
      for (let b = 0; b < 8; b++) {
        const h = 0.24 + Math.random() * 0.1;
        box(0.1, h, 0.28, pick(['#c0392b', '#2e86c1', '#27ae60', '#f1c40f', '#8e44ad', '#e67e22']), x - 0.5 + b * 0.13, 1.33 + h / 2, ROOM.zb - 0.32);
      }
    }
    // глобус на шкафу
    sph(0.22, '#3d8fd6', -1.5, 2.22, ROOM.zb - 0.25);
    cyl(0.05, 0.12, 0.12, '#6d4a2b', -1.5, 1.96, ROOM.zb - 0.25);
  }

  // ---------- Плакаты ----------
  function poster(w, h, x, y, z, ry, draw) {
    const t = canvasTex(Math.round(w * 200), Math.round(h * 200), draw);
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshStandardMaterial({ map: t.tex, roughness: 0.9 }));
    m.position.set(x, y, z); m.rotation.y = ry; scene.add(m);
    return t;
  }
  poster(1.1, 1.4, -4.6, 2.0, ROOM.zf + 0.02, 0, (c, w, h) => {
    c.fillStyle = '#fff8e1'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#c0392b'; c.font = 'bold 30px Nunito, sans-serif'; c.textAlign = 'center';
    c.fillText('АЛФАВИТ', w / 2, 40);
    const L = 'АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ';
    c.font = 'bold 30px Nunito, sans-serif';
    for (let i = 0; i < L.length; i++) {
      c.fillStyle = ['#2e86c1', '#27ae60', '#e67e22', '#8e44ad'][i % 4];
      c.fillText(L[i], 30 + (i % 6) * 34, 90 + Math.floor(i / 6) * 34);
    }
  });
  poster(1.3, 1.0, ROOM.x - 0.02, 2.1, -3, -Math.PI / 2, (c, w, h) => {
    c.fillStyle = '#e8f4fd'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#1f4e79'; c.font = 'bold 22px Nunito, sans-serif'; c.textAlign = 'center';
    c.fillText('ТАБЛИЦА УМНОЖЕНИЯ', w / 2, 28);
    c.font = '17px Nunito, sans-serif';
    for (let a = 2; a <= 9; a++) for (let b = 2; b <= 5; b++) c.fillText(`${a}×${b}=${a * b}`, 40 + (b - 2) * 62, 52 + (a - 2) * 18);
  });
  poster(2.2, 0.7, 0, 2.5, ROOM.zb - 0.02, Math.PI, (c, w, h) => {
    c.fillStyle = '#fdecc8'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#b03a2e'; c.font = 'bold 54px Caveat, cursive'; c.textAlign = 'center';
    c.fillText('Знание — сила!', w / 2, h / 2 + 18);
  });
  let classSign = null;
  function drawClassSign() {
    const c = classSign.ctx, w = classSign.canvas.width, h = classSign.canvas.height;
    c.fillStyle = '#2b4d7a'; c.fillRect(0, 0, w, h);
    c.fillStyle = '#ffd54a'; c.textAlign = 'center'; c.textBaseline = 'middle';
    let size = 60;
    const label = `${S ? S.grade : 1} «А» класс`;
    do { c.font = `bold ${size}px Nunito, sans-serif`; size -= 2; } while (c.measureText(label).width > w - 30 && size > 20);
    c.fillText(label, w / 2, h / 2 + 2);
    classSign.tex.needsUpdate = true;
  }
  classSign = poster(1.6, 0.42, 0, 3.15, ROOM.zf + 0.02, 0, () => {});

  // ---------- Доска ----------
  box(5.5, 1.95, 0.08, '#6b4628', 0, 1.9, ROOM.zf + 0.04);
  box(5.3, 0.06, 0.16, '#6b4628', 0, 0.93, ROOM.zf + 0.1);
  box(0.12, 0.03, 0.03, '#ffffff', -1.6, 0.97, ROOM.zf + 0.12);
  box(0.25, 0.06, 0.08, '#d9a441', 1.8, 0.98, ROOM.zf + 0.12);
  const boardBg = document.createElement('canvas');
  boardBg.width = 1280; boardBg.height = 420;
  {
    const c = boardBg.getContext('2d');
    c.fillStyle = '#2f5d46'; c.fillRect(0, 0, 1280, 420);
    for (let i = 0; i < 40; i++) {
      c.fillStyle = `rgba(255,255,255,${Math.random() * 0.035})`;
      c.beginPath(); c.ellipse(Math.random() * 1280, Math.random() * 420, 60 + Math.random() * 140, 20 + Math.random() * 40, Math.random(), 0, 7); c.fill();
    }
  }
  const board = canvasTex(1280, 420, c => c.drawImage(boardBg, 0, 0));
  {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(5.3, 1.74), new THREE.MeshStandardMaterial({ map: board.tex, roughness: 0.95 }));
    m.position.set(0, 1.9, ROOM.zf + 0.085);
    scene.add(m);
  }
  function drawBoard(lines, chars = Infinity) {
    const c = board.ctx;
    c.drawImage(boardBg, 0, 0);
    c.fillStyle = 'rgba(246,246,236,.93)';
    c.textBaseline = 'alphabetic';
    let left = chars;
    for (const l of lines) {
      if (left <= 0) break;
      const t = l.text.slice(0, left);
      left -= l.text.length;
      let size = l.size;
      c.font = `700 ${size}px Caveat, cursive`;
      while (c.measureText(l.text).width > 1200 && size > 20) { size -= 2; c.font = `700 ${size}px Caveat, cursive`; }
      c.textAlign = 'left';
      const full = c.measureText(l.text).width;
      const x0 = l.align === 'center' ? l.x - full / 2 : l.align === 'right' ? l.x - full : l.x;
      c.fillText(t, x0, l.y);
    }
    board.tex.needsUpdate = true;
  }

  // ---------- Часы ----------
  const clock = new THREE.Group();
  clock.position.set(4.25, 2.75, ROOM.zf + 0.05);
  scene.add(clock);
  {
    const face = canvasTex(256, 256, (c) => {
      c.fillStyle = '#fff'; c.beginPath(); c.arc(128, 128, 124, 0, 7); c.fill();
      c.lineWidth = 10; c.strokeStyle = '#333'; c.stroke();
      c.fillStyle = '#222'; c.font = 'bold 30px Nunito, sans-serif'; c.textAlign = 'center'; c.textBaseline = 'middle';
      for (let i = 1; i <= 12; i++) { const a = i / 12 * Math.PI * 2; c.fillText(i, 128 + Math.sin(a) * 92, 128 - Math.cos(a) * 92); }
    });
    const m = new THREE.Mesh(new THREE.CircleGeometry(0.33, 32), new THREE.MeshStandardMaterial({ map: face.tex }));
    clock.add(m);
  }
  function hand(len, w, color, z) {
    const p = new THREE.Group(); p.position.z = z; clock.add(p);
    const h = new THREE.Mesh(new THREE.BoxGeometry(w, len, 0.01), M(color));
    h.position.y = len / 2 - 0.03; p.add(h);
    return p;
  }
  const hHour = hand(0.17, 0.025, '#222', 0.01), hMin = hand(0.26, 0.016, '#222', 0.02), hSec = hand(0.28, 0.006, '#d33', 0.03);
  function updateClock() {
    const d = new Date();
    const s = d.getSeconds() + d.getMilliseconds() / 1000, m = d.getMinutes() + s / 60, h = (d.getHours() % 12) + m / 60;
    hSec.rotation.z = -s / 60 * Math.PI * 2;
    hMin.rotation.z = -m / 60 * Math.PI * 2;
    hHour.rotation.z = -h / 12 * Math.PI * 2;
  }

  // ---------- Учительский стол ----------
  const DESK = V3(3.4, 0, -5.0);
  {
    const g = new THREE.Group(); g.position.copy(DESK); scene.add(g);
    box(1.9, 0.07, 0.9, '#9b6b3e', 0, 0.78, 0, g);
    box(0.06, 0.75, 0.86, '#86592f', -0.9, 0.38, 0, g);
    box(0.06, 0.75, 0.86, '#86592f', 0.9, 0.38, 0, g);
    box(1.8, 0.6, 0.04, '#86592f', 0, 0.45, 0.4, g);
    // стопка тетрадей
    for (let i = 0; i < 6; i++) box(0.28, 0.018, 0.36, pick(['#4a90d9', '#e15b5b', '#5cb85c', '#f0ad4e']), -0.55, 0.825 + i * 0.019, -0.05, g).rotation.y = (Math.random() - 0.5) * 0.2;
    // яблоко
    sph(0.07, '#d62d20', 0.65, 0.88, 0.1, g);
    box(0.01, 0.05, 0.01, '#5b3a1e', 0.65, 0.96, 0.1, g);
    // журнал
    box(0.32, 0.03, 0.42, '#2c4f7c', 0.1, 0.83, -0.1, g);
    // ручка
    cyl(0.008, 0.008, 0.16, '#d02020', 0.35, 0.82, -0.05, g).rotation.z = Math.PI / 2;
    // стул учителя
    box(0.5, 0.05, 0.5, '#5a3d24', 0, 0.48, -0.75, g);
    box(0.5, 0.6, 0.05, '#5a3d24', 0, 0.8, -1.0, g);
    for (const [x, z] of [[-0.22, -0.53], [0.22, -0.53], [-0.22, -0.97], [0.22, -0.97]]) box(0.04, 0.46, 0.04, '#333', x, 0.23, z, g);
  }

  // ======================================================================
  // Ученики
  // ======================================================================
  const COLS = [-3.3, 0, 3.3], ROWS = [-2.6, -0.4, 1.8];
  const SEATS = [];
  ROWS.forEach(rz => COLS.forEach(cx => {
    // парта
    box(1.4, 0.05, 0.55, '#d8b27a', cx, 0.72, rz);
    box(1.4, 0.36, 0.03, '#7c8b99', cx, 0.52, rz - 0.25);
    for (const dx of [-0.66, 0.66]) box(0.04, 0.7, 0.5, '#7c8b99', cx + dx, 0.35, rz);
    [-0.34, 0.34].forEach(dx => {
      const sx = cx + dx, sz = rz + 0.6;
      box(0.4, 0.04, 0.38, '#c48b4a', sx, 0.44, sz);
      box(0.4, 0.34, 0.04, '#c48b4a', sx, 0.72, sz + 0.2);
      for (const [ox, oz] of [[-0.17, -0.16], [0.17, -0.16], [-0.17, 0.16], [0.17, 0.16]]) box(0.03, 0.43, 0.03, '#555', sx + ox, 0.21, sz + oz);
      SEATS.push(V3(sx, 0, sz));
    });
  }));

  const studentsRoot = new THREE.Group();
  scene.add(studentsRoot);
  let students = [];

  function gradeScale(g) { return 0.84 + (g - 1) * 0.026; }

  function buildStudent(d, i) {
    const g = new THREE.Group();
    const body = new THREE.Group(); g.add(body);
    const skin = M(d.skin), shirt = M(d.shirt), pants = M(d.pants), hairM = M(d.hair);
    // ноги (сидя)
    const legs = [-0.1, 0.1].map(x => {
      const hip = new THREE.Group(); hip.position.set(x, 0.5, 0); body.add(hip);
      box(0.13, 0.12, 0.42, pants, 0, 0, 0.2, hip);
      const knee = new THREE.Group(); knee.position.set(0, 0, 0.4); hip.add(knee);
      box(0.11, 0.45, 0.11, d.girl ? skin : pants, 0, -0.23, 0, knee);
      box(0.12, 0.07, 0.2, '#2a2a2a', 0, -0.46, 0.05, knee);
      return { hip, knee };
    });
    if (d.girl) box(0.42, 0.14, 0.44, pants, 0, 0.52, 0.12, body);
    box(0.4, 0.48, 0.24, shirt, 0, 0.77, 0, body);
    cyl(0.05, 0.05, 0.06, skin, 0, 1.03, 0, body);
    // голова
    const head = new THREE.Group(); head.position.y = 1.2; body.add(head);
    sph(0.17, skin, 0, 0, 0, head);
    const eyes = [];
    for (const x of [-0.06, 0.06]) {
      sph(0.032, '#ffffff', x, 0.02, 0.14, head).scale.z = 0.5;
      eyes.push(sph(0.019, '#1b1b1b', x, 0.02, 0.158, head));
      sph(0.028, '#f4a0a0', x * 1.6, -0.05, 0.13, head).scale.z = 0.3;
    }
    const mouth = box(0.07, 0.016, 0.01, '#8c2c2c', 0, -0.075, 0.163, head);
    const cap = mesh(new THREE.SphereGeometry(0.182, 18, 12, 0, Math.PI * 2, 0, Math.PI * 0.52), hairM, 0, 0.012, -0.012, head);
    cap.rotation.x = -0.25;
    const bows = [];
    if (d.girl) {
      box(0.3, 0.32, 0.1, hairM, 0, -0.08, -0.13, head);
      for (const x of [-0.17, 0.17]) {
        const b = new THREE.Group(); b.position.set(x, 0.1, -0.05); head.add(b);
        sph(0.06, '#ffffff', -0.04, 0, 0, b); sph(0.06, '#ffffff', 0.04, 0, 0, b);
        bows.push(b);
      }
    } else {
      box(0.26, 0.05, 0.06, hairM, 0, 0.13, 0.12, head).rotation.x = -0.4;
    }
    // выпускная лента
    const sash = box(0.08, 0.62, 0.26, '#d4232e', 0, 0.78, 0, body);
    sash.rotation.z = 0.75; sash.scale.set(1, 1, 1.02); sash.visible = false;
    // руки
    const arms = [-1, 1].map(side => {
      const p = new THREE.Group(); p.position.set(side * 0.25, 0.96, 0); body.add(p);
      box(0.1, 0.42, 0.1, shirt, 0, -0.21, 0, p);
      sph(0.055, skin, 0, -0.44, 0, p);
      p.rotation.x = -1.1;
      return p;
    });
    g.traverse(o => { o.userData.sid = i; });
    studentsRoot.add(g);
    return {
      i, g, body, head, mouth, eyes, bows, legs, sash, armL: arms[0], armR: arms[1], data: d,
      seat: SEATS[i], hand: 0, handT: 0, stand: 0, standT: 0, jumpT: 0, sad: 0, sadT: 0,
      talk: false, phase: Math.random() * 10, lookT: 0, blink: Math.random() * 4,
    };
  }

  function rebuildStudents() {
    while (studentsRoot.children.length) studentsRoot.remove(studentsRoot.children[0]);
    students = S.students.map(buildStudent);
    applyGradeLook(true);
  }
  function applyGradeLook(instant) {
    const sc = gradeScale(S.grade);
    students.forEach(st => {
      st.scaleT = sc;
      if (instant || st.scale == null) st.scale = sc;
      st.bows.forEach(b => { b.visible = S.grade <= 4; });
      st.sash.visible = S.grade === 11;
    });
    drawClassSign();
  }

  function updateStudent(st, dt, t) {
    st.scale = lerp(st.scale, st.scaleT, 1 - Math.exp(-dt * 2));
    const s = st.scale;
    st.hand = lerp(st.hand, st.handT, 1 - Math.exp(-dt * 8));
    st.stand = lerp(st.stand, st.standT, 1 - Math.exp(-dt * 6));
    st.sad = lerp(st.sad, st.sadT, 1 - Math.exp(-dt * 4));
    st.g.scale.setScalar(s);
    // сидя бёдра на стуле (0.45), стоя — на высоте выпрямленных ног
    st.g.position.set(st.seat.x, lerp(0.45 - 0.5 * s, 0.4 * s, st.stand), st.seat.z - st.stand * 0.12);
    st.legs.forEach(l => { l.hip.rotation.x = st.stand * Math.PI / 2; l.knee.rotation.x = -st.stand * Math.PI / 2; });
    st.g.rotation.y = Math.PI;

    let jumpY = 0, cheer = 0;
    if (st.jumpT > 0) {
      st.jumpT -= dt;
      jumpY = Math.abs(Math.sin(st.jumpT * Math.PI * 2.4)) * 0.22;
      cheer = 1;
    }
    st.body.position.y = jumpY;
    st.body.scale.y = 1 + Math.sin(t * 2 + st.phase) * 0.012;

    const rest = lerp(-1.1, -0.12, st.stand);
    const up = -2.95;
    st.armR.rotation.x = lerp(rest, up, Math.max(st.hand, cheer)) + (st.hand > 0.8 ? Math.sin(t * 9 + st.phase) * 0.1 : 0);
    st.armL.rotation.x = lerp(rest, up, cheer);
    st.armR.rotation.z = -0.15 * Math.max(st.hand, cheer);
    st.armL.rotation.z = 0.15 * cheer;

    // голова: оглядывается, грустит, смотрит на говорящего
    const look = st.lookT || Math.sin(t * 0.4 + st.phase) * 0.35 * (st.talk ? 0.2 : 1);
    st.head.rotation.y = lerp(st.head.rotation.y, look, 1 - Math.exp(-dt * 3));
    st.head.rotation.x = st.sad * 0.55 + (st.talk ? Math.sin(t * 6) * 0.04 : 0);
    st.body.rotation.x = st.sad * 0.25;
    st.mouth.scale.y = st.talk ? 1 + Math.abs(Math.sin(t * 18)) * 3.5 : (st.jumpT > 0 ? 3 : 1);
    st.mouth.scale.x = st.sad > 0.5 ? 0.6 : 1;

    // моргание
    st.blink -= dt;
    const closed = st.blink < 0.12;
    if (st.blink < 0) st.blink = 2 + Math.random() * 4;
    st.eyes.forEach(e => { e.scale.y = closed ? 0.15 : 1; });
  }

  // ======================================================================
  // Учитель
  // ======================================================================
  const teacher = { g: null, pos: V3(-1.7, 0, -5.1), heading: 0, headingT: 0, path: [], resolve: null, walk: 0, writing: false, talk: false, pointing: 0 };

  function buildTeacher() {
    if (teacher.g) scene.remove(teacher.g);
    const f = S.gender !== 'm';
    const g = new THREE.Group(); scene.add(g);
    const skin = M('#f0c39d'), top = M(f ? '#8a3b5a' : '#34466b'), bottom = M(f ? '#5a2840' : '#2a3550');
    const hairM = M(f ? '#5a3420' : '#3a2a20');
    const legs = [-1, 1].map(side => {
      const p = new THREE.Group(); p.position.set(side * 0.11, 0.86, 0); g.add(p);
      box(0.14, 0.82, 0.15, f ? skin : bottom, 0, -0.41, 0, p);
      box(0.15, 0.08, 0.26, '#222', 0, -0.82, 0.05, p);
      return p;
    });
    if (f) mesh(new THREE.CylinderGeometry(0.24, 0.36, 0.55, 18), bottom, 0, 0.82, 0, g);
    box(0.46, 0.6, 0.26, top, 0, 1.24, 0, g);
    if (!f) box(0.06, 0.34, 0.01, '#c0392b', 0, 1.32, 0.135, g);
    else box(0.2, 0.12, 0.01, '#f6f0e6', 0, 1.47, 0.132, g);
    cyl(0.06, 0.06, 0.08, skin, 0, 1.57, 0, g);
    const head = new THREE.Group(); head.position.y = 1.76; g.add(head);
    sph(0.19, skin, 0, 0, 0, head);
    for (const x of [-0.07, 0.07]) {
      sph(0.022, '#1b1b1b', x, 0.03, 0.172, head);
      const ring = mesh(new THREE.TorusGeometry(0.045, 0.008, 8, 20), '#333', x, 0.03, 0.18, head);
      ring.castShadow = false;
    }
    box(0.05, 0.008, 0.008, '#333', 0, 0.035, 0.185, head);
    const mouth = box(0.08, 0.016, 0.01, '#8c2c2c', 0, -0.085, 0.18, head);
    const cap = mesh(new THREE.SphereGeometry(0.2, 18, 12, 0, Math.PI * 2, 0, Math.PI * 0.5), hairM, 0, 0.02, -0.02, head);
    cap.rotation.x = -0.3;
    if (f) { sph(0.11, hairM, 0, 0.12, -0.17, head); box(0.34, 0.2, 0.1, hairM, 0, -0.02, -0.12, head); }
    else box(0.09, 0.02, 0.02, hairM, 0, -0.05, 0.185, head);
    const arms = [-1, 1].map(side => {
      const p = new THREE.Group(); p.position.set(side * 0.29, 1.5, 0); g.add(p);
      box(0.11, 0.58, 0.11, top, 0, -0.29, 0, p);
      sph(0.06, skin, 0, -0.6, 0, p);
      return p;
    });
    const chalk = box(0.03, 0.09, 0.03, '#ffffff', 0, -0.66, 0.04, arms[1]);
    chalk.visible = false;
    Object.assign(teacher, { g, legs, armL: arms[0], armR: arms[1], head, mouth, chalk });
    g.position.copy(teacher.pos);
  }

  function teacherWalk(points) {
    teacher.path = points.map(([x, z]) => V3(x, 0, z));
    return new Promise(res => { teacher.resolve = res; });
  }
  function teacherFace(angle) { teacher.headingT = angle; }
  function teacherPlace(x, z, angle) {
    teacher.pos.set(x, 0, z); teacher.path = []; teacher.heading = teacher.headingT = angle;
    if (teacher.resolve) { teacher.resolve(); teacher.resolve = null; }
  }

  function updateTeacher(dt, t) {
    if (!teacher.g) return;
    const T = teacher;
    let moving = false;
    if (T.path.length) {
      const target = T.path[0];
      const d = target.clone().sub(T.pos); d.y = 0;
      const dist = d.length();
      const step = 1.7 * dt;
      if (dist <= step) {
        T.pos.copy(target); T.path.shift();
        if (!T.path.length && T.resolve) { const r = T.resolve; T.resolve = null; r(); }
      } else {
        T.pos.add(d.multiplyScalar(step / dist));
        T.headingT = Math.atan2(target.x - T.pos.x, target.z - T.pos.z);
        moving = true;
      }
    }
    let dh = T.headingT - T.heading;
    while (dh > Math.PI) dh -= Math.PI * 2;
    while (dh < -Math.PI) dh += Math.PI * 2;
    T.heading += dh * (1 - Math.exp(-dt * 8));
    T.walk = moving ? T.walk + dt * 9 : lerp(T.walk, Math.round(T.walk / Math.PI) * Math.PI, 1 - Math.exp(-dt * 10));
    const sw = Math.sin(T.walk) * 0.55;
    T.g.position.set(T.pos.x, moving ? Math.abs(Math.cos(T.walk)) * 0.04 : 0, T.pos.z);
    T.g.rotation.y = T.heading;
    T.legs[0].rotation.x = sw; T.legs[1].rotation.x = -sw;
    if (T.writing) {
      T.armR.rotation.x = -2.0 + Math.sin(t * 11) * 0.18;
      T.armR.rotation.z = Math.sin(t * 5) * 0.25;
    } else {
      const target = T.pointing ? -1.5 : -sw * 0.8;
      T.armR.rotation.x = lerp(T.armR.rotation.x, target, 1 - Math.exp(-dt * 10));
      T.armR.rotation.z = lerp(T.armR.rotation.z, 0, 1 - Math.exp(-dt * 10));
    }
    T.armL.rotation.x = T.talk && !moving ? -0.5 + Math.sin(t * 4) * 0.25 : sw * 0.8;
    T.chalk.visible = T.writing;
    T.mouth.scale.y = T.talk ? 1 + Math.abs(Math.sin(t * 17)) * 3 : 1;
    T.head.rotation.x = T.writing ? -0.1 : 0;
  }

  // ======================================================================
  // Камера
  // ======================================================================
  const cam = { pos: V3(5, 3, 6), look: V3(0, 1, -3), tPos: V3(5, 3, 6), tLook: V3(0, 1, -3), speed: 2.4, orbit: true, shake: 0 };
  const SHOTS = {
    board: [V3(1.4, 2.4, 1.2), V3(-0.4, 1.75, -7)],
    class: [V3(0, 2.75, -6.6), V3(0, 0.9, 1.4)],
    desk: [V3(1.7, 2.0, -3.6), V3(3.4, 0.8, -5.1)],
    entry: [V3(-3.5, 2.6, 5.6), V3(2.8, 1.0, -1)],
    wide: [V3(-4.6, 3.1, 5.8), V3(0.5, 0.8, -3.5)],
  };
  function camTo(shot, speed = 2.4) {
    const [p, l] = Array.isArray(shot) ? shot : SHOTS[shot];
    cam.orbit = false; cam.speed = speed;
    cam.tPos.copy(p); cam.tLook.copy(l);
  }
  function headPos(st) { const v = V3(); st.head.getWorldPosition(v); return v; }
  function studentShot(st) {
    const h = headPos(st);
    return [V3(h.x + (h.x > 0 ? -0.45 : 0.45), h.y + 0.3, h.z - 1.55), V3(h.x, h.y - 0.05, h.z)];
  }
  function updateCamera(dt, t) {
    if (cam.orbit) {
      const a = t * 0.07;
      cam.tPos.set(Math.sin(a) * 4.8, 3.0, 0.2 + Math.cos(a) * 5.4);
      cam.tLook.set(0, 1.0, -1.8);
    }
    const k = 1 - Math.exp(-dt * cam.speed);
    cam.pos.lerp(cam.tPos, k);
    cam.look.lerp(cam.tLook, k);
    camera.position.copy(cam.pos);
    if (cam.shake > 0) {
      cam.shake -= dt;
      camera.position.x += (Math.random() - 0.5) * cam.shake * 0.12;
      camera.position.y += (Math.random() - 0.5) * cam.shake * 0.12;
    }
    camera.lookAt(cam.look);
  }

  // ======================================================================
  // Анимации-эффекты: твины, частицы, листки, самолётики
  // ======================================================================
  const tweens = [];
  function tween(dur, fn) { return new Promise(res => tweens.push({ t: 0, dur, fn, res })); }
  function updateTweens(dt) {
    for (let i = tweens.length - 1; i >= 0; i--) {
      const tw = tweens[i];
      tw.t += dt;
      const k = Math.min(1, tw.t / tw.dur);
      tw.fn(k);
      if (k >= 1) { tweens.splice(i, 1); tw.res(); }
    }
  }

  const spriteTex = (draw) => canvasTex(64, 64, draw).tex;
  const TEX = {
    star: spriteTex(c => { c.font = '56px serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#ffd23f'; c.fillText('★', 32, 35); }),
    drop: spriteTex(c => { c.fillStyle = '#4aa3ff'; c.beginPath(); c.moveTo(32, 6); c.quadraticCurveTo(54, 40, 32, 58); c.quadraticCurveTo(10, 40, 32, 6); c.fill(); }),
    heart: spriteTex(c => { c.font = '50px serif'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#ff4d6d'; c.fillText('♥', 32, 36); }),
    five: spriteTex(c => { c.font = 'bold 50px Caveat, cursive'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#2f9d5b'; c.fillText('5+', 32, 34); }),
    one: spriteTex(c => { c.font = 'bold 50px Caveat, cursive'; c.textAlign = 'center'; c.textBaseline = 'middle'; c.fillStyle = '#e0523f'; c.fillText('1−', 32, 34); }),
    cloud: spriteTex(c => { c.fillStyle = '#7d8796'; [[22, 36, 14], [36, 30, 16], [46, 38, 12]].forEach(([x, y, r]) => { c.beginPath(); c.arc(x, y, r, 0, 7); c.fill(); }); }),
  };
  const particles = [];
  function burst(pos, kind) {
    const add = (tex, p, v, life, size, grav = -3) => {
      const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, transparent: true, depthWrite: false }));
      s.position.copy(p); s.scale.setScalar(size); scene.add(s);
      particles.push({ s, v, life, max: life, grav, size });
    };
    if (kind === 'star') {
      add(TEX.five, pos.clone().add(V3(0, 0.25, 0)), V3(0, 0.6, 0), 1.8, 0.5, 0);
      for (let i = 0; i < 14; i++) add(TEX.star, pos.clone(), V3((Math.random() - 0.5) * 2.5, 1.5 + Math.random() * 2, (Math.random() - 0.5) * 2.5), 1.4, 0.16 + Math.random() * 0.1);
    } else if (kind === 'sad') {
      add(TEX.one, pos.clone().add(V3(0, 0.25, 0)), V3(0, 0.4, 0), 1.8, 0.5, 0);
      add(TEX.cloud, pos.clone().add(V3(0, 0.45, 0)), V3(0, 0, 0), 2.2, 0.45, 0);
      for (let i = 0; i < 10; i++) add(TEX.drop, pos.clone().add(V3((Math.random() - 0.5) * 0.3, 0.4 + Math.random() * 0.1, (Math.random() - 0.5) * 0.3)), V3(0, -0.5, 0), 0.6 + i * 0.12, 0.07);
    } else if (kind === 'heart') {
      for (let i = 0; i < 5; i++) add(TEX.heart, pos.clone(), V3((Math.random() - 0.5) * 0.8, 0.8 + Math.random(), (Math.random() - 0.5) * 0.8), 1.3, 0.14, 0);
    }
  }
  function confetti(n = 160) {
    const cols = ['#e74c3c', '#f1c40f', '#2ecc71', '#3498db', '#9b59b6', '#ff8c42'];
    for (let i = 0; i < n; i++) {
      const m = new THREE.Mesh(new THREE.PlaneGeometry(0.07, 0.11), new THREE.MeshBasicMaterial({ color: pick(cols), side: THREE.DoubleSide, transparent: true }));
      m.position.set((Math.random() - 0.5) * 11, ROOM.h - 0.1 + Math.random() * 1.5, -6 + Math.random() * 10);
      scene.add(m);
      particles.push({ s: m, v: V3((Math.random() - 0.5) * 0.4, -0.6 - Math.random() * 0.5, 0), life: 6, max: 6, grav: 0, spin: V3(Math.random() * 6, Math.random() * 6, 0) });
    }
  }
  function updateParticles(dt) {
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.life -= dt;
      p.v.y += p.grav * dt;
      p.s.position.addScaledVector(p.v, dt);
      if (p.spin) { p.s.rotation.x += p.spin.x * dt; p.s.rotation.y += p.spin.y * dt; }
      if (p.s.material) p.s.material.opacity = clamp(p.life / Math.min(0.6, p.max), 0, 1);
      if (p.life <= 0) {
        scene.remove(p.s);
        p.s.material.dispose(); if (p.s.geometry && !p.s.isSprite) p.s.geometry.dispose();
        particles.splice(i, 1);
      }
    }
  }

  // Листки с домашкой
  const sheetTex = canvasTex(64, 90, (c, w, h) => {
    c.fillStyle = '#fffef7'; c.fillRect(0, 0, w, h);
    c.strokeStyle = '#9cc1e6'; c.lineWidth = 1;
    for (let y = 12; y < h; y += 7) { c.beginPath(); c.moveTo(0, y); c.lineTo(w, y); c.stroke(); }
    c.strokeStyle = '#2c4a8a';
    for (let y = 14; y < 60; y += 14) { c.beginPath(); c.moveTo(8, y); c.lineTo(20 + Math.random() * 30, y - 2); c.stroke(); }
  }).tex;
  const deskSheets = [];
  async function flySheet(st, idx) {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(0.21, 0.29), new THREE.MeshStandardMaterial({ map: sheetTex, side: THREE.DoubleSide }));
    m.castShadow = true;
    const from = V3(st.seat.x, 1.0, st.seat.z - 0.35);
    const to = V3(DESK.x + 0.15 + (Math.random() - 0.5) * 0.05, 0.83 + idx * 0.004, DESK.z - 0.05);
    scene.add(m); deskSheets.push(m);
    st.handT = 1;
    SFX.paper();
    await tween(1.25, k => {
      const e = easeIO(k);
      m.position.lerpVectors(from, to, e);
      m.position.y += Math.sin(k * Math.PI) * 1.3;
      m.rotation.set(-Math.PI / 2 + Math.sin(k * Math.PI) * 0.9, Math.sin(k * 7) * 0.3, k * Math.PI * 3);
    });
    st.handT = 0;
    m.rotation.set(-Math.PI / 2, 0, (Math.random() - 0.5) * 0.4);
  }
  function clearSheets() { deskSheets.forEach(m => scene.remove(m)); deskSheets.length = 0; }

  // Бумажные самолётики — их можно поймать!
  const planeGeo = new THREE.BufferGeometry();
  planeGeo.setAttribute('position', new THREE.Float32BufferAttribute([
    0, 0, 0.25, -0.13, 0.02, -0.12, 0, -0.03, -0.1,
    0, 0, 0.25, 0, -0.03, -0.1, 0.13, 0.02, -0.12,
  ], 3));
  planeGeo.computeVertexNormals();
  const planeMat = new THREE.MeshStandardMaterial({ color: '#ffffff', side: THREE.DoubleSide });
  const hitMat = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false });
  const planes = [];
  let planeTimer = 14, planeOK = false;
  function spawnPlane() {
    const st = pick(students);
    const g = new THREE.Group();
    const m = new THREE.Mesh(planeGeo, planeMat); m.castShadow = true; g.add(m);
    const hit = new THREE.Mesh(new THREE.SphereGeometry(0.38, 8, 6), hitMat); g.add(hit);
    hit.userData.plane = true;
    scene.add(g);
    const p0 = headPos(st).add(V3(0, 0.2, 0));
    const p2 = V3((Math.random() - 0.5) * 5, 1.0, -5.5 + Math.random());
    const p1 = p0.clone().lerp(p2, 0.5).add(V3((Math.random() - 0.5) * 3, 1.8, 0));
    planes.push({ g, hit, p0, p1, p2, t: 0, dur: 3.2 + Math.random(), st, caught: false, fall: 0 });
    st.jumpT = 0.4;
  }
  const bez = (a, b, c, t) => a.clone().multiplyScalar((1 - t) * (1 - t)).add(b.clone().multiplyScalar(2 * (1 - t) * t)).add(c.clone().multiplyScalar(t * t));
  function updatePlanes(dt) {
    if (planeOK && students.length) {
      planeTimer -= dt;
      if (planeTimer <= 0) { planeTimer = 16 + Math.random() * 14; spawnPlane(); }
    }
    for (let i = planes.length - 1; i >= 0; i--) {
      const p = planes[i];
      if (p.caught) {
        p.fall += dt;
        p.g.scale.setScalar(Math.max(0.01, 1 - p.fall * 2));
        p.g.rotation.y += dt * 12;
        if (p.fall > 0.5) { scene.remove(p.g); planes.splice(i, 1); }
        continue;
      }
      p.t += dt / p.dur;
      if (p.t < 1) {
        const pos = bez(p.p0, p.p1, p.p2, p.t);
        const nxt = bez(p.p0, p.p1, p.p2, Math.min(1, p.t + 0.02));
        p.g.position.copy(pos);
        p.g.lookAt(nxt);
        p.g.rotateZ(Math.sin(p.t * 12) * 0.3);
      } else {
        p.g.position.y = Math.max(0.02, p.g.position.y - dt * 1.5);
        if (p.g.position.y <= 0.02) {
          p.fall += dt;
          if (p.fall > 4) { scene.remove(p.g); planes.splice(i, 1); }
        }
      }
    }
  }

  // ======================================================================
  // Интерфейс: пузыри речи, панель, тосты
  // ======================================================================
  const bubbles = new Set();
  function bubble(anchor, cls) {
    const el = document.createElement('div');
    el.className = 'bubble ' + (cls || '');
    $('#bubbles').appendChild(el);
    const b = { el, anchor, remove() { el.remove(); bubbles.delete(b); } };
    bubbles.add(b);
    return b;
  }
  const tmpV = V3();
  function updateBubbles() {
    const W = window.innerWidth, H = window.innerHeight;
    bubbles.forEach(b => {
      tmpV.copy(b.anchor()).project(camera);
      if (tmpV.z > 1) { b.el.style.visibility = 'hidden'; return; }
      b.el.style.visibility = 'visible';
      const w = b.el.offsetWidth, h = b.el.offsetHeight;
      const x = clamp((tmpV.x * 0.5 + 0.5) * W, w / 2 + 8, W - w / 2 - 8);
      const y = clamp((-tmpV.y * 0.5 + 0.5) * H, h + 70, H - 150);
      b.el.style.left = x + 'px';
      b.el.style.top = y + 'px';
    });
  }
  const studentAnchor = st => () => headPos(st).add(V3(0, 0.3 * st.scale, 0));
  const teacherAnchor = () => { const v = V3(); teacher.head.getWorldPosition(v); return v.add(V3(0, 0.32, 0)); };

  let skipReq = false;
  async function speak(who, text, hold = 1100, keep = false) {
    const isT = who === 'teacher';
    const b = bubble(isT ? teacherAnchor : studentAnchor(who), isT ? 'teacher' : '');
    b.el.innerHTML = `<span class="who">${esc(isT ? S.teacher : who.data.name)}</span><span class="txt"></span>`;
    const txt = b.el.querySelector('.txt');
    const actor = isT ? teacher : who;
    actor.talk = true;
    skipReq = false;
    for (let i = 1; i <= text.length; i++) {
      if (skipReq) { txt.textContent = text; break; }
      txt.textContent = text.slice(0, i);
      if (i % 3 === 0) SFX.blip();
      await sleep(22);
    }
    actor.talk = false;
    const wasSkipped = skipReq;
    skipReq = false;
    if (!wasSkipped) {
      const until = performance.now() + hold;
      while (performance.now() < until && !skipReq) await sleep(40);
      skipReq = false;
    }
    if (!keep) b.remove();
    return b;
  }

  function choose(text, opts) {
    return new Promise(res => {
      $('#panelText').innerHTML = text;
      const box = $('#panelBtns');
      box.innerHTML = '';
      planeOK = true;
      opts.forEach((o, i) => {
        const b = document.createElement('button');
        b.className = 'btn ' + (o.cls || '');
        b.textContent = o.label;
        b.onclick = () => { SFX.click(); planeOK = false; $('#panel').classList.add('hidden'); res(i); };
        box.appendChild(b);
      });
      $('#panel').classList.remove('hidden');
    });
  }

  function toast(text, delta) {
    const el = document.createElement('div');
    el.className = 'toast ' + (delta >= 0 ? 'plus' : 'minus');
    el.textContent = `${delta >= 0 ? '+' : '−'}${Math.abs(delta)} ⭐ ${text}`;
    $('#toasts').appendChild(el);
    setTimeout(() => el.remove(), 2500);
  }
  function flash(text) {
    const f = $('#flash');
    f.innerHTML = `<span>${esc(text)}</span>`;
    f.classList.remove('show'); void f.offsetWidth; f.classList.add('show');
  }

  class Fired extends Error {}
  let lessonStats = null;
  function addRep(delta, why) {
    S.rep += delta;
    if (lessonStats) lessonStats.rep += delta;
    toast(why, delta);
    updateHUD();
    if (S.rep <= 0) throw new Fired();
  }

  function rankOf(rep) {
    let idx = 0;
    RANKS.forEach((r, i) => { if (rep >= r.min) idx = i; });
    return idx;
  }
  function updateHUD() {
    $('#hudName').textContent = S.teacher;
    const ri = rankOf(S.rep);
    $('#hudRank').textContent = RANKS[ri].name;
    const lo = ri === 0 ? 0 : RANKS[ri].min, hi = RANKS[ri + 1] ? RANKS[ri + 1].min : lo + 400;
    $('#repFill').style.width = clamp((S.rep - lo) / (hi - lo) * 100, 2, 100) + '%';
    $('#repVal').textContent = S.rep;
    $('#hudGrade').textContent = `${S.grade} «А» класс`;
  }
  const setPhase = t => { $('#hudPhase').textContent = t; };

  function showScreen(id) {
    ['#menu', '#select', '#modal', '#journal', '#sheetWrap'].forEach(s => $(s).classList.add('hidden'));
    if (id) $(id).classList.remove('hidden');
  }
  function modal(html, buttons) {
    return new Promise(res => {
      const card = $('#modalCard');
      card.innerHTML = html + '<div class="row" id="modalBtns"></div>';
      buttons.forEach((b, i) => {
        const el = document.createElement('button');
        el.className = 'btn big ' + (b.cls || '');
        el.textContent = b.label;
        el.onclick = () => { SFX.click(); $('#modal').classList.add('hidden'); res(i); };
        $('#modalBtns').appendChild(el);
      });
      showScreen('#modal');
    });
  }

  // ---------- Выбор ученика кликом ----------
  const raycaster = new THREE.Raycaster();
  const ptr = new THREE.Vector2();
  let pickMode = null, hoverStudent = null, hoverBubble = null;
  function rayAt(e) {
    ptr.set(e.clientX / window.innerWidth * 2 - 1, -(e.clientY / window.innerHeight) * 2 + 1);
    raycaster.setFromCamera(ptr, camera);
  }
  function studentUnder(e) {
    rayAt(e);
    const hit = raycaster.intersectObject(studentsRoot, true)[0];
    return hit ? students[hit.object.userData.sid] : null;
  }
  canvas.addEventListener('pointermove', e => {
    if (!pickMode) return;
    const st = studentUnder(e);
    const ok = st && !pickMode.exclude.has(st.i) ? st : null;
    canvas.style.cursor = ok ? 'pointer' : 'default';
    if (ok !== hoverStudent) {
      if (hoverBubble) hoverBubble.remove();
      hoverBubble = null;
      hoverStudent = ok;
      if (ok) {
        hoverBubble = bubble(studentAnchor(ok), 'name');
        hoverBubble.el.textContent = `${ok.data.name} ${ok.data.last}`;
      }
    }
  });
  canvas.addEventListener('pointerdown', e => {
    // поймать самолётик
    rayAt(e);
    const ph = raycaster.intersectObjects(planes.filter(p => !p.caught && p.t < 1).map(p => p.hit), false)[0];
    if (ph) {
      const p = planes.find(q => q.hit === ph.object);
      p.caught = true;
      SFX.good();
      burst(p.g.position.clone(), 'heart');
      try { addRep(2, 'Поймали самолётик!'); } catch (err) { /* репутация растёт — увольнения нет */ }
      return;
    }
    if (pickMode) {
      const st = studentUnder(e);
      if (st && !pickMode.exclude.has(st.i)) { SFX.click(); pickMode.done(st); }
      return;
    }
    skipReq = true;
  });
  function pickStudent(text, exclude) {
    return new Promise(res => {
      const finish = st => {
        pickMode = null; planeOK = false;
        canvas.style.cursor = 'default';
        if (hoverBubble) hoverBubble.remove();
        hoverBubble = null; hoverStudent = null;
        $('#panel').classList.add('hidden');
        res(st);
      };
      pickMode = { exclude, done: finish };
      planeOK = true;
      $('#panelText').innerHTML = text;
      const box = $('#panelBtns');
      box.innerHTML = '';
      const b = document.createElement('button');
      b.className = 'btn blue';
      b.textContent = '🎲 Случайный ученик';
      b.onclick = () => { SFX.click(); finish(pick(students.filter(s => !exclude.has(s.i)))); };
      box.appendChild(b);
      $('#panel').classList.remove('hidden');
    });
  }

  // ======================================================================
  // Ход урока
  // ======================================================================
  const lowerFirst = s => (s.length > 1 && s[1] === s[1].toLowerCase() ? s[0].toLowerCase() + s.slice(1) : s);
  function askPhrase(q) {
    if (q.includes('___')) return `какое слово вставить: «${q}»?`;
    if (/=\s*\?\s*$/.test(q)) return `сколько будет ${q.replace(/\s*=\s*\?\s*$/, '')}?`;
    if (/[?…]$/.test(q)) return `а ${lowerFirst(q)}`.replace(/…$/, '…?');
    return `подскажите: ${q}?`;
  }
  function solvedLine(it) {
    if (/\?/.test(it.q) && /=\s*\?/.test(it.q)) return it.q.replace(/\?/, it.a);
    return `${it.q.replace(/\?$/, '')} — ${it.a}`;
  }
  function dateRu() {
    try { return new Date().toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' }); } catch (e) { return ''; }
  }
  function resetClass() {
    students.forEach(s => { s.handT = 0; s.standT = 0; s.sadT = 0; s.jumpT = 0; s.lookT = 0; s.talk = false; });
    bubbles.forEach(b => b.remove());
    clearSheets();
  }
  function lookAtStudent(target) {
    students.forEach(s => {
      if (s === target) { s.lookT = 0; return; }
      const dx = target.seat.x - s.seat.x, dz = target.seat.z - s.seat.z;
      s.lookT = clamp(-Math.atan2(dx, -dz), -1.1, 1.1) || 0.001;
    });
  }
  const stopLooking = () => students.forEach(s => { s.lookT = 0; });

  async function runLesson(subj) {
    showScreen(null);
    $('#hud').classList.remove('hidden');
    resetClass();
    const g = S.grade;
    const deck = makeDeck(subj, g, 10);
    const topic = topicFor(subj, g);
    lessonStats = { rep: 0, qOk: 0, qRude: 0, oralFair: 0, hwFair: 0, finds: 0, falseMarks: 0, missed: 0 };
    const L = lessonStats;
    $('#hudPhase').textContent = '';
    updateHUD();

    // ---- Вход учителя ----
    setPhase(`${subj.icon} ${subj.name} · звонок`);
    drawBoard([{ text: dateRu(), x: 1240, y: 60, size: 44, align: 'right' }]);
    teacherPlace(5.45, 4.6, -Math.PI / 2);
    camTo('entry');
    SFX.bell(); flash('🔔 Дзынь-дзынь!'); cam.shake = 0.6;
    await sleep(900);
    await teacherWalk([[4.9, 4.4], [4.9, -3.9], [2.0, -3.9], [-1.6, -4.9]]);
    teacherFace(0);
    students.forEach(s => { s.standT = 1; });
    await sleep(500);
    camTo('class');
    const chorus = shuffle(students).slice(0, 3).map(s => {
      const b = bubble(studentAnchor(s));
      b.el.textContent = 'Здравствуйте!';
      s.talk = true;
      return { b, s };
    });
    await sleep(1300);
    chorus.forEach(c => { c.b.remove(); c.s.talk = false; });
    await speak('teacher', 'Здравствуйте, дети! Садитесь.', 900);
    students.forEach(s => { s.standT = 0; });

    // ---- Тема на доске ----
    setPhase(`${subj.icon} ${subj.name} · тема урока`);
    await teacherWalk([[0.2, -6.25]]);
    teacherFace(Math.PI);
    camTo('board');
    const ex = deck[9];
    const lines = [
      { text: dateRu(), x: 1240, y: 60, size: 44, align: 'right' },
      { text: 'Классная работа', x: 640, y: 125, size: 60, align: 'center' },
      { text: `Тема: «${topic}»`, x: 640, y: 215, size: 62, align: 'center' },
      { text: `Пример: ${solvedLine(ex)}`, x: 70, y: 305, size: 48, align: 'left' },
    ];
    await sleep(600);
    teacher.writing = true;
    const total = lines.reduce((a, l) => a + l.text.length, 0);
    await tween(3.4, k => { drawBoard(lines, Math.floor(total * k)); if (Math.random() < 0.25) SFX.chalk(); });
    drawBoard(lines);
    teacher.writing = false;
    teacherFace(0);
    await sleep(300);
    await speak('teacher', `Сегодня тема урока — «${topic}». Слушаем внимательно!`, 1200);
    await teacherWalk([[-1.6, -4.9]]);
    teacherFace(0);

    // ---- Этап 1: вопросы учеников ----
    camTo('class');
    const used = new Set();
    for (let i = 0; i < 3; i++) {
      setPhase(`❓ Вопросы учеников ${i + 1}/3`);
      const st = pick(students.filter(s => !used.has(s.i)));
      used.add(st.i);
      const it = deck[i];
      await sleep(500);
      st.handT = 1; SFX.pop();
      await sleep(900);
      lookAtStudent(st);
      camTo(studentShot(st));
      const qb = await speak(st, `${S.teacher}, ${askPhrase(it.q)}`, 200, true);
      const opts = shuffle([
        { label: `«${it.a}»`, kind: 'ok', text: it.a },
        { label: `«${it.w[0]}»`, kind: 'bad', text: it.w[0] },
        { label: `😠 ${pick(RUDE)}`, kind: 'rude' },
      ]);
      const ci = await choose(`Что ответить ученику? <i>(${esc(st.data.name)} спрашивает)</i>`, opts.map(o => ({ label: o.label, cls: o.kind === 'rude' ? 'alt' : 'blue' })));
      qb.remove();
      const o = opts[ci];
      st.handT = 0;
      if (o.kind === 'rude') {
        await speak('teacher', o.label.slice(3), 700);
        st.sadT = 1;
        await speak(st, 'Эх… я просто хотел(а) понять… 😢', 700);
        addRep(-7, 'Грубость с учеником');
        L.qRude++;
        st.data.skill = clamp(st.data.skill - 0.03, 0.05, 0.98);
      } else {
        await speak('teacher', `Правильный ответ: ${o.text}.`, 700);
        if (o.kind === 'ok') {
          st.jumpT = 0.8; burst(headPos(st), 'heart'); SFX.good();
          await speak(st, pick(['Спасибо, теперь понятно! 😊', 'Ура, понял(а)!', 'Точно! Спасибо!']), 700);
          addRep(5, 'Верный ответ');
          L.qOk++;
          st.data.skill = clamp(st.data.skill + 0.04, 0.05, 0.98);
        } else {
          SFX.bad();
          const nerd = pick(students.filter(s => s !== st));
          nerd.handT = 1;
          await speak(nerd, `А в учебнике написано «${it.a}»… 🤓`, 900);
          nerd.handT = 0;
          addRep(-5, 'Неверный ответ ученику');
        }
      }
      st.sadT = 0;
      stopLooking();
      camTo('class');
    }

    // ---- Этап 2: опрос у доски ----
    const called = new Set();
    for (let i = 0; i < 3; i++) {
      setPhase(`🧑‍🏫 Опрос ${i + 1}/3`);
      camTo('class');
      const it = deck[3 + i];
      const st = await pickStudent('Кого спросим? <b>Нажмите на ученика</b> в классе', called);
      called.add(st.i);
      teacher.pointing = 1;
      lookAtStudent(st);
      await speak('teacher', `${st.data.name}, отвечай: ${it.q}`, 400);
      teacher.pointing = 0;
      st.standT = 1;
      camTo(studentShot(st));
      await sleep(500);
      const correct = Math.random() < 0.3 + st.data.skill * 0.6;
      const ans = correct ? it.a : pick(it.w);
      await speak(st, 'Ммм… сейчас…', 500);
      const ab = await speak(st, `${pick(['Я думаю,', 'Ответ:', 'Наверное,', 'Это'])} ${ans}!`, 200, true);
      let peeked = false, ci;
      for (;;) {
        const opts = [{ label: '5+', cls: 'grade5' }, { label: '1−', cls: 'grade1' }];
        if (!peeked) opts.push({ label: '📖 Учебник (−1 ⭐)', cls: 'alt' });
        const hint = peeked ? `<br>📖 В учебнике: <b>${esc(it.a)}</b>` : '';
        ci = await choose(`Проанализируйте ответ «${esc(ans)}» и поставьте оценку${hint}`, opts);
        if (ci === 2) { peeked = true; addRep(-1, 'Подсмотрели в учебник'); continue; }
        break;
      }
      ab.remove();
      const five = ci === 0;
      const fair = five === correct;
      st.data.marks.push(five ? '5+' : '1-');
      S.stats[five ? 'five' : 'one']++;
      S.stats[fair ? 'fair' : 'unfair']++;
      if (five) { st.jumpT = 1.4; burst(headPos(st), 'star'); SFX.good(); await speak(st, pick(['Ура! Пятёрка! 🎉', 'Йес! 5+!', 'Мама будет рада!']), 600); }
      else { st.sadT = 1; burst(headPos(st), 'sad'); SFX.bad(); await speak(st, pick(['Эх… кол с минусом…', 'Ну вот… 😭', 'Я же учил(а)…']), 600); }
      if (fair) {
        addRep(4, 'Честная оценка');
        L.oralFair++;
      } else if (correct) {
        await speak(st, 'Но ведь я ответил(а) правильно! Это нечестно! 😤', 900);
        addRep(-6, 'Несправедливая двойка');
      } else {
        const other = pick(students.filter(s => s !== st));
        other.handT = 1;
        await speak(other, `Так нечестно! Правильно же «${it.a}»!`, 900);
        other.handT = 0;
        addRep(-6, 'Пятёрка за ошибку');
      }
      st.standT = 0;
      st.sadT = 0;
      stopLooking();
      save();
    }

    // ---- Этап 3: проверка домашки ----
    setPhase('📝 Проверка домашки');
    camTo('class');
    await speak('teacher', 'А теперь сдаём домашнее задание на листочках!', 600);
    const hw = deck.slice(6, 9);
    const writers = shuffle(students).slice(0, 3);
    camTo('wide');
    await Promise.all(writers.map((st, i) => sleep(i * 350).then(() => flySheet(st, i))));
    await teacherWalk([[2.3, -5.9]]);
    teacherFace(0.5);
    camTo('desk');
    await sleep(700);
    for (let i = 0; i < writers.length; i++) {
      setPhase(`📝 Проверка домашки ${i + 1}/3`);
      const st = writers[i];
      const answers = hw.map(it => (Math.random() < 0.4 + st.data.skill * 0.5 ? { t: it.a, ok: true } : { t: pick(it.w), ok: false }));
      const res = await checkSheet(st, subj, hw, answers);
      L.finds += res.finds; L.falseMarks += res.falseMarks; L.missed += res.missed;
      if (res.fair) L.hwFair++;
      st.data.marks.push(res.five ? '5+' : '1-');
      S.stats[res.five ? 'five' : 'one']++;
      S.stats[res.fair ? 'fair' : 'unfair']++;
      if (res.five) { st.jumpT = 1; burst(headPos(st), 'star'); } else { st.sadT = 1; burst(headPos(st), 'sad'); }
      setTimeout(() => { st.sadT = 0; }, 2500);
      save();
    }
    clearSheets();

    // ---- Конец урока ----
    setPhase('🔔 Конец урока');
    camTo('class');
    await teacherWalk([[1.5, -5.2]]);
    teacherFace(0);
    SFX.bell(); flash('🔔 Урок окончен!'); cam.shake = 0.5;
    await speak('teacher', `Урок окончен! Домашнее задание — параграф ${R(3, 40)}.`, 700);
    students.forEach((s, i) => setTimeout(() => { s.jumpT = 1.2; }, i * 60));
    planeOK = false;
    await sleep(1200);

    S.done[subj.id] = L.rep;
    S.lessons++;
    save();
    return L;
  }

  function checkSheet(st, subj, tasks, answers) {
    return new Promise(res => {
      showScreen('#sheetWrap');
      const sheet = $('#sheet');
      sheet.className = subj.paper;
      $('#sheetName').innerHTML = `${esc(st.data.name)} ${esc(st.data.last)}<br><small>${esc(subj.name)} · домашняя работа</small>`;
      const mark = $('#sheetMark');
      mark.textContent = ''; mark.className = '';
      $('#sheetHint').classList.remove('hidden');
      const list = $('#sheetTasks');
      list.innerHTML = '';
      const marked = tasks.map(() => false);
      let finished = false;
      const rows = tasks.map((t, i) => {
        const el = document.createElement('div');
        el.className = 'task';
        el.innerHTML = `<span class="q">${i + 1}) ${esc(t.q)}</span><span class="ans">${esc(answers[i].t)}</span>`;
        el.onclick = () => {
          if (finished) return;
          marked[i] = !marked[i];
          el.classList.toggle('marked', marked[i]);
          SFX.paper();
        };
        list.appendChild(el);
        return el;
      });
      const btns = $('#sheetBtns');
      btns.innerHTML = '';
      const grade = five => {
        finished = true;
        SFX.click();
        $('#sheetHint').classList.add('hidden');
        mark.textContent = five ? '5+' : '1−';
        mark.style.color = five ? '#2f7d5b' : '#e0523f';
        mark.className = 'stamp';
        const wrong = answers.filter(a => !a.ok).length;
        const fair = five === (wrong === 0);
        let finds = 0, falseMarks = 0, missed = 0;
        rows.forEach((el, i) => {
          const v = document.createElement('span');
          v.className = 'verdict';
          if (!answers[i].ok) {
            const fix = document.createElement('span');
            fix.className = 'fix'; fix.textContent = `→ ${tasks[i].a}`;
            el.appendChild(fix);
          }
          if (marked[i] && !answers[i].ok) { finds++; v.textContent = '✓ ошибка найдена'; v.classList.add('ok'); }
          else if (marked[i]) { falseMarks++; v.textContent = '✗ тут всё верно'; v.classList.add('bad'); }
          else if (!answers[i].ok) { missed++; v.textContent = '✗ ошибку пропустили'; v.classList.add('bad'); }
          else { v.textContent = '✓'; v.classList.add('ok'); }
          el.appendChild(v);
        });
        let fired = false;
        try {
          if (fair) addRep(3, 'Справедливая оценка за домашку'); else addRep(-5, 'Несправедливая оценка за домашку');
          const net = finds - falseMarks - missed;
          if (net !== 0) addRep(net, net > 0 ? 'Внимательная проверка' : 'Невнимательная проверка');
        } catch (e) { fired = e; }
        if (fair) SFX.good(); else SFX.bad();
        btns.innerHTML = '';
        const next = document.createElement('button');
        next.className = 'btn green';
        next.textContent = fair ? 'Честно! Дальше →' : 'Хм… Дальше →';
        next.onclick = () => {
          SFX.click();
          showScreen(null);
          if (fired) { res(Promise.reject(fired)); return; }
          res({ five, fair, finds, falseMarks, missed });
        };
        btns.appendChild(next);
      };
      [['5+', 'grade5', true], ['1−', 'grade1', false]].forEach(([l, c, five]) => {
        const b = document.createElement('button');
        b.className = 'btn ' + c; b.textContent = l;
        b.onclick = () => grade(five);
        btns.appendChild(b);
      });
    });
  }

  function directorSays(rep) {
    if (rep >= 28) return 'Директор: «Блестящий урок! Методобъединение в восторге!» 🏆';
    if (rep >= 14) return 'Директор: «Хороший урок, так держать!» 👍';
    if (rep >= 0) return 'Директор: «Неплохо, но есть над чем поработать.»';
    return 'Директор: «Мне поступили жалобы от родителей… Зайдите ко мне.» 😠';
  }

  async function showSummary(subj, L) {
    const cls = L.rep >= 0 ? 'plus' : 'minus';
    await modal(`
      <h2 class="center">${subj.icon} Анализ урока: ${esc(subj.name)}</h2>
      <div class="big-rep ${cls}">${L.rep >= 0 ? '+' : '−'}${Math.abs(L.rep)} ⭐</div>
      <table class="result-table">
        <tr><td>❓ Верные ответы на вопросы</td><td>${L.qOk} из 3</td></tr>
        <tr><td>😠 Грубость</td><td>${L.qRude}</td></tr>
        <tr><td>🧑‍🏫 Честные оценки у доски</td><td>${L.oralFair} из 3</td></tr>
        <tr><td>📝 Честные оценки за домашку</td><td>${L.hwFair} из 3</td></tr>
        <tr><td>🔍 Найдено ошибок / ложных / пропущено</td><td>${L.finds} / ${L.falseMarks} / ${L.missed}</td></tr>
        <tr><td>⭐ Репутация сейчас</td><td>${S.rep} · ${RANKS[rankOf(S.rep)].name}</td></tr>
      </table>
      <div class="director">${directorSays(L.rep)}</div>`, [{ label: 'Дальше', cls: 'green' }]);
  }

  async function yearEnd() {
    const g = S.grade;
    $('#hud').classList.remove('hidden');
    resetClass();
    teacherPlace(-1.6, -4.9, 0);
    camTo('class', 1.6);
    planeOK = false;
    await sleep(600);
    students.forEach((s, i) => { s.standT = 1; setTimeout(() => { s.jumpT = 2; }, i * 80); });
    confetti();
    SFX.fanfare();
    if (g >= 11) {
      flash('🎓 ВЫПУСКНОЙ!');
      await sleep(2400);
      const i = await modal(`
        <div class="huge">🎓</div>
        <h2 class="center">Выпускной! Ваш класс окончил школу!</h2>
        <p class="sub center">Вы провели свой «А» класс от первого звонка до последнего.</p>
        <table class="result-table">
          <tr><td>Уроков проведено</td><td>${S.lessons}</td></tr>
          <tr><td>Поставлено 5+ / 1−</td><td>${S.stats.five} / ${S.stats.one}</td></tr>
          <tr><td>Честных оценок</td><td>${S.stats.fair} из ${S.stats.fair + S.stats.unfair}</td></tr>
          <tr><td>Итоговая репутация</td><td>${S.rep} ⭐</td></tr>
          <tr><td>Звание</td><td>${RANKS[rankOf(S.rep)].name}</td></tr>
        </table>
        <div class="director">Директор: «Спасибо за ваш труд! Выпускники вас никогда не забудут.» 💐</div>`,
        [{ label: 'Новый первый класс', cls: 'green' }, { label: 'В меню', cls: 'alt' }]);
      const keepName = S.teacher, keepG = S.gender, keepRep = S.rep;
      S = newState(keepName, keepG);
      S.rep = Math.max(30, Math.round(keepRep / 2));
      save();
      rebuildStudents();
      if (i === 0) openSelect(); else openMenu();
      return;
    }
    flash(`🎉 Переход в ${g + 1} класс!`);
    await sleep(2200);
    const avg = Math.round(Object.values(S.done).reduce((a, b) => a + b, 0));
    await modal(`
      <div class="huge">🎉</div>
      <h2 class="center">Учебный год окончен!</h2>
      <p class="sub center">Ваш класс переходит в <b>${g + 1} класс</b>. За год репутация: ${avg >= 0 ? '+' : '−'}${Math.abs(avg)} ⭐.
      Бонус за успешный год: <b>+10 ⭐</b></p>`, [{ label: `Вперёд, в ${g + 1} класс!`, cls: 'green' }]);
    S.grade = g + 1;
    S.done = {};
    S.rep += 10;
    students.forEach(s => { s.standT = 0; });
    applyGradeLook(false);
    save();
    updateHUD();
    openSelect();
  }

  async function startLesson(subj) {
    try {
      const L = await runLesson(subj);
      lessonStats = null;
      await showSummary(subj, L);
      if (Object.keys(S.done).length >= LESSONS_PER_YEAR) await yearEnd();
      else openSelect();
    } catch (e) {
      lessonStats = null;
      if (!(e instanceof Fired)) { console.error(e); openSelect(); return; }
      planeOK = false;
      $('#panel').classList.add('hidden');
      bubbles.forEach(b => b.remove());
      showScreen(null);
      resetClass();
      students.forEach(s => { s.sadT = 1; });
      SFX.bad();
      flash('😱 Вас уволили!');
      await sleep(1800);
      await modal(`
        <div class="huge">📉</div>
        <h2 class="center">Репутация упала до нуля!</h2>
        <p class="sub center">Директор вызвал вас в кабинет… Придётся заново начать ${S.grade}-й класс.
        Будьте внимательнее: отвечайте верно, ставьте честные оценки и не грубите детям.</p>`,
        [{ label: 'Попробовать снова', cls: 'green' }]);
      S.rep = 40;
      S.done = {};
      save();
      students.forEach(s => { s.sadT = 0; });
      openSelect();
    }
  }

  // ======================================================================
  // Экраны
  // ======================================================================
  function openMenu() {
    showScreen('#menu');
    $('#hud').classList.add('hidden');
    $('#panel').classList.add('hidden');
    cam.orbit = true; cam.speed = 1.2;
    const saved = load();
    $('#btnContinue').classList.toggle('hidden', !saved);
    if (saved) $('#teacherName').value = saved.teacher;
  }

  function openSelect() {
    showScreen('#select');
    $('#hud').classList.remove('hidden');
    setPhase('Выбор урока');
    updateHUD();
    resetClass();
    teacherPlace(-1.6, -4.9, 0);
    camTo('wide', 1.5);
    drawBoard([{ text: dateRu(), x: 1240, y: 60, size: 44, align: 'right' }, { text: 'Добро пожаловать в класс!', x: 640, y: 220, size: 72, align: 'center' }]);
    const doneN = Object.keys(S.done).length;
    $('#selTitle').textContent = `${S.grade} «А» класс — расписание`;
    $('#selInfo').textContent = `Проведено уроков в этом году: ${doneN} из ${LESSONS_PER_YEAR}. Выберите любой урок — после ${LESSONS_PER_YEAR} уроков класс перейдёт ${S.grade < 11 ? 'в ' + (S.grade + 1) + ' класс' : 'на выпускной'}.`;
    const box = $('#subjects');
    box.innerHTML = '';
    subjectsForGrade(S.grade).forEach(subj => {
      const done = subj.id in S.done;
      const b = document.createElement('button');
      b.className = 'subj' + (done ? ' done' : '');
      b.innerHTML = `<span class="ic">${subj.icon}</span>${esc(subj.name)}<span class="topic">${esc(topicFor(subj, S.grade))}</span>` +
        (done ? `<span class="badge">✓ ${S.done[subj.id] >= 0 ? '+' : ''}${S.done[subj.id]}</span>` : '');
      b.disabled = done;
      b.onclick = () => { SFX.click(); audio(); startLesson(subj); };
      box.appendChild(b);
    });
  }

  function openJournal() {
    const rows = S.students.map(d => {
      const marks = d.marks.slice(-14).map(m => `<span class="${m === '5+' ? 'm5' : 'm1'}">${m === '5+' ? '5+' : '1−'}</span>`).join(' ');
      const fives = d.marks.filter(m => m === '5+').length;
      return `<tr><td>${esc(d.last)} ${esc(d.name)}</td><td class="marks">${marks || '—'}</td><td>${fives}/${d.marks.length}</td></tr>`;
    }).sort();
    $('#journalBody').innerHTML = `<p class="sub">${S.grade} «А» класс · учитель: ${esc(S.teacher)}</p>
      <table class="jt"><tr><th>Ученик</th><th>Оценки</th><th>5+</th></tr>${rows.join('')}</table>`;
    $('#journal').classList.remove('hidden');
  }

  // ---------- Кнопки ----------
  let gender = 'f';
  const genderRow = document.createElement('div');
  genderRow.className = 'row';
  [['f', '👩‍🏫 Учительница'], ['m', '👨‍🏫 Учитель']].forEach(([g, label]) => {
    const b = document.createElement('button');
    b.className = 'btn ' + (g === gender ? 'blue' : 'alt');
    b.textContent = label;
    b.onclick = () => {
      gender = g;
      [...genderRow.children].forEach(x => { x.className = 'btn alt'; });
      b.className = 'btn blue';
      const inp = $('#teacherName');
      if (inp.value === 'Марья Ивановна' && g === 'm') inp.value = 'Иван Петрович';
      if (inp.value === 'Иван Петрович' && g === 'f') inp.value = 'Марья Ивановна';
    };
    genderRow.appendChild(b);
  });
  $('#teacherName').parentNode.after(genderRow);

  $('#btnNew').onclick = () => {
    audio(); SFX.click();
    const name = $('#teacherName').value.trim() || (gender === 'm' ? 'Иван Петрович' : 'Марья Ивановна');
    S = newState(name, gender);
    save();
    buildTeacher();
    rebuildStudents();
    openSelect();
  };
  $('#btnContinue').onclick = () => {
    audio(); SFX.click();
    const saved = load();
    if (!saved) return;
    S = saved;
    const nm = $('#teacherName').value.trim();
    if (nm) S.teacher = nm;
    buildTeacher();
    rebuildStudents();
    openSelect();
  };
  $('#btnToMenu').onclick = () => { SFX.click(); openMenu(); };
  $('#btnJournal').onclick = $('#btnJournal2').onclick = () => { SFX.click(); openJournal(); };
  $('#btnCloseJournal').onclick = () => { SFX.click(); $('#journal').classList.add('hidden'); };
  $('#btnSound').onclick = () => { muted = !muted; $('#btnSound').textContent = muted ? '🔇' : '🔊'; };

  // ======================================================================
  // Запуск
  // ======================================================================
  S = load() || newState('Марья Ивановна', 'f');
  gender = S.gender || 'f';
  buildTeacher();
  rebuildStudents();
  teacherPlace(0.2, -6.25, Math.PI);
  teacher.writing = true;
  drawBoard([{ text: 'Симулятор Учителя', x: 640, y: 200, size: 90, align: 'center' }]);
  openMenu();
  // перерисовать надписи, когда загрузится рукописный шрифт
  if (document.fonts && document.fonts.load) {
    document.fonts.load('700 60px Caveat').then(() => {
      if (!$('#menu').classList.contains('hidden')) drawBoard([{ text: 'Симулятор Учителя', x: 640, y: 200, size: 90, align: 'center' }]);
      drawClassSign();
    }).catch(() => {});
  }

  let last = performance.now(), time = 0;
  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now; time += dt;
    updateTweens(dt);
    students.forEach(s => updateStudent(s, dt, time));
    if (!$('#menu').classList.contains('hidden')) teacher.writing = true;
    else if (teacher.writing && !tweens.length) teacher.writing = false;
    updateTeacher(dt, time);
    updateCamera(dt, time);
    updateParticles(dt);
    updatePlanes(dt);
    updateClock();
    updateBubbles();
    renderer.render(scene, camera);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
  window.__started = true;

  // для отладки и автотестов
  window.__game = { get S() { return S; }, students: () => students, teacher, camTo, yearEnd };
})();
