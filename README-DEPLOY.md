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
Sujato translations (CC0, SuttaCentral bilara-data). library/<book>/*.json for the reader; downloads/*.epub and *.txt. "Listen" uses the browser's built-in speech voices.
