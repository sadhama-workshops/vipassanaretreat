/* Natural-voice reader: Piper neural voices running on the listener's own device.
   onnxruntime-web (MIT) and piper_phonemize/espeak-ng (GPL-3, source: github.com/rhasspy/piper-phonemize)
   are served from /assets/tts/. Voice models come from Hugging Face (rhasspy/piper-voices, MIT) and are
   kept in the browser cache after the first download. */
const BASE = new URL('tts/', self.location.href).href;
importScripts(BASE + 'ort.wasm.min.js', BASE + 'piper_phonemize.js');
ort.env.wasm.numThreads = 1;              // no cross-origin isolation needed
ort.env.wasm.wasmPaths = BASE;

const HOSTS = ['https://huggingface.co/rhasspy/piper-voices/resolve/main/',
               'https://huggingface.co/diffusionstudio/piper-voices/resolve/main/'];
const CACHE = 'piper-voices-v1';
let session = null, config = null, voiceKey = null, phon = null, phonReusable = true, printCb = null;

const post = (m, t) => self.postMessage(m, t || []);

async function cachedFetch(path, base, id, kind) {
  const cache = await caches.open(CACHE).catch(() => null);
  const key = 'https://voices.local/' + path;
  if (cache) { const hit = await cache.match(key); if (hit) return hit.arrayBuffer(); }
  let res = null, err = null;
  for (const h of (base ? [base] : HOSTS)) {
    try { res = await fetch(h + path); if (res.ok) break; err = new Error('HTTP ' + res.status); res = null; } catch (e) { err = e; }
  }
  if (!res) throw err || new Error('download failed');
  const total = +(res.headers.get('Content-Length') || 0);
  const reader = res.body.getReader(); const chunks = []; let got = 0, last = 0;
  for (;;) {
    const { done, value } = await reader.read(); if (done) break;
    chunks.push(value); got += value.length;
    if (kind === 'model' && Date.now() - last > 250) { last = Date.now(); post({ type: 'progress', id, loaded: got, total }); }
  }
  const blob = new Blob(chunks);
  if (cache) { try { await cache.put(key, new Response(blob)); } catch (e) {} }
  return blob.arrayBuffer();
}

async function loadVoice(path, base, id) {
  if (voiceKey === path && session) return;
  session = null; config = null;
  const cfg = await cachedFetch(path + '.json', base, id, 'config');
  config = JSON.parse(new TextDecoder().decode(cfg));
  const model = await cachedFetch(path, base, id, 'model');
  post({ type: 'progress', id, loaded: 1, total: 1, preparing: true });
  session = await ort.InferenceSession.create(model, { executionProviders: ['wasm'] });
  voiceKey = path;
}

async function phonModule() {
  if (phon && phonReusable) return phon;
  phon = await createPiperPhonemize({
    print: d => { const cb = printCb; printCb = null; if (cb) cb(d); },
    printErr: () => {},
    locateFile: f => BASE + f,
  });
  return phon;
}
async function phonemize(text) {
  for (let attempt = 0; attempt < 2; attempt++) {
    const m = await phonModule();
    const ids = await new Promise(resolve => {
      const timer = setTimeout(() => { printCb = null; resolve(null); }, 8000);
      printCb = d => { clearTimeout(timer); try { resolve(JSON.parse(d).phoneme_ids); } catch (e) { resolve(null); } };
      try { m.callMain(['-l', config.espeak.voice, '--input', JSON.stringify([{ text }]), '--espeak_data', '/espeak-ng-data']); }
      catch (e) { clearTimeout(timer); printCb = null; resolve(null); }
    });
    if (ids) return ids;
    phonReusable = false; phon = null;   // module could not be reused: make a fresh one each time
  }
  throw new Error('phonemizer failed');
}

function wav(pcm, rate, padSec) {
  const pad = Math.round(rate * padSec), n = pcm.length + pad;
  const v = new DataView(new ArrayBuffer(44 + n * 2));
  const s = (o, t) => { for (let i = 0; i < t.length; i++) v.setUint8(o + i, t.charCodeAt(i)); };
  s(0, 'RIFF'); v.setUint32(4, 36 + n * 2, true); s(8, 'WAVE'); s(12, 'fmt ');
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true); v.setUint32(24, rate, true);
  v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); s(36, 'data'); v.setUint32(40, n * 2, true);
  let peak = 0; for (let i = 0; i < pcm.length; i++) peak = Math.max(peak, Math.abs(pcm[i]));
  const g = peak > 0 ? Math.min(3, 0.89 / peak) : 1;      // gentle normalisation
  for (let i = 0; i < pcm.length; i++) { const x = Math.max(-1, Math.min(1, pcm[i] * g)); v.setInt16(44 + i * 2, x * 32767, true); }
  return v.buffer;
}

async function speak(text, rate, pause) {
  const ids = await phonemize(text);
  const inf = config.inference || {};
  const feeds = {
    input: new ort.Tensor('int64', ids, [1, ids.length]),
    input_lengths: new ort.Tensor('int64', [ids.length]),
    scales: new ort.Tensor('float32', [inf.noise_scale ?? 0.667, (inf.length_scale ?? 1) / (rate || 1), inf.noise_w ?? 0.8]),
  };
  if (config.num_speakers > 1) feeds.sid = new ort.Tensor('int64', [0]);
  const out = await session.run(feeds);
  return wav(out.output.data, config.audio.sample_rate, pause);
}

let busy = Promise.resolve(), epoch = 0;
self.onmessage = e => {
  const m = e.data;
  if (m.type === 'epoch') { epoch = m.n; return; }   // skip work that is no longer wanted
  busy = busy.then(async () => {
    try {
      if (m.type === 'load') { await loadVoice(m.path, m.base, m.id); post({ type: 'ready', id: m.id }); }
      else if (m.type === 'speak') {
        if ((m.epoch ?? epoch) < epoch) { post({ type: 'error', id: m.id, message: 'cancelled' }); return; }
        await loadVoice(m.path, m.base, m.id);
        const buf = await speak(m.text, m.rate, m.pause ?? 0.45);
        post({ type: 'audio', id: m.id, buf }, [buf]);
      }
      else if (m.type === 'stored') {
        const cache = await caches.open(CACHE); const keys = await cache.keys();
        post({ type: 'stored', id: m.id, paths: keys.map(k => k.url.replace('https://voices.local/', '')) });
      }
    } catch (err) { post({ type: 'error', id: m.id, message: String(err && err.message || err) }); }
  });
};
