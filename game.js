import * as THREE from "three";

// ---------- Платформа и качество графики ----------
const isTouch =
  window.matchMedia("(pointer: coarse)").matches ||
  ("ontouchstart" in window && !window.matchMedia("(pointer: fine)").matches);
if (isTouch) document.body.classList.add("touch");

// На телефоне: без теней и динамических источников света, пониженное разрешение
const QUALITY = isTouch
  ? { pixelRatio: Math.min(window.devicePixelRatio, 1), shadows: false, dynamicLights: false, maxZombies: 22 }
  : { pixelRatio: Math.min(window.devicePixelRatio, 1.5), shadows: true, dynamicLights: true, maxZombies: 40 };

// ---------- Настройки ----------
const CONFIG = {
  mapSize: 90,
  playerHeight: 1.7,
  playerRadius: 0.5,
  walkSpeed: 6,
  runSpeed: 10,
  jumpSpeed: 7,
  gravity: 20,
  maxHealth: 100,
  headshotMultiplier: 2.5,
};

// kind: "hitscan" (по умолчанию) | "flame" | "rocket"; pierce — сколько зомби пробивает пуля
const WEAPONS = [
  { name: "Пистолет", price: 0, note: "бесконечные патроны", short: "Пистолет", damage: 30, rate: 0.2, mag: 12, reserve: Infinity, reload: 1.1, spread: 0.008, recoil: 0.3,
    sound: { dur: 0.15, freq: 2400, vol: 0.25 },
    model: { len: 0.2, h: 0.1, barrel: 0.05, r: 0.016, color: 0x2e2e33 } },
  { name: "Револьвер", price: 250, note: "пробивает 2 зомби", short: "Револьвер", damage: 80, rate: 0.45, mag: 6, reserve: 36, reload: 1.8, spread: 0.004, recoil: 0.8, pierce: 2,
    sound: { dur: 0.3, freq: 1500, vol: 0.4 },
    model: { len: 0.2, h: 0.11, barrel: 0.16, r: 0.02, color: 0x9a9aa2, cylinder: true } },
  { name: "Узи", price: 150, note: "очень быстрая стрельба", short: "Узи", damage: 15, rate: 0.06, mag: 32, reserve: 192, reload: 1.3, spread: 0.03, recoil: 0.15,
    sound: { dur: 0.1, freq: 2800, vol: 0.2 },
    model: { len: 0.24, h: 0.11, barrel: 0.06, r: 0.016, color: 0x1e1e22, magH: 0.2 } },
  { name: "Автомат", price: 300, note: "надёжный и точный", short: "Автомат", damage: 26, rate: 0.1, mag: 30, reserve: 180, reload: 1.6, spread: 0.014, recoil: 0.35,
    sound: { dur: 0.22, freq: 1800, vol: 0.32 },
    model: { len: 0.45, h: 0.12, barrel: 0.3, r: 0.02, color: 0x3a3a40, magH: 0.18, stock: 0.25, wood: true } },
  { name: "Дробовик", price: 400, note: "дробь, сильный вблизи", short: "Дробовик", damage: 14, pellets: 9, rate: 0.8, mag: 8, reserve: 48, reload: 2.2, spread: 0.09, recoil: 1,
    sound: { dur: 0.4, freq: 1100, vol: 0.5 },
    model: { len: 0.4, h: 0.11, barrel: 0.4, r: 0.028, color: 0x2a2a2e, stock: 0.28, wood: true, pump: true } },
  { name: "Двустволка", price: 550, note: "12 дробин за выстрел", short: "Двустволка", damage: 16, pellets: 12, rate: 0.3, mag: 2, reserve: 40, reload: 1.8, spread: 0.13, recoil: 1.3,
    sound: { dur: 0.45, freq: 1000, vol: 0.55 },
    model: { len: 0.3, h: 0.1, barrel: 0.5, r: 0.024, barrels: 2, color: 0x5a5a5e, stock: 0.3, wood: true } },
  { name: "Снайперская винтовка", price: 800, note: "пробивает до 5 зомби", short: "Снайперка", damage: 170, rate: 1.1, mag: 5, reserve: 35, reload: 2.2, spread: 0, recoil: 1.4, pierce: 5, tracer: 0xffffff,
    sound: { dur: 0.5, freq: 1300, vol: 0.55 },
    model: { len: 0.5, h: 0.11, barrel: 0.55, r: 0.018, color: 0x3b4a2f, stock: 0.3, scope: true, magH: 0.1 } },
  { name: "Пулемёт", price: 1000, note: "магазин на 100 патронов", short: "Пулемёт", damage: 24, rate: 0.075, mag: 100, reserve: 300, reload: 3.2, spread: 0.025, recoil: 0.3,
    sound: { dur: 0.22, freq: 1600, vol: 0.32 },
    model: { len: 0.55, h: 0.15, barrel: 0.4, r: 0.026, color: 0x2b2f2b, stock: 0.25, box: true } },
  { name: "Миниган", price: 1600, note: "200 патронов, шквальный огонь", short: "Миниган", damage: 17, rate: 0.035, mag: 200, reserve: 600, reload: 4, spread: 0.035, recoil: 0.15,
    sound: { dur: 0.12, freq: 2000, vol: 0.22 },
    model: { len: 0.4, h: 0.18, barrel: 0.5, r: 0.014, barrels: 6, color: 0x444448, box: true } },
  { name: "Огнемёт", price: 1200, note: "жжёт всех перед собой", short: "Огнемёт", kind: "flame", damage: 7, range: 10, cone: 0.28, rate: 0.05, mag: 100, reserve: 300, reload: 2.5, recoil: 0.05,
    sound: { dur: 0.08, freq: 700, vol: 0.12 },
    model: { len: 0.45, h: 0.12, barrel: 0.25, r: 0.03, color: 0x6a3a1a, tank: true } },
  { name: "Гранатомёт", price: 1800, note: "взрыв по площади", short: "РПГ", kind: "rocket", damage: 240, radius: 5.5, speed: 38, rate: 1.0, mag: 1, reserve: 15, reload: 1.8, recoil: 1.2,
    sound: { dur: 0.5, freq: 600, vol: 0.45 },
    model: { len: 0.7, h: 0.1, barrel: 0.1, r: 0.06, color: 0x4a5a3a, tube: true } },
  { name: "Лазерная винтовка", price: 2500, note: "прошивает всех на пути", short: "Лазер", damage: 45, rate: 0.14, mag: 40, reserve: 160, reload: 1.8, spread: 0, recoil: 0.2, pierce: 99, tracer: 0x33ddff, laser: true,
    sound: { laser: true },
    model: { len: 0.45, h: 0.13, barrel: 0.2, r: 0.022, color: 0xd8dde8, glow: 0x33ddff, stock: 0.2 } },
];

// Виды зомби. minWave — с какой волны появляются, weight — частота
const ZOMBIE_TYPES = {
  walker: { name: "Зомби", hp: 60, speed: 2.2, damage: 10, scale: 1, skin: 0x5d8a4a, cloth: 0x3a3048, pants: 0x2a2a35, score: 10, minWave: 1, weight: 10 },
  runner: { name: "Бегун", hp: 35, speed: 4.8, damage: 7, scale: 0.9, skin: 0x8a9a4a, cloth: 0x6a2a2a, pants: 0x30302a, score: 15, minWave: 2, weight: 5 },
  crawler: { name: "Ползун", hp: 30, speed: 3.2, damage: 8, scale: 1, skin: 0x6a7a5a, cloth: 0x4a4a4a, pants: 0x2a2a2a, score: 15, minWave: 2, weight: 4, crawl: true },
  spitter: { name: "Плевун", hp: 50, speed: 2.6, damage: 12, scale: 1, skin: 0x9acd32, cloth: 0x4b3b5b, pants: 0x2a2a35, score: 25, minWave: 3, weight: 3, spit: true, keepDist: 13, spitRate: 2.2, acid: 12 },
  exploder: { name: "Взрывун", hp: 45, speed: 2.5, damage: 45, scale: 1.1, skin: 0xc8a040, cloth: 0x7a5a2a, pants: 0x4a3a2a, score: 25, minWave: 3, weight: 3, explode: true },
  armored: { name: "Спецназ", hp: 120, speed: 2.0, damage: 14, scale: 1.05, skin: 0x5a7a5a, cloth: 0x2f3f2a, pants: 0x2f3f2a, score: 30, minWave: 4, weight: 3, armor: 0.6 },
  tank: { name: "Громила", hp: 300, speed: 1.5, damage: 25, scale: 1.6, skin: 0x3a5a4a, cloth: 0x2a2a2a, pants: 0x1f1f25, score: 40, minWave: 4, weight: 2 },
  // Боссы: по одному на каждую главу сюжета
  butcher: { name: "Мясник", hp: 2200, speed: 1.9, damage: 35, scale: 2.6, skin: 0x7a3a3a, cloth: 0x1a1a1a, pants: 0x1a1a1a, score: 500, minWave: Infinity, weight: 0, boss: true, butcher: true },
  queen: { name: "Королева плевунов", hp: 2600, speed: 1.6, damage: 25, scale: 2.3, skin: 0x9acd32, cloth: 0x3b2b4b, pants: 0x2a2a35, score: 700, minWave: Infinity, weight: 0, boss: true, spit: true, volley: 5, spitRate: 2.4, keepDist: 18, acid: 12 },
  general: { name: "Генерал Громов", hp: 3200, speed: 2.0, damage: 30, scale: 2.2, skin: 0x5a7a5a, cloth: 0x2f3f2a, pants: 0x2f3f2a, score: 900, minWave: Infinity, weight: 0, boss: true, armor: 0.5, charge: true },
  patient: { name: "Нулевой пациент", hp: 5000, speed: 1.8, damage: 40, scale: 3, skin: 0xd8d8c8, cloth: 0x3a3a4a, pants: 0x2a2a35, score: 1500, minWave: Infinity, weight: 0, boss: true, volley: 3, spitRate: 3.5, acid: 15, charge: true, summon: true, patient: true },
};

// ---------- Сюжет: 4 главы по 5 волн, в конце каждой — босс ----------
const BREAK_TIME = 25; // секунд передышки между волнами
const STORY = [
  {
    chapter: "Глава 1 из 4", title: "Карантин", boss: "butcher",
    text: [
      "Научный городок Новоград-4. Под ним — лаборатория «Генезис», где создавали вакцину нового поколения под кодом Ч-4.",
      "В 02:14 сработала тревога. Вакцина оказалась вирусом: за час весь персонал лаборатории превратился в заражённых.",
      "Ты — боец охраны внешнего периметра. Связи нет, ворота заблокированы. Приказ один: держать периметр до прибытия эвакуации.",
      "Между волнами есть время перевести дух. Трать заработанные деньги в магазине: новое оружие, аптечки и броня.",
    ],
  },
  {
    chapter: "Глава 2 из 4", title: "Кислотный дождь", boss: "queen",
    text: [
      "Мясник повержен, но вертолёт так и не прилетел. Вместо него ожила рация.",
      "«Говорит доктор Вера Орлова, корпус Б. Если меня кто-то слышит: вирус мутирует. Некоторые заражённые плюются кислотой, а их матка гнездится в старом резервуаре».",
      "Орлова знает, с чего всё началось. Чтобы добраться до неё, нужно продержаться ещё пять волн.",
    ],
  },
  {
    chapter: "Глава 3 из 4", title: "Чёрный батальон", boss: "general",
    text: [
      "Королева плевунов мертва. На рассвете над лесом показались огни: прибыл армейский батальон зачистки.",
      "Через час рация батальона замолчала. Солдаты вернулись — в касках, бронежилетах и с пустыми глазами.",
      "Орлова: «Их командиру, генералу Громову, первым ввели Ч-4. Броня делает их почти неуязвимыми. Цельтесь в лицо».",
    ],
  },
  {
    chapter: "Глава 4 из 4", title: "Нулевой пациент", boss: "patient",
    text: [
      "Генерал Громов пал. Орлова наконец рассказывает правду.",
      "«Ч-4 вырастили из клеток одного человека — подопытного № 0. Он до сих пор жив и управляет заражёнными, как ульем».",
      "«Если уничтожить Нулевого пациента, улей рассыплется. Он уже идёт к тебе. И он придёт не один».",
    ],
  },
];
const EPILOGUE = {
  chapter: "Эпилог", title: "Рассвет", button: "БЕСКОНЕЧНЫЙ РЕЖИМ",
  text: [
    "Нулевой пациент рухнул, и над Новоградом-4 повисла тишина. Заражённые застыли, словно марионетки с обрезанными нитями.",
    "Через час над периметром завис вертолёт. Доктор Орлова поднялась на борт с образцами: по ним можно создать настоящую вакцину.",
    "Ты остаёшься прикрывать взлёт. Из леса уже доносится знакомый стон: улей потерял хозяина, но не всех своих детей.",
    "История окончена. Дальше — бесконечный режим: сколько волн ты продержишься?",
  ],
};
const BOSS_TYPES = STORY.map((c) => c.boss);

// ---------- DOM ----------
const $ = (id) => document.getElementById(id);
const ui = {
  hud: $("hud"),
  menu: $("menu"),
  pause: $("pause"),
  gameover: $("gameover"),
  wave: $("wave"),
  score: $("score"),
  zombiesLeft: $("zombies-left"),
  health: $("health-bar"),
  ammo: $("ammo"),
  weaponName: $("weapon-name"),
  weaponBar: $("weapon-bar"),
  message: $("message"),
  damage: $("damage-overlay"),
  hitMarker: $("hit-marker"),
  finalStats: $("final-stats"),
  touch: $("touch-controls"),
  bossWrap: $("boss-wrap"),
  bossName: $("boss-name"),
  bossBar: $("boss-bar"),
  fps: $("fps"),
  money: $("money"),
  armor: $("armor-bar"),
  breakPanel: $("break-panel"),
  breakTimer: $("break-timer"),
  shop: $("shop"),
  shopItems: $("shop-items"),
  shopMoney: $("shop-money"),
  shopTimer: $("shop-timer"),
  story: $("story"),
  storyChapter: $("story-chapter"),
  storyTitle: $("story-title"),
  storyText: $("story-text"),
  storyBtn: $("story-btn"),
};

// ---------- Рендер и сцена ----------
const renderer = new THREE.WebGLRenderer({ antialias: !isTouch, powerPreference: "high-performance" });
let pixelRatio = QUALITY.pixelRatio;
renderer.setPixelRatio(pixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = QUALITY.shadows;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1d24);
scene.fog = new THREE.Fog(0x1a1d24, 12, 65);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.05, 90);
camera.rotation.order = "YXZ";
scene.add(camera);

scene.add(new THREE.HemisphereLight(0x8899bb, 0x332211, 1.1));
const moon = new THREE.DirectionalLight(0xaabbff, 1.0);
moon.position.set(30, 50, 20);
if (QUALITY.shadows) {
  moon.castShadow = true;
  moon.shadow.mapSize.set(1024, 1024);
  Object.assign(moon.shadow.camera, { left: -50, right: 50, top: 50, bottom: -50, near: 1, far: 150 });
}
scene.add(moon);

// Lambert-материалы заметно дешевле PBR; кэшируем по цвету
const matCache = new Map();
function lambert(color, emissive = 0x000000) {
  const key = `${color}:${emissive}`;
  if (!matCache.has(key)) matCache.set(key, new THREE.MeshLambertMaterial({ color, emissive }));
  return matCache.get(key);
}
const BOX = new THREE.BoxGeometry(1, 1, 1);

// ---------- Мир ----------
function makeGroundTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d");
  g.fillStyle = "#2f3a26";
  g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 3000; i++) {
    const v = 30 + Math.random() * 40;
    g.fillStyle = `rgb(${v},${v + 15},${v - 5})`;
    g.fillRect(Math.random() * 256, Math.random() * 256, 2, 2);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(40, 40);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(CONFIG.mapSize * 2 + 40, CONFIG.mapSize * 2 + 40),
  new THREE.MeshLambertMaterial({ map: makeGroundTexture() })
);
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = QUALITY.shadows;
scene.add(ground);

// Препятствия для коллизий: { minX, maxX, minZ, maxZ, height }
const obstacles = [];
// Меши, в которые попадают пули (instanced-меши статичного мира)
const obstacleMeshes = [];

// Весь статичный мир собирается в несколько InstancedMesh — это несколько вызовов отрисовки вместо сотен
function buildWorld() {
  const S = CONFIG.mapSize;
  const boxes = [];
  const addBox = (x, z, w, h, d, color, rotated = false) => {
    const bw = rotated ? d : w;
    const bd = rotated ? w : d;
    boxes.push({ x, y: h / 2, z, w: bw, h, d: bd, color });
    obstacles.push({ minX: x - bw / 2, maxX: x + bw / 2, minZ: z - bd / 2, maxZ: z + bd / 2, height: h });
  };

  const wallColor = 0x3d3d40;
  addBox(0, -S - 1, S * 2 + 4, 4, 2, wallColor);
  addBox(0, S + 1, S * 2 + 4, 4, 2, wallColor);
  addBox(-S - 1, 0, 2, 4, S * 2 + 4, wallColor);
  addBox(S + 1, 0, 2, 4, S * 2 + 4, wallColor);

  let seed = 1337;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  for (let i = 0; i < 70; i++) {
    const x = (rnd() * 2 - 1) * (S - 6);
    const z = (rnd() * 2 - 1) * (S - 6);
    if (Math.hypot(x, z) < 8) continue;
    const kind = rnd();
    if (kind < 0.5) {
      const s = 1 + rnd() * 1.5;
      addBox(x, z, s, s, s, 0x6b4a2b);
    } else if (kind < 0.8) {
      const len = 4 + rnd() * 8;
      addBox(x, z, len, 1.5 + rnd() * 2.5, 0.6, 0x555560, rnd() < 0.5);
    } else {
      addBox(x, z, 4.2, 1.4, 2, [0x5a1f1f, 0x1f3a5a, 0x4a4a4a][Math.floor(rnd() * 3)]);
    }
  }

  const m = new THREE.Matrix4();
  const q = new THREE.Quaternion();
  const color = new THREE.Color();
  const boxMesh = new THREE.InstancedMesh(BOX, new THREE.MeshLambertMaterial(), boxes.length);
  boxes.forEach((b, i) => {
    m.compose(new THREE.Vector3(b.x, b.y, b.z), q, new THREE.Vector3(b.w, b.h, b.d));
    boxMesh.setMatrixAt(i, m);
    boxMesh.setColorAt(i, color.setHex(b.color));
  });
  boxMesh.castShadow = boxMesh.receiveShadow = QUALITY.shadows;
  scene.add(boxMesh);
  obstacleMeshes.push(boxMesh);

  // Мёртвые деревья
  const trunks = [];
  const branches = [];
  for (let i = 0; i < 40; i++) {
    const x = (rnd() * 2 - 1) * (S - 4);
    const z = (rnd() * 2 - 1) * (S - 4);
    if (Math.hypot(x, z) < 8) continue;
    const h = 4 + rnd() * 4;
    trunks.push({ x, z, h });
    obstacles.push({ minX: x - 0.3, maxX: x + 0.3, minZ: z - 0.3, maxZ: z + 0.3, height: h });
    for (let b = 0; b < 3; b++) {
      const obj = new THREE.Object3D();
      obj.position.set(x, h * (0.55 + b * 0.15), z);
      obj.rotation.set(rnd() - 0.5 + 0.8, rnd() * Math.PI * 2, 0, "YXZ");
      obj.translateY(0.8);
      obj.updateMatrix();
      branches.push(obj.matrix.clone());
    }
  }
  const trunkMat = lambert(0x2b1d14);
  const trunkMesh = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.15, 0.35, 1, 6), trunkMat, trunks.length);
  trunks.forEach((t, i) => {
    m.compose(new THREE.Vector3(t.x, t.h / 2, t.z), q, new THREE.Vector3(1, t.h, 1));
    trunkMesh.setMatrixAt(i, m);
  });
  trunkMesh.castShadow = QUALITY.shadows;
  scene.add(trunkMesh);
  obstacleMeshes.push(trunkMesh);
  const branchMesh = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.05, 0.1, 1.8, 5), trunkMat, branches.length);
  branches.forEach((mat, i) => branchMesh.setMatrixAt(i, mat));
  scene.add(branchMesh);

  // Фонари: вместо дорогих источников света — светящиеся плафоны и «пятна света» на земле
  const lamps = [[20, 20], [-25, 15], [10, -30], [-30, -30], [40, -10], [-5, 45], [55, 40], [-50, -5], [30, -55], [-45, 55]];
  const poles = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.08, 0.08, 4, 6), lambert(0x222222), lamps.length);
  const bulbs = new THREE.InstancedMesh(new THREE.SphereGeometry(0.22, 8, 6), new THREE.MeshBasicMaterial({ color: 0xffcc88 }), lamps.length);
  const glowTex = (() => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const g = c.getContext("2d");
    const grad = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grad.addColorStop(0, "rgba(255,170,90,0.55)");
    grad.addColorStop(1, "rgba(255,170,90,0)");
    g.fillStyle = grad;
    g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  })();
  const pools = new THREE.InstancedMesh(
    new THREE.PlaneGeometry(14, 14).rotateX(-Math.PI / 2),
    new THREE.MeshBasicMaterial({ map: glowTex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending }),
    lamps.length
  );
  lamps.forEach(([x, z], i) => {
    m.makeTranslation(x, 2, z);
    poles.setMatrixAt(i, m);
    m.makeTranslation(x, 4.1, z);
    bulbs.setMatrixAt(i, m);
    m.makeTranslation(x, 0.02, z);
    pools.setMatrixAt(i, m);
  });
  scene.add(poles, bulbs, pools);
}
buildWorld();

// Выталкивание круга из AABB-препятствий
function resolveCollisions(pos, radius) {
  for (const o of obstacles) {
    const cx = Math.max(o.minX, Math.min(pos.x, o.maxX));
    const cz = Math.max(o.minZ, Math.min(pos.z, o.maxZ));
    const dx = pos.x - cx;
    const dz = pos.z - cz;
    const d2 = dx * dx + dz * dz;
    if (d2 >= radius * radius) continue;
    if (d2 > 1e-6) {
      const d = Math.sqrt(d2);
      pos.x += (dx / d) * (radius - d);
      pos.z += (dz / d) * (radius - d);
    } else {
      // Центр внутри коробки — выталкиваем по кратчайшей оси
      const pushes = [
        [o.minX - radius - pos.x, 0],
        [o.maxX + radius - pos.x, 0],
        [0, o.minZ - radius - pos.z],
        [0, o.maxZ + radius - pos.z],
      ];
      pushes.sort((a, b) => Math.abs(a[0] + a[1]) - Math.abs(b[0] + b[1]));
      pos.x += pushes[0][0];
      pos.z += pushes[0][1];
    }
  }
}

function insideObstacle(p) {
  return obstacles.some((o) => p.x > o.minX && p.x < o.maxX && p.z > o.minZ && p.z < o.maxZ && p.y < o.height);
}

// ---------- Звук (синтез через WebAudio) ----------
let audioCtx = null;
const noiseCache = new Map();
function initAudio() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === "suspended") audioCtx.resume();
}

function noiseBuffer(duration) {
  if (noiseCache.has(duration)) return noiseCache.get(duration);
  const len = Math.floor(audioCtx.sampleRate * duration);
  const buf = audioCtx.createBuffer(1, len, audioCtx.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / len) ** 2;
  noiseCache.set(duration, buf);
  return buf;
}

function playNoise(dur, freq, vol) {
  if (!audioCtx) return;
  const src = audioCtx.createBufferSource();
  src.buffer = noiseBuffer(dur);
  const filter = audioCtx.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = freq;
  const gain = audioCtx.createGain();
  gain.gain.value = vol;
  src.connect(filter).connect(gain).connect(audioCtx.destination);
  src.start();
}

function playTone(freq, endFreq, duration, type = "sawtooth", volume = 0.15) {
  if (!audioCtx) return;
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  osc.type = type;
  const t = audioCtx.currentTime;
  osc.frequency.setValueAtTime(freq, t);
  osc.frequency.exponentialRampToValueAtTime(endFreq, t + duration);
  gain.gain.setValueAtTime(volume, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + duration);
  osc.connect(gain).connect(audioCtx.destination);
  osc.start(t);
  osc.stop(t + duration);
}

const sfx = {
  shot: (w) => (w.sound.laser ? playTone(1400, 300, 0.12, "square", 0.08) : playNoise(w.sound.dur, w.sound.freq, w.sound.vol)),
  empty: () => playTone(900, 600, 0.05, "square", 0.08),
  reload: () => { playTone(300, 200, 0.08, "square", 0.1); setTimeout(() => playTone(500, 400, 0.08, "square", 0.1), 700); },
  swap: () => playTone(400, 250, 0.06, "square", 0.08),
  hit: () => playTone(200, 80, 0.12, "triangle", 0.25),
  groan: (volume) => playTone(90 + Math.random() * 40, 50, 0.9, "sawtooth", 0.05 * volume),
  spit: () => playTone(500, 120, 0.25, "sawtooth", 0.1),
  hurt: () => playTone(250, 60, 0.3, "sawtooth", 0.25),
  boom: () => playNoise(0.9, 350, 0.7),
  roar: () => playTone(110, 40, 1.0, "sawtooth", 0.3),
  buy: () => { playTone(800, 1200, 0.08, "square", 0.12); setTimeout(() => playTone(1200, 1600, 0.1, "square", 0.12), 80); },
  pickup: () => { playTone(600, 900, 0.1, "sine", 0.2); setTimeout(() => playTone(900, 1300, 0.12, "sine", 0.2), 90); },
};

// ---------- Модели оружия ----------
function buildGunModel(spec) {
  const g = new THREE.Group();
  const body = lambert(spec.color, spec.glow ? 0x111111 : 0x0a0a0a);
  const dark = lambert(0x1a1a1e, 0x050505);
  const wood = lambert(0x5a3a20, 0x0a0500);
  const box = (sx, sy, sz, mat, x, y, z, rx = 0) => {
    const mesh = new THREE.Mesh(BOX, mat);
    mesh.scale.set(sx, sy, sz);
    mesh.position.set(x, y, z);
    mesh.rotation.x = rx;
    g.add(mesh);
    return mesh;
  };
  const cyl = (r, len, mat, x, y, z) => {
    const mesh = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, 10), mat);
    mesh.rotation.x = Math.PI / 2;
    mesh.position.set(x, y, z);
    g.add(mesh);
    return mesh;
  };

  const { len, h } = spec;
  if (spec.tube) {
    // Труба гранатомёта
    cyl(spec.r, len, body, 0, 0.02, -0.05);
    cyl(spec.r * 1.25, 0.12, dark, 0, 0.02, -0.05 - len / 2);
    box(0.05, 0.14, 0.06, dark, 0, -0.1, 0.05, 0.2);
  } else {
    box(0.08, h, len, body, 0, 0, 0);
  }

  const barrelZ = -len / 2 - spec.barrel / 2;
  const barrels = spec.barrels || 1;
  if (!spec.tube) {
    for (let i = 0; i < barrels; i++) {
      let x = 0;
      let y = 0.02;
      if (barrels === 2) x = (i - 0.5) * spec.r * 2.2;
      if (barrels > 2) {
        const a = (i / barrels) * Math.PI * 2;
        x = Math.cos(a) * 0.035;
        y = 0.02 + Math.sin(a) * 0.035;
      }
      cyl(spec.r, spec.barrel, dark, x, y, barrelZ);
    }
  }

  box(0.06, 0.14, 0.06, spec.wood ? wood : dark, 0, -h / 2 - 0.06, len * 0.2, 0.3); // рукоять
  if (spec.magH) box(0.05, spec.magH, 0.07, dark, 0, -h / 2 - spec.magH / 2, -len * 0.15);
  if (spec.stock) box(0.06, 0.09, spec.stock, spec.wood ? wood : dark, 0, -0.01, len / 2 + spec.stock / 2);
  if (spec.scope) cyl(0.028, 0.2, dark, 0, h / 2 + 0.04, -0.02);
  if (spec.pump) box(0.07, 0.06, 0.14, wood, 0, -0.05, -len / 2 - 0.12);
  if (spec.box) box(0.12, 0.12, 0.14, lambert(0x3a4a2a), 0.06, -h / 2 - 0.06, -0.05);
  if (spec.cylinder) cyl(0.04, 0.07, dark, 0, 0.01, -0.02);
  if (spec.tank) {
    cyl(0.05, 0.3, lambert(0xcc4422, 0x220800), 0, -h / 2 - 0.05, 0);
    box(0.03, 0.03, 0.06, lambert(0x3399ff, 0x113366), 0, 0.03, barrelZ - spec.barrel / 2);
  }
  if (spec.glow) {
    const glow = new THREE.MeshBasicMaterial({ color: spec.glow });
    box(0.085, 0.02, len * 0.8, glow, 0, h / 2 + 0.005, 0);
    box(0.03, 0.03, 0.03, glow, 0, 0.02, barrelZ - spec.barrel / 2);
  }

  g.visible = false;
  return { group: g, muzzleZ: spec.tube ? -0.05 - len / 2 - 0.08 : barrelZ - spec.barrel / 2 - 0.03 };
}

const gun = new THREE.Group();
const gunRestPos = new THREE.Vector3(0.22, -0.2, -0.5);
gun.position.copy(gunRestPos);
gun.scale.setScalar(0.7);
gun.visible = false;
camera.add(gun);
const gunModels = WEAPONS.map((w) => {
  const model = buildGunModel(w.model);
  gun.add(model.group);
  return model;
});

const muzzleFlash = new THREE.Mesh(
  new THREE.SphereGeometry(0.07, 8, 8),
  new THREE.MeshBasicMaterial({ color: 0xffdd66 })
);
muzzleFlash.visible = false;
gun.add(muzzleFlash);
// Источники света держим постоянными: смена их количества пересобирает шейдеры и даёт фризы
const muzzleLight = QUALITY.dynamicLights ? new THREE.PointLight(0xffaa33, 0, 10) : null;
if (muzzleLight) gun.add(muzzleLight);
const blastLight = QUALITY.dynamicLights ? new THREE.PointLight(0xff8833, 0, 18) : null;
if (blastLight) scene.add(blastLight);

// ---------- Частицы: одна точечная система на всё ----------
const MAX_PARTICLES = isTouch ? 500 : 1200;
const pPos = new Float32Array(MAX_PARTICLES * 3);
const pCol = new Float32Array(MAX_PARTICLES * 3);
const pVel = new Float32Array(MAX_PARTICLES * 3);
const pLife = new Float32Array(MAX_PARTICLES);
const pGrav = new Float32Array(MAX_PARTICLES);
let pNext = 0;
const particleGeo = new THREE.BufferGeometry();
particleGeo.setAttribute("position", new THREE.BufferAttribute(pPos, 3));
particleGeo.setAttribute("color", new THREE.BufferAttribute(pCol, 3));
const particles = new THREE.Points(
  particleGeo,
  new THREE.PointsMaterial({ size: 0.14, vertexColors: true, sizeAttenuation: true })
);
particles.frustumCulled = false;
scene.add(particles);

const COLORS = {
  blood: new THREE.Color(0x8a0000),
  spark: new THREE.Color(0xffcc55),
  acid: new THREE.Color(0x88ff22),
  smoke: new THREE.Color(0x555555),
  fire: [new THREE.Color(0xff6611), new THREE.Color(0xffaa22), new THREE.Color(0xffdd55)],
};

function spawnParticles(point, color, count, speed = 4, opts = {}) {
  const { dir = null, life = 0.8, gravity = CONFIG.gravity } = opts;
  for (let n = 0; n < count; n++) {
    const i = pNext;
    pNext = (pNext + 1) % MAX_PARTICLES;
    const c = Array.isArray(color) ? color[(Math.random() * color.length) | 0] : color;
    pPos[i * 3] = point.x;
    pPos[i * 3 + 1] = point.y;
    pPos[i * 3 + 2] = point.z;
    pCol[i * 3] = c.r;
    pCol[i * 3 + 1] = c.g;
    pCol[i * 3 + 2] = c.b;
    let vx = (Math.random() - 0.5) * speed;
    let vy = Math.random() * speed;
    let vz = (Math.random() - 0.5) * speed;
    if (dir) {
      vx = dir.x + (Math.random() - 0.5) * speed;
      vy = dir.y + (Math.random() - 0.5) * speed;
      vz = dir.z + (Math.random() - 0.5) * speed;
    }
    pVel[i * 3] = vx;
    pVel[i * 3 + 1] = vy;
    pVel[i * 3 + 2] = vz;
    pLife[i] = life * (0.6 + Math.random() * 0.5);
    pGrav[i] = gravity;
  }
}

function updateParticles(dt) {
  for (let i = 0; i < MAX_PARTICLES; i++) {
    if (pLife[i] <= 0) continue;
    pLife[i] -= dt;
    if (pLife[i] <= 0) {
      pPos[i * 3 + 1] = -1000;
      continue;
    }
    pVel[i * 3 + 1] -= pGrav[i] * dt;
    pPos[i * 3] += pVel[i * 3] * dt;
    pPos[i * 3 + 1] += pVel[i * 3 + 1] * dt;
    pPos[i * 3 + 2] += pVel[i * 3 + 2] * dt;
    if (pPos[i * 3 + 1] < 0.04) {
      pPos[i * 3 + 1] = 0.04;
      pVel[i * 3] = pVel[i * 3 + 1] = pVel[i * 3 + 2] = 0;
    }
  }
  particleGeo.attributes.position.needsUpdate = true;
  particleGeo.attributes.color.needsUpdate = true;
}

function clearParticles() {
  pLife.fill(0);
  for (let i = 0; i < MAX_PARTICLES; i++) pPos[i * 3 + 1] = -1000;
  particleGeo.attributes.position.needsUpdate = true;
}
clearParticles();

// ---------- Трассеры (снайперка, лазер) ----------
const tracers = [];
const tracerGeo = new THREE.CylinderGeometry(1, 1, 1, 6).rotateX(Math.PI / 2);
for (let i = 0; i < 8; i++) {
  const mesh = new THREE.Mesh(tracerGeo, new THREE.MeshBasicMaterial({ transparent: true, depthWrite: false }));
  mesh.visible = false;
  scene.add(mesh);
  tracers.push({ mesh, life: 0 });
}
let tracerNext = 0;

function showTracer(from, to, color, width) {
  const t = tracers[tracerNext];
  tracerNext = (tracerNext + 1) % tracers.length;
  const len = from.distanceTo(to);
  t.mesh.position.copy(from).lerp(to, 0.5);
  t.mesh.scale.set(width, width, len);
  t.mesh.lookAt(to);
  t.mesh.material.color.setHex(color);
  t.mesh.material.opacity = 0.9;
  t.mesh.visible = true;
  t.life = 0.12;
}

function updateTracers(dt) {
  for (const t of tracers) {
    if (t.life <= 0) continue;
    t.life -= dt;
    t.mesh.material.opacity = Math.max(0, t.life / 0.12) * 0.9;
    if (t.life <= 0) t.mesh.visible = false;
  }
}

// ---------- Снаряды (ракеты, кислота) ----------
const projectiles = [];
const rocketGeo = new THREE.CylinderGeometry(0.06, 0.06, 0.45, 8).rotateX(Math.PI / 2);
const acidGeo = new THREE.SphereGeometry(0.2, 8, 6);
const acidMat = new THREE.MeshBasicMaterial({ color: 0x88ff22 });
const raycaster = new THREE.Raycaster();
const tmpV = new THREE.Vector3();
const tmpV2 = new THREE.Vector3();

function spawnRocket(from, dir, w) {
  const mesh = new THREE.Mesh(rocketGeo, lambert(0x4a5a3a, 0x111111));
  mesh.position.copy(from);
  mesh.lookAt(tmpV.copy(from).add(dir));
  scene.add(mesh);
  projectiles.push({ kind: "rocket", mesh, vel: dir.clone().multiplyScalar(w.speed), life: 4, weapon: w });
}

function spawnAcid(from, target, damage = 12) {
  const mesh = new THREE.Mesh(acidGeo, acidMat);
  mesh.position.copy(from);
  scene.add(mesh);
  const vel = target.clone().sub(from).normalize().multiplyScalar(15);
  projectiles.push({ kind: "acid", mesh, vel, life: 3, damage });
  sfx.spit();
}

function shootTargets() {
  const targets = [...obstacleMeshes, ground];
  for (const z of zombies) if (!z.dying) targets.push(z.root);
  return targets;
}

function updateProjectiles(dt) {
  for (let i = projectiles.length - 1; i >= 0; i--) {
    const p = projectiles[i];
    p.life -= dt;
    const step = p.vel.length() * dt;
    let done = p.life <= 0;

    if (p.kind === "rocket") {
      raycaster.set(p.mesh.position, tmpV.copy(p.vel).normalize());
      raycaster.far = step;
      const hit = raycaster.intersectObjects(shootTargets(), true)[0];
      if (hit) {
        explode(hit.point, p.weapon.radius, p.weapon.damage, false);
        done = true;
      } else {
        p.mesh.position.addScaledVector(p.vel, dt);
        spawnParticles(p.mesh.position, COLORS.smoke, 1, 0.5, { life: 0.6, gravity: -1 });
        if (done) explode(p.mesh.position, p.weapon.radius, p.weapon.damage, false);
      }
    } else {
      p.mesh.position.addScaledVector(p.vel, dt);
      const pp = p.mesh.position;
      tmpV.set(player.pos.x, player.pos.y + 1.2, player.pos.z);
      if (pp.distanceTo(tmpV) < 0.9) {
        hurtPlayer(p.damage);
        done = true;
      } else if (pp.y <= 0.05 || insideObstacle(pp)) {
        done = true;
      }
      if (done) spawnParticles(pp, COLORS.acid, 10, 3);
    }

    if (done) {
      scene.remove(p.mesh);
      projectiles.splice(i, 1);
    }
  }
}

let blastTimer = 0;
function explode(point, radius, damage, hurtsPlayer) {
  point = point.clone();
  sfx.boom();
  spawnParticles(point, COLORS.fire, isTouch ? 40 : 80, 9, { life: 0.7, gravity: 4 });
  spawnParticles(point, COLORS.smoke, isTouch ? 15 : 30, 5, { life: 1.2, gravity: -2 });
  if (blastLight) {
    blastLight.position.set(point.x, point.y + 1, point.z);
    blastLight.intensity = 60;
    blastTimer = 0.25;
  }
  for (const z of zombies) {
    if (z.dying) continue;
    const center = new THREE.Vector3(z.root.position.x, 1, z.root.position.z);
    const d = center.distanceTo(point);
    if (d < radius) damageZombie(z, damage * (1 - (d / radius) * 0.6), center, false, true);
  }
  if (hurtsPlayer) {
    const d = Math.hypot(player.pos.x - point.x, player.pos.z - point.z);
    if (d < radius) hurtPlayer(Math.round(damage * (1 - d / radius)));
  }
  // Встряска камеры
  player.shake = Math.max(player.shake, Math.max(0, 1 - point.distanceTo(player.pos) / 25));
}

// ---------- Зомби ----------
const zombies = [];
const eyeMat = new THREE.MeshBasicMaterial({ color: 0xff2200 });
const bossEyeMat = new THREE.MeshBasicMaterial({ color: 0xffee00 });
const acidEyeMat = new THREE.MeshBasicMaterial({ color: 0xaaff00 });
const pustuleMat = new THREE.MeshBasicMaterial({ color: 0xffbb22 });
const hitMat = new THREE.MeshBasicMaterial({ color: 0xff3030 });
const veinMat = new THREE.MeshBasicMaterial({ color: 0xaa33ff });
const goldMat = lambert(0xc8a030, 0x221800);

function createZombie(type, x, z) {
  const t = ZOMBIE_TYPES[type];
  const skin = lambert(t.skin);
  const cloth = lambert(t.cloth);
  const pants = lambert(t.pants);

  const root = new THREE.Group();
  const body = new THREE.Group();
  root.add(body);
  const part = (sx, sy, sz, mat, px, py, pz, parent = body) => {
    const m = new THREE.Mesh(BOX, mat);
    m.scale.set(sx, sy, sz);
    m.position.set(px, py, pz);
    m.castShadow = QUALITY.shadows;
    parent.add(m);
    return m;
  };

  const fat = t.explode ? 1.5 : 1;
  const torso = part(0.6 * fat, 0.75, 0.32 * fat * 1.3, cloth, 0, 1.15, 0);
  const headH = t.spit ? 0.52 : 0.4;
  const head = part(0.4, headH, 0.4, skin, 0, 1.55 + headH / 2, 0);
  head.userData.isHead = true;
  const eyes = t.patient ? veinMat : t.spit ? acidEyeMat : t.boss ? bossEyeMat : eyeMat;
  const eyeY = 1.59 + headH * 0.55;
  part(0.08, 0.06, 0.02, eyes, -0.1, eyeY, -0.21).userData.isHead = true;
  part(0.08, 0.06, 0.02, eyes, 0.1, eyeY, -0.21).userData.isHead = true;

  if (t.armor) {
    // Каска и бронежилет: шлем не считается головой — нужен точный выстрел в лицо
    part(0.48, 0.16, 0.48, lambert(0x3a4030), 0, 1.55 + headH + 0.04, 0);
    part(0.66, 0.55, 0.42, lambert(0x2a2f25), 0, 1.2, 0);
  }
  if (t.explode) {
    for (const [px, py, pz] of [[0.3, 1.3, -0.3], [-0.25, 1.0, -0.3], [0.1, 0.95, -0.32], [-0.3, 1.35, 0.2], [0.35, 1.0, 0.25]]) {
      part(0.14, 0.14, 0.14, pustuleMat, px, py, pz);
    }
  }
  if (t.spit) part(0.22, 0.1, 0.05, acidEyeMat, 0, 1.62, -0.21).userData.isHead = true;
  if (t.boss && t.spit) {
    // Корона из наростов у Королевы
    for (let k = 0; k < 5; k++) part(0.07, 0.18, 0.07, acidEyeMat, -0.16 + k * 0.08, 1.55 + headH + 0.08, 0);
  }
  if (t.boss && t.armor) {
    // Погоны генерала
    part(0.2, 0.05, 0.3, goldMat, -0.38, 1.53, 0);
    part(0.2, 0.05, 0.3, goldMat, 0.38, 1.53, 0);
  }
  if (t.patient) {
    // Светящиеся вены
    part(0.04, 0.6, 0.02, veinMat, -0.15, 1.15, -0.21);
    part(0.04, 0.5, 0.02, veinMat, 0.12, 1.2, -0.21);
    part(0.3, 0.03, 0.02, veinMat, 0, 1.35, -0.21);
    part(0.03, 0.2, 0.02, veinMat, 0.15, 1.85, -0.21).userData.isHead = true;
  }
  if (t.butcher) {
    part(0.12, 0.3, 0.12, lambert(0xbbbbaa), -0.42, 1.65, 0);
    part(0.12, 0.3, 0.12, lambert(0xbbbbaa), 0.42, 1.65, 0);
    part(0.7, 0.3, 0.36, lambert(0x553322), 0, 0.85, 0); // фартук
  }

  // Конечности с точкой вращения у плеча/бедра
  const limb = (px, py, w, h, mat) => {
    const pivot = new THREE.Group();
    pivot.position.set(px, py, 0);
    body.add(pivot);
    part(w, h, w, mat, 0, -h / 2, 0, pivot);
    return pivot;
  };
  const armL = limb(-0.31 * fat - 0.09, 1.48, 0.18, 0.7, skin);
  const armR = limb(0.31 * fat + 0.09, 1.48, 0.18, 0.7, skin);
  const legL = limb(-0.15, 0.78, 0.22, 0.78, pants);
  const legR = limb(0.15, 0.78, 0.22, 0.78, pants);
  if (t.patient) {
    for (const arm of [armL, armR]) part(0.04, 0.5, 0.2, veinMat, 0, -0.35, 0, arm).userData.isHead = false;
  }

  if (t.crawl) {
    // Ползёт на руках, ноги волочатся сзади
    body.rotation.x = -1.3;
    body.position.set(0, 0.28, 0.9);
  }

  root.scale.setScalar(t.scale);
  root.position.set(x, 0, z);
  scene.add(root);

  const waveMul = 1 + (game.wave - 1) * 0.08;
  const zombie = {
    type, t, root, body, torso, head, skin, armL, armR, legL, legR,
    hp: t.hp * waveMul,
    maxHp: t.hp * waveMul,
    speed: t.speed * (1 + Math.min(game.wave - 1, 10) * 0.04) * (0.9 + Math.random() * 0.2),
    radius: 0.4 * t.scale,
    attackCooldown: 0,
    spitCooldown: 1 + Math.random() * 2,
    chargeTimer: 3 + Math.random() * 3,
    charging: 0,
    summonTimer: 6,
    walkPhase: Math.random() * Math.PI * 2,
    groanTimer: 2 + Math.random() * 6,
    dying: 0,
    flash: 0,
  };
  root.traverse((o) => { o.userData.zombie = zombie; });
  zombies.push(zombie);
  return zombie;
}

function damageZombie(z, amount, hitPoint, headshot = false, quiet = false) {
  if (z.dying) return;
  if (z.t.armor && !headshot) amount *= 1 - z.t.armor;
  z.hp -= amount;
  z.flash = 0.08;
  if (!quiet) spawnParticles(hitPoint, COLORS.blood, isTouch ? 4 : 8);
  if (z.hp <= 0) killZombie(z, true, hitPoint, headshot);
}

function killZombie(z, byPlayer, point, headshot = false) {
  if (z.dying) return;
  z.dying = 0.001;
  z.head.material = z.skin;
  spawnParticles(point, COLORS.blood, isTouch ? 10 : 20, 6);
  if (byPlayer) {
    game.kills++;
    const reward = z.t.score * (headshot ? 2 : 1);
    game.score += reward;
    game.money += reward;
    maybeDropPickup(z.root.position, z.t.boss ? 6 : 1);
  }
  if (z.t.explode) explode(new THREE.Vector3(z.root.position.x, 1, z.root.position.z), 4.5, z.t.damage, true);
  if (z.t.boss) showMessage(`${z.t.name.toUpperCase()} ПОВЕРЖЕН!`, 2500);
  updateHud();
}

const toPlayer = new THREE.Vector3();
function updateZombies(dt) {
  const playerPos = player.pos;
  let boss = null;
  for (let i = zombies.length - 1; i >= 0; i--) {
    const z = zombies[i];
    if (!z) continue; // массив мог укоротиться из-за цепочки взрывов

    if (z.dying) {
      z.dying += dt;
      if (z.t.explode) {
        // Взрывун разлетается на куски
        scene.remove(z.root);
        zombies.splice(i, 1);
        continue;
      }
      // Падение и исчезновение
      z.root.rotation.x = Math.max(-Math.PI / 2, -z.dying * 4);
      if (z.dying > 1.5) z.root.position.y -= dt * 0.6;
      if (z.dying > 2.5) {
        scene.remove(z.root);
        zombies.splice(i, 1);
      }
      continue;
    }
    if (z.t.boss) boss = z;

    toPlayer.set(playerPos.x - z.root.position.x, 0, playerPos.z - z.root.position.z);
    const dist = toPlayer.length();
    toPlayer.divideScalar(dist || 1);

    // Разворот к игроку
    const targetYaw = Math.atan2(-toPlayer.x, -toPlayer.z);
    let diff = targetYaw - z.root.rotation.y;
    diff = Math.atan2(Math.sin(diff), Math.cos(diff));
    z.root.rotation.y += diff * Math.min(1, dt * 6);

    const reach = 0.7 + 0.4 * z.t.scale + CONFIG.playerRadius + (z.t.crawl ? 0.3 : 0);

    // Рывок: босс разгоняется и несётся на игрока
    if (z.t.charge) {
      z.chargeTimer -= dt;
      if (z.charging > 0) z.charging -= dt;
      else if (z.chargeTimer <= 0 && dist > 6 && dist < 30) {
        z.charging = 1.2;
        z.chargeTimer = 6 + Math.random() * 2;
        sfx.roar();
      }
      z.body.rotation.x = z.charging > 0 ? -0.35 : 0;
    }
    const speed = z.speed * (z.charging > 0 ? 3.5 : 1);

    // Плевуны держат дистанцию
    const keepsDistance = z.t.keepDist && dist < z.t.keepDist && dist > reach + 2;
    if (dist > reach && !keepsDistance) {
      z.root.position.addScaledVector(toPlayer, speed * dt);
      z.walkPhase += dt * speed * 3;
    }

    // Плевок кислотой (у боссов — веером)
    if ((z.t.spit || z.t.volley) && dist > reach + 2 && dist < 25 && z.charging <= 0) {
      z.spitCooldown -= dt;
      if (z.spitCooldown <= 0) {
        z.spitCooldown = z.t.spitRate + Math.random();
        z.head.getWorldPosition(tmpV);
        const n = z.t.volley || 1;
        const side = new THREE.Vector3(-toPlayer.z, 0, toPlayer.x);
        for (let k = 0; k < n; k++) {
          const off = (k - (n - 1) / 2) * 1.6;
          tmpV2.set(playerPos.x + side.x * off, playerPos.y + 1.3, playerPos.z + side.z * off);
          spawnAcid(tmpV, tmpV2, z.t.acid);
        }
        z.armL.rotation.x = z.armR.rotation.x = -Math.PI / 1.4;
      }
    }

    // Призыв: Нулевой пациент зовёт бегунов
    if (z.t.summon) {
      z.summonTimer -= dt;
      if (z.summonTimer <= 0) {
        z.summonTimer = 12;
        sfx.roar();
        for (let k = 0; k < 3 && aliveCount() < QUALITY.maxZombies; k++) {
          const a = Math.random() * Math.PI * 2;
          createZombie("runner", z.root.position.x + Math.cos(a) * 3, z.root.position.z + Math.sin(a) * 3);
        }
        updateHud();
      }
    }

    // Отталкивание друг от друга
    for (const other of zombies) {
      if (other === z || other.dying) continue;
      const dx = z.root.position.x - other.root.position.x;
      const dz = z.root.position.z - other.root.position.z;
      const minD = z.radius + other.radius;
      if (Math.abs(dx) > minD || Math.abs(dz) > minD) continue;
      const d = Math.hypot(dx, dz);
      if (d > 0 && d < minD) {
        z.root.position.x += (dx / d) * (minD - d) * 0.5;
        z.root.position.z += (dz / d) * (minD - d) * 0.5;
      }
    }
    resolveCollisions(z.root.position, z.radius);

    // Анимация
    const swing = Math.sin(z.walkPhase) * 0.6;
    if (z.t.crawl) {
      z.armL.rotation.x = -0.3 + swing;
      z.armR.rotation.x = -0.3 - swing;
      z.legL.rotation.x = 0.2 + swing * 0.2;
      z.legR.rotation.x = 0.2 - swing * 0.2;
    } else {
      z.legL.rotation.x = swing;
      z.legR.rotation.x = -swing;
      const k = Math.min(1, dt * 8);
      z.armL.rotation.x += (-Math.PI / 2.3 + swing * 0.2 - z.armL.rotation.x) * k;
      z.armR.rotation.x += (-Math.PI / 2.3 - swing * 0.2 - z.armR.rotation.x) * k;
      z.torso.rotation.z = Math.sin(z.walkPhase * 0.5) * 0.08;
    }
    if (z.t.explode) {
      // Раздувается, когда подбирается к игроку
      const pulse = 1 + Math.max(0, 1 - dist / 8) * Math.abs(Math.sin(performance.now() * 0.012)) * 0.15;
      z.torso.scale.set(0.9 * pulse, 0.75 * pulse, 0.62 * pulse);
    }

    // Атака
    z.attackCooldown -= dt;
    if (dist <= reach + 0.2 && z.attackCooldown <= 0 && player.alive) {
      if (z.t.explode) {
        killZombie(z, false, new THREE.Vector3(z.root.position.x, 1, z.root.position.z));
        continue;
      }
      z.attackCooldown = z.t.boss ? 1.4 : 1.1;
      z.charging = 0;
      z.armL.rotation.x = z.armR.rotation.x = -Math.PI / 1.6;
      hurtPlayer(z.t.damage);
    }

    // Подсветка при попадании
    if (z.flash > 0) {
      z.flash -= dt;
      z.head.material = z.flash > 0 ? hitMat : z.skin;
    }

    z.groanTimer -= dt;
    if (z.groanTimer <= 0) {
      z.groanTimer = 4 + Math.random() * 8;
      if (dist < 30) sfx.groan(1 - dist / 30);
    }
  }

  ui.bossWrap.classList.toggle("hidden", !boss);
  if (boss) {
    ui.bossName.textContent = `БОСС: ${boss.t.name}`;
    ui.bossBar.style.width = `${Math.max(0, boss.hp / boss.maxHp) * 100}%`;
  }
}

// ---------- Подбираемые предметы ----------
const pickups = [];
const ammoMat = lambert(0x556b2f, 0x223311);
const medMat = lambert(0xffffff, 0x333333);
const redMat = new THREE.MeshBasicMaterial({ color: 0xdd0000 });

function maybeDropPickup(pos, rolls = 1) {
  for (let n = 0; n < rolls; n++) {
    let kind = null;
    if (rolls > 1) kind = n % 2 ? "health" : "ammo";
    else {
      const r = Math.random();
      if (r < 0.2) kind = "ammo";
      else if (r < 0.3) kind = "health";
    }
    if (!kind) continue;

    const group = new THREE.Group();
    const box = (sx, sy, sz, mat) => {
      const m = new THREE.Mesh(BOX, mat);
      m.scale.set(sx, sy, sz);
      group.add(m);
    };
    if (kind === "ammo") {
      box(0.5, 0.3, 0.35, ammoMat);
    } else {
      box(0.45, 0.3, 0.45, medMat);
      box(0.3, 0.31, 0.08, redMat);
      box(0.08, 0.31, 0.3, redMat);
    }
    const scatter = rolls > 1 ? 3 : 0;
    group.position.set(pos.x + (Math.random() - 0.5) * scatter, 0.4, pos.z + (Math.random() - 0.5) * scatter);
    scene.add(group);
    pickups.push({ kind, group, age: 0 });
  }
}

function giveAmmo(fraction) {
  WEAPONS.forEach((w, i) => {
    if (w.reserve !== Infinity && weaponState[i].owned) weaponState[i].reserve += Math.ceil(w.reserve * fraction);
  });
}

function updatePickups(dt) {
  for (let i = pickups.length - 1; i >= 0; i--) {
    const p = pickups[i];
    p.age += dt;
    p.group.rotation.y += dt * 2;
    p.group.position.y = 0.4 + Math.sin(p.age * 3) * 0.1;
    const d = Math.hypot(p.group.position.x - player.pos.x, p.group.position.z - player.pos.z);
    let taken = false;
    if (d < 1.3) {
      if (p.kind === "ammo") {
        giveAmmo(0.25);
        taken = true;
      } else if (player.health < CONFIG.maxHealth) {
        player.health = Math.min(CONFIG.maxHealth, player.health + 35);
        taken = true;
      }
    }
    if (taken) sfx.pickup();
    if (taken || p.age > 30) {
      scene.remove(p.group);
      pickups.splice(i, 1);
      updateHud();
    }
  }
}

// ---------- Игрок ----------
const player = {
  pos: new THREE.Vector3(),
  velY: 0,
  onGround: true,
  yaw: 0,
  pitch: 0,
  health: CONFIG.maxHealth,
  armor: 0,
  weapon: 0,
  switching: 0,
  reloading: 0,
  fireCooldown: 0,
  recoil: 0,
  shake: 0,
  bob: 0,
  alive: true,
};
const weaponState = WEAPONS.map((w, i) => ({ ammo: w.mag, reserve: w.reserve, owned: i === 0 }));

const keys = {};
let mouseDown = false;

function hurtPlayer(amount) {
  if (!player.alive || amount <= 0) return;
  // Броня принимает на себя 70% урона, пока не кончится
  const absorbed = Math.min(player.armor, amount * 0.7);
  player.armor -= absorbed;
  player.health -= amount - absorbed;
  sfx.hurt();
  ui.damage.style.opacity = 1;
  setTimeout(() => (ui.damage.style.opacity = 0), 150);
  if (player.health <= 0) {
    player.health = 0;
    gameOver();
  }
  updateHud();
}

function currentWeapon() {
  return WEAPONS[player.weapon];
}

function switchWeapon(index) {
  index = (index + WEAPONS.length) % WEAPONS.length;
  if (index === player.weapon || !player.alive || !weaponState[index].owned) return;
  if (gunModels[player.weapon]) gunModels[player.weapon].group.visible = false;
  player.weapon = index;
  gunModels[index].group.visible = true;
  muzzleFlash.position.set(0, 0.02, gunModels[index].muzzleZ);
  if (muzzleLight) muzzleLight.position.copy(muzzleFlash.position);
  player.switching = 0.3;
  player.reloading = 0;
  sfx.swap();
  updateHud();
  updateWeaponBar();
}

// Следующее купленное оружие в направлении dir
function cycleWeapon(dir) {
  for (let k = 1; k < WEAPONS.length; k++) {
    const i = (player.weapon + dir * k + WEAPONS.length * k) % WEAPONS.length;
    if (weaponState[i].owned) return switchWeapon(i);
  }
}

function startReload() {
  const w = currentWeapon();
  const st = weaponState[player.weapon];
  if (player.reloading > 0 || player.switching > 0 || st.ammo === w.mag || st.reserve === 0) return;
  player.reloading = w.reload;
  sfx.reload();
  updateHud();
}

const screenOffset = new THREE.Vector2();
const camDir = new THREE.Vector3();
const muzzleWorld = new THREE.Vector3();

function shoot() {
  const w = currentWeapon();
  const st = weaponState[player.weapon];
  if (player.reloading > 0 || player.switching > 0) return;
  if (st.ammo <= 0) {
    sfx.empty();
    player.fireCooldown = 0.25;
    startReload();
    return;
  }
  st.ammo--;
  player.fireCooldown = w.rate;
  player.recoil = Math.min(player.recoil + w.recoil * 0.4, 1.2);
  sfx.shot(w);

  camera.getWorldDirection(camDir);
  muzzleFlash.getWorldPosition(muzzleWorld);

  if (w.kind !== "flame") {
    muzzleFlash.visible = true;
    muzzleFlash.rotation.z = Math.random() * Math.PI;
    if (muzzleLight) muzzleLight.intensity = 8;
    setTimeout(() => {
      muzzleFlash.visible = false;
      if (muzzleLight) muzzleLight.intensity = 0;
    }, 50);
  }

  if (w.kind === "rocket") spawnRocket(muzzleWorld, camDir, w);
  else if (w.kind === "flame") shootFlame(w);
  else shootHitscan(w);
  updateHud();
}

// Нажатие на спуск стреляет сразу, даже если отпустить до следующего кадра
function pullTrigger() {
  if (game.state !== "playing" || game.modal) return;
  mouseDown = true;
  if (player.fireCooldown <= 0) shoot();
}

function shootFlame(w) {
  spawnParticles(muzzleWorld, COLORS.fire, isTouch ? 4 : 7, 2.5, {
    dir: tmpV.copy(camDir).multiplyScalar(w.range * 1.4),
    life: 0.6,
    gravity: -3,
  });
  const cosCone = Math.cos(w.cone);
  for (const z of zombies) {
    if (z.dying) continue;
    tmpV.copy(z.root.position).setY(z.t.crawl ? 0.4 : 1.1 * z.t.scale).sub(camera.position);
    const d = tmpV.length();
    if (d > w.range + z.radius) continue;
    if (tmpV.normalize().dot(camDir) < cosCone) continue;
    tmpV2.copy(camera.position).addScaledVector(tmpV, d);
    damageZombie(z, w.damage, tmpV2, false, true);
    if (Math.random() < 0.3) spawnParticles(tmpV2, COLORS.fire, 2, 1.5, { gravity: -3, life: 0.4 });
  }
}

function shootHitscan(w) {
  const targets = shootTargets();
  const pellets = w.pellets || 1;
  let hitZombie = false;
  for (let n = 0; n < pellets; n++) {
    const spread = (w.spread || 0) + (w.pellets ? 0 : player.recoil * 0.01);
    screenOffset.set((Math.random() - 0.5) * spread * 2, (Math.random() - 0.5) * spread * 2);
    raycaster.setFromCamera(screenOffset, camera);
    raycaster.far = 120;
    const hits = raycaster.intersectObjects(targets, true);
    let pierceLeft = w.pierce || 1;
    const damaged = new Set();
    let end = null;
    for (const hit of hits) {
      const z = hit.object.userData.zombie;
      if (z) {
        if (damaged.has(z) || z.dying) continue;
        damaged.add(z);
        const headshot = !!hit.object.userData.isHead;
        damageZombie(z, w.damage * (headshot ? CONFIG.headshotMultiplier : 1), hit.point, headshot);
        hitZombie = true;
        if (--pierceLeft <= 0) {
          end = hit.point;
          break;
        }
      } else {
        spawnParticles(hit.point, w.laser ? COLORS.acid : COLORS.spark, isTouch ? 3 : 5, 3);
        end = hit.point;
        break;
      }
    }
    if (w.tracer) {
      const to = end || tmpV.copy(raycaster.ray.origin).addScaledVector(raycaster.ray.direction, 80);
      showTracer(muzzleWorld, to, w.tracer, w.laser ? 0.03 : 0.012);
    }
  }
  if (hitZombie) {
    sfx.hit();
    ui.hitMarker.classList.add("show");
    setTimeout(() => ui.hitMarker.classList.remove("show"), 80);
  }
}

const moveVec = new THREE.Vector3();
const UP = new THREE.Vector3(0, 1, 0);

function updatePlayer(dt) {
  // Движение: клавиатура + джойстик
  const running = keys.ShiftLeft || keys.ShiftRight || Math.hypot(joystick.x, joystick.y) > 0.95;
  const speed = running ? CONFIG.runSpeed : CONFIG.walkSpeed;
  const forward = (keys.KeyW ? 1 : 0) - (keys.KeyS ? 1 : 0) - joystick.y;
  const strafe = (keys.KeyD ? 1 : 0) - (keys.KeyA ? 1 : 0) + joystick.x;
  moveVec.set(strafe, 0, -forward);
  const moving = moveVec.lengthSq() > 0.01;
  if (moving) {
    if (moveVec.lengthSq() > 1) moveVec.normalize();
    moveVec.applyAxisAngle(UP, player.yaw).multiplyScalar(speed * dt);
    player.pos.add(moveVec);
    if (player.onGround) player.bob += dt * speed * 1.6;
  }
  resolveCollisions(player.pos, CONFIG.playerRadius);

  // Прыжок и гравитация
  if ((keys.Space || touchJump) && player.onGround) {
    player.velY = CONFIG.jumpSpeed;
    player.onGround = false;
  }
  player.velY -= CONFIG.gravity * dt;
  player.pos.y += player.velY * dt;
  if (player.pos.y <= 0) {
    player.pos.y = 0;
    player.velY = 0;
    player.onGround = true;
  }

  // Стрельба и перезарядка
  const w = currentWeapon();
  const st = weaponState[player.weapon];
  player.fireCooldown -= dt;
  player.switching = Math.max(0, player.switching - dt);
  if (mouseDown && player.fireCooldown <= 0) shoot();
  if (player.reloading > 0) {
    player.reloading -= dt;
    if (player.reloading <= 0) {
      const take = Math.min(w.mag - st.ammo, st.reserve);
      st.ammo += take;
      st.reserve -= take;
      updateHud();
    }
  }
  player.recoil = Math.max(0, player.recoil - dt * 4);
  player.shake = Math.max(0, player.shake - dt * 2);

  // Камера
  const bobY = moving && player.onGround ? Math.sin(player.bob) * 0.05 : 0;
  const shake = player.shake * 0.08;
  camera.position.set(
    player.pos.x + (Math.random() - 0.5) * shake,
    player.pos.y + CONFIG.playerHeight + bobY + (Math.random() - 0.5) * shake,
    player.pos.z
  );
  camera.rotation.set(player.pitch + player.recoil * 0.03, player.yaw, 0);

  // Оружие: отдача, покачивание, перезарядка, смена
  gun.position.copy(gunRestPos);
  gun.position.z += player.recoil * 0.06;
  gun.position.x += moving ? Math.cos(player.bob * 0.5) * 0.015 : 0;
  gun.position.y += bobY * 0.4;
  gun.rotation.x = player.recoil * 0.12;
  if (player.reloading > 0) {
    const k = Math.sin((1 - player.reloading / w.reload) * Math.PI);
    gun.position.y -= k * 0.25;
    gun.rotation.x -= k * 0.6;
  }
  if (player.switching > 0) gun.position.y -= (player.switching / 0.3) * 0.3;
  // Стволы минигана крутятся при стрельбе
  if (w.model.barrels > 2 && mouseDown) gunModels[player.weapon].group.rotation.z += dt * 25;
}

// ---------- Волны ----------
const game = {
  state: "menu", // menu | playing | paused | over
  modal: null, // null | "story" | "shop" — окно поверх игры, которое не считается паузой
  wave: 0,
  score: 0,
  money: 0,
  kills: 0,
  toSpawn: 0,
  spawnTimer: 0,
  inBreak: false,
  breakTime: 0,
  storyDone: false,
};

function showMessage(text, duration = 2000) {
  ui.message.textContent = text;
  ui.message.classList.add("show");
  clearTimeout(showMessage.t);
  showMessage.t = setTimeout(() => ui.message.classList.remove("show"), duration);
}

function chapterOf(wave) {
  return wave <= STORY.length * 5 ? Math.ceil(wave / 5) : null;
}

function startWave() {
  game.wave++;
  game.toSpawn = 4 + game.wave * 3;
  game.spawnTimer = 0;
  if (game.wave % 5 === 0) {
    // Босс главы; в бесконечном режиме — случайный
    const chapter = chapterOf(game.wave);
    const bossType = chapter ? STORY[chapter - 1].boss : BOSS_TYPES[Math.floor(Math.random() * BOSS_TYPES.length)];
    spawnZombie(bossType);
    showMessage(`ВОЛНА ${game.wave}: ${ZOMBIE_TYPES[bossType].name.toUpperCase()}!`, 2500);
  } else {
    const fresh = Object.values(ZOMBIE_TYPES).filter((t) => t.minWave === game.wave && game.wave > 1);
    showMessage(fresh.length ? `ВОЛНА ${game.wave}: ${fresh.map((t) => t.name).join(", ")}` : `ВОЛНА ${game.wave}`, 2500);
  }
  updateHud();
}

function pickZombieType() {
  const pool = Object.entries(ZOMBIE_TYPES).filter(([, t]) => t.minWave <= game.wave);
  let r = Math.random() * pool.reduce((s, [, t]) => s + t.weight, 0);
  for (const [type, t] of pool) {
    r -= t.weight;
    if (r <= 0) return type;
  }
  return "walker";
}

function spawnZombie(type = pickZombieType()) {
  // Точка появления в 25–45 м от игрока
  for (let attempt = 0; attempt < 30; attempt++) {
    const angle = Math.random() * Math.PI * 2;
    const r = 25 + Math.random() * 20;
    const x = player.pos.x + Math.cos(angle) * r;
    const z = player.pos.z + Math.sin(angle) * r;
    const lim = CONFIG.mapSize - 3;
    if (Math.abs(x) > lim || Math.abs(z) > lim) continue;
    const pos = new THREE.Vector3(x, 0, z);
    const before = pos.clone();
    resolveCollisions(pos, ZOMBIE_TYPES[type].boss ? 1.2 : 0.6);
    if (pos.distanceToSquared(before) > 0.01) continue;
    createZombie(type, x, z);
    return true;
  }
  return false;
}

function aliveCount() {
  let n = 0;
  for (const z of zombies) if (!z.dying) n++;
  return n;
}

function onWaveCleared() {
  const bonus = game.wave * 50;
  game.score += bonus;
  game.money += bonus;
  giveAmmo(0.2);
  showMessage(`ВОЛНА ${game.wave} ПРОЙДЕНА! +${bonus} $`, 2500);
  // После босса главы — следующая часть истории
  if (game.wave === STORY.length * 5 && !game.storyDone) {
    game.storyDone = true;
    showStory(EPILOGUE, beginBreak);
  } else if (game.wave % 5 === 0 && chapterOf(game.wave) && game.wave < STORY.length * 5) {
    showStory(STORY[game.wave / 5], beginBreak);
  } else {
    beginBreak();
  }
  updateHud();
}

function beginBreak() {
  game.inBreak = true;
  game.breakTime = BREAK_TIME;
  ui.breakPanel.classList.remove("hidden");
  updateBreakTimer();
}

function endBreak() {
  game.inBreak = false;
  ui.breakPanel.classList.add("hidden");
  if (game.modal === "shop") closeModal();
  startWave();
}

function skipBreak() {
  if (game.inBreak) game.breakTime = 0;
}

function updateBreakTimer() {
  const text = `Следующая волна через ${Math.ceil(game.breakTime)} с`;
  ui.breakTimer.textContent = text;
  ui.shopTimer.textContent = text;
}

function updateWaves(dt) {
  if (game.inBreak) {
    game.breakTime -= dt;
    updateBreakTimer();
    if (game.breakTime <= 0) endBreak();
    return;
  }
  if (game.toSpawn > 0) {
    game.spawnTimer -= dt;
    if (game.spawnTimer <= 0 && aliveCount() < Math.min(12 + game.wave * 2, QUALITY.maxZombies)) {
      if (spawnZombie()) game.toSpawn--;
      game.spawnTimer = Math.max(0.35, 1.6 - game.wave * 0.1);
      updateHud();
    }
  } else if (aliveCount() === 0 && game.wave > 0) {
    onWaveCleared();
  }
}

// ---------- HUD ----------
function updateHud() {
  const w = currentWeapon();
  const st = weaponState[player.weapon];
  const chapter = chapterOf(game.wave);
  ui.wave.textContent = chapter ? `Глава ${chapter} · Волна ${game.wave}` : `Волна ${game.wave}`;
  ui.score.textContent = `Очки: ${game.score}`;
  ui.money.textContent = `$ ${game.money}`;
  ui.zombiesLeft.textContent = `Зомби: ${aliveCount() + game.toSpawn}`;
  ui.health.style.width = `${(player.health / CONFIG.maxHealth) * 100}%`;
  ui.armor.style.width = `${player.armor}%`;
  ui.weaponName.textContent = w.name;
  const reserve = st.reserve === Infinity ? "∞" : st.reserve;
  ui.ammo.textContent = player.reloading > 0 ? "ПЕРЕЗАРЯДКА..." : `${st.ammo} / ${reserve}`;
  ui.ammo.classList.toggle("low", st.ammo <= Math.ceil(w.mag * 0.2) && player.reloading <= 0);
  if (game.modal === "shop") renderShop();
}

const KEY_LABELS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "="];
const KEY_CODES = ["Digit1", "Digit2", "Digit3", "Digit4", "Digit5", "Digit6", "Digit7", "Digit8", "Digit9", "Digit0", "Minus", "Equal"];
WEAPONS.forEach((w, i) => {
  const chip = document.createElement("button");
  chip.className = "weapon-chip";
  chip.innerHTML = `<span class="key">${KEY_LABELS[i]}</span>${w.short}`;
  chip.addEventListener("click", () => switchWeapon(i));
  ui.weaponBar.appendChild(chip);
});

function updateWeaponBar() {
  [...ui.weaponBar.children].forEach((chip, i) => {
    chip.classList.toggle("active", i === player.weapon);
    chip.hidden = !weaponState[i].owned;
  });
  const chip = ui.weaponBar.children[player.weapon];
  const bar = ui.weaponBar;
  // Прокручиваем панель к выбранному оружию (без scrollIntoView, чтобы не дёргать страницу)
  if (chip.offsetLeft < bar.scrollLeft) bar.scrollLeft = chip.offsetLeft;
  else if (chip.offsetLeft + chip.offsetWidth > bar.scrollLeft + bar.clientWidth) {
    bar.scrollLeft = chip.offsetLeft + chip.offsetWidth - bar.clientWidth;
  }
}

// ---------- Магазин ----------
const SUPPLIES = [
  { name: "Аптечка", note: "+50 здоровья", price: 120, can: () => player.health < CONFIG.maxHealth,
    buy: () => (player.health = Math.min(CONFIG.maxHealth, player.health + 50)) },
  { name: "Большая аптечка", note: "Полное здоровье", price: 250, can: () => player.health < CONFIG.maxHealth,
    buy: () => (player.health = CONFIG.maxHealth) },
  { name: "Бронежилет", note: "+50 брони", price: 150, can: () => player.armor < 100,
    buy: () => (player.armor = Math.min(100, player.armor + 50)) },
  { name: "Тяжёлая броня", note: "Броня до 100", price: 300, can: () => player.armor < 100,
    buy: () => (player.armor = 100) },
  { name: "Ящик патронов", note: "+50% патронов ко всему купленному оружию", price: 200, can: () => true,
    buy: () => giveAmmo(0.5) },
];

// Товары: расходники, затем оружие (покупка или пополнение патронов)
function shopOffers() {
  const offers = SUPPLIES.map((s) => ({ ...s, kind: "Снаряжение" }));
  WEAPONS.forEach((w, i) => {
    const st = weaponState[i];
    const stats = `Урон ${w.damage}${w.pellets ? "×" + w.pellets : ""} · магазин ${w.mag}`;
    if (!st.owned) {
      offers.push({ name: w.name, note: `${w.note}. ${stats}`, price: w.price, kind: "Оружие", can: () => true,
        buy: () => {
          st.owned = true;
          st.ammo = w.mag;
          st.reserve = w.reserve;
          switchWeapon(i);
          updateWeaponBar();
        } });
    } else if (w.reserve !== Infinity) {
      offers.push({ name: w.name, note: `Есть. Пополнить патроны до ${w.reserve}`, price: Math.max(50, Math.round(w.price * 0.2)),
        kind: "Патроны", can: () => st.reserve < w.reserve, buy: () => (st.reserve = w.reserve) });
    } else {
      offers.push({ name: w.name, note: "Есть. Патроны бесконечные", price: null, kind: "Оружие", can: () => false });
    }
  });
  return offers;
}

let currentOffers = [];
function renderShop() {
  currentOffers = shopOffers();
  ui.shopMoney.textContent = `$ ${game.money}`;
  ui.shopItems.innerHTML = currentOffers
    .map((o, i) => {
      const afford = o.price !== null && game.money >= o.price && o.can();
      const label = o.price === null ? "Есть" : !o.can() ? "Не нужно" : `$ ${o.price}`;
      return `<div class="shop-card${o.kind === "Оружие" && o.price ? " weapon" : ""}">
        <div class="shop-kind">${o.kind}</div>
        <div class="shop-name">${o.name}</div>
        <div class="shop-note">${o.note}</div>
        <button class="shop-buy" data-i="${i}" ${afford ? "" : "disabled"}>${label}</button>
      </div>`;
    })
    .join("");
}

ui.shopItems.addEventListener("click", (e) => {
  const btn = e.target.closest(".shop-buy");
  if (!btn || btn.disabled) return;
  const offer = currentOffers[Number(btn.dataset.i)];
  if (!offer || game.money < offer.price || !offer.can()) return;
  game.money -= offer.price;
  offer.buy();
  sfx.buy();
  updateHud();
  renderShop();
});

function openShop() {
  if (!game.inBreak || game.state !== "playing" || game.modal) return;
  renderShop();
  openModal("shop", ui.shop);
}

// ---------- Окна поверх игры: сюжет и магазин ----------
function openModal(kind, el) {
  game.modal = kind;
  el.classList.remove("hidden");
  releaseTouchInput();
  ui.touch.classList.add("hidden");
  if (document.pointerLockElement) document.exitPointerLock();
}

function closeModal() {
  ui.shop.classList.add("hidden");
  ui.story.classList.add("hidden");
  game.modal = null;
  if (game.state === "playing") lockPointer();
}

let storyDone = null;
function showStory(part, onDone) {
  ui.storyChapter.textContent = part.chapter;
  ui.storyTitle.textContent = part.title;
  ui.storyText.innerHTML = part.text.map((t) => `<p>${t}</p>`).join("");
  ui.storyBtn.textContent = part.button || "ПРОДОЛЖИТЬ";
  ui.story.scrollTop = 0;
  storyDone = onDone;
  openModal("story", ui.story);
}

ui.storyBtn.addEventListener("click", () => {
  closeModal();
  const done = storyDone;
  storyDone = null;
  done?.();
});

$("btn-shop").addEventListener("click", openShop);
$("btn-skip").addEventListener("click", skipBreak);
$("shop-close").addEventListener("click", closeModal);
$("shop-skip").addEventListener("click", () => {
  closeModal();
  skipBreak();
});

// ---------- Управление состоянием ----------
function resetGame() {
  for (const z of zombies) scene.remove(z.root);
  zombies.length = 0;
  for (const p of pickups) scene.remove(p.group);
  pickups.length = 0;
  for (const p of projectiles) scene.remove(p.mesh);
  projectiles.length = 0;
  clearParticles();

  Object.assign(player, {
    velY: 0, onGround: true, yaw: 0, pitch: 0, health: CONFIG.maxHealth, armor: 0,
    switching: 0, reloading: 0, fireCooldown: 0, recoil: 0, shake: 0, bob: 0, alive: true,
  });
  WEAPONS.forEach((w, i) => Object.assign(weaponState[i], { ammo: w.mag, reserve: w.reserve, owned: i === 0 }));
  gunModels.forEach((m) => (m.group.visible = false));
  player.weapon = -1;
  player.pos.set(0, 0, 0);
  Object.assign(game, {
    modal: null, wave: 0, score: 0, money: 0, kills: 0, toSpawn: 0, spawnTimer: 0, inBreak: false, breakTime: 0, storyDone: false,
  });
  ui.breakPanel.classList.add("hidden");
  ui.shop.classList.add("hidden");
  switchWeapon(0); // начинаем с пистолетом, остальное — в магазине
  player.switching = 0;
  updateHud();
}

function lockPointer() {
  initAudio();
  if (isTouch) {
    // На телефоне нет захвата курсора: просто продолжаем игру
    game.state = "playing";
    ui.pause.classList.add("hidden");
    ui.touch.classList.remove("hidden");
    document.documentElement.requestFullscreen?.().catch(() => {});
    return;
  }
  // Захват курсора может быть запрещён (например, во встроенном окне) — игра всё равно продолжится
  try {
    renderer.domElement.requestPointerLock()?.catch?.(() => {});
  } catch {}
}

function pauseGame() {
  if (game.state !== "playing" || game.modal) return;
  game.state = "paused";
  mouseDown = false;
  ui.pause.classList.remove("hidden");
  ui.touch.classList.add("hidden");
}

function gameOver() {
  player.alive = false;
  game.state = "over";
  game.modal = null;
  mouseDown = false;
  document.exitPointerLock?.();
  const chapter = chapterOf(game.wave);
  ui.finalStats.innerHTML =
    `${chapter ? `Глава ${chapter}: «${STORY[chapter - 1].title}»<br>` : "Бесконечный режим<br>"}` +
    `Волна: <b>${game.wave}</b><br>Убито зомби: <b>${game.kills}</b><br>Очки: <b>${game.score}</b>`;
  ui.gameover.classList.remove("hidden");
  ui.hud.classList.add("hidden");
  ui.touch.classList.add("hidden");
  ui.shop.classList.add("hidden");
  ui.story.classList.add("hidden");
  releaseTouchInput();
}

function startGame() {
  initAudio();
  ui.menu.classList.add("hidden");
  ui.gameover.classList.add("hidden");
  ui.hud.classList.remove("hidden");
  resetGame();
  game.state = "playing";
  gun.visible = true;
  showStory(STORY[0], startWave);
}

renderer.domElement.addEventListener("click", () => {
  if (!isTouch && game.state === "playing" && !game.modal && !document.pointerLockElement) lockPointer();
});

$("start-btn").addEventListener("click", startGame);
$("restart-btn").addEventListener("click", startGame);
$("resume-btn").addEventListener("click", lockPointer);

document.addEventListener("pointerlockchange", () => {
  const locked = document.pointerLockElement === renderer.domElement;
  if (locked) {
    if (game.state === "paused") game.state = "playing";
    ui.pause.classList.add("hidden");
  } else {
    pauseGame();
  }
});

document.addEventListener("mousemove", (e) => {
  if (game.state !== "playing" || document.pointerLockElement !== renderer.domElement) return;
  player.yaw -= e.movementX * 0.0022;
  player.pitch -= e.movementY * 0.0022;
  player.pitch = Math.max(-Math.PI / 2 + 0.05, Math.min(Math.PI / 2 - 0.05, player.pitch));
});

document.addEventListener("mousedown", (e) => {
  if (e.button === 0 && document.pointerLockElement === renderer.domElement) pullTrigger();
});
document.addEventListener("mouseup", (e) => {
  if (e.button === 0) mouseDown = false;
});
document.addEventListener("wheel", (e) => {
  if (game.state === "playing" && document.pointerLockElement === renderer.domElement) {
    cycleWeapon(Math.sign(e.deltaY) || 1);
  }
});

document.addEventListener("keydown", (e) => {
  keys[e.code] = true;
  if (e.code === "Space") e.preventDefault();
  if (game.state !== "playing") return;
  if (game.modal === "shop") {
    if (e.code === "KeyB" || e.code === "Escape") closeModal();
    if (e.code === "KeyN") {
      closeModal();
      skipBreak();
    }
    return;
  }
  if (game.modal) return;
  if (e.code === "KeyB") openShop();
  if (e.code === "KeyN") skipBreak();
  if (e.code === "KeyR") startReload();
  if (e.code === "KeyQ") cycleWeapon(-1);
  if (e.code === "KeyE") cycleWeapon(1);
  const slot = KEY_CODES.indexOf(e.code);
  if (slot >= 0) switchWeapon(slot);
});
document.addEventListener("keyup", (e) => {
  keys[e.code] = false;
});
window.addEventListener("blur", () => {
  for (const k in keys) keys[k] = false;
  mouseDown = false;
});

// ---------- Сенсорное управление ----------
const joystick = { x: 0, y: 0, id: null };
let touchJump = false;
let lookTouchId = null;
let lookLast = { x: 0, y: 0 };
const joyEl = $("joystick");
const knobEl = $("joystick-knob");

function setJoystick(t) {
  const rect = joyEl.getBoundingClientRect();
  const max = rect.width / 2;
  let dx = t.clientX - (rect.left + max);
  let dy = t.clientY - (rect.top + max);
  const len = Math.hypot(dx, dy);
  if (len > max) {
    dx = (dx / len) * max;
    dy = (dy / len) * max;
  }
  joystick.x = dx / max;
  joystick.y = dy / max;
  knobEl.style.transform = `translate(${dx}px, ${dy}px)`;
}

function resetJoystick() {
  joystick.x = joystick.y = 0;
  joystick.id = null;
  knobEl.style.transform = "";
}

function releaseTouchInput() {
  resetJoystick();
  lookTouchId = null;
  touchJump = false;
  mouseDown = false;
  document.querySelectorAll(".touch-btn.active").forEach((b) => b.classList.remove("active"));
}

const findTouch = (list, id) => [...list].find((t) => t.identifier === id);

joyEl.addEventListener("touchstart", (e) => {
  e.preventDefault();
  const t = e.changedTouches[0];
  joystick.id = t.identifier;
  setJoystick(t);
}, { passive: false });

// Кнопки: удержание
function holdButton(id, onDown, onUp) {
  const el = $(id);
  el.addEventListener("touchstart", (e) => {
    e.preventDefault();
    e.stopPropagation();
    el.classList.add("active");
    initAudio();
    onDown();
  }, { passive: false });
  const up = (e) => {
    e.preventDefault();
    el.classList.remove("active");
    onUp?.();
  };
  el.addEventListener("touchend", up);
  el.addEventListener("touchcancel", up);
}
holdButton("btn-fire", pullTrigger, () => { mouseDown = false; });
holdButton("btn-jump", () => { touchJump = true; }, () => { touchJump = false; });
holdButton("btn-reload", () => { if (game.state === "playing") startReload(); });
holdButton("btn-pause", pauseGame);

// Обзор: свайп по свободной области экрана
document.addEventListener("touchstart", (e) => {
  if (game.state !== "playing") return;
  for (const t of e.changedTouches) {
    if (t.target.closest?.(".touch-btn, #joystick, #weapon-bar, #break-panel")) continue;
    if (lookTouchId === null) {
      lookTouchId = t.identifier;
      lookLast = { x: t.clientX, y: t.clientY };
    }
  }
}, { passive: true });

document.addEventListener("touchmove", (e) => {
  if (game.state !== "playing" || game.modal) return; // в окнах — обычная прокрутка
  if (e.target.closest?.("#weapon-bar")) return; // даём прокрутить панель оружия
  e.preventDefault();
  const jt = joystick.id !== null && findTouch(e.changedTouches, joystick.id);
  if (jt) setJoystick(jt);
  const lt = lookTouchId !== null && findTouch(e.changedTouches, lookTouchId);
  if (lt) {
    const sens = 0.006;
    player.yaw -= (lt.clientX - lookLast.x) * sens;
    player.pitch -= (lt.clientY - lookLast.y) * sens;
    player.pitch = Math.max(-Math.PI / 2 + 0.05, Math.min(Math.PI / 2 - 0.05, player.pitch));
    lookLast = { x: lt.clientX, y: lt.clientY };
  }
}, { passive: false });

function onTouchEnd(e) {
  if (joystick.id !== null && findTouch(e.changedTouches, joystick.id)) resetJoystick();
  if (lookTouchId !== null && findTouch(e.changedTouches, lookTouchId)) lookTouchId = null;
}
document.addEventListener("touchend", onTouchEnd);
document.addEventListener("touchcancel", onTouchEnd);

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

// ---------- Адаптивное качество ----------
// Если FPS проседает, снижаем разрешение рендера, пока игра не станет плавной
let fpsFrames = 0;
let fpsTime = 0;
let lowFpsStreak = 0;
function trackFps(dt) {
  fpsFrames++;
  fpsTime += dt;
  if (fpsTime < 1) return;
  const fps = Math.round(fpsFrames / fpsTime);
  ui.fps.textContent = `${fps} FPS`;
  fpsFrames = 0;
  fpsTime = 0;
  if (game.state !== "playing") return;
  lowFpsStreak = fps < 50 ? lowFpsStreak + 1 : 0;
  if (lowFpsStreak >= 2 && pixelRatio > 0.5) {
    pixelRatio = Math.max(0.5, pixelRatio - 0.15);
    renderer.setPixelRatio(pixelRatio);
    lowFpsStreak = 0;
  }
}

// ---------- Главный цикл ----------
let lastTime = performance.now();
let menuAngle = 0;

function loop(now) {
  requestAnimationFrame(loop);
  const rawDt = Math.max(0, (now - lastTime) / 1000);
  lastTime = now;
  const dt = Math.min(rawDt, 0.05);
  trackFps(rawDt);

  if (game.state === "playing" && game.modal !== "story") {
    updatePlayer(dt);
    updateZombies(dt);
    updateProjectiles(dt);
    updateWaves(dt);
    updatePickups(dt);
    updateParticles(dt);
    updateTracers(dt);
    if (blastLight && blastTimer > 0) {
      blastTimer -= dt;
      blastLight.intensity = Math.max(0, blastTimer / 0.25) * 60;
    }
  } else if (game.state === "menu") {
    // Облёт камеры на фоне меню
    menuAngle += dt * 0.1;
    camera.position.set(Math.cos(menuAngle) * 30, 12, Math.sin(menuAngle) * 30);
    camera.lookAt(0, 0, 0);
  }

  renderer.render(scene, camera);
}
requestAnimationFrame(loop);
