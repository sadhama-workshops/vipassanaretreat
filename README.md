# vipassanaretreat.com

Silent Insight Vipassana retreats at Hardwick Estate — by Sadhama.

- `public/` — the live website (Cloudflare Pages serves this folder; no build step)
- `content/` — articles (Markdown) and Ask Ananda answers (`ananda_qa.py`)
- `src/` — CSS and JavaScript
- `tools/` — generators: `build_library.py` (sutta library from SuttaCentral bilara-data, CC0) and `build_site.py` (pages)

Cloudflare Pages settings: Framework preset **None**, build command **(empty)**, output directory **public**.
