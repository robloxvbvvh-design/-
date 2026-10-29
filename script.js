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
