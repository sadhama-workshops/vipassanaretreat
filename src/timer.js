{
  const $ = id => document.getElementById(id);
  const store = { get: k => { try { return localStorage.getItem(k); } catch (e) { return null; } },
                  set: (k, v) => { try { localStorage.setItem(k, v); } catch (e) {} } };
  const jget = (k, d) => { try { return JSON.parse(store.get(k)) ?? d; } catch (e) { return d; } };

  // All segments are MP3, 24 kHz mono, 48 kbps CBR, so they join into one seamless track.
  // Durations are the exact encoded lengths (frames x 576 / 24000).
  const SEG = { gong1: 22.056, gong3: 36.048, soft: 16.056, sil10: 10.056, sil1: 1.056 };
  const FILE = { gong1: 'gong1.mp3', gong3: 'gong3.mp3', soft: 'gong-soft.mp3', sil10: 'sil10.mp3', sil1: 'sil1.mp3' };
  const GUIDED = window.MT_GUIDED || [];   // [{id, title, file, dur, blurb}] filled in when recordings are added

  const audio = $('mt-audio'), form = $('mt-form'), live = $('mt-live'), clock = $('mt-clock'), phase = $('mt-phase'), ring = $('mt-ring');
  const cfg = Object.assign({ mode: 'silent', min: 20, interval: 0, start: 1, prep: 10, guided: GUIDED[0]?.id || '', after: 0 }, jget('mt-cfg', {}));
  let track = null, plan = null, bufs = {}, running = false, finished = false, url = null;

  // ---------- settings UI ----------
  const pick = (name, val) => document.querySelectorAll(`[data-${name}]`).forEach(b => b.setAttribute('aria-pressed', String(b.dataset[name] === String(val))));
  const bind = (name, key, num = true) => document.querySelectorAll(`[data-${name}]`).forEach(b => b.addEventListener('click', () => {
    cfg[key] = num ? +b.dataset[name] : b.dataset[name]; pick(name, cfg[key]); save(); refresh(); }));
  const save = () => store.set('mt-cfg', JSON.stringify(cfg));
  bind('min', 'min'); bind('interval', 'interval'); bind('start', 'start'); bind('prep', 'prep'); bind('mode', 'mode', false); bind('after', 'after');
  const custom = $('mt-custom');
  custom.addEventListener('input', () => { const v = Math.round(+custom.value); if (v >= 1 && v <= 240) { cfg.min = v; pick('min', -1); save(); refresh(); } });
  const gsel = $('mt-guided');
  if (gsel) { gsel.innerHTML = GUIDED.map(g => `<option value="${g.id}">${g.title} · ${Math.round(g.dur / 60)} min</option>`).join(''); if (cfg.guided) gsel.value = cfg.guided;
    gsel.onchange = () => { cfg.guided = gsel.value; save(); refresh(); }; }

  function refresh() {
    pick('min', cfg.min); pick('interval', cfg.interval); pick('start', cfg.start); pick('prep', cfg.prep); pick('mode', cfg.mode); pick('after', cfg.after);
    if (![5, 10, 15, 20, 30, 45, 60].includes(cfg.min)) custom.value = cfg.min;
    const g = cfg.mode === 'guided';
    document.querySelectorAll('.mt-silent').forEach(el => el.hidden = g);
    document.querySelectorAll('.mt-guided').forEach(el => el.hidden = !g);
    const gg = GUIDED.find(x => x.id === cfg.guided) || GUIDED[0];
    $('mt-go').disabled = g && !gg;
    const total = g ? (gg ? Math.round((gg.dur + cfg.after * 60) / 60) : 0) : cfg.min;
    $('mt-summary').textContent = g ? (gg ? `${gg.title} · about ${total} minutes, with a gong at the start and the end` : 'The guided recording is on its way.')
      : `${cfg.min} minutes of silence${cfg.interval ? `, a soft gong every ${cfg.interval} minutes` : ''}, three gongs to close`;
  }
  refresh();

  // ---------- build one continuous track ----------
  function fill(seq, s) {   // add silence lasting about s seconds; returns the exact length added
    let added = 0;
    while (s - added >= SEG.sil10 - 0.02) { seq.push('sil10'); added += SEG.sil10; }
    while (s - added >= SEG.sil1 / 2) { seq.push('sil1'); added += SEG.sil1; }
    return added;
  }
  function makePlan() {
    const seq = [], marks = [];
    let t = 0;
    t += fill(seq, cfg.prep);
    const begin = t;
    if (cfg.mode === 'guided') {
      const g = GUIDED.find(x => x.id === cfg.guided) || GUIDED[0];
      seq.push('gong1'); t += SEG.gong1;
      seq.push('g:' + g.id); t += g.dur;
      if (cfg.after) { marks.push({at: t, label: 'Sitting in silence'}); t += fill(seq, cfg.after * 60); }
      const end = t; seq.push('gong3'); t += SEG.gong3;
      return {seq, begin, end, total: t, title: g.title, sitLen: end - begin, marks};
    }
    const T = cfg.min * 60, startG = cfg.start === 3 ? 'gong3' : 'gong1';
    seq.push(startG); t += SEG[startG];
    if (cfg.interval) for (let m = cfg.interval * 60; m < T - 30; m += cfg.interval * 60) {
      const gap = begin + m - t; if (gap < 2) continue;
      t += fill(seq, gap); seq.push('soft'); t += SEG.soft;
    }
    const gap = begin + T - t; if (gap > 0) t += fill(seq, gap);
    const end = t; seq.push('gong3'); t += SEG.gong3;
    return {seq, begin, end, total: t, title: `Silent meditation · ${cfg.min} min`, sitLen: end - begin, marks};
  }
  async function load(name) {
    if (bufs[name]) return bufs[name];
    const file = name.startsWith('g:') ? (GUIDED.find(x => 'g:' + x.id === name) || {}).file : 'assets/gong/' + FILE[name];
    const r = await fetch(file); if (!r.ok) throw new Error('load ' + file);
    return (bufs[name] = await r.arrayBuffer());
  }

  // ---------- run ----------
  const fmt = s => { s = Math.max(0, Math.round(s)); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60; return (h ? h + ':' + String(m).padStart(2, '0') : m) + ':' + String(x).padStart(2, '0'); };
  async function begin() {
    // unlock audio inside the tap (iPhone), then build the track
    audio.src = 'assets/gong/sil1.mp3'; audio.play().catch(() => {});
    $('mt-go').disabled = true; $('mt-go').textContent = 'Preparing…';
    try {
      plan = makePlan();
      const uniq = [...new Set(plan.seq)]; await Promise.all(uniq.map(load));
      if (url) URL.revokeObjectURL(url);
      url = URL.createObjectURL(new Blob(plan.seq.map(n => bufs[n]), {type: 'audio/mpeg'}));
      audio.src = url; audio.currentTime = 0;
      await audio.play();
    } catch (e) { $('mt-go').disabled = false; $('mt-go').textContent = 'Begin'; alert('Sorry, the timer could not start. Please check your connection and try again.'); return; }
    running = true; finished = false;
    form.hidden = true; live.hidden = false; showMini(true); media(); tick();
    document.querySelector('.mt-card').scrollIntoView({behavior: 'smooth', block: 'start'});
    $('mt-go').textContent = 'Begin'; $('mt-go').disabled = false;
  }
  function tick() {
    if (!running) return;
    const t = audio.currentTime || 0;
    let left, label;
    if (t < plan.begin) { left = plan.begin - t; label = 'Settling in'; }
    else if (t < plan.end) { left = plan.end - t; label = cfg.mode === 'guided' ? (plan.marks.length && t >= plan.marks[0].at ? 'Sitting in silence' : 'Loving-kindness') : 'Sitting'; }
    else { left = 0; label = 'Closing gongs'; }
    clock.textContent = fmt(left); phase.textContent = label;
    const done = Math.min(1, Math.max(0, (t - plan.begin) / plan.sitLen));
    ring.style.setProperty('--p', (done * 100).toFixed(2));
    const ms = $('mini-status'); if (ms) ms.textContent = `${label} · ${fmt(left)} left`;
    try { navigator.mediaSession.setPositionState({duration: plan.total, position: Math.min(t, plan.total), playbackRate: 1}); } catch (e) {}
    setTimeout(tick, 500);
  }
  function media() {
    const mt = $('mini-title'); if (mt) mt.textContent = plan.title;
    if (!('mediaSession' in navigator)) return;
    try { navigator.mediaSession.metadata = new MediaMetadata({title: plan.title, artist: 'Vipassana Retreat UK', album: 'Meditation timer',
      artwork: [{src: 'assets/cover-timer.jpg', sizes: '512x512', type: 'image/jpeg'}]}); } catch (e) {}
  }
  function pauseResume() { if (!running) return; if (audio.paused) audio.play(); else audio.pause(); }
  function end(completed) {
    if (!running) return;
    running = false; audio.pause();
    const sat = Math.min(plan.sitLen, Math.max(0, (audio.currentTime || 0) - plan.begin));
    if (sat >= 60) logSit(Math.round(sat / 60));
    live.hidden = true; form.hidden = false; showMini(false);
    $('mt-done').hidden = false;
    $('mt-done-msg').textContent = completed ? 'Well sat. Take a moment before you get up, and carry this quiet with you.' : `You sat for ${fmt(sat)}. Every minute counts.`;
    try { navigator.mediaSession.playbackState = 'none'; } catch (e) {}
    stats();
  }
  audio.addEventListener('ended', () => { if (running) end(true); });
  audio.addEventListener('pause', () => { if (!running) return; $('mt-pause').textContent = '▶ Resume'; const mp = $('mini-play'); if (mp) mp.textContent = '▶'; });
  audio.addEventListener('play', () => { if (!running) return; $('mt-pause').textContent = '❚❚ Pause'; const mp = $('mini-play'); if (mp) mp.textContent = '❚❚'; });

  $('mt-go').onclick = () => { $('mt-done').hidden = true; begin(); };
  $('mt-pause').onclick = pauseResume;
  $('mt-end').onclick = () => end(false);
  const mini = $('mini');
  const showMini = on => { if (mini) { mini.hidden = !on; document.body.classList.toggle('has-mini', on); } };
  if (mini) { $('mini-play').onclick = pauseResume; $('mini-stop').onclick = () => end(false); }
  if ('mediaSession' in navigator) {
    const set = (a, f) => { try { navigator.mediaSession.setActionHandler(a, f); } catch (e) {} };
    set('play', () => audio.play()); set('pause', () => audio.pause()); set('stop', () => end(false));
    set('seekto', null); set('seekforward', null); set('seekbackward', null); set('nexttrack', null); set('previoustrack', null);
  }
  $('mt-sample').onclick = async () => { const a = new Audio('assets/gong/gong1.mp3'); a.play(); };

  // ---------- practice log (kept on this device only) ----------
  function logSit(min) { const log = jget('mt-log', []); log.push({d: new Date().toISOString().slice(0, 10), m: min}); store.set('mt-log', JSON.stringify(log.slice(-1000))); }
  function stats() {
    const log = jget('mt-log', []), el = $('mt-stats'); if (!el) return;
    if (!log.length) { el.hidden = true; return; }
    const day = d => new Date(d + 'T12:00:00'), today = new Date(); today.setHours(12, 0, 0, 0);
    const week = log.filter(x => (today - day(x.d)) / 864e5 < 7);
    const days = new Set(log.map(x => x.d)); let streak = 0;
    for (let k = 0; ; k++) { const d = new Date(today - k * 864e5).toISOString().slice(0, 10); if (days.has(d)) streak++; else if (k > 0) break; else continue; }
    const total = log.reduce((a, x) => a + x.m, 0);
    el.hidden = false;
    el.innerHTML = `<div><strong>${week.length}</strong><span>sits this week</span></div><div><strong>${week.reduce((a, x) => a + x.m, 0)}</strong><span>minutes this week</span></div><div><strong>${streak}</strong><span>day${streak === 1 ? '' : 's'} in a row</span></div><div><strong>${Math.round(total / 60 * 10) / 10}</strong><span>hours in all</span></div>`;
  }
  stats();
}
