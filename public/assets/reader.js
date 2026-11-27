{
  const $ = id => document.getElementById(id);
  const text = $('text'), chapterSel = $('chapter'), suttasEl = $('suttas'), playBtn = $('play'), stopBtn = $('stop'),
        rateSel = $('rate'), voiceSel = $('voice'), status = $('status');
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const store = { get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } },
                  set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} } };
  let CAT = [], book = null, toc = [], chunk = null;
  const tts = 'speechSynthesis' in window ? window.speechSynthesis : null;
  let blocks = [], idx = 0, playing = false, paused = false, queue = [], qi = 0;

  // font size
  let fs = parseInt(store.get('rv-fs') || '20', 10);
  const setFs = () => { text.style.setProperty('--fs', fs + 'px'); store.set('rv-fs', fs); };
  $('smaller').onclick = () => { fs = Math.max(15, fs - 2); setFs(); };
  $('bigger').onclick = () => { fs = Math.min(30, fs + 2); setFs(); };
  setFs();

  const parseHash = () => {
    const h = decodeURIComponent(location.hash.slice(1));
    const b = CAT.find(c => h === c.slug || h.startsWith(c.slug + '-')) || CAT.find(c => c.slug === 'dhammapada');
    const rest = h.startsWith(b.slug + '-') ? h.slice(b.slug.length + 1) : '';
    return [b, rest];
  };

  async function openBook(b, chunkId) {
    stop();
    if (!book || book.slug !== b.slug) {
      book = b; toc = (await (await fetch(`library/${b.slug}/index.json`)).json()).toc;
      $('bookTitle').textContent = `${b.title}: ${b.en}`;
      $('bookSub').textContent = b.blurb;
      $('crumb').textContent = b.title;
      document.title = `${b.title} (${b.en}): Read & Listen | Vipassana Retreat UK`;
      chapterSel.innerHTML = toc.map(c => `<option value="${esc(c.id)}">${esc(c.label)}</option>`).join('');
      $('dl').innerHTML = `Download ${b.epub ? `<a href="downloads/${b.slug}.epub" download>EPUB</a> · ` : ''}<a href="downloads/${b.slug}.txt" download>Text</a>`;
    }
    const id = toc.some(c => c.id === chunkId) ? chunkId : (store.get('rv-pos-' + b.slug) || toc[0].id);
    await openChunk(toc.some(c => c.id === id) ? id : toc[0].id);
  }

  async function openChunk(id) {
    stop();
    chunk = toc.find(c => c.id === id); chapterSel.value = id;
    text.innerHTML = '<p class="muted">Loading…</p>';
    const data = await (await fetch(`library/${book.slug}/${id}.json`)).json();
    text.innerHTML = data.html; // generated at build time from the translation, text already escaped
    suttasEl.innerHTML = chunk.suttas.map(([sid, t]) => `<li><a href="#${esc(book.slug)}-${esc(id)}" data-sid="${esc(sid)}">${esc(sid.toUpperCase())}${t ? ' · ' + esc(t) : ''}</a></li>`).join('');
    store.set('rv-pos-' + book.slug, id);
    const want = `${book.slug}-${id}`;
    if (location.hash.slice(1) !== want) { try { history.replaceState(null, '', '#' + want); } catch (e) {} }
    blocks = [...text.querySelectorAll('h1, h2, p, li:not(.division):not(.subdivision)')].filter(el => el.textContent.trim() && !el.closest('header ul'));
    blocks.forEach((el, i) => el.dataset.i = i);
    idx = 0; status.textContent = `${chunk.suttas.length} texts in this chapter`;
    window.scrollTo({top: 0});
  }

  suttasEl.addEventListener('click', e => {
    const a = e.target.closest('a[data-sid]'); if (!a) return; e.preventDefault();
    const el = document.getElementById(a.dataset.sid); if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
    suttasEl.querySelectorAll('a.on').forEach(x => x.classList.remove('on')); a.classList.add('on');
  });
  chapterSel.addEventListener('change', () => openChunk(chapterSel.value));

  // ---------- listen ----------
  const ACC = {'en-GB':'British','en-US':'American','en-AU':'Australian','en-IE':'Irish','en-IN':'Indian','en-ZA':'South African','en-NZ':'New Zealand','en-CA':'Canadian','en-SG':'Singaporean'};
  const quality = v => {
    const n = v.name;
    let q = 0;
    if (/natural|neural|premium|enhanced|wavenet|studio|journey/i.test(n)) q += 6;
    if (/online/i.test(n)) q += 3;
    if (/siri/i.test(n)) q += 4;
    if (/^Google/i.test(n)) q += 3;
    if (/Daniel|Serena|Kate|Arthur|Martha|Sonia|Ryan|Libby|Maisie|Thomas|Stephanie|Jenny|Aria|Guy|Ava|Andrew|Emma|Brian/i.test(n)) q += 2;
    if (/espeak|robot|Fred|Albert|Bad News|Bells|Boing|Bubbles|Cellos|Jester|Organ|Trinoids|Whisper|Wobble|Zarvox|Junior|Ralph|Superstar|Grandma|Grandpa|Eddy|Flo|Reed|Rocko|Sandy|Shelley/i.test(n)) q -= 10;
    if (v.localService === false) q += 1;
    return q;
  };
  const voices = () => (tts ? tts.getVoices() : []).filter(v => /^en/i.test(v.lang) && quality(v) > -5)
      .sort((a, b) => quality(b) - quality(a) || a.name.localeCompare(b.name));
  const label = v => {
    const nm = v.name.replace(/^(Microsoft|Google|Apple)\s+/i, '').replace(/\s*\(.*?\)\s*/g, ' ').replace(/ - English.*$/i, '').replace(/Online|Natural/gi, '').trim();
    return nm + (quality(v) >= 6 ? ' ★ natural' : '');
  };
  const fillVoices = () => {
    const vs = voices(), saved = store.get('rv-voice');
    if (!vs.length) { voiceSel.innerHTML = '<option>Default voice</option>'; return; }
    const groups = {};
    vs.forEach(v => { const k = ACC[v.lang.replace('_', '-')] || 'Other English'; (groups[k] = groups[k] || []).push(v); });
    const order = ['British', 'Irish', 'American', 'Australian', 'New Zealand', 'Canadian', 'Indian', 'South African', 'Singaporean', 'Other English'];
    voiceSel.innerHTML = order.filter(k => groups[k]).map(k => `<optgroup label="${k}">` + groups[k].map(v => `<option value="${esc(v.name)}">${esc(label(v))}</option>`).join('') + '</optgroup>').join('');
    const pref = vs.find(v => v.name === saved) || vs.find(v => /en-GB/i.test(v.lang) && quality(v) >= 3) || vs[0];
    if (pref) voiceSel.value = pref.name;
    const best = Math.max(...vs.map(quality));
    const note = $('tts-note');
    if (note) note.innerHTML = best >= 6 ? 'Voices marked ★ sound the most natural.' :
      'For more natural voices: on a Mac or iPhone, add a “Premium” or “Enhanced” English voice in Settings → Accessibility → Spoken Content; in Microsoft Edge, the “Natural” voices appear here automatically; on Android, install Google Speech Services.';
  };
  if (tts) { fillVoices(); tts.onvoiceschanged = fillVoices; setTimeout(fillVoices, 800); }
  else { playBtn.disabled = true; stopBtn.disabled = true; $('tts-note').textContent = 'Listening is not supported in this browser.'; }
  const sample = $('sample');
  if (sample) sample.onclick = () => { if (!tts) return; tts.cancel(); const u = new SpeechSynthesisUtterance('Just as the ocean has one taste, the taste of salt, so this teaching has one taste, the taste of freedom.'); const v = voices().find(x => x.name === voiceSel.value); if (v) { u.voice = v; u.lang = v.lang; } u.rate = parseFloat(rateSel.value) * 0.95; tts.speak(u); };
  voiceSel.onchange = () => store.set('rv-voice', voiceSel.value);

  const spoken = el => (el.innerText || el.textContent).replace(/\s+/g, ' ').trim();
  const split = s => s.length < 220 ? [s] : (s.match(/[^.!?;:]+[.!?;:]*["’”]?\s*/g) || [s]).reduce((a, x) => { if (a.length && (a[a.length - 1] + x).length < 220) a[a.length - 1] += x; else a.push(x); return a; }, []);
  const mark = () => { text.querySelectorAll('.reading').forEach(x => x.classList.remove('reading'));
    const el = blocks[idx]; if (el) { el.classList.add('reading'); el.scrollIntoView({block: 'center', behavior: 'smooth'}); } };

  function speakBlock() {
    if (!playing) return;
    if (idx >= blocks.length) { // continue into the next chapter
      const n = toc.findIndex(c => c.id === chunk.id) + 1;
      if (n < toc.length) { openChunk(toc[n].id).then(() => { playing = true; setUI(); speakBlock(); }); }
      else { stop(); status.textContent = 'Finished.'; }
      return;
    }
    mark(); queue = split(spoken(blocks[idx])); qi = 0; speakPart();
  }
  function speakPart() {
    if (!playing) return;
    if (qi >= queue.length) { idx++; speakBlock(); return; }
    const u = new SpeechSynthesisUtterance(queue[qi]);
    const v = voices().find(x => x.name === voiceSel.value); if (v) { u.voice = v; u.lang = v.lang; } else u.lang = 'en-GB';
    u.rate = parseFloat(rateSel.value);
    u.onend = () => { qi++; speakPart(); };
    u.onerror = e => { if (e.error !== 'interrupted' && e.error !== 'canceled') { qi++; speakPart(); } };
    tts.speak(u);
  }
  const setUI = () => { playBtn.textContent = playing && !paused ? '❚❚ Pause' : '▶ Listen'; document.body.classList.toggle('listening', playing);
    status.textContent = playing ? (paused ? 'Paused' : 'Reading aloud… tap any paragraph to jump there') : status.textContent; };
  function stop() { playing = false; paused = false; if (tts) tts.cancel(); text.querySelectorAll('.reading').forEach(x => x.classList.remove('reading')); setUI(); }
  playBtn.onclick = () => {
    if (!tts) return;
    if (playing && !paused) { tts.pause(); paused = true; }
    else if (playing && paused) { tts.resume(); paused = false; }
    else { playing = true; paused = false; tts.cancel(); speakBlock(); }
    setUI();
  };
  stopBtn.onclick = () => { stop(); idx = 0; status.textContent = 'Stopped'; };
  rateSel.onchange = () => { if (playing) { tts.cancel(); paused = false; setTimeout(speakBlock, 50); setUI(); } };
  text.addEventListener('click', e => {
    if (!playing) return; const el = e.target.closest('[data-i]'); if (!el) return;
    tts.cancel(); idx = +el.dataset.i; paused = false; setTimeout(speakBlock, 50); setUI();
  });
  window.addEventListener('beforeunload', () => tts && tts.cancel());

  fetch('library/catalog.json').then(r => r.json()).then(c => {
    CAT = c; const [b, rest] = parseHash(); openBook(b, rest);
    window.addEventListener('hashchange', () => { const [b2, r2] = parseHash(); if (!book || b2.slug !== book.slug || (r2 && r2 !== chunk?.id)) openBook(b2, r2); });
  }).catch(() => { text.innerHTML = '<p>Sorry, the library could not load. Please refresh.</p>'; });
}
