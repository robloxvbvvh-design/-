// Тутор: всё видео — функция от времени t (секунды озвучки).
// Во время просмотра t берётся из audio.currentTime, поэтому кадры и субтитры
// идут ровно по голосу. Для записи в файл: ?capture=1 и window.renderAt(t).

const AUDIO_END = 16.93;
const DURATION = 17.6; // после голоса держим финальный кадр

// Тайминги слов из расшифровки озвучки: [начало, конец, слово]
const PHRASES = [
  [[0.00, 0.28, "Это"], [0.28, 0.76, "тутор"], [0.76, 0.88, "на"], [0.88, 1.42, "создание"], [1.42, 1.78, "видео."]],
  [[2.30, 2.64, "Сначала"], [2.64, 3.14, "заходим"], [3.14, 4.14, "в ElevenLabs."]],
  [[4.38, 4.98, "Выбираем"], [4.98, 5.38, "голос,"], [5.38, 5.96, "текст."], [6.32, 6.56, "Всё."]],
  [[7.02, 7.52, "Заходим"], [7.52, 7.64, "в"], [7.64, 7.98, "Claude"], [7.98, 8.32, "Code"]],
  [[8.32, 8.60, "и"], [8.60, 9.06, "просим"], [9.06, 9.48, "создать"], [9.48, 10.04, "субтитры."]],
  [[10.30, 10.48, "И"], [10.48, 10.94, "кидаем"], [10.94, 11.34, "текст."]],
  [[11.70, 11.86, "Он"], [11.86, 12.36, "создаёт"], [12.36, 12.76, "видео,"]],
  [[13.12, 13.80, "скачиваем"], [13.80, 14.20, "и"], [14.20, 14.48, "всё."]],
  [[14.80, 15.14, "Даже"], [15.14, 15.32, "не"], [15.32, 15.56, "нужно"], [15.56, 16.08, "заходить"], [16.08, 16.16, "в"], [16.16, 16.70, "монтаж."]],
];

const EL_TEXT = "Это тутор на создание видео. Сначала заходим в ElevenLabs…";
const CC_TEXT = "Создай видео с субтитрами: слово горит красным, когда диктор его говорит";

// ---------- помощники ----------
const $ = (id) => document.getElementById(id);
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
const prog = (t, a, b) => clamp((t - a) / (b - a));
const lerp = (a, b, k) => a + (b - a) * k;
const easeOut = (k) => 1 - Math.pow(1 - k, 3);
const easeInOut = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
const easeBack = (k) => { const c = 1.7; return 1 + (c + 1) * Math.pow(k - 1, 3) + c * Math.pow(k - 1, 2); };
const pop = (t, at, len = 0.35) => easeBack(prog(t, at, at + len));
// Видимость сцены в окне [a, b] с коротким перекрёстным переходом
const sceneOpacity = (t, a, b, f = 0.14) => Math.min(prog(t, a, a + f), 1 - prog(t, b - f, b));

function set(el, styles) { Object.assign(el.style, styles); }
function popIn(el, t, at, extra = "") {
  const k = pop(t, at);
  set(el, { opacity: clamp(k * 2), transform: `${extra} scale(${k})` });
}
function typeText(el, bar, ph, text, t, a, b) {
  const n = Math.round(prog(t, a, b) * text.length);
  el.textContent = text.slice(0, n);
  ph.style.display = n ? "none" : "";
  bar.style.opacity = n > 0 && n < text.length ? 1 : Math.floor(t * 3) % 2 ? 0 : 1;
}

// ---------- персонаж: пиксельный человечек с картинки ----------
const MASCOT_SVG = `
<svg viewBox="0 100 387 315" shape-rendering="crispEdges">
  <rect class="arm arm-l" x="0" y="180" width="40" height="76"/>
  <rect class="arm arm-r" x="347" y="180" width="40" height="76"/>
  <rect class="leg" x="35" y="325" width="34" height="85"/>
  <rect class="leg" x="106" y="325" width="34" height="85"/>
  <rect class="leg" x="247" y="325" width="34" height="85"/>
  <rect class="leg" x="318" y="325" width="34" height="85"/>
  <rect class="body" x="35" y="105" width="317" height="226"/>
  <g class="eyes">
    <rect class="eye" x="70" y="180" width="36" height="38"/>
    <rect class="eye" x="283" y="180" width="35" height="38"/>
  </g>
</svg>`;
document.querySelectorAll(".mascot").forEach((m) => (m.innerHTML = MASCOT_SVG));

function animateMascot(m, t, offset = 0) {
  const ph = (t + offset) % 3.1;
  const k = ph < 0.12 ? 0.15 : 1;
  m.querySelector(".eyes").style.transform = `translateY(${(1 - k) * 199}px) scaleY(${k})`;
  m.querySelector(".arm-l").style.transform = `translateY(${Math.sin(t * 7 + offset) * 10}px)`;
  m.querySelector(".arm-r").style.transform = `translateY(${-Math.sin(t * 7 + offset) * 10}px)`;
}

// ---------- субтитры ----------
const phraseEls = PHRASES.map((words) => {
  const p = document.createElement("div");
  p.className = "phrase";
  p.innerHTML = words.map((w) => `<span class="w">${w[2]}</span>`).join(" ");
  $("subs").appendChild(p);
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
      const ws = p.words[j][0];
      const next = p.words[j + 1] ? p.words[j + 1][0] : p.words[j][1] + 0.35;
      const on = t >= ws && t < next;
      s.className = "w" + (on ? " on" : "");
      s.style.transform = on ? `scale(${1 + 0.12 * (1 - prog(t, ws, ws + 0.2))})` : "";
    });
  });
}

// ---------- курсор мыши ----------
let stageScale = 1;
function centerOf(id) {
  const st = $("stage").getBoundingClientRect();
  const r = $(id).getBoundingClientRect();
  return { x: (r.left + r.width / 2 - st.left) / stageScale, y: (r.top + r.height / 2 - st.top) / stageScale };
}

// Отрезки, когда курсор на экране: ключевые точки — координаты или id кнопки
const POINTER = [
  { from: 4.3, to: 7.0, keys: [
    { t: 4.3, x: 900, y: 1500 }, { t: 4.75, id: "vArtem" }, { t: 5.3, id: "vArtem" },
    { t: 5.7, x: 930, y: 1150 }, { t: 6.12, id: "elGen" }, { t: 6.5, id: "elGen" }, { t: 6.75, id: "listen" },
  ] },
  { from: 10.55, to: 11.55, keys: [{ t: 10.55, x: 860, y: 1500 }, { t: 11.0, id: "send" }] },
  { from: 12.75, to: 13.85, keys: [{ t: 12.75, x: 860, y: 1560 }, { t: 13.12, id: "dlBtn" }] },
];
const CLICKS = [
  { t: 4.8, id: "vArtem" }, { t: 6.28, id: "elGen" }, { t: 6.85, id: "listen" },
  { t: 11.1, id: "send" }, { t: 13.22, id: "dlBtn" },
];

function renderPointer(t) {
  const ptr = $("pointer");
  const seg = POINTER.find((s) => t >= s.from && t < s.to);
  if (!seg) { ptr.style.opacity = 0; } else {
    const pos = (k) => (k.id ? centerOf(k.id) : k);
    let p = pos(seg.keys[seg.keys.length - 1]);
    for (let i = 0; i < seg.keys.length - 1; i++) {
      const a = seg.keys[i], b = seg.keys[i + 1];
      if (t <= b.t) {
        const k = easeInOut(prog(t, a.t, b.t));
        const pa = pos(a), pb = pos(b);
        p = { x: lerp(pa.x, pb.x, k), y: lerp(pa.y, pb.y, k) };
        break;
      }
    }
    const clicking = CLICKS.some((c) => t > c.t - 0.03 && t < c.t + 0.12);
    set(ptr, {
      opacity: Math.min(prog(t, seg.from, seg.from + 0.12), 1 - prog(t, seg.to - 0.12, seg.to)),
      left: `${p.x - 8}px`, top: `${p.y - 4}px`,
      transform: `scale(${clicking ? 0.82 : 1})`,
    });
  }
  const rp = $("ripple");
  const c = [...CLICKS].reverse().find((c) => t >= c.t);
  const rk = c ? prog(t, c.t, c.t + 0.3) : 1;
  if (c && rk < 1) {
    const p = centerOf(c.id);
    set(rp, { left: `${p.x}px`, top: `${p.y}px`, opacity: 1 - rk, transform: `scale(${lerp(0.2, 1.4, rk)})` });
  } else rp.style.opacity = 0;
}

// ---------- 1. «Это тутор на создание видео» ----------
function renderS1(t) {
  $("s1").style.opacity = sceneOpacity(t, -1, 2.3);
  popIn($("tag"), t, 0.0, "translateX(-50%) rotate(-4deg)");
  const tk = pop(t, 0.2, 0.4);
  set($("title"), { opacity: clamp(tk * 2), transform: `translateY(${(1 - tk) * 60}px)` });
  const m = $("m1");
  const mk = pop(t, 0.5, 0.45);
  m.style.transform = `translateY(${Math.sin(t * 4) * 10}px) scale(${mk})`;
  animateMascot(m, t);
  [["st1", 0.88], ["ar1", 1.05], ["st2", 1.2], ["ar2", 1.35], ["st3", 1.48]].forEach(([id, at]) => {
    const k = pop(t, at, 0.3);
    set($(id), { opacity: clamp(k * 2), transform: `translateY(${(1 - k) * 50}px) scale(${lerp(0.6, 1, k)})` });
  });
}

// ---------- 2. ElevenLabs ----------
function renderS2(t) {
  $("s2").style.opacity = sceneOpacity(t, 2.2, 7.05);
  popIn($("num1"), t, 2.3);

  // иконка ElevenLabs появляется на «заходим», название — на «ElevenLabs»
  const ik = pop(t, 2.64, 0.45);
  const away = easeInOut(prog(t, 4.05, 4.4));
  set($("elIcon"), {
    opacity: 1 - away,
    transform: `translate(${-away * 380}px, ${-away * 320}px) scale(${ik * lerp(1, 0.2, away)}) rotate(${(1 - ik) * -20}deg)`,
  });
  const nk = pop(t, 3.14, 0.35);
  set($("elName"), { opacity: clamp(nk * 2) * (1 - away), transform: `scale(${nk})` });

  // окно приложения
  const wk = pop(t, 4.15, 0.4);
  set($("elWin"), { opacity: clamp(wk * 2), transform: `translateY(${(1 - wk) * 100}px) scale(${lerp(0.9, 1, wk)})` });

  // выбор голоса Artem
  const sel = t >= 4.82;
  set($("vArtem"), {
    borderColor: sel ? "#000" : "#eee",
    background: sel ? "#f6f3ef" : "#fff",
    transform: `scale(${t > 4.8 && t < 4.95 ? 0.97 : 1})`,
  });
  $("vArtem").querySelector(".check").style.opacity = sel ? 1 : 0;

  // ввод текста
  typeText($("elTyped"), $("elBar"), $("elPh"), EL_TEXT, t, 5.38, 6.1);

  // «Создать» → «Создаю…» → плеер
  const gen = $("elGen");
  const generating = t >= 6.28 && t < 6.6;
  gen.style.transform = `scale(${t > 6.26 && t < 6.38 ? 0.96 : 1})`;
  gen.style.background = generating ? "#444" : t >= 6.6 ? "#2e9d5f" : "#000";
  $("elGenLabel").textContent = generating ? "Создаю…" : t >= 6.6 ? "✓ Готово" : "Создать озвучку";
  const pk = pop(t, 6.55, 0.3);
  set($("player"), { opacity: clamp(pk * 2), transform: `translateY(${(1 - pk) * 20}px)` });
  // «Слушать»: волна заполняется
  const lk = prog(t, 6.85, 7.6);
  $("plWave").style.setProperty("--p", `${lk * 100}%`);
  $("playBtn").textContent = t >= 6.85 ? "❚❚" : "▶";
  $("listen").style.transform = `scale(${t > 6.83 && t < 6.95 ? 0.92 : 1})`;
}

// ---------- 3. Claude Code ----------
function renderS3(t) {
  $("s3").style.opacity = sceneOpacity(t, 6.95, 11.6);
  popIn($("num2"), t, 7.02);
  const wk = pop(t, 7.0, 0.45);
  $("win").style.transform = `translateY(${(1 - wk) * 120}px) scale(${lerp(0.9, 1, wk)})`;
  // логотип вспыхивает на «Claude Code»
  const g = Math.sin(prog(t, 7.64, 8.3) * Math.PI);
  $("hello").style.transform = `scale(${1 + 0.06 * g})`;
  $("hello").style.textShadow = `0 0 ${40 * g}px rgba(217,119,87,${g})`;
  animateMascot($("hello").querySelector(".mascot"), t, 0.7);

  typeText($("ccTyped"), $("ccBar"), $("ccPh"), CC_TEXT, t, 8.6, 10.1);

  // «кидаем текст»: файлы падают в поле ввода
  [["fVoice", 10.48], ["fText", 10.7]].forEach(([id, at]) => {
    const k = easeBack(prog(t, at, at + 0.35));
    set($(id), { opacity: clamp(k * 3), transform: `translateY(${(1 - k) * -260}px) rotate(${(1 - k) * 8}deg)` });
  });
  const send = $("send");
  send.className = "send" + (t > 10.7 ? " ready" : "");
  send.style.transform = `scale(${t > 11.08 && t < 11.22 ? 0.88 : 1})`;
}

// ---------- 4. Создаёт видео → скачиваем → и всё ----------
function renderS4(t) {
  $("s4").style.opacity = sceneOpacity(t, 11.5, 14.75);
  popIn($("num3"), t, 11.6);
  const phk = pop(t, 11.55, 0.45);
  $("phone").style.transform = `translateY(${(1 - phk) * 160}px) scale(${lerp(0.85, 1, phk)})`;

  const m = $("m4");
  m.style.transform = `translateY(${-Math.abs(Math.sin(t * 5)) * 24}px)`;
  animateMascot(m, t, 1.4);
  // мини-субтитры внутри ролика тоже загораются красным
  const demo = ["ВИДЕО", "С", "СУБТИТРАМИ"];
  const on = Math.floor(t * 3) % demo.length;
  $("phSub").innerHTML = demo.map((w, i) => (i === on ? `<b>${w}</b>` : w)).join(" ");

  // рендер 0 → 100 %
  const rk = easeInOut(prog(t, 11.75, 12.7));
  $("rFill").style.width = `${rk * 100}%`;
  $("rPct").textContent = `${Math.round(rk * 100)}%`;
  $("rLabel").textContent = rk >= 1 ? "✓ Видео готово" : "Создаю видео…";
  $("render").style.opacity = 1 - prog(t, 13.0, 13.3);

  // кнопка «Скачать»
  const dk = pop(t, 12.72, 0.35);
  const press = t > 13.2 && t < 13.34 ? 0.92 : 1;
  set($("dlBtn"), { opacity: clamp(dk * 2), transform: `translateX(-50%) scale(${dk * press})` });

  // загрузка файла в браузере
  const tk = pop(t, 13.32, 0.35);
  set($("dlToast"), { opacity: clamp(tk * 2), transform: `translateY(${(1 - tk) * -80}px)` });
  const ring = prog(t, 13.35, 14.05);
  $("dlRing").style.height = `${ring * 100}%`;
  $("dlState").textContent = ring >= 1 ? "Скачано ✓" : `Загрузка… ${Math.round(ring * 100)}%`;

  // «и всё» — большая галочка
  const ak = pop(t, 14.18, 0.35);
  set($("allDone"), { opacity: clamp(ak * 2), transform: `scale(${ak})` });
}

// ---------- 5. Без монтажа: иконка монтажа и красный крест ----------
function renderS5(t) {
  $("s5").style.opacity = sceneOpacity(t, 14.68, 99);
  const ik = pop(t, 14.75, 0.45);
  // на «не» иконка дёргается, после креста — тускнеет
  const shake = t > 15.14 && t < 15.5 ? Math.sin(t * 60) * 10 * (1 - prog(t, 15.14, 15.5)) : 0;
  const dead = prog(t, 16.4, 16.8);
  set($("editIcon"), {
    transform: `translateX(${shake}px) scale(${ik * lerp(1, 0.94, dead)})`,
    filter: `grayscale(${dead}) brightness(${lerp(1, 0.6, dead)})`,
  });
  const nk = pop(t, 15.0, 0.35);
  set($("editName"), { opacity: clamp(nk * 2) * lerp(1, 0.5, dead), transform: `scale(${nk})` });

  $("x1").style.strokeDashoffset = 114 * (1 - easeOut(prog(t, 16.1, 16.32)));
  $("x2").style.strokeDashoffset = 114 * (1 - easeOut(prog(t, 16.3, 16.52)));
  const xs = t > 16.1 && t < 16.6 ? 1 + 0.05 * Math.sin(prog(t, 16.1, 16.6) * Math.PI) : 1;
  $("cross").style.transform = `scale(${xs})`;

  const bk = pop(t, 16.6, 0.4);
  set($("noEdit"), { opacity: clamp(bk * 2), transform: `translateX(-50%) scale(${bk}) rotate(-3deg)` });
}

// ---------- общий рендер ----------
function renderAt(t) {
  t = clamp(t, 0, DURATION);
  renderS1(t);
  renderS2(t);
  renderS3(t);
  renderS4(t);
  renderS5(t);
  renderPointer(t);
  renderSubs(t);
}
window.renderAt = renderAt;

// ---------- масштаб кадра под окно ----------
function fit() {
  stageScale = Math.min(innerWidth / 1080, innerHeight / 1920);
  $("stage").style.transform = `scale(${stageScale}) translate(-50%, -50%)`;
}
addEventListener("resize", fit);
fit();

// ---------- воспроизведение ----------
const audio = $("voice");
const playBtn = $("play");
const params = new URLSearchParams(location.search);
let playing = false;
let tailStart = 0;

if (params.has("capture")) {
  document.body.classList.add("capture");
  renderAt(Number(params.get("t") || 0));
} else {
  renderAt(1.6); // заставка до запуска
}

function currentTime() {
  // после конца озвучки ещё немного держим финал по часам браузера
  return audio.ended ? AUDIO_END + (performance.now() - tailStart) / 1000 : audio.currentTime;
}

function loop() {
  if (!playing) return;
  const t = currentTime();
  renderAt(t);
  if (t >= DURATION) {
    playing = false;
    playBtn.innerHTML = "<span>↻</span> Ещё раз";
    playBtn.style.display = "";
    return;
  }
  requestAnimationFrame(loop);
}

playBtn.addEventListener("click", () => {
  audio.currentTime = 0;
  audio.play();
  playing = true;
  playBtn.style.display = "none";
  loop();
});

audio.addEventListener("ended", () => { tailStart = performance.now(); });
