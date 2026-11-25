
  const root = document.documentElement;
  const themeBtn = document.getElementById('themeBtn');
  const printBtn = document.getElementById('printBtn');

  function setTheme(theme){
    root.dataset.theme = theme;
    const dark = theme === 'dark';
    themeBtn.textContent = dark ? 'Modo claro' : 'Modo oscuro';
    themeBtn.setAttribute('aria-pressed', String(dark));
    try { localStorage.setItem('guia-theme', theme); } catch(e) {}
  }
  try {
    const saved = localStorage.getItem('guia-theme');
    if (saved === 'dark' || saved === 'light') setTheme(saved);
  } catch(e) {}
  themeBtn.addEventListener('click', () => setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'));
  printBtn.addEventListener('click', () => window.print());
  window.addEventListener('beforeprint', () => document.querySelectorAll('details').forEach(d => d.open = true));

  const links = [...document.querySelectorAll('.toc a[href^="#"]')];
  const sections = [...document.querySelectorAll('main section[id]')];
  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) return;
        const id = entry.target.id;
        links.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + id));
      });
    }, {rootMargin: '-15% 0px -70% 0px', threshold: 0});
    sections.forEach(s => obs.observe(s));
  }

  document.querySelectorAll('.openAll').forEach(b => b.addEventListener('click', () =>
    b.closest('section').querySelectorAll('details.qa').forEach(d => d.open = true)));
  document.querySelectorAll('.closeAll').forEach(b => b.addEventListener('click', () =>
    b.closest('section').querySelectorAll('details.qa').forEach(d => d.open = false)));
