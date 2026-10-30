(() => {
  const nav = document.querySelector('header > .wrap > nav[aria-label="Main navigation"]');
  if (!nav || !nav.parentElement || nav.parentElement.querySelector('.bry-menu-toggle')) return;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'bry-menu-toggle';
  button.setAttribute('aria-label', 'Open navigation menu');
  button.setAttribute('aria-expanded', 'false');
  nav.id = nav.id || 'bry-primary-navigation';
  button.setAttribute('aria-controls', nav.id);
  const menuIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16"/></svg>';
  const closeIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5L5 19"/></svg>';
  const setOpen = (open) => {
    nav.classList.toggle('bry-menu-open', open);
    button.setAttribute('aria-expanded', String(open));
    button.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
    button.innerHTML = open ? closeIcon : menuIcon;
  };
  setOpen(false);
  nav.before(button);
  button.addEventListener('click', () => setOpen(!nav.classList.contains('bry-menu-open')));
  nav.addEventListener('click', (event) => { if (event.target.closest('a')) setOpen(false); });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && nav.classList.contains('bry-menu-open')) {
      setOpen(false); button.focus();
    }
  });
  document.addEventListener('click', (event) => {
    if (!nav.parentElement.contains(event.target)) setOpen(false);
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth > 760) setOpen(false);
  });
})();
