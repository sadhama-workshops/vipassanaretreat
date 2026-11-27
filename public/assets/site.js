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
{
  // newsletter (Brevo). Hidden until a Brevo form link is configured.
  const action = window.NL_ACTION, pop = document.getElementById('nl-pop');
  const store = { get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } }, set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} } };
  if (action) {
    document.querySelectorAll('[data-nl]').forEach(el => { if (el !== pop) el.hidden = false; });
    document.querySelectorAll('.nl-form').forEach(f => f.addEventListener('submit', async e => {
      e.preventDefault();
      const msg = f.querySelector('.nl-msg'), em = f.querySelector('[name=EMAIL]');
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(em.value.trim())) { msg.textContent = 'Please enter a valid email address.'; em.focus(); return; }
      const fd = new FormData(f); fd.append('email_address_check', ''); fd.append('locale', 'en'); fd.append('html_type', 'simple');
      msg.textContent = 'Subscribing…';
      try { await fetch(action, { method: 'POST', mode: 'no-cors', body: fd }); msg.textContent = 'Thank you. Please check your inbox to confirm your subscription.'; f.querySelector('button').disabled = true; store.set('nl-done', '1'); }
      catch (err) { msg.textContent = 'Sorry, that didn’t go through. Please try again, or email info@sadhama.com.'; }
    }));
    const close = () => { pop.hidden = true; store.set('nl-seen', String(Date.now())); };
    const seen = +store.get('nl-seen') || 0, done = store.get('nl-done');
    if (pop && !done && Date.now() - seen > 1000 * 60 * 60 * 24 * 14) {
      let shown = false; const show = () => { if (shown) return; shown = true; pop.hidden = false; pop.querySelector('input[type=email]').focus({ preventScroll: true }); };
      setTimeout(show, 35000);
      addEventListener('scroll', () => { if (scrollY > document.body.scrollHeight * 0.55) show(); }, { passive: true });
      pop.querySelector('.nl-x').onclick = close; pop.addEventListener('click', e => { if (e.target === pop) close(); });
      addEventListener('keydown', e => { if (e.key === 'Escape' && !pop.hidden) close(); });
    }
  }
}
