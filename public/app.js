// ВПН-кликер — клиент
const $ = (id) => document.getElementById(id);
let cfg = null;
let user = null;
let token = null;
let pendingTaps = 0;
let localBonus = 0; // тапы, показанные, но ещё не подтверждённые сервером

try { token = localStorage.getItem('vpnclicker_token'); } catch {}

async function api(method, url, body) {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw Object.assign(new Error(data.error || 'Ошибка'), { status: res.status });
  return data;
}

function toast(text) {
  const t = $('toast');
  t.textContent = text;
  t.classList.add('show');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => t.classList.remove('show'), 2200);
}

function fmtDuration(min) {
  const d = Math.floor(min / 1440), h = Math.floor((min % 1440) / 60), m = min % 60;
  return (d ? `${d} д ` : '') + `${h} ч ${m} мин`;
}

// ---------- Отрисовка ----------
function balance() { return user.minutes + localBonus; }

function renderBalance() {
  const b = balance();
  $('minutes').textContent = b.toLocaleString('ru-RU');
  $('hours').textContent = `≈ ${fmtDuration(b)} ВПН`;
  const pct = Math.min(100, (b / cfg.minWithdraw) * 100);
  $('progressBar').style.width = pct + '%';
  $('progressText').textContent = b >= cfg.minWithdraw
    ? '✅ Можно выводить! Откройте вкладку «Серверы»'
    : `До вывода осталось ${cfg.minWithdraw - b} мин`;
  renderServers();
}

function applySkin() {
  const skin = cfg.skins.find(s => s.id === user.skin) || cfg.skins[0];
  document.documentElement.style.setProperty('--c1', skin.colors[0]);
  document.documentElement.style.setProperty('--c2', skin.colors[1]);
  $('tapEmoji').textContent = skin.emoji;
}

function renderSkins() {
  $('skinsList').innerHTML = '';
  for (const s of cfg.skins) {
    const owned = user.ownedSkins.includes(s.id);
    const equipped = user.skin === s.id;
    const el = document.createElement('div');
    el.className = 'skin' + (equipped ? ' equipped' : '');
    el.innerHTML = `
      <div class="preview" style="background:radial-gradient(circle at 30% 30%, ${s.colors[0]}, ${s.colors[1]})">${s.emoji}</div>
      <div class="name">${s.name}</div>
      <div class="price">${s.price ? s.price.toLocaleString('ru-RU') + ' мин' : 'Бесплатно'}</div>`;
    const btn = document.createElement('button');
    btn.className = 'btn' + (equipped ? ' ok' : owned ? ' ghost' : '');
    btn.textContent = equipped ? 'Надет' : owned ? 'Надеть' : 'Купить';
    btn.disabled = equipped || (!owned && balance() < s.price);
    btn.onclick = async () => {
      await flushTaps();
      try {
        const r = await api('POST', owned ? '/api/skins/equip' : '/api/skins/buy', { skinId: s.id });
        user = r.user;
        applySkin(); renderAll();
        toast(owned ? `Скин «${s.name}» надет` : `Куплен скин «${s.name}» 🎉`);
      } catch (e) { toast(e.message); }
    };
    el.appendChild(btn);
    $('skinsList').appendChild(el);
  }
}

function renderPackages() {
  const sel = $('pkgSelect');
  sel.innerHTML = cfg.packages.map(p => `<option value="${p}">${fmtDuration(p)} (${p} мин)</option>`).join('');
  sel.onchange = renderServers;
}

function renderServers() {
  const need = Number($('pkgSelect').value);
  const enough = balance() >= need;
  $('withdrawBtn').disabled = !enough;
  $('withdrawBtn').textContent = enough ? `Активировать ${fmtDuration(need)}` : `Натапайте ещё ${need - balance()} мин`;
  const list = $('serversList');
  list.innerHTML = '';
  if (!cfg.servers.length) {
    list.innerHTML = '<div class="empty">🔎 Ищу рабочие бесплатные серверы…<br>Обычно это занимает до минуты.</div>';
    return;
  }
  for (const s of cfg.servers) {
    const row = document.createElement('div');
    row.className = 'row';
    row.innerHTML = `<span class="flag">${s.flag}</span>
      <div class="info"><b>${s.name}</b><small>Shadowsocks · ${s.free ? 'бесплатный' : 'свой'} · #${s.id}</small></div>`;
    list.appendChild(row);
  }
}

function subUrl() {
  return `${cfg.publicUrl || location.origin}/sub/${user.subId}`;
}

function renderHapp() {
  const url = subUrl();
  $('subUrl').textContent = url;
  $('happBtn').href = `happ://add/${url}`;
  $('stTaps').textContent = user.totalTaps.toLocaleString('ru-RU');
  $('stWithdrawn').textContent = user.totalWithdrawn.toLocaleString('ru-RU');
  $('stBalance').textContent = balance().toLocaleString('ru-RU');
  $('lastSync').textContent = user.lastSubFetch
    ? 'Happ обновлял: ' + new Date(user.lastSubFetch).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
    : 'Happ ещё не подключён';
  tickTimers();
}

function tickTimers() {
  const el = $('vpnTimer');
  const left = Math.max(0, user.vpnUntil - Date.now());
  const s = Math.floor(left / 1000);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
  el.textContent = left ? `осталось ${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}` : 'выключен';
  el.classList.toggle('off', !left);
}

function renderAll() { renderBalance(); renderSkins(); renderHapp(); }

// ---------- Действия ----------
function onTap(e) {
  pendingTaps++;
  localBonus += cfg.minutesPerTap;
  renderBalance();
  if (navigator.vibrate) navigator.vibrate(8);
  const f = document.createElement('div');
  f.className = 'floater';
  f.textContent = `+${cfg.minutesPerTap} мин`;
  const x = e.clientX || window.innerWidth / 2, y = e.clientY || window.innerHeight / 2;
  f.style.left = (x - 30) + 'px';
  f.style.top = (y - 20) + 'px';
  document.body.appendChild(f);
  setTimeout(() => f.remove(), 800);
}

let flushing = null;
async function flushTaps() {
  if (flushing) return flushing;
  if (!pendingTaps) return;
  const count = pendingTaps;
  pendingTaps = 0;
  flushing = api('POST', '/api/tap', { count })
    .then(r => {
      user = r.user;
      localBonus = Math.max(0, localBonus - count * cfg.minutesPerTap);
      if (r.accepted < count) toast('Слишком быстро! Часть тапов не засчитана');
      renderAll();
    })
    .catch(() => { pendingTaps += count; })
    .finally(() => { flushing = null; });
  return flushing;
}

async function withdraw() {
  const minutes = Number($('pkgSelect').value);
  await flushTaps();
  if (!confirm(`Потратить ${minutes} мин и включить ВПН на ${fmtDuration(minutes)}?`)) return;
  try {
    const r = await api('POST', '/api/withdraw', { minutes });
    user = r.user;
    renderAll();
    switchTab('keys');
    toast(user.lastSubFetch ? 'Готово! Обновите подписку в Happ' : 'Готово! Нажмите «Добавить в Happ»');
  } catch (e) { toast(e.message); }
}

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.id === 'tab-' + name));
  document.querySelectorAll('.bottom button').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
}

// ---------- Старт ----------
async function init() {
  cfg = await api('GET', '/api/config');
  $('minW').textContent = cfg.minWithdraw;
  try {
    if (!token) throw new Error();
    user = (await api('GET', '/api/me')).user;
  } catch {
    const r = await api('POST', '/api/register');
    token = r.token;
    user = r.user;
    try { localStorage.setItem('vpnclicker_token', token); } catch {}
  }
  renderPackages();
  applySkin();
  renderAll();

  $('tapBtn').addEventListener('pointerdown', onTap);
  document.querySelectorAll('.bottom button').forEach(b => b.onclick = () => switchTab(b.dataset.tab));
  setInterval(flushTaps, 1000);
  // Список бесплатных серверов меняется — обновляем его
  setInterval(async () => {
    try { cfg = await api('GET', '/api/config'); renderServers(); } catch {}
  }, cfg.servers.length ? 5 * 60_000 : 15_000);
  $('withdrawBtn').onclick = withdraw;
  $('copySub').onclick = async () => {
    try { await navigator.clipboard.writeText(subUrl()); toast('Ссылка скопирована'); }
    catch { toast('Не удалось скопировать — выделите ссылку вручную'); }
  };
  setInterval(tickTimers, 1000);
  // Подтягиваем, когда Happ последний раз забирал подписку
  setInterval(async () => {
    try { user = (await api('GET', '/api/me')).user; renderHapp(); } catch {}
  }, 30_000);
  window.addEventListener('pagehide', flushTaps);
}

init().catch(() => toast('Сервер недоступен'));
