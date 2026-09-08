/**
 * MediVision AI — Minimal Clinical Theme Engine & UI Utilities
 * Instant light/dark mode toggling, state persistence, and responsive controls.
 */
(function () {
  // 1. Immediately apply saved theme before DOM paint
  const savedTheme = localStorage.getItem('mv_theme') || 'dark';
  if (savedTheme === 'light') {
    document.documentElement.classList.add('light-mode');
  } else {
    document.documentElement.classList.remove('light-mode');
  }

  // 2. Global Theme Toggle Function
  window.toggleTheme = function () {
    const isLight = document.documentElement.classList.toggle('light-mode');
    localStorage.setItem('mv_theme', isLight ? 'light' : 'dark');
    updateToggleButtons(isLight);
  };

  function updateToggleButtons(isLight) {
    document.querySelectorAll('.theme-toggle-btn, .theme-toggle, #themeToggleBtn').forEach(btn => {
      btn.innerHTML = isLight
        ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
    });
  }

  // 3. Setup Floating/Topbar Toggle and Mobile Nav on DOMContentLoaded
  document.addEventListener('DOMContentLoaded', () => {
    const isLight = document.documentElement.classList.contains('light-mode');

    // Attach click to any existing theme toggle buttons
    document.querySelectorAll('.theme-toggle, #themeToggleBtn').forEach(btn => {
      btn.addEventListener('click', window.toggleTheme);
    });

    // Create a floating theme toggle button on auth / landing pages if not already inside a topbar
    if (!document.querySelector('.theme-toggle-btn') && !document.querySelector('.theme-toggle') && !document.querySelector('#themeToggleBtn')) {
      const floatBtn = document.createElement('button');
      floatBtn.className = 'theme-toggle-btn btn btn-secondary btn-icon';
      floatBtn.setAttribute('title', 'Toggle Theme (Light/Dark)');
      floatBtn.setAttribute('aria-label', 'Toggle Theme');
      floatBtn.style.position = 'fixed';
      floatBtn.style.bottom = '20px';
      floatBtn.style.right = '20px';
      floatBtn.style.zIndex = '999';
      floatBtn.style.borderRadius = '50%';
      floatBtn.style.width = '42px';
      floatBtn.style.height = '42px';
      floatBtn.style.boxShadow = 'var(--shadow-md)';
      floatBtn.onclick = window.toggleTheme;
      document.body.appendChild(floatBtn);
    }

    updateToggleButtons(isLight);

    // Setup Mobile Sidebar Toggle
    const mobileToggle = document.querySelector('.mobile-nav-toggle');
    const sidebar = document.querySelector('.app-sidebar');
    if (mobileToggle && sidebar) {
      mobileToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        sidebar.classList.toggle('mobile-open');
      });
      document.addEventListener('click', (e) => {
        if (!sidebar.contains(e.target) && !mobileToggle.contains(e.target)) {
          sidebar.classList.remove('mobile-open');
        }
      });
    }
  });
})();
