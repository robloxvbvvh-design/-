// Всё видео — функция от времени t (секунды озвучки).
// Во время просмотра t берётся из audio.currentTime, поэтому картинка и
// субтитры всегда идут ровно по голосу. Для записи в файл: ?capture=1 и window.renderAt(t).

const DURATION = 16.12;

// Тайминги слов из расшифровки озвучки: [начало, конец, слово]
const PHRASES = [
  [[0.00, 0.28, "Это"], [0.28, 0.62, "видео"], [0.62, 0.84, "не"], [0.84, 1.06, "я"], [1.38, 1.96, "создавал."]],
  [[2.18, 2.44, "Это"], [2.44, 2.96, "Claude"], [3.06, 3.40, "Code."]],
  [[3.50, 4.16, "Субтитры,"], [4.32, 4.92, "картинки,"], [5.10, 5.86, "персонажи —"]],
  [[6.10, 6.36, "он"], [6.36, 6.62, "всё"], [6.62, 7.06, "делает."]],
  [[7.42, 7.66, "Я"], [7.66, 7.90, "только"], [7.90, 8.16, "дал"], [8.16, 8.38, "ему"], [8.38, 8.68, "голос,"], [8.68, 9.22, "текст,"]],
  [[9.44, 9.56, "а"], [9.56, 9.76, "он"], [9.76, 10.28, "подобрал"], [10.28, 10.74, "кадры"], [10.74, 10.88, "и"], [10.88, 11.38, "создал."]],
  [[11.76, 12.02, "Просто"], [12.02, 12.52, "напиши"], [12.52, 12.88, "запрос"], [12.88, 13.06, "с"], [13.06, 13.56, "озвучкой."]],
  [[13.86, 13.98, "А"], [13.98, 14.34, "теперь"], [14.34, 14.74, "он"], [14.74, 15.28, "создаёт"], [15.28, 15.44, "вам"], [15.44, 15.76, "видео."]],
];

const PROMPT = "Сделай видео по этой озвучке: субтитры, кадры, персонажи";

// ---------- помощники ----------
const $ = (id) => document.getElementById(id);
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const easeOut = (k) => 1 - Math.pow(1 - k, 3);
const easeInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const easeBack = (k) => { const c = 1.7; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
// Плавное появление/исчезание сцены в окне [a, b]
const fade = (t, a, b, f = 0.2) => Math.min(prog(t, a - f / 2, a + f / 2), 1 - prog(t, b - f / 2, b + f / 2));
const pop = (t, at, len = 0.35) => easeBack(prog(t, at, at + len));

function set(el, styles) { Object.assign(el.style, styles); }

// ---------- персонаж: тот же пиксельный человечек, что на картинке ----------
const MASCOT_SVG = `
<svg viewBox="0 100 387 315" shape-rendering="crispEdges">
  <rect class="arm arm-l" x="0" y="180" width="40" height="76"/>
  <rect class="arm arm-r" x="347" y="180" width="40" height="76"/>
  <g class="legs">
    <rect class="leg" x="35" y="325" width="34" height="85"/>
    <rect class="leg" x="106" y="325" width="34" height="85"/>
    <rect class="leg" x="247" y="325" width="34" height="85"/>
    <rect class="leg" x="318" y="325" width="34" height="85"/>
  </g>
  <rect class="body" x="35" y="105" width="317" height="226"/>
  <g class="eyes">
    <rect class="eye" x="70" y="180" width="36" height="38"/>
    <rect class="eye" x="283" y="180" width="35" height="38"/>
  </g>
</svg>`;
document.querySelectorAll(".mascot").forEach((m) => (m.innerHTML = MASCOT_SVG));

// Моргание: в кадр t глаза сжимаются по вертикали
function blink(mascot, t, offset = 0) {
  const ph = (t + offset) % 3.1;
  const k = ph < 0.12 ? 0.15 : 1;
  const eyes = mascot.querySelector(".eyes");
  return { eyes, k };
}

// ---------- сборка сцены 1: дорожки монтажа ----------
function buildTimeline(el, rows, seed) {
  const colors = ["#5b8def", "#d97757", "#58c18a", "#c46bd8", "#f2c14e", "#4fc6d9"];
  let s = seed;
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  const h = 100 / rows;
  for (let r = 0; r < rows; r++) {
    const track = document.createElement("div");
    track.className = "track";
    set(track, { top: `${r * h}%`, height: `${h}%` });
    let x = rnd() * 6;
    while (x < 190) {
      const w = 14 + rnd() * 30;
      const clip = document.createElement("div");
      clip.className = "clip";
      set(clip, { left: `${x}%`, width: `${w}%`, background: colors[Math.floor(rnd() * colors.length)] });
      track.appendChild(clip);
      x += w + 1 + rnd() * 4;
    }
    el.appendChild(track);
  }
}
buildTimeline($("tl1"), 4, 7);
buildTimeline($("tl2"), 5, 42);

// ---------- сцена 2: буквы «CLAUDE CODE» ----------
const BIG = "CLAUDE CODE";
$("coverBig").innerHTML = BIG.split("").map((c) => (c === " " ? "<br>" : `<span class="ch">${c}</span>`)).join("");
const bigChars = [...document.querySelectorAll("#coverBig .ch")];

// ---------- сцена 3: искры ----------
const sparks = [];
for (let i = 0; i < 14; i++) {
  const d = document.createElement("div");
  d.className = "spark-dot";
  $("sparks3").appendChild(d);
  sparks.push({ el: d, a: (i / 14) * Math.PI * 2, r: 280 + (i % 3) * 60 });
}

// ---------- субтитры ----------
const subs = $("subs");
const phraseEls = PHRASES.map((words) => {
  const p = document.createElement("div");
  p.className = "phrase";
  p.innerHTML = words.map((w) => `<span class="w">${w[2]}</span>`).join(" ");
  subs.appendChild(p);
  return { el: p, words, spans: [...p.querySelectorAll(".w")], start: words[0][0] };
});

function renderSubs(t) {
  let cur = -1;
  phraseEls.forEach((p, i) => { if (t >= p.start - 0.08) cur = i; });
  phraseEls.forEach((p, i) => {
    if (i !== cur) { p.el.style.display = "none"; return; }
    p.el.style.display = "block";
    const k = pop(t, p.start - 0.08, 0.22);
    p.el.style.transform = `scale(${lerp(0.82, 1, k)})`;
    p.el.style.opacity = clamp(k * 1.5);
    p.spans.forEach((s, j) => {
      const [ws] = p.words[j];
      const next = p.words[j + 1] ? p.words[j + 1][0] : p.words[j][1] + 0.35;
      const on = t >= ws && t < next;
      s.className = "w" + (on ? " on" : t < ws ? " future" : "");
      s.style.transform = on ? `scale(${1 + 0.12 * (1 - prog(t, ws, ws + 0.2))})` : "";
    });
  });
}

// ---------- кадр сцены 1 ----------
function renderS1(t) {
  const s1 = $("s1");
  s1.style.opacity = t < 2.6 ? 1 : 0;
  // лёгкий наезд камеры
  s1.style.transform = `scale(${1.08 - 0.08 * easeOut(prog(t, 0, 2.4))})`;
  document.querySelectorAll("#s1 .playhead").forEach((ph, i) => {
    ph.style.left = `${8 + ((t * (i ? 24 : 32)) % 84)}%`;
  });
  document.querySelectorAll("#s1 .track").forEach((tr, i) => {
    tr.style.transform = `translateX(${-((t * (6 + (i % 3) * 2)) % 40)}%)`;
  });
  $("s1").querySelector(".viewer-sun").style.transform = `translateY(${Math.sin(t * 2) * 14}px)`;
  document.querySelectorAll("#s1 .person").forEach((p, i) => {
    const base = i ? "scale(.9) " : "";
    p.style.transform = base + `translateY(${Math.sin(t * 5 + i * 2) * 6}px) rotate(${Math.sin(t * 3 + i) * 1.5}deg)`;
  });
  // штамп «НЕ Я» хлопает на слове «я»
  const k = prog(t, 0.84, 1.04);
  const stamp = $("stamp");
  stamp.style.opacity = k > 0 ? 1 : 0;
  stamp.style.transform = `translateX(-50%) rotate(-12deg) scale(${lerp(2.4, 1, easeOut(k))})`;
  $("s1").querySelector(".rec-dot").style.opacity = Math.floor(t * 2) % 2 ? 0.3 : 1;
}

// ---------- кадр сцены 2: текст закрывает экран ----------
function renderCover(t) {
  const cover = $("cover");
  const inK = easeOut(prog(t, 2.1, 2.36));
  const outK = easeInOut(prog(t, 3.22, 3.52));
  cover.style.opacity = t >= 2.1 && t < 3.52 ? 1 : 0;
  cover.style.transform = `translateY(${(1 - inK) * 100 - outK * 100}%)`;
  const sk = pop(t, 2.18, 0.3);
  set($("coverSmall"), { transform: `scale(${sk})` });
  bigChars.forEach((c, i) => {
    const k = pop(t, 2.44 + i * 0.045, 0.3);
    c.style.transform = `translateY(${(1 - k) * 80}px) scale(${k})`;
    c.style.opacity = clamp(k * 2);
  });
  const subK = pop(t, 3.0, 0.25);
  set($("coverSub"), { opacity: subK, transform: `scale(${subK})` });
}

// ---------- кадр сцены 3: персонаж + карточки ----------
function renderS3(t) {
  const s3 = $("s3");
  s3.style.opacity = t >= 3.2 && t < 7.25 ? fade(t, 3.22, 7.18, 0.04) : 0;
  const m = $("m3");
  const appear = pop(t, 3.32, 0.45);
  // «он всё делает» — два прыжка
  const hop = t > 6.1 && t < 7.0 ? Math.abs(Math.sin((t - 6.1) * Math.PI / 0.45)) * 110 : 0;
  const bob = Math.sin(t * 4) * 8;
  const squash = hop < 10 && t > 6.1 && t < 7.0 ? 0.92 : 1;
  m.style.transform = `translateY(${-hop + bob}px) scale(${appear}) scaleY(${squash})`;
  const { eyes, k } = blink(m, t);
  eyes.style.transform = `translateY(${(1 - k) * 199}px) scaleY(${k})`;
  // ручки машут
  m.querySelector(".arm-l").style.transform = `translateY(${Math.sin(t * 7) * 10}px)`;
  m.querySelector(".arm-r").style.transform = `translateY(${-Math.sin(t * 7) * 10}px)`;

  const times = [3.5, 4.32, 5.1];
  ["c1", "c2", "c3"].forEach((id, i) => {
    const c = $(id);
    const k = pop(t, times[i] - 0.05, 0.38);
    // на «он всё делает» карточки влетают в персонажа
    const fly = easeInOut(prog(t, 6.1 + i * 0.08, 6.5 + i * 0.08));
    const dy = -(860 + i * 180 - 520) * fly;
    c.style.opacity = clamp(k * 2) * (1 - fly);
    c.style.transform = `translateX(${(1 - k) * (i % 2 ? 300 : -300)}px) translateY(${dy}px) scale(${lerp(0.6, 1, k) * (1 - fly * 0.8)})`;
  });
  const b = pop(t, 6.4, 0.4);
  set($("b3"), { opacity: clamp(b * 2), transform: `translateX(-50%) scale(${b}) rotate(-3deg)` });
  const sp = prog(t, 6.5, 7.1);
  sparks.forEach((s, i) => {
    const r = s.r * easeOut(sp);
    set(s.el, {
      opacity: sp > 0 && sp < 1 ? 1 - sp : 0,
      left: `${540 + Math.cos(s.a + t) * r - 11}px`,
      top: `${520 + Math.sin(s.a + t) * r - 11}px`,
    });
  });
}

// ---------- кадр сцены 4: за компьютером ----------
function renderS4(t) {
  const s4 = $("s4");
  s4.style.opacity = t >= 7.05 && t < 11.75 ? fade(t, 7.15, 11.66, 0.16) : 0;
  s4.style.transform = `scale(${1.04 - 0.04 * easeOut(prog(t, 7.1, 8))})`;
  const m = $("m4");
  const typing = t > 7.3 && t < 11.3;
  m.querySelector(".arm-l").style.transform = typing ? `translate(${-10}px, ${Math.sin(t * 34) * 12}px)` : "";
  m.querySelector(".arm-r").style.transform = typing ? `translateY(${Math.sin(t * 34 + Math.PI) * 12}px)` : "";
  m.querySelector(".legs").style.opacity = 0;
  const { eyes, k } = blink(m, t, 1.2);
  // смотрит на монитор (влево), а на «создал» — на нас
  const look = t > 10.9 ? 0 : -22;
  eyes.style.transform = `translate(${look}px, ${(1 - k) * 199}px) scaleY(${k})`;
  const hop = t > 10.9 && t < 11.4 ? Math.sin(prog(t, 10.9, 11.4) * Math.PI) * 50 : 0;
  m.style.transform = `translateY(${-hop + Math.sin(t * 6) * 3}px)`;

  const chip = (el, at) => {
    const kk = pop(t, at, 0.3);
    set(el, { opacity: clamp(kk * 2), transform: `translateY(${(1 - kk) * -40}px) scale(${lerp(0.7, 1, kk)})` });
  };
  chip($("chipVoice"), 8.38);
  chip($("chipText"), 8.68);

  const pv = pop(t, 9.3, 0.4);
  set($("preview"), { opacity: clamp(pv * 2), transform: `scale(${lerp(0.85, 1, pv)})` });
  $("preview").querySelector(".preview-scene").style.transform =
    `translateX(-50%) translateY(${Math.abs(Math.sin(t * 5)) * -10}px) scale(2.6)`;
  [9.76, 10.0, 10.28, 10.5].forEach((at, i) => {
    const kk = pop(t, at, 0.3);
    set(document.querySelector(`#s4 .f${i + 1}`), { opacity: clamp(kk * 2), transform: `translateY(${(1 - kk) * 60}px) scale(${kk})` });
  });
  const sb = pop(t, 10.88, 0.3);
  set($("previewSub"), { opacity: clamp(sb * 2), transform: `scale(${lerp(0.6, 1, sb)})` });
  const dn = pop(t, 11.05, 0.3);
  set($("done"), { opacity: clamp(dn * 2), transform: `scale(${dn})` });
}

// ---------- кадр сцены 5–6: окно Opus 5.5 и загрузка ----------
let targets = null;
function measure() {
  // координаты кнопок внутри кадра 1080×1920 (без учёта масштаба окна)
  const stage = $("stage").getBoundingClientRect();
  const scale = stage.width / 1080;
  const c = (el) => {
    const r = el.getBoundingClientRect();
    return { x: (r.left + r.width / 2 - stage.left) / scale, y: (r.top + r.height / 2 - stage.top) / scale };
  };
  const win = $("win");
  const prev = win.style.transform;
  win.style.transform = "none";
  targets = { upload: c($("upload")), send: c($("send")) };
  win.style.transform = prev;
}

function pointerPath(t) {
  const up = targets.upload, sd = targets.send;
  const keys = [
    { t: 13.7, x: 820, y: 1500 },
    { t: 14.15, x: up.x + 10, y: up.y + 6 },
    { t: 14.45, x: up.x + 10, y: up.y + 6 },
    { t: 14.85, x: sd.x + 6, y: sd.y + 8 },
    { t: 16.2, x: sd.x + 6, y: sd.y + 8 },
  ];
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (t <= b.t) {
      const k = easeInOut(prog(t, a.t, b.t));
      return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k) };
    }
  }
  return keys[keys.length - 1];
}

function renderS5(t) {
  const s5 = $("s5");
  s5.style.opacity = t >= 11.55 ? fade(t, 11.65, 99, 0.16) : 0;
  const w = pop(t, 11.6, 0.45);
  $("win").style.transform = `translateY(${(1 - w) * 120}px) scale(${lerp(0.9, 1, w)})`;

  // модель Opus 5.5 подсвечивается на «просто»
  const mk = prog(t, 11.76, 12.3);
  const glow = Math.sin(mk * Math.PI);
  set($("model"), {
    borderColor: mk > 0 ? "#d97757" : "#4a4540",
    boxShadow: `0 0 ${60 * glow}px rgba(217,119,87,${0.9 * glow})`,
    transform: `scale(${1 + 0.08 * glow})`,
  });

  // печать запроса
  const n = Math.round(prog(t, 12.0, 13.55) * PROMPT.length);
  $("typed").textContent = PROMPT.slice(0, n);
  $("ph").style.display = n ? "none" : "";
  $("bar").style.opacity = t < 14.2 && Math.floor(t * 3) % 2 === 0 ? 1 : n > 0 && n < PROMPT.length ? 1 : 0;

  // кнопка «Загрузите файл» привлекает внимание
  const up = $("upload");
  const pulse = t > 13.6 && t < 14.2 ? 1 + 0.05 * Math.sin(t * 18) : 1;
  const pressed = t > 14.2 && t < 14.32;
  set(up, {
    transform: `scale(${pressed ? 0.92 : pulse})`,
    borderColor: t > 13.6 ? "#d97757" : "#8d877f",
    background: pressed ? "rgba(217,119,87,.3)" : t > 13.6 ? "rgba(217,119,87,.12)" : "transparent",
  });

  // файл прикреплён
  const fk = pop(t, 14.32, 0.35);
  set($("file"), { opacity: clamp(fk * 2), transform: `translateY(${(1 - fk) * 30}px) scale(${lerp(0.8, 1, fk)})` });

  const send = $("send");
  send.className = "send" + (t > 14.32 ? " ready" : "");
  send.style.transform = `scale(${t > 14.88 && t < 15.0 ? 0.88 : 1})`;

  // шкала загрузки
  const pk = prog(t, 15.0, 15.95);
  set($("progress"), { opacity: clamp(prog(t, 14.92, 15.1)) });
  $("progFill").style.width = `${easeInOut(pk) * 100}%`;
  $("progPct").textContent = `${Math.round(easeInOut(pk) * 100)}%`;
  $("progLabel").textContent = pk >= 1 ? "✓ Создаю видео…" : "Загрузка файла…";

  // курсор мыши
  if (!targets) measure();
  const p = pointerPath(t);
  const ptr = $("pointer");
  set(ptr, { opacity: clamp(prog(t, 13.65, 13.8)), left: `${p.x}px`, top: `${p.y}px` });
  const clicking = (t > 14.15 && t < 14.3) || (t > 14.85 && t < 15.0);
  ptr.style.transform = `scale(${clicking ? 0.82 : 1})`;
  // круги от кликов
  const rp = $("ripple");
  const click = t < 14.7 ? { at: 14.18, ...targets.upload } : { at: 14.88, ...targets.send };
  const rk = prog(t, click.at, click.at + 0.45);
  set(rp, { left: `${click.x}px`, top: `${click.y}px`, opacity: rk > 0 && rk < 1 ? 1 - rk : 0, transform: `scale(${lerp(0.2, 1.4, rk)})` });
}

// ---------- общий рендер ----------
function renderAt(t) {
  t = clamp(t, 0, DURATION);
  renderS1(t);
  renderCover(t);
  renderS3(t);
  renderS4(t);
  renderS5(t);
  renderSubs(t);
}
window.renderAt = renderAt;

// ---------- масштаб кадра под окно ----------
function fit() {
  const s = Math.min(innerWidth / 1080, innerHeight / 1920);
  $("stage").style.transform = `scale(${s}) translate(-50%, -50%)`;
  targets = null;
}
addEventListener("resize", fit);
fit();

// ---------- воспроизведение ----------
const audio = $("voice");
const playBtn = $("play");
const params = new URLSearchParams(location.search);
let playing = false;

if (params.has("capture")) {
  document.body.classList.add("capture");
  renderAt(Number(params.get("t") || 0));
} else {
  renderAt(3.9); // заставка до запуска
}

function loop() {
  if (!playing) return;
  renderAt(audio.currentTime);
  requestAnimationFrame(loop);
}

playBtn.addEventListener("click", () => {
  audio.currentTime = 0;
  audio.play();
  playing = true;
  playBtn.style.display = "none";
  loop();
});

audio.addEventListener("ended", () => {
  playing = false;
  renderAt(DURATION);
  playBtn.innerHTML = "<span>↻</span> Ещё раз";
  playBtn.style.display = "";
});
