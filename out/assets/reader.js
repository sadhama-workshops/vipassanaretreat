{
  const $ = id => document.getElementById(id);
  const text = $('text'), chapterSel = $('chapter'), suttasEl = $('suttas'), playBtn = $('play'), stopBtn = $('stop'),
        rateSel = $('rate'), voiceSel = $('voice'), status = $('status'), note = $('tts-note'), audio = $('player');
  const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const store = { get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } },
                  set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} } };
  const jget = k => { try { return JSON.parse(store.get(k)); } catch (e) { return null; } };

  let CAT = [], book = null, toc = [], chunk = null;
  let blocks = [], segs = [], si = 0, playing = false, paused = false;

  // ---------- font size ----------
  let fs = parseInt(store.get('rv-fs') || '20', 10);
  const setFs = () => { text.style.setProperty('--fs', fs + 'px'); store.set('rv-fs', fs); };
  $('smaller').onclick = () => { fs = Math.max(15, fs - 2); setFs(); };
  $('bigger').onclick = () => { fs = Math.min(30, fs + 2); setFs(); };
  setFs();

  // ---------- voices ----------
  // Natural voices: Piper neural voices that run on the listener's own device (downloaded once, then cached).
  const NATURAL = [
    ['en_GB-cori-medium', 'Cori', 'British', 'female, calm and clear'],
    ['en_GB-jenny_dioco-medium', 'Jenny', 'British', 'female, warm'],
    ['en_GB-alba-medium', 'Alba', 'Scottish', 'female, soft'],
    ['en_GB-alan-medium', 'Alan', 'British', 'male, steady'],
    ['en_GB-northern_english_male-medium', 'Tom', 'Northern English', 'male, gentle'],
    ['en_US-norman-medium', 'Norman', 'American', 'male, deep and slow'],
    ['en_US-john-medium', 'John', 'American', 'male, mature'],
    ['en_US-ryan-medium', 'Ryan', 'American', 'male, bright'],
    ['en_US-lessac-medium', 'Lessac', 'American', 'female, clear'],
    ['en_US-amy-medium', 'Amy', 'American', 'female, friendly'],
    ['en_US-kristin-medium', 'Kristin', 'American', 'female, soft'],
  ];
  const npath = id => { const [lc, name, q] = id.split('-'); return `en/${lc}/${name}/${q}/${id}.onnx`; };
  const canNatural = typeof WebAssembly === 'object' && 'Worker' in window && 'caches' in window && !!audio;
  const tts = 'speechSynthesis' in window ? window.speechSynthesis : null;
  const isNat = () => voiceSel.value.startsWith('n:');

  const ACC = {'en-GB':'British','en-US':'American','en-AU':'Australian','en-IE':'Irish','en-IN':'Indian','en-ZA':'South African','en-NZ':'New Zealand','en-CA':'Canadian'};
  const quality = v => { const n = v.name; let q = 0;
    if (/natural|neural|premium|enhanced|wavenet|studio|journey/i.test(n)) q += 6; if (/online/i.test(n)) q += 3;
    if (/siri/i.test(n)) q += 4; if (/^Google/i.test(n)) q += 3;
    if (/Daniel|Serena|Kate|Arthur|Martha|Sonia|Ryan|Libby|Maisie|Thomas|Stephanie|Jenny|Aria|Guy|Ava|Andrew|Emma|Brian/i.test(n)) q += 2;
    if (/espeak|robot|Fred|Albert|Bad News|Bells|Boing|Bubbles|Cellos|Jester|Organ|Trinoids|Whisper|Wobble|Zarvox|Junior|Ralph|Superstar|Grandma|Grandpa|Eddy|Flo|Reed|Rocko|Sandy|Shelley/i.test(n)) q -= 10;
    return q; };
  const devVoices = () => (tts ? tts.getVoices() : []).filter(v => /^en/i.test(v.lang) && quality(v) > -5).sort((a, b) => quality(b) - quality(a) || a.name.localeCompare(b.name));
  const devLabel = v => v.name.replace(/^(Microsoft|Google|Apple)\s+/i, '').replace(/\s*\(.*?\)\s*/g, ' ').replace(/ - English.*$/i, '').replace(/Online|Natural/gi, '').trim() + ` (${ACC[v.lang.replace('_', '-')] || v.lang})`;

  const fillVoices = () => {
    const saved = store.get('rv-voice2') || (canNatural ? 'n:en_GB-cori-medium' : '');
    let h = '';
    if (canNatural) h += '<optgroup label="Natural voices · work with the screen off">' +
      NATURAL.map(([id, nm, acc, d]) => `<option value="n:${id}">${nm} · ${acc}, ${d}</option>`).join('') + '</optgroup>';
    const dv = devVoices();
    if (dv.length) h += '<optgroup label="This device’s voices · instant, no download">' + dv.map(v => `<option value="d:${esc(v.name)}">${esc(devLabel(v))}</option>`).join('') + '</optgroup>';
    if (!h) { voiceSel.innerHTML = '<option value="d:">Default voice</option>'; return; }
    voiceSel.innerHTML = h;
    if ([...voiceSel.options].some(o => o.value === saved)) voiceSel.value = saved;
    showNote();
  };
  const showNote = () => {
    if (!note) return;
    note.innerHTML = isNat()
      ? 'Natural voices download once (about 60 MB) and then live in this browser. Listening carries on with the screen off, and the lock screen gives you play, pause, next and previous. Your place is remembered.'
      : 'Device voices start instantly, but on most phones they stop when the screen turns off. Choose a natural voice to listen with the screen off.';
  };
  fillVoices();
  if (tts) { tts.onvoiceschanged = fillVoices; setTimeout(fillVoices, 800); }
  voiceSel.onchange = () => { store.set('rv-voice2', voiceSel.value); showNote(); if (playing) restartHere(); };

  // ---------- natural engine (worker) ----------
  let worker = null, token = 0, waiters = new Map(), gen = new Map(), preparing = false;
  const getWorker = () => {
    if (worker) return worker;
    worker = new Worker('assets/tts-worker.js');
    worker.onmessage = e => {
      const m = e.data, w = waiters.get(m.id);
      if (m.type === 'progress') {
        if (m.preparing) { setStatus('Preparing the voice…'); return; }
        const pct = m.total ? Math.round(m.loaded * 100 / m.total) : 0;
        setStatus(`Downloading the voice, just this once… ${pct}%`); preparing = true; return;
      }
      if (!w) return;
      waiters.delete(m.id);
      if (m.type === 'audio') w.resolve(URL.createObjectURL(new Blob([m.buf], {type: 'audio/wav'})));
      else if (m.type === 'error') w.reject(new Error(m.message));
      else w.resolve(m);
    };
    worker.onerror = () => { waiters.forEach(w => w.reject(new Error('worker'))); waiters.clear(); };
    return worker;
  };
  let reqId = 0;
  const ask = msg => new Promise((resolve, reject) => { const id = ++reqId; waiters.set(id, {resolve, reject}); getWorker().postMessage({...msg, id}); });
  const rate = () => parseFloat(rateSel.value) || 1;
  const synth = i => {
    const key = token + ':' + i;
    if (!gen.has(key)) { const s = segs[i]; gen.set(key, ask({type: 'speak', path: npath(voiceSel.value.slice(2)), text: s.text, rate: rate(), pause: s.last ? 0.6 : 0.25})); }
    return gen.get(key);
  };
  const dropOld = () => { for (const [k, p] of gen) { const [t, i] = k.split(':').map(Number); if (t !== token || i < si - 1) { p.then(u => URL.revokeObjectURL(u)).catch(() => {}); gen.delete(k); } } };

  // a short silent clip keeps the audio session alive while the next paragraph is being prepared
  const silentUrl = (() => { const r = 8000, n = r; const v = new DataView(new ArrayBuffer(44 + n * 2));
    const s = (o, t) => { for (let i = 0; i < t.length; i++) v.setUint8(o + i, t.charCodeAt(i)); };
    s(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); s(8, 'WAVE'); s(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, r, true); v.setUint32(28, r * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); s(36, 'data'); v.setUint32(40, n * 2, true);
    return URL.createObjectURL(new Blob([v.buffer], {type: 'audio/wav'})); })();
  const holdSession = () => { if (!audio) return; audio.dataset.kind = 'hold'; audio.loop = true; if (audio.src !== silentUrl) audio.src = silentUrl; audio.play().catch(() => {}); };

  // ---------- library ----------
  const parseHash = () => {
    const h = decodeURIComponent(location.hash.slice(1));
    const b = CAT.find(c => h === c.slug || h.startsWith(c.slug + '-'));
    if (!b) return [null, ''];
    return [b, h.startsWith(b.slug + '-') ? h.slice(b.slug.length + 1) : ''];
  };

  async function openBook(b, chunkId, blockIdx) {
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
    await openChunk(toc.some(c => c.id === id) ? id : toc[0].id, blockIdx);
  }

  async function openChunk(id, blockIdx) {
    chunk = toc.find(c => c.id === id); chapterSel.value = id;
    text.innerHTML = '<p class="muted">Loading…</p>';
    const data = await (await fetch(`library/${book.slug}/${id}.json`)).json();
    text.innerHTML = data.html; // generated at build time from the translation, text already escaped
    suttasEl.innerHTML = chunk.suttas.map(([sid, t]) => `<li><a href="#${esc(book.slug)}-${esc(id)}" data-sid="${esc(sid)}">${esc(sid.toUpperCase())}${t ? ' · ' + esc(t) : ''}</a></li>`).join('');
    store.set('rv-pos-' + book.slug, id);
    const want = `${book.slug}-${id}`;
    if (location.hash.slice(1) !== want) { try { history.replaceState(null, '', '#' + want); } catch (e) {} }
    blocks = [...text.querySelectorAll('h1, h2, p, li:not(.division):not(.subdivision)')].filter(el => el.textContent.trim() && !el.closest('header ul') && !el.parentElement.closest('p, li'));
    blocks.forEach((el, i) => el.dataset.i = i);
    buildSegs();
    const saved = blockIdx ?? (jget('rv-blk') || {})[`${book.slug}/${id}`];
    si = 0;
    if (saved != null && saved > 0) { si = Math.max(0, segs.findIndex(s => s.b >= saved)); mark(false); blocks[segs[si].b]?.scrollIntoView({block: 'center'}); }
    else window.scrollTo({top: 0});
    setStatus(`${chunk.suttas.length} texts in this chapter`);
  }

  // speakable segments: one or more per paragraph, at most ~300 characters each
  const spoken = el => (el.innerText || el.textContent).replace(/\s+/g, ' ').trim();
  const split = s => s.length < 300 ? [s] : (s.match(/[^.!?;:]+[.!?;:]*["’”]?\s*/g) || [s]).reduce((a, x) => { if (a.length && (a[a.length - 1] + x).length < 300) a[a.length - 1] += x; else a.push(x); return a; }, []);
  function buildSegs() {
    segs = [];
    blocks.forEach((el, b) => { const parts = split(spoken(el)).map(t => t.trim()).filter(t => /[a-z0-9]/i.test(t));
      parts.forEach((t, k) => segs.push({b, text: t, last: k === parts.length - 1})); });
  }

  suttasEl.addEventListener('click', e => {
    const a = e.target.closest('a[data-sid]'); if (!a) return; e.preventDefault();
    const el = document.getElementById(a.dataset.sid); if (!el) return;
    suttasEl.querySelectorAll('a.on').forEach(x => x.classList.remove('on')); a.classList.add('on');
    const first = blocks.findIndex(x => el.contains(x));
    if (playing && first >= 0) jumpToBlock(first); else el.scrollIntoView({behavior: 'smooth', block: 'start'});
  });
  chapterSel.addEventListener('change', async () => { const was = playing; stop(true); await openChunk(chapterSel.value, 0); if (was) start(); });

  // ---------- position memory ----------
  const sectionOf = el => el && el.closest('section[id]');
  const sectionTitle = el => { const s = sectionOf(el); const h = s && s.querySelector('.sutta-title, h1, h2'); return h ? h.textContent.trim() : (chunk ? chunk.label : ''); };
  const savePos = () => {
    if (!book || !chunk || !segs[si]) return;
    const b = segs[si].b, all = jget('rv-blk') || {};
    all[`${book.slug}/${chunk.id}`] = b; store.set('rv-blk', JSON.stringify(all));
    store.set('rv-last', JSON.stringify({slug: book.slug, chunk: chunk.id, b, title: sectionTitle(blocks[b]), book: book.title, label: chunk.label, t: Date.now()}));
  };

  // ---------- playback ----------
  const mark = (scroll = true) => {
    text.querySelectorAll('.reading').forEach(x => x.classList.remove('reading'));
    const el = segs[si] && blocks[segs[si].b];
    if (el) { el.classList.add('reading'); if (scroll && !document.hidden) el.scrollIntoView({block: 'center', behavior: 'smooth'}); }
  };
  const setStatus = t => { status.textContent = t; const ms = $('mini-status'); if (ms) ms.textContent = t; };

  function updateMedia() {
    const el = segs[si] && blocks[segs[si].b];
    const title = sectionTitle(el), mt = $('mini-title');
    if (mt) mt.textContent = title ? `${title} · ${book.title}` : book.title;
    if (!('mediaSession' in navigator)) return;
    try {
      navigator.mediaSession.metadata = new MediaMetadata({ title: title || book.title, artist: `${book.title} · ${chunk.label}`, album: 'Vipassana Retreat UK · Dhamma library',
        artwork: [{src: 'assets/cover-library.jpg', sizes: '512x512', type: 'image/jpeg'}] });
      navigator.mediaSession.playbackState = playing && !paused ? 'playing' : 'paused';
    } catch (e) {}
  }

  async function playNatural(myToken) {
    if (!playing || myToken !== token) return;
    if (si >= segs.length) { await nextChapter(); return; }
    mark(); savePos(); updateMedia();
    let url;
    const p = synth(si);
    const quick = await Promise.race([p.then(() => 1, () => 1), new Promise(r => setTimeout(() => r(0), 60))]);
    if (!quick) holdSession();
    try { url = await p; } catch (e) { fallbackToDevice(e); return; }
    if (!playing || myToken !== token) return;
    preparing = false;
    audio.loop = false; audio.volume = 1; audio.dataset.kind = 'speech'; audio.src = url; audio.playbackRate = 1;
    try { await audio.play(); } catch (e) { paused = true; setUI(); setStatus('Tap ▶ to carry on listening'); return; }
    setStatus('Reading aloud · tap any paragraph to jump there');
    for (let k = 1; k <= 3 && si + k < segs.length; k++) synth(si + k).catch(() => {});
    dropOld();
  }
  if (audio) {
    audio.addEventListener('ended', () => { if (audio.dataset.kind !== 'speech' || !playing || !isNat()) return; si++; playNatural(token); });
    audio.addEventListener('pause', () => { if (playing && isNat() && audio.dataset.kind === 'speech' && !audio.ended && !paused) { paused = true; setUI(); } });
    audio.addEventListener('play', () => { if (playing && isNat() && paused) { paused = false; setUI(); } });
  }

  function fallbackToDevice(err) {
    console.warn('natural voice failed', err);
    const dv = devVoices();
    stop(true);
    if (dv.length) { voiceSel.value = 'd:' + dv[0].name; showNote(); setStatus('The natural voice could not load here, so this device’s voice is reading.'); start(); }
    else setStatus('Sorry, listening is not available in this browser.');
  }

  // device voices (Web Speech)
  function speakDevice(myToken) {
    if (!playing || myToken !== token) return;
    if (si >= segs.length) { nextChapter(); return; }
    mark(); savePos(); updateMedia();
    const u = new SpeechSynthesisUtterance(segs[si].text);
    const v = devVoices().find(x => 'd:' + x.name === voiceSel.value); if (v) { u.voice = v; u.lang = v.lang; } else u.lang = 'en-GB';
    u.rate = rate();
    u.onend = () => { if (myToken !== token || !playing) return; si++; speakDevice(myToken); };
    u.onerror = e => { if (myToken !== token) return; if (e.error !== 'interrupted' && e.error !== 'canceled') { si++; speakDevice(myToken); } };
    tts.speak(u);
    setStatus('Reading aloud · tap any paragraph to jump there');
  }

  async function nextChapter() {
    const n = toc.findIndex(c => c.id === chunk.id) + 1;
    if (n >= toc.length) { stop(); setStatus('You have reached the end of this book.'); return; }
    if (isNat()) holdSession();
    await openChunk(toc[n].id, 0);
    si = 0; token++; run();
  }

  function run() { if (isNat()) playNatural(token); else speakDevice(token); setUI(); }

  function start() {
    if (!segs.length) return;
    playing = true; paused = false; token++;
    if (isNat()) { audio.volume = 1; holdSession(); }   // first play() inside the tap unlocks audio on iPhone
    else if (tts) { tts.cancel(); keepAliveForDevice(); }
    run(); showMini(true);
  }
  function pause() {
    if (!playing || paused) return; paused = true;
    if (isNat()) audio.pause(); else if (tts) tts.pause();
    savePos(); setUI(); setStatus('Paused');
  }
  function resume() {
    if (!playing) { start(); return; } if (!paused) return; paused = false;
    if (isNat()) { if (audio.dataset.kind === 'speech' && audio.src && !audio.ended) audio.play().catch(() => {}); else playNatural(token); }
    else if (tts) { if (tts.paused) tts.resume(); else { tts.cancel(); token++; speakDevice(token); } }
    setUI(); setStatus('Reading aloud · tap any paragraph to jump there');
  }
  function stop(silent) {
    if (playing) savePos();
    playing = false; paused = false; token++;
    if (audio) { audio.pause(); audio.loop = false; audio.dataset.kind = ''; }
    if (tts) tts.cancel();
    text.querySelectorAll('.reading').forEach(x => x.classList.remove('reading'));
    setUI(); if (!silent) { showMini(false); setStatus('Stopped · your place is saved'); }
    try { navigator.mediaSession.playbackState = 'none'; } catch (e) {}
  }
  function restartHere() { token++; if (tts) tts.cancel(); if (audio) audio.pause(); paused = false; run(); }
  function jumpToSeg(i) { si = Math.max(0, Math.min(segs.length - 1, i)); if (playing) restartHere(); else { mark(); savePos(); } }
  function jumpToBlock(b) { const i = segs.findIndex(s => s.b >= b); if (i >= 0) jumpToSeg(i); }

  // next / previous text (sutta); falls back to paragraphs where a chapter has no sections
  function nextText() {
    const cur = sectionOf(blocks[segs[si]?.b]);
    const i = segs.findIndex((s, k) => k > si && sectionOf(blocks[s.b]) !== cur);
    if (cur && i >= 0) jumpToSeg(i);
    else if (!cur && si + 1 < segs.length) jumpToSeg(si + 1);
    else { if (playing) { token++; if (audio) audio.pause(); if (tts) tts.cancel(); nextChapter(); } }
  }
  function prevText() {
    const cur = sectionOf(blocks[segs[si]?.b]);
    if (!cur) { jumpToSeg(si - 1); return; }
    const firstOfCur = segs.findIndex(s => sectionOf(blocks[s.b]) === cur);
    const target = si - firstOfCur > 1 ? firstOfCur : (() => { const prev = sectionOf(blocks[segs[Math.max(0, firstOfCur - 1)].b]); return segs.findIndex(s => sectionOf(blocks[s.b]) === prev); })();
    jumpToSeg(Math.max(0, target));
  }

  // lock-screen and headphone controls
  if ('mediaSession' in navigator) {
    const ms = navigator.mediaSession, set = (a, f) => { try { ms.setActionHandler(a, f); } catch (e) {} };
    set('play', () => resume()); set('pause', () => pause()); set('stop', () => stop());
    set('nexttrack', () => nextText()); set('previoustrack', () => prevText());
  }

  // Device voices have no audio element of their own; a silent loop lets the system show media controls
  function keepAliveForDevice() { if (audio) { audio.dataset.kind = 'hold'; audio.loop = true; audio.src = silentUrl; audio.volume = 0.01; audio.play().catch(() => {}); } }

  // ---------- controls ----------
  const setUI = () => {
    const lbl = playing && !paused ? '❚❚ Pause' : '▶ Listen';
    playBtn.textContent = lbl; const mp = $('mini-play'); if (mp) { mp.textContent = playing && !paused ? '❚❚' : '▶'; mp.setAttribute('aria-label', playing && !paused ? 'Pause' : 'Play'); }
    document.body.classList.toggle('listening', playing);
    if (book && chunk) updateMedia();
  };
  playBtn.onclick = () => { hideResume(); if (playing && !paused) pause(); else if (playing) resume(); else start(); };
  stopBtn.onclick = () => stop();
  rateSel.onchange = () => { store.set('rv-rate', rateSel.value); if (playing) restartHere(); };
  if (store.get('rv-rate')) rateSel.value = store.get('rv-rate');
  text.addEventListener('click', e => { if (!playing) return; const el = e.target.closest('[data-i]'); if (el) jumpToBlock(+el.dataset.i); });

  const sample = $('sample');
  if (sample) sample.onclick = async () => {
    const line = 'Just as the ocean has one taste, the taste of salt, so this teaching has one taste, the taste of freedom.';
    if (playing) stop(true);
    if (isNat()) {
      sample.disabled = true; const old = status.textContent;
      try { audio.loop = false; audio.dataset.kind = 'sample'; audio.src = silentUrl; audio.play().catch(() => {});
        const url = await ask({type: 'speak', path: npath(voiceSel.value.slice(2)), text: line, rate: rate()});
        audio.src = url; await audio.play(); setStatus(old); }
      catch (e) { setStatus('That voice could not load. Please try another.'); }
      sample.disabled = false;
    } else if (tts) { tts.cancel(); const u = new SpeechSynthesisUtterance(line); const v = devVoices().find(x => 'd:' + x.name === voiceSel.value); if (v) { u.voice = v; u.lang = v.lang; } u.rate = rate(); tts.speak(u); }
  };

  // floating mini player
  const mini = $('mini');
  const showMini = on => { if (mini) { mini.hidden = !on; document.body.classList.toggle('has-mini', on); } };
  if (mini) {
    $('mini-play').onclick = () => { hideResume(); if (playing && !paused) pause(); else if (playing) resume(); else start(); };
    $('mini-prev').onclick = () => prevText();
    $('mini-next').onclick = () => nextText();
    $('mini-stop').onclick = () => stop();
  }

  // ---------- welcome back ----------
  const resumeBox = $('resume');
  const hideResume = () => { if (resumeBox) resumeBox.hidden = true; };
  function offerResume(last) {
    if (!resumeBox || !last) return;
    resumeBox.querySelector('[data-where]').textContent = `${last.title ? '“' + last.title + '”, ' : ''}${last.book}, ${last.label}`;
    resumeBox.hidden = false;
    resumeBox.querySelector('button').onclick = () => { hideResume(); start(); };
  }

  document.addEventListener('visibilitychange', () => { if (document.hidden) savePos(); else if (playing) mark(); });
  window.addEventListener('pagehide', savePos);

  fetch('library/catalog.json').then(r => r.json()).then(async c => {
    CAT = c;
    let [b, rest] = parseHash();
    const last = jget('rv-last');
    if (!b && last) { b = CAT.find(x => x.slug === last.slug); rest = last.chunk; }
    if (!b) b = CAT.find(x => x.slug === 'dhammapada');
    await openBook(b, rest);
    if (last && last.slug === book.slug && last.chunk === chunk.id && last.b > 0) offerResume(last);
    window.addEventListener('hashchange', () => { const [b2, r2] = parseHash(); if (b2 && (!book || b2.slug !== book.slug || (r2 && r2 !== chunk?.id))) { stop(true); openBook(b2, r2); } });
    if (/[?&]listen=1/.test(location.search)) setStatus('Tap ▶ Listen to begin');
  }).catch(() => { text.innerHTML = '<p>Sorry, the library could not load. Please refresh.</p>'; });
}
