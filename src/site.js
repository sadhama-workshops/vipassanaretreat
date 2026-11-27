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
    // Gentle invitation: a small corner card, never a blocking window.
    // Shows only after a real read (60s on the page AND half-way down), at most once a month,
    // stays away for 3 months after "No thanks" or ×, never on the booking page, never steals focus.
    const DAY = 864e5, now = Date.now();
    const quiet = +store.get('nl-quiet') || 0, done = store.get('nl-done');
    const close = (days) => { pop.classList.remove('in'); setTimeout(() => pop.hidden = true, 400); store.set('nl-quiet', String(Date.now() + days * DAY)); };
    if (pop && !done && now > quiet && !document.querySelector('.bookbox')) {
      let timeOk = false, scrollOk = false, shown = false;
      const maybe = () => { if (shown || !timeOk || !scrollOk) return; shown = true; pop.hidden = false; requestAnimationFrame(() => pop.classList.add('in')); store.set('nl-quiet', String(Date.now() + 30 * DAY)); };
      setTimeout(() => { timeOk = true; maybe(); }, 60000);
      addEventListener('scroll', () => { if (scrollY + innerHeight > document.body.scrollHeight * 0.5) { scrollOk = true; maybe(); } }, { passive: true });
      pop.querySelector('.nl-x').onclick = () => close(90);
      pop.querySelector('.nl-later').onclick = () => close(90);
      addEventListener('keydown', e => { if (e.key === 'Escape' && !pop.hidden) close(90); });
    }
  }
}
