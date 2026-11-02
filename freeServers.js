// Автоподбор бесплатных Shadowsocks-серверов из публичных списков на GitHub.
// Скачивает списки, проверяет, какие серверы отвечают, и выбирает нужное количество
// (по возможности — из разных стран).

const net = require('node:net');

const SOURCES = [
  'https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Splitted-By-Protocol/ss.txt',
  'https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/splitted/ss.txt',
];

const regionNames = (() => {
  try { return new Intl.DisplayNames(['ru'], { type: 'region' }); } catch { return null; }
})();

function b64decode(s) {
  return Buffer.from(s.replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8');
}

// Разбирает ss://-ключ (форматы SIP002 и старый base64). Возвращает null, если ключ кривой.
function parseSS(line) {
  line = line.trim();
  if (!line.startsWith('ss://')) return null;
  let body = line.slice(5);
  let tag = '';
  const hash = body.indexOf('#');
  if (hash >= 0) {
    try { tag = decodeURIComponent(body.slice(hash + 1)); } catch { tag = body.slice(hash + 1); }
    body = body.slice(0, hash);
  }
  if (body.includes('?')) return null; // ключи с плагинами пропускаем

  let userInfo, hostPort;
  const at = body.lastIndexOf('@');
  if (at >= 0) {
    userInfo = body.slice(0, at);
    hostPort = body.slice(at + 1);
    try { userInfo = decodeURIComponent(userInfo); } catch {}
    if (!userInfo.includes(':')) userInfo = b64decode(userInfo);
  } else {
    const decoded = b64decode(body);
    const at2 = decoded.lastIndexOf('@');
    if (at2 < 0) return null;
    userInfo = decoded.slice(0, at2);
    hostPort = decoded.slice(at2 + 1);
  }

  const colon = userInfo.indexOf(':');
  if (colon < 0) return null;
  const method = userInfo.slice(0, colon);
  const password = userInfo.slice(colon + 1);

  const m = hostPort.replace(/\/$/, '').match(/^\[?([^\]]+?)\]?:(\d+)$/);
  if (!m || !method || !password) return null;
  const port = Number(m[2]);
  if (!port || port > 65535) return null;

  return { method, password, host: m[1], port, tag };
}

// Флаг-эмодзи из названия ключа -> код страны
function countryFromTag(tag) {
  const chars = [...tag];
  for (let i = 0; i < chars.length - 1; i++) {
    const a = chars[i].codePointAt(0), b = chars[i + 1].codePointAt(0);
    if (a >= 0x1f1e6 && a <= 0x1f1ff && b >= 0x1f1e6 && b <= 0x1f1ff) {
      const code = String.fromCharCode(a - 0x1f1e6 + 65, b - 0x1f1e6 + 65);
      return { code, flag: chars[i] + chars[i + 1] };
    }
  }
  return null;
}

// Проверка: открывается ли TCP-соединение с сервером
function isAlive(host, port, timeout = 3000) {
  return new Promise(resolve => {
    const sock = net.connect({ host, port });
    const done = ok => { sock.destroy(); resolve(ok); };
    sock.setTimeout(timeout, () => done(false));
    sock.once('connect', () => done(true));
    sock.once('error', () => done(false));
  });
}

function shuffle(a) {
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

async function fetchCandidates() {
  const seen = new Set();
  const out = [];
  for (const url of SOURCES) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(20000) });
      if (!res.ok) continue;
      for (const line of (await res.text()).split('\n')) {
        const s = parseSS(line);
        if (!s) continue;
        const k = `${s.host}:${s.port}`;
        if (seen.has(k)) continue;
        seen.add(k);
        out.push(s);
      }
    } catch (e) {
      console.warn(`Не удалось скачать ${url}: ${e.message}`);
    }
  }
  return out;
}

// Находит `count` рабочих серверов. Сначала по одному на страну, потом добивает любыми.
async function findFreeServers(count = 10) {
  const candidates = shuffle(await fetchCandidates());
  console.log(`Бесплатных ключей найдено: ${candidates.length}, проверяю доступность...`);

  const alive = [];
  const BATCH = 60;
  for (let i = 0; i < candidates.length && alive.length < count * 3; i += BATCH) {
    const batch = candidates.slice(i, i + BATCH);
    const results = await Promise.all(batch.map(s => isAlive(s.host, s.port)));
    batch.forEach((s, j) => { if (results[j]) alive.push(s); });
  }

  const picked = [];
  const usedCountries = new Set();
  for (const s of alive) {
    const c = countryFromTag(s.tag);
    if (c && !usedCountries.has(c.code) && picked.length < count) { usedCountries.add(c.code); picked.push(s); }
  }
  for (const s of alive) if (picked.length < count && !picked.includes(s)) picked.push(s);

  return picked.map(s => {
    const c = countryFromTag(s.tag);
    const name = c ? (regionNames?.of(c.code) || c.code) : 'Неизвестно';
    return { name, flag: c ? c.flag : '🌐', host: s.host, port: s.port, method: s.method, password: s.password, free: true };
  });
}

module.exports = { findFreeServers, parseSS };
