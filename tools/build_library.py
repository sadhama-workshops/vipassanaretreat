#!/usr/bin/env python3
"""Build the 8-collection Dhamma library (Bhikkhu Sujato, CC0) for vipassanaretreat.com.
Outputs: out/library/<book>/<chunk>.json (HTML for the online reader + TTS),
         out/library/<book>/index.json, out/downloads/<book>.epub and .txt
"""
import json, re, sys, html, zipfile, uuid
from pathlib import Path

SRC = Path(sys.argv[1]); OUT = Path(sys.argv[2])
T = SRC / 'translation/en/sujato/sutta'; H = SRC / 'html/pli/ms/sutta'

BOOKS = [
  dict(slug='samyutta-nikaya', code='sn', path='sn', title='Saṁyutta Nikāya', en='The Linked Discourses',
       blurb='Short discourses grouped by theme — including the Satipaṭṭhāna and Ānāpāna saṁyuttas that the vipassana method comes from.'),
  dict(slug='anguttara-nikaya', code='an', path='an', title='Aṅguttara Nikāya', en='The Numbered Discourses',
       blurb='Teachings arranged by number, from the Ones to the Elevens: practical, direct guidance for daily life and practice.'),
  dict(slug='dhammapada', code='dhp', path='kn/dhp', title='Dhammapada', en='Sayings of the Dhamma',
       blurb='423 verses on mind, heart and the path. The most-loved book of the Pāḷi canon.'),
  dict(slug='sutta-nipata', code='snp', path='kn/snp', title='Sutta Nipāta', en='The Anthology of Discourses',
       blurb='Some of the oldest teachings, including the Mettā Sutta and the Maṅgala Sutta (Blessings).'),
  dict(slug='udana', code='ud', path='kn/ud', title='Udāna', en='Heartfelt Sayings',
       blurb='Short stories that end in an inspired utterance of the Buddha.'),
  dict(slug='itivuttaka', code='iti', path='kn/iti', title='Itivuttaka', en='So It Was Said',
       blurb='112 short teachings in prose and verse, remembered by the lay disciple Khujjuttarā.'),
  dict(slug='theragatha', code='thag', path='kn/thag', title='Theragāthā', en='Verses of the Senior Monks',
       blurb='Poems of awakening by the early monks — honest, vivid, often set in forest and mountain.'),
  dict(slug='therigatha', code='thig', path='kn/thig', title='Therīgāthā', en='Verses of the Senior Nuns',
       blurb='The world’s oldest collection of women’s spiritual poetry.'),
]

def natkey(p):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', p.name)]

def segments(tfile):
    tr = json.load(open(tfile))
    sid = tfile.name.split('_')[0]
    hf = list(H.glob(f'**/{sid}_html.json'))
    hm = json.load(open(hf[0])) if hf else {}
    parts = []
    for k, v in tr.items():
        tmpl = hm.get(k, '{}')
        parts.append(tmpl.replace('{}', html.escape(v)))
    body = ''.join(parts)
    body = re.sub(r'<article[^>]*>|</article>', '', body)
    body = re.sub(r"=''([^'])", r"='\1", body)
    body = re.sub(r"(class='[^']*')'", r'\1', body)
    title = ''
    m = re.search(r"<h1[^>]*>(.*?)</h1>", body)
    if m: title = re.sub('<[^>]+>', '', m.group(1)).strip()
    return sid, title, body

def chunks_for(b):
    base = T / b['path']
    subdirs = sorted([d for d in base.iterdir() if d.is_dir()], key=natkey)
    if b['code'] in ('sn', 'an'):
        for d in subdirs:
            yield d.name, sorted(d.glob('*.json'), key=natkey)
    elif subdirs:  # snp vaggas, thag/thig? (thag flat)
        for d in subdirs:
            yield d.name, sorted(d.glob('*.json'), key=natkey)
    else:
        yield 'all', sorted(base.glob('*.json'), key=natkey)

def text_of(h):
    t = re.sub(r'</(p|h\d|li|header|blockquote|div|section)>', '\n', h)
    t = re.sub(r'<br\s*/?>', '\n', t)
    t = html.unescape(re.sub('<[^>]+>', '', t))
    return re.sub(r'\n\s*\n+', '\n\n', t).strip()

SN_NAMES = ['With Gods', 'Gods', 'Kosala', 'Māra', 'Nuns', 'Brahmā', 'Brahmins', 'Vaṅgīsa', 'Forest', 'Native Spirits', 'Sakka', 'Causation', 'Comprehension', 'Elements', 'Transmigration', 'Kassapa', 'Possessions, Honor, and Popularity', 'Rāhula', 'Lakkhaṇa', 'Similes', 'Monks', 'Aggregates', 'Rādha', 'Views', 'Entering', 'Arising', 'Corruptions', 'Sāriputta', 'Dragons', 'Phoenixes', 'Centaurs', 'Cloud Gods', 'Vacchagotta', 'Absorption', 'The Six Sense Fields', 'Feeling', 'Females', 'Jambukhādaka', 'Sāmaṇḍaka', 'Moggallāna', 'Citta', 'Chiefs', 'The Unconditioned', 'The Undeclared Points', 'The Path', 'Awakening Factors', 'Mindfulness Meditation', 'Faculties', 'Right Efforts', 'Powers', 'Bases of Psychic Power', 'Anuruddha', 'Absorptions', 'Breath Meditation', 'Stream-Entry', 'Truths']
def chunk_label(b, name, first_title):
    if b['code'] == 'sn': return f"SN {name[2:]} · {SN_NAMES[int(name[2:])-1]}"
    if b['code'] == 'an': return f"Book of the {['','Ones','Twos','Threes','Fours','Fives','Sixes','Sevens','Eights','Nines','Tens','Elevens'][int(name[2:])]}"
    if name.startswith('vagga'): return f"Chapter {name[5:]}"
    return b['en']

def epub(b, chapters, path):
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, 'vipassanaretreat.com/' + b['slug']))
    z = zipfile.ZipFile(path, 'w')
    z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml', '<?xml version="1.0"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
    items, spine, nav = [], [], []
    css = 'body{font-family:serif;line-height:1.5}h1{font-size:1.3em}.verse,.rule{margin-left:1em}'
    z.writestr('OEBPS/style.css', css, compress_type=zipfile.ZIP_DEFLATED)
    for i, (label, body) in enumerate(chapters):
        fn = f'c{i:03d}.xhtml'
        xb = re.sub(r'<br>', '<br/>', body)
        xb = re.sub(r"<(\w+)([^>]*?)(?<!/)>", lambda m: m.group(0), xb)
        doc = f'<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{html.escape(label)}</title><link rel="stylesheet" href="style.css"/></head><body><h1>{html.escape(label)}</h1>{xb}</body></html>'
        z.writestr('OEBPS/' + fn, doc, compress_type=zipfile.ZIP_DEFLATED)
        items.append(f'<item id="c{i}" href="{fn}" media-type="application/xhtml+xml"/>'); spine.append(f'<itemref idref="c{i}"/>')
        nav.append(f'<li><a href="{fn}">{html.escape(label)}</a></li>')
    z.writestr('OEBPS/nav.xhtml', f'<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Contents</title></head><body><nav epub:type="toc"><h1>Contents</h1><ol>{"".join(nav)}</ol></nav></body></html>', compress_type=zipfile.ZIP_DEFLATED)
    opf = f'''<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">urn:uuid:{uid}</dc:identifier><dc:title>{b['title']} — {b['en']}</dc:title><dc:creator>Translated by Bhikkhu Sujato</dc:creator><dc:language>en</dc:language><dc:rights>CC0 Public Domain (SuttaCentral)</dc:rights><dc:publisher>vipassanaretreat.com</dc:publisher><meta property="dcterms:modified">2026-11-27T00:00:00Z</meta></metadata><manifest><item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/><item id="css" href="style.css" media-type="text/css"/>{"".join(items)}</manifest><spine>{"".join(spine)}</spine></package>'''
    z.writestr('OEBPS/content.opf', opf, compress_type=zipfile.ZIP_DEFLATED)
    z.close()

catalog = []
for b in BOOKS:
    bdir = OUT / 'library' / b['slug']; bdir.mkdir(parents=True, exist_ok=True)
    (OUT / 'downloads').mkdir(parents=True, exist_ok=True)
    toc, chapters, txt = [], [], [f"{b['title']} — {b['en']}\nTranslated by Bhikkhu Sujato (SuttaCentral). Public domain (CC0).\nShared by vipassanaretreat.com\n\n"]
    nsuttas = 0
    for name, files in chunks_for(b):
        parts, suttas = [], []
        for f in files:
            sid, title, body = segments(f)
            parts.append(f"<section id='{sid}'>{body}</section>"); suttas.append([sid, title]); nsuttas += 1
        body = ''.join(parts)
        label = chunk_label(b, name, suttas[0][1] if suttas else '')
        json.dump({'label': label, 'html': body}, open(bdir / f'{name}.json', 'w'), ensure_ascii=False, separators=(',', ':'))
        toc.append({'id': name, 'label': label, 'suttas': suttas})
        chapters.append((label, body)); txt.append(f"\n\n==== {label} ====\n\n" + text_of(body))
    json.dump({'toc': toc}, open(bdir / 'index.json', 'w'), ensure_ascii=False, separators=(',', ':'))
    (OUT / 'downloads' / f"{b['slug']}.txt").write_text(''.join(txt))
    epub(b, chapters, OUT / 'downloads' / f"{b['slug']}.epub")
    catalog.append({k: b[k] for k in ('slug', 'code', 'title', 'en', 'blurb')} | {'chapters': len(toc), 'suttas': nsuttas})
    print(b['slug'], len(toc), nsuttas)
json.dump(catalog, open(OUT / 'library' / 'catalog.json', 'w'), ensure_ascii=False, indent=1)
