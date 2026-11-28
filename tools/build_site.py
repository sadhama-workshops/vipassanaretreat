#!/usr/bin/env python3
"""Generate vipassanaretreat.com as a static site into out/."""
import json, re, html, sys, shutil
from pathlib import Path
import markdown

ROOT = Path(__file__).parent.parent; OUT = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'out'); SRC = ROOT / 'src'; CONTENT = ROOT / 'content'
DOMAIN = 'https://vipassanaretreat.com'
sys.path.insert(0, str(CONTENT)); from ananda_qa import QA

WT = dict(env='https://www.wetravel.com', uid='202227', vip='68342383', thai='7915926147', peace='6139477701')
CHECKOUT = f"https://www.wetravel.com/checkout_embed?uuid={WT['vip']}"
TRIP = 'https://sadhama.wetravel.com/trips/insight-vipassana-silent-meditation-retreats-2026-sadhama-rewild-retreats-68342383'
PROFILE = 'https://www.wetravel.com/users/sadhama'
# Brevo subscription form link (Brevo > Contacts > Forms > your form > Share > link). Empty = sign-up hidden.
BREVO_FORM_URL = 'https://3cda042e.sibforms.com/serve/MUIFAFoC-7B41FIhIknUzWi_EUL8s3z2sYQtNM_B_DoOpqzE-NmmmIELIeGLVuX0svfNNv3IqSGmLw_usAlpmUi1TFNDGW-NdusISRrS0lIUueimXwtAMefntX5Ws7QGxRKr2xcBnGlteih456aRNd4Vgfo1QSX6BYnDFNl0jzzkavaqBGnZ071pFqX61oRiUc4U4OYOFQdzvQm3'
DATES = [('2027-05-31', '2027-06-06', '31 May – 6 June'), ('2027-07-26', '2027-08-01', '26 July – 1 August'), ('2027-08-30', '2027-09-05', '30 August – 5 September')]
NAV = [('retreats.html', 'Retreats & booking'), ('testimonials.html', 'Reviews'), ('gallery.html', 'Gallery'), ('articles.html', 'Articles'), ('ask-ananda.html', 'Ask Ananda'), ('library.html', 'Dhamma library'), ('timer.html', 'Meditation timer'), ('teacher.html', 'Teacher')]

def book_btn(label='Book your place', cls='btn book', extra='', uuid=None):
    u = uuid or WT['vip']
    return (f'<a class="{cls} wtrvl-checkout_button" data-env="{WT["env"]}" data-version="v0.4" data-uid="{WT["uid"]}" '
            f'data-uuid="{u}" href="https://www.wetravel.com/checkout_embed?uuid={u}" rel="noopener"{extra}>{label}</a>')

LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="15" fill="var(--oak)"/><path d="M5 21c4-3 7-4 11-4s7 1 11 4v3H5z" fill="var(--sky)"/><path d="M10 21l6-8 6 8z" fill="#fff"/><circle cx="23" cy="10" r="2.6" fill="var(--sun)"/></svg>'

def rel(href, depth):
    """Map site-absolute content links to relative static paths."""
    m = {'/': 'index.html', '/retreats/': 'retreats.html', '/teacher/': 'teacher.html', '/ask-ananda/': 'ask-ananda.html',
         '/library/': 'library.html', '/articles/': 'articles.html', '/testimonials/': 'testimonials.html', '/gallery/': 'gallery.html'}
    if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'): return href
    h = m.get(href)
    if h is None:
        h = href.lstrip('/')
        h = h.replace('library/read.html', 'read.html')
    return '../' * depth + h

def fix_links(s, depth):
    return re.sub(r'href="(/[^"]*)"', lambda m: f'href="{rel(m.group(1), depth)}"', s)

NEWSLETTER = '''<section class="nl-band" data-nl hidden><div class="wrap nl-in"><div><h2>Retreat news and Dhamma letters</h2><p>New dates, early-bird places and short teachings from Dmitry, a few times a year. No spam; unsubscribe any time.</p></div>
<form class="nl-form" novalidate><label class="sr" for="nl-e1">Email address</label><input id="nl-e1" type="email" name="EMAIL" placeholder="Your email" autocomplete="email" required><button class="btn book" type="submit">Subscribe</button><p class="nl-msg small" role="status"></p></form></div></section>
<aside class="nl-pop" id="nl-pop" aria-labelledby="nl-t" hidden data-nl><button type="button" class="nl-x" aria-label="Close">×</button>
<p class="nl-t" id="nl-t">Retreat news, now and then</p><p class="small">New dates and a short Dhamma letter from Dmitry, a few times a year.</p>
<form class="nl-form" novalidate><label class="sr" for="nl-e2">Email address</label><input id="nl-e2" type="email" name="EMAIL" placeholder="Your email" autocomplete="email" required><button class="btn ghost" type="submit">Subscribe</button><p class="nl-msg small" role="status"></p></form>
<button type="button" class="nl-later small">No thanks</button></aside>'''

def page(path, title, desc, body, active='', image='oak-marquee-dawn', jsonld=None, scripts='', depth=0, canonical=None, extra_head=''):
    up = '../' * depth
    canon = canonical or (DOMAIN + '/' + (path if path != 'index.html' else ''))
    nav = ''.join(f'<a href="{up}{h}"{" aria-current=page" if h == active else ""}>{t}</a>' for h, t in NAV)
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>' for j in (jsonld or []))
    doc = f'''<!DOCTYPE html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website"><meta property="og:site_name" content="Vipassana Retreat UK">
<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{canon}"><meta property="og:image" content="{DOMAIN}/img/{image}.jpg">
<meta name="twitter:card" content="summary_large_image"><meta name="theme-color" content="#1f3a2e">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,600;1,6..72,400&display=swap" rel="stylesheet">
<link rel="icon" type="image/png" href="{up}assets/favicon.png"><link rel="apple-touch-icon" href="{up}assets/apple-touch-icon.png">
<link rel="stylesheet" href="{up}assets/site.css">{extra_head}{ld}
</head><body>
<header class="top"><div class="wrap"><a class="brand" href="{up}index.html"><img src="{up}assets/sadhama-logo-white.png" width="91" height="56" alt="Sadhama"><span>Vipassana Retreat</span></a>
<button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav">Menu</button>
<nav class="nav" id="nav" aria-label="Main">{nav}</nav></div></header>
<main id="main">{fix_links(body, depth)}</main>
{NEWSLETTER}
<footer><div class="wrap"><div class="cols">
<div><img src="{up}assets/sadhama-logo-white-lg.png" width="160" height="99" alt="Sadhama" style="margin-bottom:14px"><p>Silent Insight Vipassana retreats in nature, on the River Thames at Hardwick Estate, Oxfordshire. Run by <a href="https://sadhama.com" rel="noopener">Sadhama</a>.</p></div>
<div><h4>Retreats</h4><ul><li><a href="{up}retreats.html">2027 dates &amp; booking</a></li><li><a href="{up}articles/what-is-a-vipassana-retreat.html">What is a vipassana retreat?</a></li><li><a href="{up}articles/silent-retreat-near-london.html">Silent retreat near London</a></li></ul></div>
<div><h4>Learn</h4><ul><li><a href="{up}ask-ananda.html">Ask Ananda</a></li><li><a href="{up}library.html">Dhamma library</a></li><li><a href="{up}timer.html">Meditation timer</a></li><li><a href="{up}articles.html">All articles</a></li></ul></div>
<div><h4>Contact</h4><ul><li>info@sadhama.com</li><li>Hardwick Estate, Whitchurch-on-Thames, RG8 7RA</li><li><a href="https://www.instagram.com/sadhamayoga/" rel="noopener">Instagram</a></li></ul></div>
</div><p class="small" style="margin-top:28px;opacity:.75">Sutta translations by Bhikkhu Sujato, SuttaCentral, dedicated to the public domain (CC0). Photographs © Sadhama.</p></div></footer>
{book_btn('Book a retreat', 'btn book float-book')}
<script>window.NL_ACTION={json.dumps(BREVO_FORM_URL)};</script><script src="{up}assets/site.js"></script>{scripts}
<script src="https://cdn.wetravel.com/widgets/embed_checkout.js"></script>
</body></html>'''
    p = OUT / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(doc)

def img(name, alt, cls='', sizes='100vw', depth=0, eager=False):
    up = '../' * depth
    return (f'<img src="{up}img/{name}.jpg" srcset="{up}img/{name}-sm.jpg 800w, {up}img/{name}.jpg 1800w" sizes="{sizes}" '
            f'alt="{html.escape(alt)}" {"" if eager else "loading=lazy "}decoding="async"{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>')

SMILE = 'fb-group-smiling'
ALT = {'oak-marquee-dawn': 'Meditators in a white marquee beneath an old oak at dawn, mist over the Thames valley',
       'marquee-dawn': 'The meditation marquee in a misty meadow at Hardwick Estate, early morning',
       'lily-pond-mist': 'Mist over still water with lily pads and reeds at dawn',
       'dmitry-teaching': 'Dmitry Glazkov giving a Dhamma talk to meditators in the meadow',
       'circle-dmitry': 'Retreat participants standing in a circle with arms around each other, the teacher smiling',
       'circle-meadow': 'Meditators standing in a circle in the meadow, eyes closed',
       'morning-stretch': 'Retreat group raising their arms together in the morning sun',
       'group-meadow': 'Retreat group standing arm in arm in a meadow with the Chiltern hills behind',
       'group-hills': 'Retreat participants arm in arm in front of rolling green hills',
       'group-panorama': 'A large retreat group in a half circle beside the marquee on the last morning',
       'riverside-talk': 'Teacher and guests sitting in a circle on the bank of the River Thames',
       'sauna-dmitry': 'Dmitry relaxing in the riverside wooden sauna'}
ALT.update(json.loads((CONTENT / 'fb_alts.json').read_text()))

# ---------- articles ----------
def load_articles():
    arts = []
    for f in sorted((CONTENT / 'articles').glob('*.md')):
        raw = f.read_text(); fm, body = raw.split('---', 2)[1:]
        meta = dict(re.findall(r'^(\w+):\s*(.*)$', fm, flags=re.M)); meta['slug'] = f.stem; meta['md'] = body.strip()
        words = len(re.findall(r'\w+', body)); meta['mins'] = max(3, round(words / 220))
        arts.append(meta)
    order = ['what-is-a-vipassana-retreat', 'first-silent-retreat-what-to-expect', 'silent-retreat-near-london', 'vipassana-for-beginners',
             'goenka-10-day-vs-7-day-insight-retreat', 'what-to-bring-silent-retreat', 'vipassana-retreat-cost-dana', 'noting-meditation-rising-falling',
             'walking-meditation-how-to', 'pain-while-meditating', 'five-hindrances-meditation', 'loving-kindness-metta-meditation', 'keep-practising-after-retreat']
    arts.sort(key=lambda a: order.index(a['slug']) if a['slug'] in order else 99)
    return arts

def card(a, depth=0):
    up = '../' * depth
    return (f'<article class="card"><a class="stretch" href="{up}articles/{a["slug"]}.html">{img(a["image"], ALT.get(a["image"], ""), sizes="(max-width:600px) 100vw, 400px", depth=depth)}'
            f'<div class="body"><h3>{html.escape(a["title"])}</h3><p>{html.escape(a["description"])}</p><span class="more">Read · {a["mins"]} min</span></div></a></article>')

AUTHOR = {"@type": "Person", "name": "Dmitry Glazkov", "url": DOMAIN + "/teacher.html"}
ORG = {"@type": "Organization", "name": "Sadhama Rewild Retreats", "url": "https://sadhama.com", "email": "info@sadhama.com", "logo": DOMAIN + "/assets/sadhama-logo-white-lg.png"}

def build_articles(arts):
    for i, a in enumerate(arts):
        body_html = markdown.markdown(a['md'], extensions=['tables'])
        related = [x for x in arts if x['slug'] != a['slug']][i % 4: i % 4 + 3]
        body = f'''<div class="band"><div class="wrap"><div class="article">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/articles/">Articles</a></nav>
<h1>{html.escape(a["title"])}</h1>
<p class="meta">By <a href="/teacher/">Dmitry Glazkov</a>, vipassana teacher · {a["mins"]} min read</p>
{img(a["image"], ALT.get(a["image"], ""), sizes="(max-width:760px) 100vw, 720px", depth=1, eager=True).replace("<img ", "<img style=\"border-radius:14px;aspect-ratio:16/9;object-fit:cover;width:100%;margin-bottom:28px\" ")}
<div class="prose">{body_html}</div>
<div class="cta-box"><p>Practise this with a teacher, in silence, by the river. Seven days at Hardwick, 2027.</p>{book_btn("Book a place")}</div>
<p class="muted small" style="margin-top:18px">Have a question about the practice? <a href="/ask-ananda/">Ask Ananda</a>, our Dhamma assistant.</p>
</div></div></div>
<section class="band mist"><div class="wrap"><h2>Keep reading</h2><div class="grid">{"".join(card(r, 1) for r in related)}</div></div></section>'''
        ld = [{"@context": "https://schema.org", "@type": "Article", "headline": a['title'], "description": a['description'], "author": AUTHOR,
               "publisher": ORG, "datePublished": a['date'], "dateModified": a['date'], "image": f"{DOMAIN}/img/{a['image']}.jpg",
               "mainEntityOfPage": f"{DOMAIN}/articles/{a['slug']}.html", "keywords": a['keyword']},
              {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                  {"@type": "ListItem", "position": 1, "name": "Home", "item": DOMAIN + "/"},
                  {"@type": "ListItem", "position": 2, "name": "Articles", "item": DOMAIN + "/articles.html"},
                  {"@type": "ListItem", "position": 3, "name": a['title']}]}]
        page(f'articles/{a["slug"]}.html', a['title'] + ' | Vipassana Retreat UK', a['description'], body, 'articles.html', a['image'], ld, depth=1)
    body = f'''<section class="page-hero">{img("fb-river-sunset", ALT["fb-river-sunset"], eager=True)}<div class="wrap"><h1>Articles on silent retreat and vipassana practice</h1>
<p>Practical guides from Dmitry's retreat talks: what to expect, how to practise, and how to keep going at home.</p></div></section>
<section class="band"><div class="wrap"><div class="grid">{"".join(card(a) for a in arts)}</div></div></section>'''
    page('articles.html', 'Vipassana & Silent Retreat Articles | Vipassana Retreat UK', 'Guides to silent meditation retreats and vipassana practice: first retreat, what to bring, noting and walking meditation, pain, the hindrances, mettā.', body, 'articles.html', 'lily-pond-mist')

# ---------- FAQ ----------
FAQ = [
 ('What is a vipassana retreat?', 'A residential silent meditation retreat where you train in insight meditation, vipassana, based on the Buddha\'s four foundations of mindfulness. Our retreats follow the Mahasi Sayadaw noting tradition: sitting and walking meditation, Dhamma talks and teacher interviews, in noble silence.'),
 ('Can beginners attend?', 'Yes. Every group includes first-timers. The technique is taught step by step from the first evening, sittings are 45 minutes, alternating with walking meditation, and there is gentle yoga each morning.'),
 ('How much does it cost?', 'The organisational fee is £149 (deposit £75), covering plant-based meals and camping. The teaching is offered for dāna: you give what you feel moved to give at the end. A few reduced-cost seva places are available on application.'),
 ('Where are the retreats held?', 'At Hardwick Estate, Whitchurch-on-Thames, South Oxfordshire (RG8 7RA), on the River Thames in the Chilterns. About 40 minutes by train from London Paddington, or 20 minutes from Junction 12 of the M4.'),
 ('Where do I sleep?', 'You camp in the riverside campsite: bring your own tent, campervan or caravan, or rent a pre-erected tent or a bell tent with a framed bed when you book. Tents are single occupancy. There are hot showers and a riverside sauna.'),
 ('Do I need to be Buddhist?', 'No. Vipassana is a universal method of observing your own experience. It needs no belief system, and people of any religion or none practise it.'),
 ('How is it different from a Goenka 10-day course?', 'Both come from the Satipaṭṭhāna. Goenka courses use breath at the nostrils and body scanning over ten days; we teach rising-and-falling noting with formal walking meditation, live teacher talks and interviews, and daily yoga, over seven days.'),
 ('How do I book?', 'Booking is through WeTravel: press "Book your place", choose your date and accommodation, and pay a £75 deposit to secure your place.'),
]
def faq_html(items):
    return '<div class="faq">' + ''.join(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>' for q, a in items) + '</div>'
FAQ_LD = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}

def event_ld(s, e, label):
    return {"@context": "https://schema.org", "@type": "Event", "name": f"7-Day Insight Vipassana Silent Meditation Retreat ({label} 2027)",
            "startDate": s, "endDate": e, "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode", "eventStatus": "https://schema.org/EventScheduled",
            "location": {"@type": "Place", "name": "Hardwick Estate", "address": {"@type": "PostalAddress", "streetAddress": "Hardwick Estate", "addressLocality": "Whitchurch-on-Thames", "postalCode": "RG8 7RA", "addressRegion": "Oxfordshire", "addressCountry": "GB"}},
            "image": [f"{DOMAIN}/img/oak-marquee-dawn.jpg"], "description": "Seven days of silent Insight Vipassana meditation in nature on the River Thames: sitting and walking meditation, daily yoga, Dhamma talks, plant-based Ayurvedic food. Teaching offered for dāna.",
            "offers": {"@type": "Offer", "price": "149", "priceCurrency": "GBP", "url": TRIP, "availability": "https://schema.org/InStock", "validFrom": "2026-11-27"},
            "organizer": ORG, "performer": AUTHOR}

QUOTES = [
 ('This was an amazing retreat - my best yet and I’ve been on a lot all over the world. The teachings were amazing, the food exemplary. It was a truly nurturing experience.', 'Anita M.'),
 ('This retreat was truly exceptional, possibly the best I’ve ever attended… Their deep knowledge of yoga and wellness was evident in every session, making each practice enriching and accessible for all levels.', 'Ian M.'),
 ('Under Dmitry’s kind, humorous and humble guidance, one can find their way back to their true selves… The food was another level!', 'Rachel B.'),
 ('Dmitry is a brilliant communicator, able to make everyone laugh and to push on in cold weather, and to pay close attention and offer incisive, precise and compassionate guidance when required.', 'Daniel A.'),
 ('The silence allowed for a deep immersion into the practice, fostering an environment of profound inner peace and clarity.', 'Dionne H.'),
]
def quotes_html():
    return '<div class="quotes">' + ''.join(f'<blockquote class="quote"><p>“{html.escape(q)}”</p><cite>{n}, Sadhama retreat guest</cite></blockquote>' for q, n in QUOTES) + '</div>'

TIMETABLE = [('4:30', 'Wake up'), ('5:00', 'Sitting meditation'), ('5:45', 'Meditative yoga'), ('6:45', 'Sitting meditation'), ('7:30', 'Breakfast, shower, mindful work'),
             ('9:00', 'Meditation instructions'), ('10:00', 'Walking meditation'), ('10:45', 'Sitting meditation'), ('11:30', 'Lunch and rest'),
             ('13:30', 'Sitting meditation'), ('14:15', 'Walking meditation'), ('15:00', 'Meditation instructions'), ('15:45', 'Walking meditation · teacher interviews'),
             ('16:30', 'Sitting meditation · teacher interviews'), ('17:15', 'Drinks, rest, shower'), ('19:00', 'Dhamma talk, Q&A or loving-kindness'),
             ('20:00', 'Walking meditation'), ('20:30', 'Sitting meditation'), ('21:00', 'Rest')]
def timetable_html():
    return '<ul class="timetable">' + ''.join(f'<li><time>{t}</time><span>{html.escape(x)}</span></li>' for t, x in TIMETABLE) + '</ul>'

def dates_html():
    return '<div class="grid">' + ''.join(f'<div class="date-card"><span class="yr">7-day Insight Vipassana · 2027</span><span class="when">{lbl}</span><span class="muted">Hardwick Estate, Oxfordshire · £149 + dāna</span>{book_btn("Book this date")}</div>' for s, e, lbl in DATES) + '</div>'

# ---------- home ----------
WHY = [
 ("My mind never switches off", "Rest for a nervous system that is always on.", "I was overworked, burnt out, stressed, depressed, and never switched off properly. I gained a true mindset shift with new habits formed.", "Alex G."),
 ("I need to put the phone down", "Five days with your phone handed in, and nothing to scroll.", "The peace of being without a phone was amazing and gave me a proper reset.", "Elise S."),
 ("Life has piled up", "Space to step back and see your life from a different angle.", "A retreat can give you the time you really need to disconnect from everyday life and see everything from a different perspective.", "Dawid K."),
 ("I've lost touch with myself", "Silence, the river and the old oaks do much of the work.", "Being surrounded by nature was wonderful for nourishing the soul and reconnecting with myself.", "Guest, BookRetreats"),
 ("I've never meditated", "Even better: a clean slate. You learn step by step, with the teacher beside you every day.", "Even as a beginner in meditation, the guidance, kindness, and support I received throughout the retreat helped me feel grounded and never lost.", "Estela S."),
 ("I want something that lasts", "A simple method you can keep using at home.", "I now use the tools every day, and I feel the change immediately.", "Guest, BookRetreats"),
]
def why_html():
    cards = ''.join(f'<article class="why-c"><h3>“{html.escape(t)}”</h3><p class="why-a">{html.escape(a)}</p><blockquote><p>{html.escape(q)}</p><cite>{html.escape(n)}</cite></blockquote></article>' for t, a, q, n in WHY)
    return f'<div class="why">{cards}</div>'
WHY_SECTION = '''<section class="band"><div class="wrap"><h2>Why people come to sit in silence</h2>
<p class="lede" style="margin-bottom:26px">Before they arrive, guests tell us much the same few things. Here is what they wrote afterwards.</p>''' + "{why}" + '''
<p class="small" style="margin-top:22px">Research agrees: a study of 195 people on a one-week vipassana retreat found less anxiety and depression and more mindfulness, still there a month later. <a href="https://link.springer.com/article/10.1007/s12671-017-0682-5" rel="noopener">Read the study</a>.</p></div></section>'''

def build_home(arts):
    body = f'''<section class="hero">{img("oak-marquee-dawn", ALT["oak-marquee-dawn"], eager=True)}<div class="wrap">
<h1>Silent vipassana retreats in nature, an hour from London</h1>
<p>Seven days to rest a busy mind, put the phone away and discover the peace of a quiet, clear mind. Noble silence, insight meditation and gentle care in a meadow on the River Thames, with the teaching offered for donation.</p>
<div class="ctas">{book_btn()}<a class="btn light" href="/retreats/">See 2027 dates</a></div></div></section>

<section class="band"><div class="wrap"><h2>2027 retreat dates</h2><p class="lede" style="margin-bottom:24px">Three 7-day Insight Vipassana retreats at Hardwick Estate, South Oxfordshire, in early summer, high summer and the turning of the season. Each has five full days of silence, and every group welcomes first-timers.</p>{dates_html()}</div></section>

<section class="band mist"><div class="wrap split"><div>
<h2>Rest for a mind that never switches off</h2>
<p class="lede">Vipassanā means seeing clearly. For one week the bell keeps time, your phone rests in a drawer, and you learn to meet thoughts, feelings and sensations without being swept along by them. Nothing in your life has to change first. You simply learn a kinder, clearer way of holding what is already there.</p>
<ul class="ticks"><li>Sitting and walking meditation in the Mahasi Sayadaw noting tradition</li><li>Gentle yoga each morning, so the body can sit with ease</li><li>Evening Dhamma talks and personal interviews with the teacher</li><li>Five full days of noble silence, in a marquee beneath an old oak</li></ul>
<p style="margin-top:20px"><a href="/articles/what-is-a-vipassana-retreat.html">What is a vipassana retreat? →</a></p></div>
{img(SMILE, ALT[SMILE], sizes="(max-width:820px) 100vw, 600px")}</div></section>

<section class="band"><div class="wrap split">{img("sauna-dmitry", ALT["sauna-dmitry"], sizes="(max-width:820px) 100vw, 560px").replace("<img ", "<img style=\"aspect-ratio:4/5\" ")}<div>
<h2>Serious practice, gently held</h2>
<p class="lede">A silent retreat asks a lot of you, so we make sure everything else is taken care of. This softness is what guests remember most about a Sadhama vipassana.</p>
<ul class="ticks"><li><b>Nourishing food.</b> Karen's Ayurvedic plant-based cooking, much of it grown organically on the estate. Guests call it “another level”.</li><li><b>A wood-fired sauna by the river.</b> Warm your bones after a long day of sitting, then cool off with a dip in the Thames.</li><li><b>Caring hands on site.</b> Lomi lomi massage, Thai yoga massage, reiki and pravilo with our trusted therapists, for backs and hips that have been sitting all week.</li><li><b>The land itself.</b> Dawn mist on the river, swallows over the meadow, the ancient oaks of Hardwick. Nature does much of the work.</li></ul>
<p style="margin-top:18px"><a href="/retreats/#care">The wellbeing side of the retreat →</a></p></div></div></section>

<section class="band mist"><div class="wrap split"><div>
<h2>Never meditated? That can be an advantage</h2>
<p class="lede">Every group has first-timers, and they often do very well. With a clean slate there is nothing to unlearn and no other techniques to mix in. You simply follow what you are shown.</p>
<blockquote class="pull"><p>“Sometimes even the beginners’ clean slate has its benefits. When you don’t know other techniques, you just do what you’re told, and it’s easier to go.”</p><cite>Dmitry, from a retreat talk</cite></blockquote>
<ul class="ticks"><li>You learn the authentic Mahasi Sayadaw method from the very beginning, one step each day</li><li>An experienced teacher guides every sitting and gives a Dhamma talk each evening</li><li>Personal interviews with the teacher, to ask questions and clear up anything unclear</li><li>This is how vipassana has always been passed on in the monasteries of Burma and Thailand</li></ul>
<p style="margin-top:18px"><a href="/articles/vipassana-for-beginners.html">Vipassana for beginners →</a></p></div>
{img("fb-interview", ALT["fb-interview"], sizes="(max-width:820px) 100vw, 600px")}</div></section>

<section class="band"><div class="wrap"><h2>What's included</h2><p class="lede" style="margin-bottom:22px">One simple price for food and camping. The teaching itself is offered for dāna, a donation you give at the end, as vipassana has been offered for 2,500 years.</p>
<div class="inc"><div><h3>Included in £149</h3><ul class="ticks"><li>Six nights on the riverside campsite</li><li>All meditation sessions, instructions and Dhamma talks</li><li>Personal interviews with the teacher</li><li>Morning yoga and breathwork</li><li>Ayurvedic plant-based breakfast and lunch, a warming evening drink, herbal teas</li><li>The riverside sauna and wild swimming in the Thames</li><li>Hot showers, toilets and parking</li></ul></div>
<div><h3>Optional extras</h3><ul class="ticks"><li>A pre-erected tent or a canvas bell tent, from essential comfort to deluxe glamping with a proper bed</li><li>Massage and bodywork with our on-site therapists, booked on arrival</li><li>Dāna for the teaching: whatever you feel moved to give</li></ul><p style="margin-top:18px">{book_btn("See dates and book")}</p></div></div></div></section>

<section class="band oak"><div class="wrap"><h2>From people who have sat with us</h2>
<div class="stats" style="margin-bottom:28px"><div><b>4.9</b><span>average from 167 WeTravel reviews</span></div><div><b>35+</b><span>retreats run by Sadhama</span></div><div><b>1,700+</b><span>participants</span></div></div>
<h3 style="margin:8px 0 14px">What guests mention most</h3>{themes_html(4)}<div style="margin-top:28px">{quotes_html()}</div><p style="margin-top:24px"><a class="btn light" href="/testimonials/">Read all guest reviews</a></p></div></section>

<section class="band"><div class="wrap split">{img("fb-teacher-smile", ALT["fb-teacher-smile"], sizes="(max-width:820px) 100vw, 600px")}<div>
<h2>Ask Ananda, your Dhamma assistant</h2>
<p class="lede">Questions about sleepiness, pain, a wandering mind, the precepts, or what to bring? Ananda answers from Dmitry's retreat talks, in his words.</p>
<p><a class="btn ghost" href="/ask-ananda/">Ask a question</a></p></div></div></section>

<section class="band mist"><div class="wrap split"><div>
<h2>A free library of the Buddha's words</h2>
<p class="lede">Eight collections from the Pāḷi Canon, in Bhikkhu Sujato's public-domain translation. Read online, download as an ebook, or press Listen and have them read aloud.</p>
<p><a class="btn ghost" href="/library/">Open the library</a></p></div>
{img("fb-river-dawn", ALT["fb-river-dawn"], sizes="(max-width:820px) 100vw, 600px")}</div></section>

<section class="band"><div class="wrap"><h2>Guides for your practice</h2><div class="grid">{"".join(card(a) for a in arts[:6])}</div>
<p style="margin-top:22px"><a href="/articles/">All articles →</a></p></div></section>

<section class="band mist"><div class="wrap" style="max-width:860px"><h2>Questions people ask</h2>{faq_html(FAQ)}</div></section>
<section class="band"><div class="wrap cta-box" style="margin:0 auto;max-width:1100px"><p>Come carrying the noise of life. Leave a little quieter, with a practice to take home.</p>{book_btn()}</div></section>'''
    ld = [FAQ_LD, {"@context": "https://schema.org", "@type": "WebSite", "name": "Vipassana Retreat UK", "url": DOMAIN + "/"},
          ORG | {"@context": "https://schema.org", "sameAs": ["https://sadhama.com", "https://www.instagram.com/sadhamayoga/", PROFILE]}] + [event_ld(*d) for d in DATES]
    page('index.html', 'Vipassana Retreat UK: Silent Meditation Retreats near London 2027', 'Silent 7-day vipassana meditation retreats in nature on the River Thames, Oxfordshire, 40 minutes from London. 2027 dates, teaching offered for donation. Beginners welcome.', body, '', 'oak-marquee-dawn', ld)

# ---------- retreats ----------
def stars(n):
    return '<span class="stars" aria-label="%d out of 5 stars">%s</span>' % (n, '★' * n)

REVIEWS = json.loads((CONTENT / 'reviews.json').read_text())

def review_card(r, clamp=True):
    paras = ''.join(f'<p>{html.escape(p)}</p>' for p in r['text'].split('\n') if p.strip())
    return (f'<article class="rv{" clamp" if clamp else ""}" data-cat="{r["cat"]}" data-src="{r["src"]}"><header>{stars(r["stars"])}<span class="rv-src">{r["src"]}</span></header>'
            f'<div class="rv-text">{paras}</div><footer><b>{html.escape(r["name"])}</b><span>{html.escape(r["retreat"])}{(" · " + html.escape(r["date"])) if r["date"] else ""}</span></footer></article>')

THEMES = [
 ("Nourished", "food|karen", "the food, cooked with love by Karen", "Gorgeous food, tranquillity of mind"),
 ("At one with nature", "river|nature|oak|dawn|meadow|forest", "the river, the meadow and the old oaks", "Totally at one with nature"),
 ("Peace and calm", "peace|calm|stillness|tranquil", "a deep, quiet peace", "I spent the whole week in tranquil peace"),
 ("Life-changing", "life[- ]chang|transform|profound", "a change that stayed with them", "Amazing, life changing"),
 ("Rested and reset", r"burn ?out|exhaust|rest(ed|ful)?\b|recharg|reset", "rest for a tired body and mind", "Both restful and recharging"),
 ("Safe and held", "safe|held|judg", "a kind space, free of judgement", "A warm, safe and thoughtful environment"),
]
def themes_html(limit=None):
    n = len(REVIEWS)
    rows = []
    for t, pat, line, q in THEMES:
        c = sum(1 for r in REVIEWS if re.search(pat, r['text'], re.I))
        rows.append((c, t, line, q))
    rows.sort(reverse=True)
    rows = rows[:limit] if limit else rows
    tiles = ''.join(f'<div class="th"><b>{c}</b><span class="th-t">{html.escape(t)}</span><span class="th-l">reviews mention {html.escape(line)}</span><span class="th-q">“{html.escape(q)}”</span></div>' for c, t, line, q in rows)
    return f'<div class="themes">{tiles}</div><p class="small muted" style="margin-top:10px">From {n} guest reviews on WeTravel, BookRetreats and Google.</p>'

BR_SCORES = [('Teachers', 4.91), ('Location', 4.91), ('Value', 4.89), ('Accuracy', 4.89), ('Food', 4.88), ('Communication', 4.85), ('Accommodation', 4.71)]
def scores_html():
    return '<div class="scores">' + ''.join(f'<div class="score"><span>{k}</span><span class="bar"><i style="width:{(v/5)*100:.1f}%"></i></span><b>{v:.2f}</b></div>' for k, v in BR_SCORES) + '</div>'

RATINGS = '<div class="ratings"><span><b>★ 4.9</b> 167 WeTravel reviews</span><span><b>★ 4.85</b> 85 BookRetreats reviews</span><span><b>★ 5.0</b> Google</span></div>'

def build_retreats():
    top = [r for r in REVIEWS if r['cat'] == 'vipassana' and len(r['text']) > 160][:6]
    radio = ''.join(f'<label class="pick"><input type="radio" name="d" {"checked" if i == 0 else ""}><span><b>{lbl}</b> 2027</span></label>' for i, (s, e, lbl) in enumerate(DATES))
    body = f'''<section class="page-hero">{img("marquee-dawn", ALT["marquee-dawn"], eager=True)}<div class="wrap"><h1>7-Day Insight Vipassana Silent Retreat in Nature, UK</h1>
<p>Hardwick Estate on the River Thames, Oxfordshire · 40 minutes from London · Five full days of noble silence · Teaching offered for dāna</p>{RATINGS}</div></section>
<nav class="secnav scroll" aria-label="On this page"><div class="wrap"><a href="#overview">Overview</a><a href="#included">What's included</a><a href="#program">Program</a><a href="#food">Food</a><a href="#care">Sauna & therapies</a><a href="#stay">Accommodation</a><a href="#teachers">Teachers</a><a href="#reviews">Reviews</a><a href="#location">Location</a><a href="#faq">FAQ</a></div></nav>
<div class="wrap listing"><div class="main">

<section id="overview" class="sec"><h2>A week to rest, see clearly and find real peace of mind</h2>
<p class="lede">An ancient method, simple in principle and profound in practice. For one week you live in silence by the Thames, your phone switched off, your meals cooked for you, your tired body cared for. All that is left to do is the one thing we rarely make time for: to sit, to walk, and to see the mind clearly.</p>
<div class="hl"><div><b>Five days of silence</b><span>The rare peace of total quiet, with personal teacher interviews.</span></div><div><b>Authentic method</b><span>Mahasi Sayadaw noting, as practised in the monasteries of Burma and Thailand.</span></div><div><b>Yoga every morning</b><span>Prepares the body so you can sit with less pain.</span></div><div><b>Wild nature</b><span>Meadow, ancient oaks, river swimming and a riverside sauna.</span></div><div><b>Ayurvedic food</b><span>Organic, plant-based, much of it grown on the estate.</span></div><div><b>Offered for dāna</b><span>£149 covers food and camping; give what you wish for the teaching.</span></div></div>
<h3>Who this retreat is for</h3><ul class="ticks"><li><b>If your mind never switches off:</b> burnout, stress, worry, or a full head you can't put down.</li><li><b>If you're at a turning point:</b> a big birthday, a loss, a decision, a new chapter.</li><li><b>If you need a break from screens:</b> five days with your phone handed in.</li><li><b>Complete beginners:</b> a clean slate is an advantage. You learn the authentic method step by step, with daily guidance and personal interviews. Experienced meditators are welcome too.</li><li>People who've done a Goenka 10-day course and want to try the noting method, with a live teacher.</li><li>Adults 18+. If you have a mental health condition, please tell us when you book.</li></ul>
<h3>What you may take home</h3><ul class="ticks"><li>A calmer, clearer mind and better concentration</li><li>Less reactivity to stress, worry and difficult emotions</li><li>The skill of stepping back from thoughts instead of drowning in them</li><li>A daily practice you can keep at home</li><li>A deep rest for the nervous system, and a full digital detox</li></ul></section>

<section id="included" class="sec"><h2>What's included</h2><div class="grid two" style="align-items:start"><ul class="ticks">
<li>6 nights on the riverside campsite (ground for your own tent)</li><li>All sitting and walking meditations</li><li>Daily morning yoga</li><li>Dhamma talks and personal teacher interviews</li><li>Ayurvedic plant-based meals and teas</li><li>Riverside sauna on day one and day seven</li><li>Wild swimming in the Thames</li><li>Hot showers, toilets and parking</li><li>Support before and after the retreat</li></ul>
<div><h3 style="margin-top:0">Not included</h3><ul class="ticks muted"><li>Travel to Hardwick</li><li>Tent hire (add at checkout), bedding</li><li>Cutlery and crockery: bring your own</li><li>Yoga mat and sitting blanket (a few to borrow)</li><li>Massage and bodywork with our on-site therapists (bring cash)</li></ul><p class="small"><a href="/articles/what-to-bring-silent-retreat.html">Full packing list →</a></p></div></div></section>

<section id="program" class="sec"><h2>Program</h2>
<ol class="days"><li><b>Day 1</b> Arrive from the afternoon, settle into your tent, orientation and first talk. Noble silence begins in the evening.</li><li><b>Days 2–6</b> Five days of silent practice: sitting and walking meditation, yoga, Dhamma talks, interviews. One new meditation object each day.</li><li><b>Day 7</b> Closing talk on taking the practice home, silence ends, sharing circle, sauna and departure.</li></ol>
<h3>A day on retreat</h3><p class="muted">A bell instead of a clock. The schedule replicates monastery life and is designed for continuity of practice.</p>{timetable_html()}</section>

<section id="food" class="sec split">{img("fb-meal-laughter", ALT["fb-meal-laughter"], sizes="(max-width:820px) 100vw, 480px")}<div><h2>Food</h2><p>Fresh, organic, plant-based meals, cooked by Karen and her kitchen crew on the Ayurvedic principle of food as medicine. Much of the fruit and vegetables come from Tolhurst Organic, the stock-free farm on the estate, often picked the same morning. Expect warming dals and seasonal stews, bright salads, golden porridge at dawn and herbal teas through the day: sattvic food that supports your meditation and leaves you nourished, light and steady.</p><p>Following the tradition, breakfast and lunch are the main meals, and the evening brings a warming drink rather than a full supper, which keeps the mind clear for the evening sit.</p><p class="muted">Tell us about allergies and intolerances when you book.</p></div></section>

<section id="care" class="sec split">{img("sauna-dmitry", ALT["sauna-dmitry"], sizes="(max-width:820px) 100vw, 480px").replace("<img ", "<img style=\"aspect-ratio:4/5\" ")}<div><h2>Sauna, river and caring hands</h2>
<p>Long days of sitting ask a lot of the body, so we built in softness. Our hand-built wood-fired sauna stands close to the river: warm your bones, then step down for a cool dip in the Thames, or simply sit outside wrapped in a towel and listen to the water.</p>
<p>Our trusted therapists stay on site through the retreat, and treatments are held in silence:</p>
<ul class="ticks"><li><b>Lomi lomi and deep tissue massage</b> with Greta, long flowing strokes that ease the back and shoulders</li><li><b>Thai yoga massage</b> with Bara, gentle stretching and pressure along the energy lines</li><li><b>Reiki</b> with Lara, for calming and centring when the practice feels intense</li><li><b>Pravilo</b> with Tibi, suspension stretching that decompresses a stiff spine</li></ul>
<p class="muted small">About £35 for 30 minutes or £70 for an hour, booked when you arrive and paid to the therapist. Bring cash, as your phone will be switched off.</p></div></section>

<section id="stay" class="sec"><h2>Accommodation</h2><p>You stay in our secluded riverside campsite, with hot showers, composting toilets and fresh running water, a short walk from the meditation marquee. Tents are single occupancy, so everyone has their own space for silence. Nights by the river can be cool even in summer, so bring a hot water bottle and more warm socks than you think you need.</p>
<div class="pk"><div><b>Your own tent, campervan or caravan</b><span>Included in the £149</span></div><div><b>Private pre-erected tent</b><span>Small or medium, add at checkout</span></div><div><b>Canvas bell tent · Essential comfort</b><span>Add at checkout</span></div><div><b>Deluxe glamping bell tent</b><span>With a framed bed, add at checkout</span></div></div>
<p class="small muted">No dogs, please. The retreat is free from alcohol, drugs and intoxicants.</p></section>

<section id="teachers" class="sec"><h2>Your teachers</h2><div class="team">
<div>{img("dmitry-teaching", ALT["dmitry-teaching"], sizes="200px")}<b>Dmitry Glazkov</b><span>Vipassana teacher in the Mahasi tradition, yoga and Ayurveda. Sits a month-long retreat every year and teaches at Indriya in Thailand. <a href="/teacher/">More</a></span></div>
<div>{img("group-hills", ALT["group-hills"], sizes="200px")}<b>Karen Buckland</b><span>Co-founder of Sadhama and plant-based chef with 15+ years of experience, cooking Ayurvedically.</span></div>
<div>{img("morning-stretch", ALT["morning-stretch"], sizes="200px")}<b>Bara Cechova</b><span>Leads the morning yoga, breathwork and bodywork.</span></div></div></section>

<section id="reviews" class="sec"><h2>What guests say</h2><div class="rv-top"><div class="big"><b>4.85</b><span>{stars(5)}</span><span class="muted small">85 reviews on BookRetreats</span></div>{scores_html()}</div>
<div class="rv-grid">{"".join(review_card(r) for r in top)}</div><p><a class="btn ghost" href="/testimonials/">Read all {len(REVIEWS)} reviews</a></p></section>

<section id="location" class="sec"><h2>Location and travel</h2><p>Hardwick Estate, Whitchurch-on-Thames, RG8 7RA: a community-run rural estate in the Chilterns, with ancient oaks, wildflower meadows and a clean stretch of the upper Thames. Easy to reach, yet deeply held in wild nature.</p>
<ul class="ticks"><li><b>Train:</b> about 40 minutes from London Paddington to Reading or Pangbourne, then a short taxi</li><li><b>Car:</b> 20 minutes from Junction 12 of the M4, parking on site</li><li><b>Air:</b> London Heathrow is about an hour by car</li></ul></section>

<section id="faq" class="sec"><h2>FAQ</h2>{faq_html(FAQ + RETREAT_FAQ)}</section>
</div>

<aside class="bookbox" aria-label="Book this retreat"><div class="bb-in"><span class="muted small">7 days / 6 nights</span><div class="price">£149 <small>+ dāna</small></div><span class="small muted">Organisational fee · deposit £75</span>
<fieldset><legend class="small">Choose your dates</legend>{radio}</fieldset>{book_btn("Book now")}
<ul class="small bb-list"><li>Secure your place with a £75 deposit</li><li>Balance due about a month before</li><li>Tents and bell tents can be added at checkout</li><li>Reduced-cost seva places on application</li></ul><p class="small muted" style="margin:0">Questions? info@sadhama.com</p></div></aside>
</div>

<section class="band mist"><div class="wrap"><h2>More silent retreats with Dmitry</h2><div class="grid two" style="align-items:start">
<div class="date-card"><span class="yr">Thailand · 7 days</span><span class="when">25–31 January 2027</span><p style="margin:0"><b>Insight Vipassana Silent Retreat, Koh Phangan.</b> The same Mahasi noting practice, at the Indriya Retreat Centre by the sea on Koh Phangan, Thailand. From $350 (deposit $100).</p>{book_btn("Book Thailand", uuid=WT["thai"])}</div>
<div class="date-card"><span class="yr">Hardwick · 4 days of gentle silence</span><span class="when">27–30 August 2027</span><p style="margin:0"><b>Practice of Peace.</b> Gentle meditation, yoga, forest bathing, sauna and plenty of time for yourself over the August bank holiday. A soft first step towards a 7 or 10-day vipassana.</p>{book_btn("Book Practice of Peace", uuid=WT["peace"])}</div>
</div></div></section>'''
    thai = event_ld('2027-01-25', '2027-01-31', 'Thailand January')
    thai.update(name='7-Day Insight Vipassana Silent Meditation Retreat, Koh Phangan, Thailand (January 2027)', location={"@type": "Place", "name": "Indriya Retreat Centre", "address": {"@type": "PostalAddress", "streetAddress": "66/9 Moo 5", "addressLocality": "Koh Phangan", "addressRegion": "Surat Thani", "postalCode": "84280", "addressCountry": "TH"}},
                offers={"@type": "Offer", "price": "350", "priceCurrency": "USD", "url": "https://www.wetravel.com/trips/thailand-vipassana-silent-meditation-retreat-in-koh-phangan-sadhama-rewild-retreats-7915926147", "availability": "https://schema.org/InStock"})
    peace = event_ld('2027-08-27', '2027-08-30', 'August')
    peace.update(name='Practice of Peace: 4-Day Gentle Silent Retreat (August 2027)', description='Four days of gentle silence at Hardwick Estate: simple meditation, yoga, forest bathing, riverside sauna and Ayurvedic food.')
    peace.pop('offers', None)
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ + RETREAT_FAQ]}
    ld = [faq_ld] + [event_ld(*d) for d in DATES] + [thai, peace]
    page('retreats.html', '7-Day Silent Vipassana Retreat UK 2027: Dates & Booking', 'Book a 7-day silent Insight Vipassana retreat at Hardwick Estate, Oxfordshire, in 2027: 31 May, 26 July or 30 August. £149 organisational fee, teaching for dāna. Rated 4.9 by 167 guests.', body, 'retreats.html', 'marquee-dawn', ld)

RETREAT_FAQ = [
 ('Can I use my phone?', 'Phones are switched off and put away for the whole retreat. Give your family the retreat contact details for emergencies. Most people find this the greatest gift of the week.'),
 ('Can I share a tent with my partner or a friend?', 'No. On this retreat tents are single occupancy, so each person has their own space for silence and practice.'),
 ('What if I arrive late or need to leave early?', 'Please plan to stay for the whole retreat: the technique is taught step by step and the schedule is designed for continuity. If something unavoidable comes up, tell us before you book.'),
 ('Is a silent retreat suitable if I have mental health difficulties?', 'Often yes, but not always. If you have a mental health condition, or are going through a crisis, please tell us when you book so we can talk it through first.'),
 ('How much should I give as dāna?', 'Whatever you feel moved to give, based on what the week gave you and what you can afford. There is no fixed amount and nobody checks.'),
]

def build_testimonials():
    cats = [('all', 'All'), ('vipassana', 'Insight Vipassana'), ('peace', 'Practice of Peace'), ('meditation', 'Other retreats')]
    chips = ''.join(f'<button type="button" class="chip{" on" if k == "all" else ""}" data-f="{k}">{t}</button>' for k, t in cats)
    body = f'''<section class="page-hero">{img("fb-group-marquee", ALT["fb-group-marquee"], eager=True)}<div class="wrap"><h1>Reviews from our silent retreats</h1><p>{len(REVIEWS)} guests in their own words, about vipassana and meditation with Dmitry and Karen.</p>{RATINGS}</div></section>
<section class="band mist"><div class="wrap"><h2>What guests mention most</h2><p class="lede" style="margin-bottom:22px">A quick summary, if you would rather not read every review.</p>{themes_html()}</div></section>
<section class="band"><div class="wrap"><div class="rv-top"><div class="big"><b>4.85</b><span>{stars(5)}</span><span class="muted small">BookRetreats, Insight Vipassana UK</span></div>{scores_html()}</div>
<div class="chips" role="group" aria-label="Filter reviews">{chips}</div><div class="rv-grid" id="rvs">{"".join(review_card(r, False) for r in REVIEWS)}</div>
<p class="muted small" style="margin-top:24px">All Vipassana, Practice of Peace and meditation-related reviews rated 4 or 5 stars on WeTravel, BookRetreats and Google, shown with first name and initial.</p>
<div class="cta-box"><p>Ready to experience it yourself? Seven days by the Thames, 2027.</p>{book_btn()}</div></div></section>'''
    page('testimonials.html', 'Vipassana Retreat Reviews & Testimonials | Vipassana Retreat UK', f'Read {len(REVIEWS)} reviews of our silent Insight Vipassana retreats in Oxfordshire: rated 4.9 from 167 WeTravel reviews and 4.85 on BookRetreats.', body, 'testimonials.html', 'group-panorama',
         scripts="<script>{const g=document.getElementById('rvs');document.querySelectorAll('.chip[data-f]').forEach(c=>c.onclick=()=>{document.querySelectorAll('.chip[data-f]').forEach(x=>x.classList.toggle('on',x===c));const f=c.dataset.f;g.querySelectorAll('.rv').forEach(r=>r.hidden=!(f==='all'||r.dataset.cat===f));});}</script>")

GALLERY = []  # filled at build time from img/gallery-*.jpg plus the core photos
def build_gallery():
    names = sorted(p.stem for p in (OUT / 'img').glob('*.jpg') if not p.stem.endswith('-sm'))
    skip = {'group-meadow'}  # near-identical to group-hills
    pics = list(dict.fromkeys([n for n in names if n.startswith('fb-')] + [n for n in ALT if n in names]))
    pics = [n for n in pics if n not in skip]
    tiles = ''.join(f'<a class="tile" href="img/{n}.jpg" data-i="{i}">{img(n, ALT.get(n, "Insight Vipassana retreat at Hardwick Estate"), sizes="(max-width:600px) 50vw, 300px")}</a>' for i, n in enumerate(pics))
    body = f'''<section class="page-hero">{img("oak-marquee-dawn", ALT["oak-marquee-dawn"], eager=True)}<div class="wrap"><h1>Gallery</h1><p>Dawn mist, the old oak, the marquee in the meadow, and the people who sat with us.</p></div></section>
<section class="band"><div class="wrap"><div class="gal" id="gal">{tiles}</div></div></section>
<div class="lb" id="lb" hidden><button type="button" class="lb-x" aria-label="Close">×</button><button type="button" class="lb-p" aria-label="Previous photo">‹</button><img alt=""><button type="button" class="lb-n" aria-label="Next photo">›</button></div>
<section class="band mist"><div class="wrap cta-box" style="margin:0 auto;max-width:1100px"><p>Come and sit in the meadow with us in 2027.</p>{book_btn()}</div></section>'''
    js = """<script>{const lb=document.getElementById('lb'),im=lb.querySelector('img'),t=[...document.querySelectorAll('#gal .tile')];let i=0;
const show=k=>{i=(k+t.length)%t.length;im.src=t[i].getAttribute('href');im.alt=t[i].querySelector('img').alt;lb.hidden=false;};
t.forEach((a,k)=>a.addEventListener('click',e=>{e.preventDefault();show(k);}));
lb.querySelector('.lb-x').onclick=()=>lb.hidden=true;lb.querySelector('.lb-p').onclick=()=>show(i-1);lb.querySelector('.lb-n').onclick=()=>show(i+1);
lb.addEventListener('click',e=>{if(e.target===lb)lb.hidden=true;});document.addEventListener('keydown',e=>{if(lb.hidden)return;if(e.key==='Escape')lb.hidden=true;if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1);});}</script>"""
    page('gallery.html', 'Photo Gallery: Silent Vipassana Retreat on the Thames | Vipassana Retreat UK', 'Photos from our silent Insight Vipassana retreats at Hardwick Estate, Oxfordshire: dawn meditation in the meadow, the old oak, the river and the retreat community.', body, 'gallery.html', 'oak-marquee-dawn', scripts=js)


# ---------- teacher ----------
def build_teacher():
    body = f'''<section class="page-hero">{img("group-hills", ALT["group-hills"], eager=True)}<div class="wrap"><h1>Dmitry Glazkov, vipassana teacher</h1><p>“I don't offer my personal experience; I give tools so that your unique personality can see its own inner wisdom.”</p></div></section>
<section class="band"><div class="wrap split"><div class="prose" style="font-size:19px">
<p>Dmitry teaches Insight Vipassana in the tradition of Mahasi Sayadaw, alongside yoga and Ayurveda. He has practised for more than sixteen years and taught for over eleven, and every year he sits a month-long or 21-day intensive retreat himself.</p>
<p>For years he assisted a Buddhist monk teacher at the Indriya Retreat Centre on Koh Phangan, Thailand, and now teaches retreats there. In England he founded <a href="https://sadhama.com" rel="noopener">Sadhama</a> with his wife, Karen Buckland, on the community-led Hardwick Estate in South Oxfordshire. Together they have run more than 35 retreats for over 1,700 participants.</p>
<p>Born in the Tian Shan mountains on the Kazakhstan–China border, Dmitry studied in Russia and Prague, walked 2,000 km to Santiago, and trained in Kundalini and Hatha yoga and in Ayurveda before giving his life to the Dhamma. For five years he taught yoga and meditation to people experiencing homelessness with Crisis Skylight.</p>
<p>Guests describe his teaching as humour and wisdom together: clear, grounded, compassionate, and lived. He loves the original suttas. As he says, “If you don't study the diamond itself, how are you going to know what diamond is?”</p>
<p>In the Dhamma, he says, he is more of a friend than a guru: someone a few steps ahead, helping you with yours.</p></div>
{img("sauna-dmitry", ALT["sauna-dmitry"], sizes="(max-width:820px) 100vw, 560px").replace("<img ", "<img style=\"aspect-ratio:3/4\" ")}</div></section>
<section class="band mist"><div class="wrap split">{img("riverside-talk", ALT["riverside-talk"], sizes="(max-width:820px) 100vw, 600px")}<div><h2>Karen Buckland</h2>
<p class="lede">Co-founder of Sadhama and the heart of the kitchen.</p><p>Karen is a plant-based chef with more than fifteen years of experience in vegan fine dining and festival catering. She cooks according to Ayurvedic principles, food as medicine, using organic produce grown on the estate. Guests regularly call the food "another level".</p></div></div></section>
<section class="band"><div class="wrap cta-box" style="max-width:1100px;margin:0 auto"><p>Sit with Dmitry by the Thames in 2027.</p>{book_btn()}</div></section>'''
    ld = [{"@context": "https://schema.org", "@type": "Person", "name": "Dmitry Glazkov", "jobTitle": "Vipassana meditation teacher", "worksFor": ORG, "url": DOMAIN + "/teacher.html", "image": DOMAIN + "/img/sauna-dmitry.jpg"}]
    page('teacher.html', 'Dmitry Glazkov, Vipassana Teacher | Vipassana Retreat UK', 'Meet Dmitry Glazkov, Insight Vipassana teacher in the Mahasi tradition, who leads silent retreats at Hardwick Estate, Oxfordshire, and in Thailand.', body, 'teacher.html', 'sauna-dmitry', ld)

# ---------- ask ananda ----------
def build_ananda():
    data = [{k: e[k] for k in ('id', 'q', 'k', 'a', 'refs')} for e in QA]
    for d in data: d['refs'] = [[l, rel(h, 0)] for l, h in d['refs']]
    (OUT / 'assets' / 'ananda-data.json').write_text(json.dumps(data, ensure_ascii=False))
    starters = ['I keep falling asleep when I meditate. What can I do?', 'How do I deal with knee or back pain while sitting?', 'My mind keeps wandering. Am I doing it wrong?', 'What does "note, know, let go" mean?', 'Can a beginner come on a silent retreat?', 'How do I keep practising after the retreat?']
    chips = ''.join(f'<button type="button" class="chip" data-q="{html.escape(s)}">{html.escape(s)}</button>' for s in starters)
    body = f'''<section class="band" style="padding-top:clamp(28px,4vw,48px)"><div class="wrap ananda">
<div class="ananda-head"><div><h1>Ask Ananda</h1><p class="lede">A Dhamma assistant that answers from Dmitry's retreat talks, in his words. Ask about the practice, the teaching or the retreat.</p></div></div>
<div class="chat" id="chat" aria-live="polite"><div class="msg bot"><div class="who">Ananda</div><div class="bubble"><p>Welcome. Arrive for a moment. Hearing is occurring… Good.</p><p>What would you like to ask about the practice?</p></div></div></div>
<form class="ask" id="ask" autocomplete="off"><label for="q" class="sr">Your question</label><input id="q" name="q" type="text" placeholder="Ask about meditation, the Dhamma or the retreat…" maxlength="300" required><button class="btn book" type="submit">Ask</button></form>
<div class="chips" id="chips">{chips}</div>
<p class="muted small">Ananda chooses the closest answer from a curated collection of Dmitry's teachings. It is not a live AI and can't discuss your personal situation in depth. For anything about your health, please speak to a professional. For the retreat, write to info@sadhama.com.</p>
</div></section>'''
    head = '''<style>.ananda{max-width:820px}.chat{display:flex;flex-direction:column;gap:16px;margin:24px 0 18px;min-height:220px}
.msg .who{font:600 13px var(--sans);color:var(--soft);margin:0 0 4px 4px}.msg .bubble{background:var(--paper);border:1px solid var(--line);border-radius:18px 18px 18px 6px;padding:16px 18px;font-family:var(--serif);font-size:19px;line-height:1.55;max-width:100%}
.msg .bubble p:last-child{margin-bottom:0}.msg.me{align-self:flex-end;max-width:85%}.msg.me .bubble{background:var(--oak);color:light-dark(#fff,#0e1714);border:0;border-radius:18px 18px 6px 18px;font-family:var(--sans);font-size:16px}.msg.me .who{text-align:right}
.refs{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}.refs a{font:600 14px var(--sans);background:var(--mist);border-radius:999px;padding:8px 14px;text-decoration:none;min-height:36px;display:inline-flex;align-items:center}
.ask{display:flex;gap:10px;position:sticky;bottom:12px;background:var(--bg);padding:8px 0}.ask input{flex:1;min-height:52px;border-radius:999px;border:1.5px solid var(--line);background:var(--paper);color:var(--ink);font:16px var(--sans);padding:0 20px}
.ask input:focus{border-color:var(--oak);outline:none;box-shadow:0 0 0 3px color-mix(in srgb,var(--oak) 25%,transparent)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 18px}.chip{font:15px var(--sans);border:1px solid var(--line);background:var(--paper);color:var(--ink);border-radius:999px;padding:10px 14px;cursor:pointer;min-height:44px;text-align:left}.chip:hover{border-color:var(--oak);color:var(--oak)}
.also{margin-top:14px;font:14px var(--sans);color:var(--soft)}.also .chip{font-size:14px;padding:8px 12px;min-height:40px;margin:6px 6px 0 0}
.typing span{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--soft);margin-right:4px;animation:b 1s infinite}.typing span:nth-child(2){animation-delay:.15s}.typing span:nth-child(3){animation-delay:.3s}@keyframes b{50%{opacity:.25}}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
@media(max-width:600px){.msg .bubble{font-size:17px}}</style>'''
    page('ask-ananda.html', 'Ask Ananda: Vipassana & Dhamma Questions Answered | Vipassana Retreat UK', 'Ask Ananda, a Dhamma assistant answering meditation questions from vipassana teacher Dmitry Glazkov\'s retreat talks: sleepiness, pain, noting, emotions, retreats.', body, 'ask-ananda.html', 'riverside-talk', scripts='<script src="assets/ananda.js"></script>', extra_head=head)

# ---------- library ----------
def build_library():
    cat = json.loads((OUT / 'library' / 'catalog.json').read_text())
    for c in cat: c['epub'] = (OUT / 'downloads' / (c['slug'] + '.epub')).exists()
    (OUT / 'library' / 'catalog.json').write_text(json.dumps(cat, ensure_ascii=False, indent=1))
    cards = ''.join(f'''<article class="card book"><div class="body"><span class="muted small">{c["en"]} · {c["suttas"]} texts</span><h3>{c["title"]}</h3><p>{html.escape(c["blurb"])}</p>
<div class="book-actions"><a class="btn ghost" href="read.html#{c["slug"]}">Read online</a><a class="btn ghost" href="read.html#{c["slug"]}" data-listen="1">▶ Listen</a></div>
<p class="small" style="margin-top:6px">Download: {(chr(60)+'a href="downloads/'+c["slug"]+'.epub" download>EPUB</a> · ') if c.get("epub") else ""}<a href="downloads/{c["slug"]}.txt" download>Text</a></p></div></article>''' for c in cat)
    body = f'''<section class="page-hero">{img("lily-pond-mist", ALT["lily-pond-mist"], eager=True)}<div class="wrap"><h1>The Dhamma library</h1><p>Eight collections of the Buddha's discourses. Read online, download, or listen aloud.</p></div></section>
<section class="band"><div class="wrap"><p class="lede" style="margin-bottom:28px">These are the original teachings from the Pāḷi Canon that Dmitry draws on in his Dhamma talks, in Bhikkhu Sujato's clear modern translation, which he dedicated to the public domain. Free for everyone, forever.</p>
<div class="grid">{cards}</div>
<p class="muted small" style="margin-top:24px">Translations by Bhikkhu Sujato, from <a href="https://suttacentral.net" rel="noopener">SuttaCentral</a>, CC0 public domain. "Listen" reads aloud in natural voices that run in your browser and keep going with your phone locked. Your place is remembered. Want to sit, not read? Try the <a href="timer.html">meditation timer</a>.</p></div></section>'''
    head = '<style>.book-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.book-actions .btn{min-height:44px;padding:0 16px;font-size:15px}</style>'
    ld = [{"@context": "https://schema.org", "@type": "CollectionPage", "name": "Dhamma library", "hasPart": [{"@type": "Book", "name": f"{c['title']} ({c['en']})", "translator": {"@type": "Person", "name": "Bhikkhu Sujato"}, "license": "https://creativecommons.org/publicdomain/zero/1.0/", "url": f"{DOMAIN}/read.html#{c['slug']}"} for c in cat]}]
    page('library.html', 'Free Dhamma Library: Read & Listen to the Suttas | Vipassana Retreat UK', 'Read, download or listen to eight collections of the Buddha\'s discourses: Dhammapada, Saṁyutta and Aṅguttara Nikāya, Sutta Nipāta, Udāna, Itivuttaka, Thera- and Therīgāthā.', body, 'library.html', 'lily-pond-mist', ld, extra_head=head)
    reader_head = '''<style>.reader{display:grid;grid-template-columns:300px minmax(0,1fr);gap:32px;align-items:start}
.toc{position:sticky;top:84px;max-height:calc(100vh - 98px);overflow:auto;background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:14px}
.toc select{width:100%;min-height:44px;font:15px var(--sans);border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink);padding:0 10px;margin-bottom:10px}
.toc ol{list-style:none;margin:0;padding:0;font-size:14px}.toc li a{display:block;padding:7px 8px;border-radius:8px;text-decoration:none;color:var(--ink)}.toc li a:hover,.toc li a.on{background:var(--mist);color:var(--oak)}
.tools{position:sticky;top:72px;z-index:5;display:flex;flex-wrap:wrap;gap:8px;align-items:center;background:var(--bg);padding:10px 0;border-bottom:1px solid var(--line);margin-bottom:18px}
.tools button,.tools select{min-height:44px;border-radius:999px;border:1px solid var(--line);background:var(--paper);color:var(--ink);font:600 14px var(--sans);padding:0 14px;cursor:pointer}
.tools .play{background:var(--sun);color:#fff;border-color:var(--sun)}.tools select{font-weight:400;max-width:200px}
.text{font-family:var(--serif);font-size:var(--fs,20px);line-height:1.65;max-width:70ch}.text header ul{list-style:none;padding:0;margin:2em 0 0;color:var(--soft);font:14px var(--sans)}.text header li{display:inline}.text header li+li::before{content:" · "}
.text h1{font-size:1.5em;margin:.3em 0 .6em}.text h2{font-size:1.25em}.text .verse-line{display:block}.text blockquote{margin:1em 0 1em 1em}.text section{scroll-margin-top:130px}
.text .reading{background:color-mix(in srgb,var(--sun) 18%,transparent);border-radius:6px;box-shadow:0 0 0 6px color-mix(in srgb,var(--sun) 18%,transparent)}
.text p,.text li,.text h1,.text h2{cursor:default}.listening .text p,.listening .text h1{cursor:pointer}
.status{font:14px var(--sans);color:var(--soft)}.dl{font:14px var(--sans)}.tools select#voice{max-width:280px}
.resume{display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between;background:var(--mist);border-radius:14px;padding:14px 18px;margin:0 0 18px;font:15px var(--sans)}
@media(max-width:900px){.reader{grid-template-columns:minmax(0,1fr)}.toc{position:static;max-height:300px}}</style>'''
    rbody = '''<section class="band" style="padding-top:28px"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/library/">Library</a> › <span id="crumb">Reader</span></nav>
<h1 id="bookTitle">Dhamma library</h1><p class="muted" id="bookSub"></p>
<div class="reader"><aside class="toc" aria-label="Contents"><label class="small muted" for="chapter">Chapter</label><select id="chapter"></select><ol id="suttas"></ol></aside>
<div><div class="tools" role="toolbar" aria-label="Reading tools"><button class="play" id="play" type="button">▶ Listen</button><button id="stop" type="button">■ Stop</button>
<select id="rate" aria-label="Reading speed"><option value=".75">Slow</option><option value=".9" selected>Gentle</option><option value="1">Normal</option><option value="1.15">Faster</option></select>
<select id="voice" aria-label="Voice"></select><button id="sample" type="button" aria-label="Hear this voice">Try voice</button><button id="smaller" type="button" aria-label="Smaller text">A−</button><button id="bigger" type="button" aria-label="Larger text">A+</button>
<span class="dl" id="dl"></span><span class="status" id="status"></span></div>
<p class="small muted" id="tts-note" style="margin:6px 0 14px"></p>
<div class="resume" id="resume" hidden><span>Welcome back. Carry on from <strong data-where></strong>?</span><button type="button" class="btn">▶ Continue listening</button></div>
<article class="text" id="text"><p class="muted">Loading…</p></article>
<p class="muted small" style="margin-top:32px">Translated by Bhikkhu Sujato (SuttaCentral), public domain. Natural voices: Piper (Rhasspy) running in your browser.</p></div></div></div></section>
<audio id="player" playsinline preload="auto"></audio>
<div class="mini" id="mini" hidden role="region" aria-label="Now playing"><div class="mini-info"><strong id="mini-title">Dhamma library</strong><span id="mini-status"></span></div>
<div class="mini-btns"><button id="mini-prev" type="button" aria-label="Previous text">⏮</button><button id="mini-play" class="mini-main" type="button" aria-label="Pause">❚❚</button><button id="mini-next" type="button" aria-label="Next text">⏭</button><button id="mini-stop" type="button" aria-label="Stop">■</button></div></div>'''
    page('read.html', 'Read the Suttas Online | Vipassana Retreat UK', 'Read and listen to the Buddha\'s discourses online in Bhikkhu Sujato\'s public-domain translation.', rbody, 'library.html', 'lily-pond-mist', scripts='<script src="assets/reader.js"></script>', extra_head=reader_head)

# ---------- meditation timer ----------
GUIDED = []   # e.g. [{"id": "metta-hardwick", "title": "Loving-kindness with Dmitry", "file": "assets/guided/metta-hardwick.mp3", "dur": 1534.272}]
TIMER_HEAD = '''<style>
.mt{max-width:760px;margin:0 auto}.mt-card{scroll-margin-top:90px;background:var(--paper);border:1px solid var(--line);border-radius:22px;padding:clamp(20px,4vw,36px);box-shadow:0 10px 30px rgba(20,40,30,.06)}
.mt-row{margin:0 0 22px}.mt-row>label,.mt-row>.mt-lbl{display:block;font:600 14px var(--sans);letter-spacing:.02em;margin:0 0 10px;color:var(--soft)}
.mt-chips{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.mt-chip{min-height:44px;min-width:56px;padding:0 16px;border-radius:999px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:600 15px var(--sans);cursor:pointer}
.mt-chip[aria-pressed=true]{background:#1f3a2e;border-color:#1f3a2e;color:#fff}
.mt-mode .mt-chip{flex:1;min-height:54px;font-size:16px}
#mt-custom{width:90px;min-height:44px;border-radius:999px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:15px var(--sans);padding:0 14px}
.mt-go{width:100%;min-height:58px;font-size:18px;margin-top:6px}.mt-summary{text-align:center;color:var(--soft);font:15px var(--sans);margin:12px 0 0}
.mt-live{text-align:center}.mt-ring{--p:0;width:min(300px,78vw);aspect-ratio:1;margin:8px auto 22px;border-radius:50%;display:grid;place-items:center;
  background:radial-gradient(closest-side,var(--paper) 86%,transparent 87%),conic-gradient(var(--sun) calc(var(--p)*1%),var(--mist) 0)}
.mt-clock{font:600 clamp(44px,12vw,68px)/1 var(--sans);font-variant-numeric:tabular-nums;letter-spacing:-.02em}.mt-phase{font:15px var(--sans);color:var(--soft);margin-top:8px}
.mt-live .mt-chips{justify-content:center}.mt-done{background:var(--mist);border-radius:16px;padding:16px 20px;margin:0 0 22px;font-size:18px}
.mt-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:22px 0 0}.mt-stats div{background:var(--mist);border-radius:14px;padding:12px;text-align:center}
.mt-stats strong{display:block;font:600 24px var(--sans)}.mt-stats span{font:13px var(--sans);color:var(--soft)}
.mt select{min-height:44px;border-radius:12px;border:1px solid var(--line);background:var(--bg);color:var(--ink);font:15px var(--sans);padding:0 12px;max-width:100%}
@media(max-width:560px){.mt-stats{grid-template-columns:repeat(2,1fr)}}</style>'''

def build_timer():
    def chips(attr, vals, fmt):
        return ''.join(f'<button type="button" class="mt-chip" data-{attr}="{v}" aria-pressed="false">{fmt(v)}</button>' for v in vals)
    guided_pick = ('<label for="mt-guided">Recording</label><select id="mt-guided"></select>' if GUIDED
                   else '<p class="small muted" style="margin:0">Dmitry’s recording is being added. Choose silent sitting for now.</p>')
    body = (
'<section class="band" style="padding-top:clamp(28px,4vw,48px)"><div class="wrap mt">'
'<h1>Meditation timer with a Burmese gong</h1>'
'<p class="lede">Sit at home the way we sit at Hardwick: one deep gong to begin, quiet in between, three gongs to close. Free, no app, nothing to sign up for.</p>'
'<div class="mt-card">'
'<div class="mt-done" id="mt-done" hidden><p id="mt-done-msg" style="margin:0"></p></div>'
'<div id="mt-form">'
'<div class="mt-row mt-mode"><div class="mt-chips"><button type="button" class="mt-chip" data-mode="silent" aria-pressed="true">Silent sitting</button><button type="button" class="mt-chip" data-mode="guided" aria-pressed="false">Guided loving-kindness</button></div></div>'
'<div class="mt-silent">'
f'<div class="mt-row"><span class="mt-lbl">How long</span><div class="mt-chips">{chips("min", [5,10,15,20,30,45,60], lambda v: f"{v} min")}<label class="sr" for="mt-custom">Custom minutes</label><input id="mt-custom" type="number" min="1" max="240" inputmode="numeric" placeholder="Other"></div></div>'
f'<div class="mt-row"><span class="mt-lbl">Soft gong along the way</span><div class="mt-chips">{chips("interval", [0,5,10,15], lambda v: "None" if not v else f"Every {v} min")}</div></div>'
f'<div class="mt-row"><span class="mt-lbl">To begin</span><div class="mt-chips">{chips("start", [1,3], lambda v: "One gong" if v == 1 else "Three gongs")}</div></div>'
'</div>'
'<div class="mt-guided" hidden>'
'<div class="mt-row"><p style="margin:0 0 12px">The evening mettā we sit together on retreat, recorded at Hardwick as the sun goes down. Dmitry guides you to place the warmth of the sun in your heart and shine it out: to yourself, to the people you love, and to all beings.</p>'
f'{guided_pick}</div>'
f'<div class="mt-row"><span class="mt-lbl">Then stay in silence</span><div class="mt-chips">{chips("after", [0,5,10,15], lambda v: "No" if not v else f"{v} min")}</div></div>'
'</div>'
f'<div class="mt-row"><span class="mt-lbl">Settle in first</span><div class="mt-chips">{chips("prep", [0,10,30,60], lambda v: "Start now" if not v else (f"{v} s" if v < 60 else "1 min"))}</div></div>'
'<button class="btn book mt-go" id="mt-go" type="button">Begin</button>'
'<p class="mt-summary" id="mt-summary"></p>'
'<p class="small muted" style="text-align:center;margin:10px 0 0"><button type="button" id="mt-sample" class="mt-chip" style="min-height:36px">Hear the gong</button></p>'
'</div>'
'<div class="mt-live" id="mt-live" hidden><div class="mt-ring" id="mt-ring"><div><div class="mt-clock" id="mt-clock">0:00</div><div class="mt-phase" id="mt-phase">Settling in</div></div></div>'
'<div class="mt-chips"><button type="button" class="mt-chip" id="mt-pause">❚❚ Pause</button><button type="button" class="mt-chip" id="mt-end">End</button></div>'
'<p class="small muted" style="margin:18px 0 0">You can lock your phone. The gongs will still ring, and the lock screen lets you pause or end.</p></div>'
'<div class="mt-stats" id="mt-stats" hidden></div>'
'</div>'
'<audio id="mt-audio" playsinline preload="auto"></audio>'
'<div class="prose" style="margin-top:40px">'
'<h2>How to sit with the timer</h2>'
'<p>Find a seat that keeps your back upright without strain. A cushion, a bench or a chair are all fine; comfort helps you stay. Close your eyes and let the first gong ring all the way out.</p>'
'<p>Then rest your attention on the rising and falling of the belly. When the mind wanders, and it will, simply note it: “thinking, thinking”. Then come back. No fighting, no judging. That coming back is the practice.</p>'
'<p>Begin with fifteen or twenty minutes. Sitting every day does more than one heroic hour once a week. When the closing gongs sound, stay a moment longer. Notice how you feel before you get up.</p>'
'<p>New to the method? Read <a href="articles/noting-meditation-rising-falling.html">noting meditation: rising and falling</a>, or try <a href="articles/walking-meditation-how-to.html">walking meditation</a> between sits. And when you are ready to go deeper, come and <a href="retreats.html">sit with us for seven days by the Thames</a>.</p>'
'<p class="small muted">Your sits are counted on this device only; nothing is sent anywhere. The gong is a deep, slow Burmese-style gong, like those that call meditators to the hall in Myanmar.</p>'
'</div></div></section>'
'<div class="mini" id="mini" hidden role="region" aria-label="Meditation in progress"><div class="mini-info"><strong id="mini-title">Meditation</strong><span id="mini-status"></span></div>'
'<div class="mini-btns"><button id="mini-play" class="mini-main" type="button" aria-label="Pause">❚❚</button><button id="mini-stop" type="button" aria-label="End">■</button></div></div>')
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "Meditation timer with Burmese gong", "url": DOMAIN + "/timer.html",
           "applicationCategory": "HealthApplication", "operatingSystem": "Any (web browser)", "offers": {"@type": "Offer", "price": "0", "priceCurrency": "GBP"},
           "description": "Free online meditation timer with a deep Burmese gong, interval gongs, silent or guided loving-kindness sessions. Works with the screen off.", "publisher": ORG}]
    page('timer.html', 'Free Meditation Timer with Burmese Gong | Vipassana Retreat UK',
         'A free online meditation timer with a deep Burmese gong: choose your time, add soft interval gongs, or sit with a guided loving-kindness meditation. Works with your phone locked.',
         body, 'timer.html', 'fb-golden-sunrise', ld, scripts=f'<script>window.MT_GUIDED={json.dumps(GUIDED)};</script><script src="assets/timer.js"></script>', extra_head=TIMER_HEAD)

def build_seo(arts):
    urls = ['', 'retreats.html', 'testimonials.html', 'gallery.html', 'articles.html', 'ask-ananda.html', 'library.html', 'teacher.html', 'read.html', 'timer.html'] + [f'articles/{a["slug"]}.html' for a in arts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{DOMAIN}/{u}</loc><lastmod>2026-11-27</lastmod></url>\n' for u in urls) + '</urlset>\n'
    (OUT / 'sitemap.xml').write_text(sm)
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n')

if __name__ == '__main__':
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    for f in ('site.css', 'site.js', 'ananda.js', 'reader.js', 'tts-worker.js', 'timer.js'):
        shutil.copy(SRC / f, OUT / 'assets' / f)
    arts = load_articles()
    build_home(arts); build_retreats(); build_testimonials(); build_gallery(); build_teacher(); build_articles(arts); build_ananda(); build_library(); build_timer(); build_seo(arts)
    # Cloudflare Pages serves /page for /page.html (308): use the clean form in absolute URLs (canonical, og, JSON-LD, sitemap)
    clean = re.compile(r'(https://vipassanaretreat\.com/[^"\'<>\s]*?)\.html')
    for f in list(OUT.rglob('*.html')) + [OUT / 'sitemap.xml']:
        t = f.read_text(encoding='utf-8'); n = clean.sub(r'\1', t)
        if n != t: f.write_text(n, encoding='utf-8')
    print('built', len(arts), 'articles')
