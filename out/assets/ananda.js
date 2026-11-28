{
  const chat = document.getElementById('chat'), form = document.getElementById('ask'), input = document.getElementById('q');
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const STOP = new Set('a an the and or but if of to in on at for with is are was were be been am i im me my you your it its this that do does did can could should would how what why when where who which there their they we our us so as about from by not no just really very get got have has had will into out up down too also than then'.split(' '));
  const SYN = {sleepy:'drowsy',sleep:'drowsy',asleep:'drowsy',tired:'drowsy',doze:'drowsy',nod:'drowsy',hurt:'pain',hurts:'pain',ache:'pain',aching:'pain',knee:'pain',knees:'pain',back:'pain',
    thoughts:'thinking',thought:'thinking',distracted:'wandering',wander:'wandering',focus:'concentrate',concentration:'concentrate',anxious:'anxiety',anxiety:'anxiety',angry:'anger',sad:'sadness',
    depressed:'depression',noisy:'noise',loud:'noise',sound:'noise',sounds:'noise',kindness:'metta',loving:'metta',compassion:'metta',donation:'dana',cost:'dana',price:'dana',pay:'dana',fee:'dana',money:'dana',
    dates:'dates',date:'dates',when:'dates',book:'booking',booking:'booking',location:'where',venue:'where',directions:'where',train:'where',london:'where',pack:'bring',packing:'bring',
    enlightenment:'nibbana',nirvana:'nibbana',goenka:'goenka',breath:'breathing',breathe:'breathing',newbie:'beginner',novice:'beginner',first:'beginner',dima:'dmitry',teacher:'dmitry',
    walk:'walking',walks:'walking',sit:'sitting',sat:'sitting',posture:'posture',chair:'posture',cushion:'posture',lotus:'posture',vegan:'food',meals:'food',eat:'food'};
  const norm = w => { w = w.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, ''); w = SYN[w] || w;
    if (w.length > 4) w = w.replace(/(ings|ing|edly|ed|ies|es|s)$/, ''); return SYN[w] || w; };
  const toks = s => (s.toLowerCase().match(/[\p{L}']+/gu) || []).map(w => w.replace(/'/g, '')).filter(w => w && !STOP.has(w)).map(norm);
  let DATA = [], IDF = {};
  const fields = d => ({q: toks(d.q), k: toks(d.k), a: toks(d.a)});
  const addMsg = (who, html, cls) => { const m = document.createElement('div'); m.className = 'msg ' + cls;
    m.innerHTML = `<div class="who">${who}</div><div class="bubble">${html}</div>`; chat.appendChild(m); m.scrollIntoView({block: 'nearest', behavior: reduce ? 'auto' : 'smooth'}); return m; };
  const score = (qt, d) => { let s = 0; const f = d._f;
    for (const t of new Set(qt)) { const w = IDF[t] || 0; if (!w) continue;
      if (f.q.includes(t)) s += 3 * w; if (f.k.includes(t)) s += 2 * w; if (f.a.includes(t)) s += 0.6 * w; }
    return s / Math.sqrt(1 + new Set(qt).size * 0.15); };
  const answer = q => {
    const qt = toks(q);
    const ranked = DATA.map(d => [score(qt, d), d]).filter(x => x[0] > 0).sort((a, b) => b[0] - a[0]);
    if (!ranked.length || ranked[0][0] < 1.6) {
      const sug = DATA.filter(d => ['how-to-start', 'mind-wandering', 'retreat-dates', 'emotions'].includes(d.id));
      return `<p>Hmm. I don't have a good answer for that one yet. I only speak from Dmitry's teachings, and I'd rather say "I don't know" than guess.</p><p>Try asking in a different way, or about the practice itself: sitting, walking, noting, the hindrances, mettā, the retreat. For anything personal, you can write to info@sadhama.com, or bring it to your teacher interview on retreat.</p>` + also(sug);
    }
    const d = ranked[0][1];
    const paras = d.a.split(/\n\n/).map(p => `<p>${esc(p)}</p>`).join('');
    const refs = d.refs.length ? `<div class="refs">${d.refs.map(([l, h]) => `<a href="${esc(h)}">${esc(l)}</a>`).join('')}</div>` : '';
    const more = ranked.slice(1, 4).filter(x => x[0] > ranked[0][0] * 0.45).map(x => x[1]);
    return paras + refs + also(more);
  };
  const also = list => list.length ? `<div class="also">Related: ${list.map(d => `<button type="button" class="chip" data-q="${esc(d.q)}">${esc(d.q)}</button>`).join('')}</div>` : '';
  const ask = q => {
    q = q.trim(); if (!q) return;
    addMsg('You', `<p>${esc(q)}</p>`, 'me');
    const t = addMsg('Ananda', '<span class="typing" aria-label="Ananda is answering"><span></span><span></span><span></span></span>', 'bot');
    setTimeout(() => { t.querySelector('.bubble').innerHTML = DATA.length ? answer(q) : '<p>Sorry, the teachings could not load. Please refresh the page.</p>'; }, reduce ? 0 : 650);
  };
  form.addEventListener('submit', e => { e.preventDefault(); ask(input.value); input.value = ''; input.focus(); });
  document.addEventListener('click', e => { const c = e.target.closest('.chip[data-q]'); if (c) { ask(c.dataset.q); } });
  fetch('assets/ananda-data.json').then(r => r.json()).then(d => {
    DATA = d; DATA.forEach(x => x._f = fields(x));
    const df = {}; DATA.forEach(x => new Set([...x._f.q, ...x._f.k, ...x._f.a]).forEach(t => df[t] = (df[t] || 0) + 1));
    for (const t in df) IDF[t] = Math.log(1 + DATA.length / df[t]);
    const p = new URLSearchParams(location.search).get('q'); if (p) ask(p);
  }).catch(() => {});
}
