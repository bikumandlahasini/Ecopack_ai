// ── Flash auto-dismiss ────────────────────────────────────────────────────────
document.querySelectorAll('.alert').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  }, 5000);
});

// ── Active nav link ───────────────────────────────────────────────────────────
(function () {
  const path = window.location.pathname;
  document.querySelectorAll('.navbar-links a').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });
})();

// ── Button loading state ──────────────────────────────────────────────────────
function setLoading(btn, loading) {
  if (loading) {
    btn.dataset.orig = btn.innerHTML;
    btn.innerHTML = '<span class="spinner"></span> Processing…';
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.orig || 'Submit';
    btn.disabled = false;
  }
}

// ── Recommend form submit ─────────────────────────────────────────────────────
const recForm = document.getElementById('recommend-form');
if (recForm) {
  recForm.addEventListener('submit', function (e) {
    const btn = this.querySelector('button[type="submit"]');
    if (btn) setLoading(btn, true);
  });
}

// ── Animate progress bars on load ────────────────────────────────────────────
window.addEventListener('load', () => {
  document.querySelectorAll('.progress-fill').forEach(el => {
    const w = el.dataset.width || '0';
    el.style.width = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { el.style.width = w + '%'; }, 100);
    });
  });
});
