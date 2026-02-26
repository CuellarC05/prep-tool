/* ═══════════════════════════════════════════════════════════
   Hibbs Institute — Prep Tool — Global JS
   ═══════════════════════════════════════════════════════════ */

// ── Dark mode ────────────────────────────────────────────
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('prep-theme', next);
    // Update icon
    const icon = document.querySelector('.theme-toggle i');
    if (icon) {
        icon.className = next === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
}

// Apply saved theme
(function() {
    const saved = localStorage.getItem('prep-theme');
    if (saved) {
        document.documentElement.setAttribute('data-theme', saved);
        const icon = document.querySelector('.theme-toggle i');
        if (icon) {
            icon.className = saved === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
        }
    }
})();
