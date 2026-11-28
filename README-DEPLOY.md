# vipassanaretreat.com — deployable site

Static site: upload this whole folder to any web host (WordPress.com Business plan via SFTP, Netlify, Cloudflare Pages, GitHub Pages). Point vipassanaretreat.com at it.

## Booking (WeTravel)
Every "Book" button uses your WeTravel embed (uid 202227, trip uuid 68342383) with `embed_checkout.js`, so on the live domain it opens the floating WeTravel checkout window, same as sadhama.com. The retreats page also loads your WeTravel reviews widget.
- Trips: Vipassana UK 68342383 (2027 dates), Thailand 7915926147 (25–31 Jan 2027), Practice of Peace 3370709561 — uuids in tools/build_site.py (WT).

## After going live
1. Google Search Console: add the domain, submit /sitemap.xml.
2. Keep vipassanaretreat.com detached from sadhama.com (or 301-redirect any old paths).
3. Link to the new site from sadhama.com's Vipassana page and your BookRetreats/WeTravel profiles.

## Ask Ananda
assets/ananda-data.json holds 49 curated answers in Dmitry's voice (source: content/ananda_qa.py). No AI key needed. To upgrade to a live AI later, the same answers can become its knowledge base.

## Library
Sujato translations (CC0, SuttaCentral bilara-data). library/<book>/*.json for the reader; downloads/*.epub and *.txt. "Listen" uses Piper neural voices running in the browser (assets/tts-worker.js + assets/tts/: onnxruntime-web MIT, piper_phonemize/espeak-ng GPL-3, source github.com/rhasspy/piper-phonemize). Voice models load from Hugging Face rhasspy/piper-voices and are cached. Plays through an <audio> element, so it continues with the screen off; Media Session gives lock-screen controls; position saved in localStorage. Device voices remain as a fallback.

## Meditation timer
timer.html + assets/timer.js. Gong segments in assets/gong/ (made by tools/make_gong.py, MP3 24 kHz mono 48 kbps CBR) are joined in the browser into one continuous track, so it plays with the screen locked. Add guided recordings to GUIDED in tools/build_site.py (encode with the same settings; set dur = frames x 576 / 24000).
