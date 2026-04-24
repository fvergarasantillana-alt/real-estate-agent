// ── Language Toggle ────────────────────────────────────────────────────
const LANG_KEY = 'preferred_lang';

function setLang(lang) {
  localStorage.setItem(LANG_KEY, lang);
  document.querySelectorAll('[data-en]').forEach(el => {
    el.textContent = lang === 'en' ? el.dataset.en : el.dataset.es;
  });
  document.querySelectorAll('[data-placeholder-en]').forEach(el => {
    el.placeholder = lang === 'en' ? el.dataset.placeholderEn : el.dataset.placeholderEs;
  });
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
  });
  document.documentElement.setAttribute('lang', lang);
}

document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => setLang(btn.dataset.lang));
});

// Apply saved or browser preference on load
const savedLang = localStorage.getItem(LANG_KEY)
  || (navigator.language.startsWith('es') ? 'es' : 'en');
setLang(savedLang);

// ── Contact Form ───────────────────────────────────────────────────────
const form = document.getElementById('contact-form');
if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('.form-submit');
    btn.disabled = true;

    const payload = {
      name:    form.name.value.trim(),
      email:   form.email.value.trim(),
      phone:   form.phone.value.trim(),
      message: form.message.value.trim(),
      source:  'contact_form',
    };

    try {
      const res = await fetch('/api/contact', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      });
      if (res.ok) {
        form.reset();
        const success = document.getElementById('form-success');
        if (success) { success.style.display = 'block'; }
      }
    } catch (_) {
      // silently fail — form stays filled so user can try again
    } finally {
      btn.disabled = false;
    }
  });
}

// ── Smooth anchor nav highlight ────────────────────────────────────────
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav-links a[href^="#"]');

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      navLinks.forEach(link => {
        link.style.color = link.getAttribute('href') === `#${entry.target.id}`
          ? 'var(--brand)'
          : '';
      });
    }
  });
}, { threshold: 0.4 });

sections.forEach(s => observer.observe(s));
