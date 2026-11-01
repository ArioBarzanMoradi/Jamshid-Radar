(() => {
  'use strict';
  const root = document.documentElement;
  let theme = 'dark';
  try { if (localStorage.getItem('jamshid-site-theme') === 'light') theme = 'light'; } catch (_) {}
  const applyTheme = value => {
    theme = value === 'light' ? 'light' : 'dark';
    root.dataset.theme = theme;
    root.style.colorScheme = theme;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = theme === 'dark' ? '#202124' : '#F5F1E8';
    document.querySelectorAll('[data-theme-toggle]').forEach(button => {
      button.setAttribute('aria-label', theme === 'dark' ? 'تغییر تم به روشن' : 'تغییر تم به تیره');
      button.querySelector('.theme-symbol').textContent = theme === 'dark' ? '☀' : '☾';
    });
  };
  applyTheme(theme);
  document.querySelectorAll('[data-theme-toggle]').forEach(button => button.addEventListener('click', () => {
    applyTheme(theme === 'dark' ? 'light' : 'dark');
    try { localStorage.setItem('jamshid-site-theme', theme); } catch (_) {}
  }));

  // Resolve the repository when deployed as a GitHub Pages project site:
  // https://OWNER.github.io/REPO/ -> https://github.com/OWNER/REPO
  const metaRepo = document.querySelector('meta[name="jamshid-repository"]')?.content || '';
  let repo = /^[-\w]+\/[-.\w]+$/.test(metaRepo) && !metaRepo.startsWith('USERNAME/') ? metaRepo : '';
  if (/^[\w-]+\.github\.io$/i.test(location.hostname)) {
    const owner = location.hostname.split('.')[0];
    const name = location.pathname.split('/').filter(Boolean)[0];
    if (name && /^[A-Za-z0-9_.-]+$/.test(name)) repo = `${owner}/${name}`;
  }
  if (repo) {
    document.querySelectorAll('[data-repo-link]').forEach(link => {
      link.href = `https://github.com/${repo}`;
    });
    const installer = document.querySelector('#terminal-code');
    if (installer) installer.innerHTML = installer.innerHTML.replace('ArioBarzanMoradi/Jamshid-Radar', repo);
  }

  const previewImages = {
    dark: 'assets/dashboard-dark.webp',
    light: 'assets/dashboard-light.webp'
  };
  const previewAlts = {
    dark: 'پیش‌نمایش تم تیره با داده‌های آزمایشی',
    light: 'پیش‌نمایش تم روشن با داده‌های آزمایشی'
  };
  const previewMain = document.querySelector('#preview-main');
  document.querySelectorAll('[data-preview-mode]').forEach(button => button.addEventListener('click', () => {
    const next = button.dataset.previewMode;
    if (!(next in previewImages)) return;
    previewMain.src = previewImages[next];
    previewMain.alt = previewAlts[next];
    document.querySelectorAll('[data-preview-mode]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.previewMode === next)));
  }));

  document.querySelectorAll('[data-copy]').forEach(button => button.addEventListener('click', async () => {
    const element = document.querySelector(button.dataset.copy);
    if (!element) return;
    const original = button.textContent;
    try {
      // textContent includes the shell comments; that's intentional for a readable copy.
      await navigator.clipboard.writeText(element.textContent);
      button.textContent = 'Copied ✓';
    } catch (_) {
      button.textContent = 'Select & copy';
    }
    window.setTimeout(() => { button.textContent = original; }, 2100);
  }));
})();
