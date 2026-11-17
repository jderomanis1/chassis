/* Applied before first paint. Only the theme preference is stored. */
(() => {
  const root = document.documentElement, media = matchMedia('(prefers-color-scheme: light)');
  const query = new URLSearchParams(location.search), forced = query.get('theme');
  let saved;
  try { saved = localStorage.getItem('chassis-theme'); } catch {}
  const valid = value => ['dark', 'light'].includes(value);
  root.dataset.theme = valid(forced) ? forced : valid(saved) ? saved : media.matches ? 'light' : 'dark';
  if (query.has('static')) root.classList.add('still');
  media.addEventListener('change', event => {
    try { saved = localStorage.getItem('chassis-theme'); } catch {}
    if (!valid(forced) && !valid(saved)) {
      root.dataset.theme = event.matches ? 'light' : 'dark';
      window.dispatchEvent(new Event('chassis-theme-change'));
    }
  });
})();
