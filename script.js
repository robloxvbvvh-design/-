// Плавное появление блоков при прокрутке
const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.15 });

document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));

// Кнопка «Да» в политике конфиденциальности
const consent = document.getElementById('consent');
const yesBtn = document.getElementById('consent-yes');
const toast = document.getElementById('toast');

function markAccepted() {
  consent.classList.add('accepted');
  consent.querySelector('p').textContent = 'Вы приняли политику конфиденциальности ✓';
  yesBtn.disabled = true;
  yesBtn.textContent = 'Принято';
}

try {
  if (localStorage.getItem('privacyAccepted') === 'yes') markAccepted();
} catch (e) {}

yesBtn.addEventListener('click', () => {
  try { localStorage.setItem('privacyAccepted', 'yes'); } catch (e) {}
  markAccepted();
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 3000);
});

// ---------- Покупка курса (демо) ----------

const TARIFFS = [
  { id: 'base', name: 'Базовый', price: 490, desc: 'Все уроки курса' },
  { id: 'pro', name: 'Про', price: 990, desc: 'Уроки + советы профессионала' },
  { id: 'max', name: 'Макс', price: 1990, desc: 'Уроки, советы и бонусный рецепт' },
];

const KEY_PRICE = 299;

const COURSES = {
  'Обыкновенная': {
    lessons: [
      { title: 'Эспрессо', steps: ['Смелите 18 г зёрен мелко, как соль.', 'Утрамбуйте кофе в холдере ровно и плотно.', 'Пролейте 36 мл за 25–30 секунд.'], tip: 'Прогрейте чашку горячей водой — эспрессо дольше останется вкусным.' },
      { title: 'Американо', steps: ['Налейте в чашку 120 мл горячей воды (90 °C).', 'Приготовьте порцию эспрессо.', 'Влейте эспрессо в воду, чтобы сохранить пенку.'], tip: 'Сначала вода, потом кофе — так пенка не разрушится.' },
      { title: 'Капучино', steps: ['Приготовьте эспрессо в чашку 180 мл.', 'Взбейте 120 мл холодного молока до 60–65 °C.', 'Влейте молоко по центру, оставив шапку пены 1 см.'], tip: 'Постучите питчером по столу — уйдут крупные пузыри.' },
    ],
    bonus: { title: 'Бонус: Раф', steps: ['Смешайте эспрессо, 100 мл сливок 10% и ванильный сахар.', 'Взбейте всё вместе паром до 65 °C.', 'Перелейте в стакан.'] },
  },
  'Бармен': {
    lessons: [
      { title: 'Идеальное молоко', steps: ['Налейте холодное молоко в питчер до носика.', 'Опустите паровик на 1 см и «впустите воздух» 3 секунды.', 'Погрузите глубже и закрутите воронку до 65 °C.'], tip: 'Молоко должно блестеть, как краска, — без видимых пузырей.' },
      { title: 'Латте', steps: ['Приготовьте эспрессо в высокий стакан.', 'Взбейте 200 мл молока с тонкой пеной.', 'Вливайте тонкой струёй с высоты 10 см.'], tip: 'Чем выше питчер — тем глубже молоко уходит под кофе.' },
      { title: 'Латте-арт «Сердце»', steps: ['Наклоните чашку на 45°.', 'Влейте молоко с высоты, затем опустите питчер к поверхности.', 'Когда появится белое пятно, проведите струёй через центр.'], tip: 'Последнее движение — быстро вверх и вперёд, тогда сердце будет острым.' },
    ],
    bonus: { title: 'Бонус: Латте-арт «Тюльпан»', steps: ['Сделайте маленькое пятно и остановитесь.', 'Повторите ещё 2 раза, подталкивая предыдущие.', 'Прорежьте все слои одной линией.'] },
  },
  'Дегустатор': {
    lessons: [
      { title: 'Каппинг', steps: ['Насыпьте 12 г кофе среднего помола в чашку.', 'Залейте 200 мл воды 93 °C и подождите 4 минуты.', 'Разбейте корочку ложкой и вдохните аромат.'], tip: 'Пробуйте кофе с ложки с громким прихлёбом — так вкус раскрывается сильнее.' },
      { title: 'Колесо вкусов', steps: ['Определите группу: фрукты, орехи, шоколад, цветы.', 'Уточните ноту: например, «фрукты → ягоды → черника».', 'Оцените кислотность, сладость и послевкусие.'], tip: 'Записывайте ощущения сразу — первое впечатление самое точное.' },
      { title: 'Сорта и обжарка', steps: ['Арабика — мягкая и ароматная, робуста — крепкая и горькая.', 'Светлая обжарка — кислотность, тёмная — горечь и шоколад.', 'Сравните Эфиопию и Бразилию рядом.'], tip: 'Для эспрессо чаще берут среднюю обжарку, для фильтра — светлую.' },
    ],
    bonus: { title: 'Бонус: Кофе с сыром', steps: ['Возьмите светлую обжарку из Кении.', 'Подайте с кусочком твёрдого сыра.', 'Почувствуйте, как меняется кислотность.'] },
  },
};

const modal = document.getElementById('modal');
const content = document.getElementById('modal-content');
const state = { course: null, tariff: null, key: null };

function openModal() {
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
  document.body.style.overflow = '';
}

function render(html) {
  content.innerHTML = html;
  modal.querySelector('.modal__box').scrollTop = 0;
}

const rub = (n) => n.toLocaleString('ru-RU') + ' ₽';

document.getElementById('modal-close').addEventListener('click', closeModal);
modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

document.querySelectorAll('.card').forEach((card) => {
  card.querySelector('button').addEventListener('click', () => {
    state.course = card.querySelector('h3').textContent.trim();
    showTariffs();
    openModal();
  });
});

// Шаг 1: выбор тарифа
function showTariffs() {
  render(`
    <h2>Курс «${state.course}»</h2>
    <p class="modal__sub">Выберите тариф.</p>
    <div class="tariffs">
      ${TARIFFS.map((t) => `
        <button class="tariff ${t.id === 'pro' ? 'tariff--hot' : ''}" data-id="${t.id}">
          <div><strong>${t.name}</strong><span>${t.desc}</span></div>
          <b>${rub(t.price)}</b>
        </button>`).join('')}
    </div>
  `);
  content.querySelectorAll('.tariff').forEach((btn) => {
    btn.addEventListener('click', () => {
      state.tariff = TARIFFS.find((t) => t.id === btn.dataset.id);
      showPayment(`Курс «${state.course}», тариф «${state.tariff.name}»`, state.tariff.price, () => showLesson(0));
    });
  });
}

// Шаг 2: демо-оплата картой (данные никуда не отправляются и не сохраняются)
function showPayment(title, price, onPaid) {
  render(`
    <h2>Оплата</h2>
    <p class="modal__sub">${title} — <b>${rub(price)}</b></p>
    <div class="demo-note">Демо-оплата: деньги не списываются, данные карты никуда не отправляются. Используйте тестовую карту ниже.</div>
    <form class="form" id="pay-form" autocomplete="off" novalidate>
      <label>Номер карты
        <input id="card-number" inputmode="numeric" maxlength="19" value="4242 4242 4242 4242">
      </label>
      <div class="form__row">
        <label>Срок действия
          <input id="card-exp" inputmode="numeric" maxlength="5" placeholder="ММ/ГГ" value="12/30">
        </label>
        <label>CVC
          <input id="card-cvc" inputmode="numeric" maxlength="3" value="123">
        </label>
      </div>
      <p class="form__error" id="pay-error"></p>
      <button class="btn" type="submit">Оплатить ${rub(price)}</button>
    </form>
  `);

  const num = document.getElementById('card-number');
  const exp = document.getElementById('card-exp');
  const cvc = document.getElementById('card-cvc');

  num.addEventListener('input', () => {
    num.value = num.value.replace(/\D/g, '').slice(0, 16).replace(/(\d{4})(?=\d)/g, '$1 ');
  });
  exp.addEventListener('input', () => {
    const d = exp.value.replace(/\D/g, '').slice(0, 4);
    exp.value = d.length > 2 ? d.slice(0, 2) + '/' + d.slice(2) : d;
  });
  cvc.addEventListener('input', () => { cvc.value = cvc.value.replace(/\D/g, '').slice(0, 3); });

  document.getElementById('pay-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const error = document.getElementById('pay-error');
    const month = Number(exp.value.slice(0, 2));
    if (num.value.replace(/\s/g, '').length !== 16) return (error.textContent = 'Введите 16 цифр номера карты.');
    if (!/^\d{2}\/\d{2}$/.test(exp.value) || month < 1 || month > 12) return (error.textContent = 'Введите срок в формате ММ/ГГ.');
    if (cvc.value.length !== 3) return (error.textContent = 'Введите 3 цифры CVC.');

    render(`<div class="center"><div class="spinner"></div><p class="modal__sub">Обработка платежа…</p></div>`);
    setTimeout(() => {
      render(`
        <div class="center">
          <div class="big-icon">✅</div>
          <h2>Оплачено!</h2>
          <p class="modal__sub">${title}</p>
          <button class="btn" id="paid-next">Продолжить</button>
        </div>
      `);
      document.getElementById('paid-next').addEventListener('click', onPaid);
    }, 1500);
  });
}

// Шаг 3: уроки курса
function getLessons() {
  const course = COURSES[state.course];
  return state.tariff.id === 'max' ? [...course.lessons, course.bonus] : course.lessons;
}

function showLesson(i) {
  const lessons = getLessons();
  const lesson = lessons[i];
  const isLast = i === lessons.length - 1;
  const showTip = state.tariff.id !== 'base' && lesson.tip;

  render(`
    <div class="progress"><div style="width:${((i + 1) / lessons.length) * 100}%"></div></div>
    <div class="lesson">
      <p class="lesson__num">Урок ${i + 1} из ${lessons.length} · ${state.course}</p>
      <h2>${lesson.title}</h2>
      <ol>${lesson.steps.map((s) => `<li>${s}</li>`).join('')}</ol>
      ${showTip ? `<div class="tip">💡 <b>Совет профи:</b> ${lesson.tip}</div>` : ''}
      <div class="lesson__nav">
        <button class="btn btn--outline" id="prev" ${i === 0 ? 'style="visibility:hidden"' : ''}>Назад</button>
        <button class="btn" id="next">${isLast ? 'Завершить' : 'Далее'}</button>
      </div>
    </div>
  `);
  document.getElementById('prev').addEventListener('click', () => showLesson(i - 1));
  document.getElementById('next').addEventListener('click', () => (isLast ? showKeyEntry() : showLesson(i + 1)));
}

// Шаг 4: спасибо + ключ доступа
function makeKey() {
  const part = () => Math.random().toString(36).slice(2, 6).toUpperCase().padEnd(4, '0');
  return `COFFEE-${part()}-${part()}`;
}

function showKeyEntry() {
  render(`
    <div class="center">
      <div class="big-icon">☕</div>
      <h2>Спасибо за прохождение курса!</h2>
      <p class="modal__sub">Чтобы получить сертификат, введите ключ доступа.</p>
    </div>
    <form class="form" id="key-form" autocomplete="off">
      <input id="key-input" placeholder="COFFEE-XXXX-XXXX" value="${state.key || ''}">
      <p class="form__error" id="key-error"></p>
      <button class="btn" type="submit">Активировать</button>
    </form>
    <div class="center">
      <button class="link-btn" id="buy-key">Нет ключа? Купить за ${rub(KEY_PRICE)}</button>
    </div>
  `);

  document.getElementById('buy-key').addEventListener('click', () => {
    showPayment('Ключ доступа', KEY_PRICE, () => {
      state.key = makeKey();
      render(`
        <div class="center">
          <div class="big-icon">🔑</div>
          <h2>Ваш ключ доступа</h2>
          <div class="key">${state.key}</div>
          <p class="modal__sub">Сохраните его и введите на следующем шаге.</p>
          <button class="btn" id="to-key">Ввести ключ</button>
        </div>
      `);
      document.getElementById('to-key').addEventListener('click', showKeyEntry);
    });
  });

  document.getElementById('key-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const value = document.getElementById('key-input').value.trim().toUpperCase();
    if (!state.key || value !== state.key) {
      document.getElementById('key-error').textContent = 'Неверный ключ. Купите ключ доступа, если у вас его нет.';
      return;
    }
    render(`
      <div class="center">
        <div class="big-icon">🎓</div>
        <h2>Доступ открыт!</h2>
        <p class="modal__sub">Поздравляем! Вы прошли курс «${state.course}» (тариф «${state.tariff.name}»). Сертификат ваш.</p>
        <button class="btn" id="done">Готово</button>
      </div>
    `);
    document.getElementById('done').addEventListener('click', closeModal);
  });
}
