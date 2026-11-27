{
  const btn = document.querySelector('.menu-btn'), nav = document.getElementById('nav');
  if (btn && nav) btn.addEventListener('click', () => {
    const open = nav.classList.toggle('open');
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  });
  // label stacked table cells on phones
  for (const c of document.querySelectorAll('.stack td:not([data-l])')) {
    let i = 0, p = c; while ((p = p.previousElementSibling)) i += p.colSpan;
    c.dataset.l = c.closest('table').rows[0].cells[i]?.textContent || '';
  }
}
