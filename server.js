// ВПН-кликер: сервер без внешних зависимостей (только Node.js >= 18).
// Запуск: node server.js  ->  http://localhost:3000

const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const PORT = Number(process.env.PORT) || 3000;
const ROOT = __dirname;
const PUBLIC_DIR = path.join(ROOT, 'public');
const DATA_DIR = path.join(ROOT, 'data');
const DB_FILE = path.join(DATA_DIR, 'db.json');

// ---- Правила игры ----
const MINUTES_PER_TAP = 1;      // 1 нажатие = 1 минута
const MAX_TAPS_PER_SEC = 15;    // защита от автокликеров
const MAX_BURST = 60;           // максимум тапов, накопленных за паузу
const MIN_WITHDRAW = 60;        // вывести можно минимум 60 минут
const WITHDRAW_PACKAGES = [60, 180, 720, 1440, 10080]; // 1ч, 3ч, 12ч, сутки, неделя

const { findFreeServers } = require('./freeServers');

const SERVER_SLOTS = 10;
const REFRESH_MS = 30 * 60_000; // обновлять бесплатные серверы каждые 30 минут

// Свои серверы из config/servers.json (заглушки *.example.com игнорируются)
const ownServers = JSON.parse(fs.readFileSync(path.join(ROOT, 'config/servers.json'), 'utf8'))
  .filter(s => s.ssKey || (s.host && !s.host.endsWith('example.com')));
const skins = JSON.parse(fs.readFileSync(path.join(ROOT, 'config/skins.json'), 'utf8'));

let servers = ownServers.map((s, i) => ({ ...s, id: i + 1 }));

async function refreshFreeServers() {
  const need = SERVER_SLOTS - ownServers.length;
  if (need <= 0) return;
  try {
    const free = await findFreeServers(need);
    if (!free.length) return console.warn('Рабочих бесплатных серверов не найдено, оставляю старые');
    servers = [...ownServers, ...free].map((s, i) => ({ ...s, id: i + 1 }));
    console.log(`Серверы обновлены: ${servers.map(s => `${s.flag} ${s.name}`).join(', ')}`);
  } catch (e) {
    console.warn('Ошибка обновления бесплатных серверов:', e.message);
  }
}
refreshFreeServers();
setInterval(refreshFreeServers, REFRESH_MS);

// ---- Простейшая база в JSON-файле ----
fs.mkdirSync(DATA_DIR, { recursive: true });
let db = { users: {} };
try { db = JSON.parse(fs.readFileSync(DB_FILE, 'utf8')); } catch { /* новая база */ }

let saveTimer = null;
function save() {
  if (saveTimer) return;
  saveTimer = setTimeout(() => {
    saveTimer = null;
    const tmp = DB_FILE + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(db));
    fs.renameSync(tmp, DB_FILE);
  }, 500);
}

function publicUser(u) {
  return {
    minutes: u.minutes,
    totalTaps: u.totalTaps,
    skin: u.skin,
    ownedSkins: u.ownedSkins,
    grants: u.grants.filter(g => g.expiresAt > Date.now()),
  };
}

// ---- Shadowsocks-ключи ----
function ssLink(s) {
  if (s.ssKey) return s.ssKey; // можно вставить готовый ss:// ключ в конфиг
  const userInfo = Buffer.from(`${s.method}:${s.password}`).toString('base64url');
  return `ss://${userInfo}@${s.host}:${s.port}#${encodeURIComponent(`${s.flag} ${s.name}`)}`;
}

// Ссылка, которая открывает приложение Happ и добавляет в него ключ
function happLink(key) {
  return `happ://add/${key}`;
}

// ---- HTTP-помощники ----
function send(res, code, obj) {
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(JSON.stringify(obj));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let data = '';
    req.on('data', c => { data += c; if (data.length > 1e4) req.destroy(); });
    req.on('end', () => { try { resolve(data ? JSON.parse(data) : {}); } catch (e) { reject(e); } });
    req.on('error', reject);
  });
}

function getUser(req) {
  const token = (req.headers.authorization || '').replace(/^Bearer\s+/i, '');
  return token && db.users[token] ? db.users[token] : null;
}

const MIME = { '.html': 'text/html; charset=utf-8', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.json': 'application/json' };

function serveStatic(req, res) {
  const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  const file = path.normalize(path.join(PUBLIC_DIR, urlPath === '/' ? 'index.html' : urlPath));
  if (!file.startsWith(PUBLIC_DIR)) { res.writeHead(403); return res.end(); }
  fs.readFile(file, (err, buf) => {
    if (err) { res.writeHead(404); return res.end('Not found'); }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream' });
    res.end(buf);
  });
}

// ---- API ----
const routes = {
  'GET /api/config': () => [200, {
    minutesPerTap: MINUTES_PER_TAP,
    minWithdraw: MIN_WITHDRAW,
    packages: WITHDRAW_PACKAGES,
    skins,
    servers: servers.map(({ id, name, flag, free }) => ({ id, name, flag, free: !!free })),
  }],

  'POST /api/register': () => {
    const token = crypto.randomBytes(24).toString('hex');
    db.users[token] = {
      minutes: 0, totalTaps: 0, skin: 'default', ownedSkins: ['default'],
      grants: [], lastTapAt: Date.now(), createdAt: Date.now(),
    };
    save();
    return [200, { token, user: publicUser(db.users[token]) }];
  },

  'GET /api/me': (u) => [200, { user: publicUser(u) }],

  'POST /api/tap': (u, body) => {
    const now = Date.now();
    const requested = Math.max(0, Math.floor(Number(body.count) || 0));
    const allowance = Math.min(MAX_BURST, Math.floor(((now - u.lastTapAt) / 1000) * MAX_TAPS_PER_SEC));
    const accepted = Math.min(requested, allowance);
    if (accepted > 0) {
      u.minutes += accepted * MINUTES_PER_TAP;
      u.totalTaps += accepted;
      u.lastTapAt = now;
      save();
    }
    return [200, { accepted, user: publicUser(u) }];
  },

  'POST /api/skins/buy': (u, body) => {
    const skin = skins.find(s => s.id === body.skinId);
    if (!skin) return [404, { error: 'Скин не найден' }];
    if (u.ownedSkins.includes(skin.id)) return [400, { error: 'Скин уже куплен' }];
    if (u.minutes < skin.price) return [400, { error: `Нужно ещё ${skin.price - u.minutes} мин.` }];
    u.minutes -= skin.price;
    u.ownedSkins.push(skin.id);
    u.skin = skin.id;
    save();
    return [200, { user: publicUser(u) }];
  },

  'POST /api/skins/equip': (u, body) => {
    if (!u.ownedSkins.includes(body.skinId)) return [400, { error: 'Сначала купите скин' }];
    u.skin = body.skinId;
    save();
    return [200, { user: publicUser(u) }];
  },

  'POST /api/withdraw': (u, body) => {
    const server = servers.find(s => s.id === Number(body.serverId));
    const minutes = Number(body.minutes);
    if (!server) return [404, { error: 'Сервер не найден' }];
    if (!WITHDRAW_PACKAGES.includes(minutes)) return [400, { error: 'Неверный пакет минут' }];
    if (minutes < MIN_WITHDRAW) return [400, { error: `Минимум ${MIN_WITHDRAW} мин.` }];
    if (u.minutes < minutes) return [400, { error: `Натапайте ещё ${minutes - u.minutes} мин.` }];

    u.minutes -= minutes;
    const now = Date.now();
    // Если на этом сервере уже есть активный доступ — продлеваем его
    const key = ssLink(server);
    // Продлеваем, только если это тот же самый ключ (бесплатные серверы меняются)
    const active = u.grants.find(g => g.key === key && g.expiresAt > now);
    let grant;
    if (active) {
      active.expiresAt += minutes * 60_000;
      grant = active;
    } else {
      grant = {
        id: crypto.randomUUID(), serverId: server.id, serverName: `${server.flag} ${server.name}`,
        key, happ: happLink(key), createdAt: now, expiresAt: now + minutes * 60_000,
      };
      u.grants.push(grant);
    }
    u.grants = u.grants.filter(g => g.expiresAt > now);
    save();
    return [200, { grant, user: publicUser(u) }];
  },
};

http.createServer(async (req, res) => {
  const pathname = new URL(req.url, 'http://x').pathname;
  const handler = routes[`${req.method} ${pathname}`];
  if (!handler) return pathname.startsWith('/api/') ? send(res, 404, { error: 'Not found' }) : serveStatic(req, res);

  try {
    const open = pathname === '/api/config' || pathname === '/api/register';
    const user = getUser(req);
    if (!open && !user) return send(res, 401, { error: 'Не авторизован' });
    const body = req.method === 'POST' ? await readBody(req) : {};
    const [code, payload] = handler(user, body);
    send(res, code, payload);
  } catch (e) {
    send(res, 400, { error: 'Плохой запрос' });
  }
}).listen(PORT, () => console.log(`ВПН-кликер запущен: http://localhost:${PORT}`));
