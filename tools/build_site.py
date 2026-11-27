#!/usr/bin/env python3
"""Generate vipassanaretreat.com as a static site into out/."""
import json, re, html, sys, shutil
from pathlib import Path
import markdown

ROOT = Path(__file__).parent.parent; OUT = ROOT / (sys.argv[1] if len(sys.argv) > 1 else 'out'); SRC = ROOT / 'src'; CONTENT = ROOT / 'content'
DOMAIN = 'https://vipassanaretreat.com'
sys.path.insert(0, str(CONTENT)); from ananda_qa import QA

WT = dict(env='https://www.wetravel.com', uid='202227', vip='68342383', thai='7915926147', peace='3370709561')
CHECKOUT = f"https://www.wetravel.com/checkout_embed?uuid={WT['vip']}"
TRIP = 'https://sadhama.wetravel.com/trips/insight-vipassana-silent-meditation-retreats-2026-sadhama-rewild-retreats-68342383'
PROFILE = 'https://www.wetravel.com/users/sadhama'
DATES = [('2027-05-31', '2027-06-06', '31 May – 6 June'), ('2027-07-26', '2027-08-01', '26 July – 1 August'), ('2027-08-30', '2027-09-05', '30 August – 5 September')]
NAV = [('retreats.html', 'Retreats & booking'), ('articles.html', 'Articles'), ('ask-ananda.html', 'Ask Ananda'), ('library.html', 'Dhamma library'), ('teacher.html', 'Teacher')]

def book_btn(label='Book your place', cls='btn book', extra='', uuid=None):
    u = uuid or WT['vip']
    return (f'<a class="{cls} wtrvl-checkout_button" data-env="{WT["env"]}" data-version="v0.4" data-uid="{WT["uid"]}" '
            f'data-uuid="{u}" href="https://www.wetravel.com/checkout_embed?uuid={u}" rel="noopener"{extra}>{label}</a>')

LOGO = '<svg viewBox="0 0 32 32" aria-hidden="true"><circle cx="16" cy="16" r="15" fill="var(--oak)"/><path d="M5 21c4-3 7-4 11-4s7 1 11 4v3H5z" fill="var(--sky)"/><path d="M10 21l6-8 6 8z" fill="#fff"/><circle cx="23" cy="10" r="2.6" fill="var(--sun)"/></svg>'

def rel(href, depth):
    """Map site-absolute content links to relative static paths."""
    m = {'/': 'index.html', '/retreats/': 'retreats.html', '/teacher/': 'teacher.html', '/ask-ananda/': 'ask-ananda.html',
         '/library/': 'library.html', '/articles/': 'articles.html'}
    if href.startswith('http') or href.startswith('#') or href.startswith('mailto:'): return href
    h = m.get(href)
    if h is None:
        h = href.lstrip('/')
        h = h.replace('library/read.html', 'read.html')
    return '../' * depth + h

def fix_links(s, depth):
    return re.sub(r'href="(/[^"]*)"', lambda m: f'href="{rel(m.group(1), depth)}"', s)

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
<footer><div class="wrap"><div class="cols">
<div><img src="{up}assets/sadhama-logo-white-lg.png" width="160" height="99" alt="Sadhama" style="margin-bottom:14px"><p>Silent Insight Vipassana retreats in nature, on the River Thames at Hardwick Estate, Oxfordshire. Run by <a href="https://sadhama.com" rel="noopener">Sadhama</a>.</p></div>
<div><h4>Retreats</h4><ul><li><a href="{up}retreats.html">2027 dates &amp; booking</a></li><li><a href="{up}articles/what-is-a-vipassana-retreat.html">What is a vipassana retreat?</a></li><li><a href="{up}articles/silent-retreat-near-london.html">Silent retreat near London</a></li></ul></div>
<div><h4>Learn</h4><ul><li><a href="{up}ask-ananda.html">Ask Ananda</a></li><li><a href="{up}library.html">Dhamma library</a></li><li><a href="{up}articles.html">All articles</a></li></ul></div>
<div><h4>Contact</h4><ul><li>info@sadhama.com</li><li>Hardwick Estate, Whitchurch-on-Thames, RG8 7RA</li><li><a href="https://www.instagram.com/sadhamayoga/" rel="noopener">Instagram</a></li></ul></div>
</div><p class="small" style="margin-top:28px;opacity:.75">Sutta translations by Bhikkhu Sujato, SuttaCentral, dedicated to the public domain (CC0). Photographs © Sadhama.</p></div></footer>
{book_btn('Book a retreat', 'btn book float-book')}
<script src="{up}assets/site.js"></script>{scripts}
<script src="https://cdn.wetravel.com/widgets/embed_checkout.js"></script>
</body></html>'''
    p = OUT / path; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(doc)

def img(name, alt, cls='', sizes='100vw', depth=0, eager=False):
    up = '../' * depth
    return (f'<img src="{up}img/{name}.jpg" srcset="{up}img/{name}-sm.jpg 800w, {up}img/{name}.jpg 1800w" sizes="{sizes}" '
            f'alt="{html.escape(alt)}" {"" if eager else "loading=lazy "}decoding="async"{(" class=" + chr(34) + cls + chr(34)) if cls else ""}>')

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
    body = f'''<section class="page-hero">{img("lily-pond-mist", ALT["lily-pond-mist"], eager=True)}<div class="wrap"><h1>Articles on silent retreat and vipassana practice</h1>
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
def build_home(arts):
    body = f'''<section class="hero">{img("oak-marquee-dawn", ALT["oak-marquee-dawn"], eager=True)}<div class="wrap">
<h1>Silent vipassana retreats in nature, an hour from London</h1>
<p>Seven days of noble silence, insight meditation and Dhamma, in a meadow on the River Thames. The teaching is offered for donation.</p>
<div class="ctas">{book_btn()}<a class="btn light" href="/retreats/">See 2027 dates</a></div></div></section>

<section class="band"><div class="wrap"><h2>2027 retreat dates</h2><p class="lede" style="margin-bottom:24px">Three 7-day Insight Vipassana retreats at Hardwick Estate, South Oxfordshire. Each has five full days of silence, and every group includes first-timers.</p>{dates_html()}</div></section>

<section class="band mist"><div class="wrap split"><div>
<h2>A mind-training retreat, not a holiday</h2>
<p class="lede">Vipassanā means seeing clearly. For a week you follow a simple monastery rhythm, the bell tells you where to be, and you learn to meet thoughts, feelings and sensations as they are.</p>
<ul class="ticks"><li>Sitting and walking meditation in the Mahasi Sayadaw noting tradition</li><li>Daily yoga to prepare the body for sitting</li><li>Dhamma talks and personal interviews with the teacher</li><li>Plant-based Ayurvedic meals, much of it grown on the estate</li><li>Wild swimming in the Thames and a riverside sauna</li></ul>
<p style="margin-top:20px"><a href="/articles/what-is-a-vipassana-retreat.html">What is a vipassana retreat? →</a></p></div>
{img("dmitry-teaching", ALT["dmitry-teaching"], sizes="(max-width:820px) 100vw, 600px")}</div></section>

<section class="band oak"><div class="wrap"><h2>From people who have sat with us</h2>
<div class="stats" style="margin-bottom:28px"><div><b>4.9</b><span>average from 167 WeTravel reviews</span></div><div><b>35+</b><span>retreats run by Sadhama</span></div><div><b>1,700+</b><span>participants</span></div></div>
{quotes_html()}</div></section>

<section class="band"><div class="wrap split">{img("riverside-talk", ALT["riverside-talk"], sizes="(max-width:820px) 100vw, 600px")}<div>
<h2>Ask Ananda, your Dhamma assistant</h2>
<p class="lede">Questions about sleepiness, pain, a wandering mind, the precepts, or what to bring? Ananda answers from Dmitry's retreat talks, in his words.</p>
<p><a class="btn ghost" href="/ask-ananda/">Ask a question</a></p></div></div></section>

<section class="band mist"><div class="wrap split"><div>
<h2>A free library of the Buddha's words</h2>
<p class="lede">Eight collections from the Pāḷi Canon, in Bhikkhu Sujato's public-domain translation. Read online, download as an ebook, or press Listen and have them read aloud.</p>
<p><a class="btn ghost" href="/library/">Open the library</a></p></div>
{img("lily-pond-mist", ALT["lily-pond-mist"], sizes="(max-width:820px) 100vw, 600px")}</div></section>

<section class="band"><div class="wrap"><h2>Guides for your practice</h2><div class="grid">{"".join(card(a) for a in arts[:6])}</div>
<p style="margin-top:22px"><a href="/articles/">All articles →</a></p></div></section>

<section class="band mist"><div class="wrap" style="max-width:860px"><h2>Questions people ask</h2>{faq_html(FAQ)}</div></section>
<section class="band"><div class="wrap cta-box" style="margin:0 auto;max-width:1100px"><p>Seven days. Five of silence. One meadow by the river.</p>{book_btn()}</div></section>'''
    ld = [FAQ_LD, {"@context": "https://schema.org", "@type": "WebSite", "name": "Vipassana Retreat UK", "url": DOMAIN + "/"},
          ORG | {"@context": "https://schema.org", "sameAs": ["https://sadhama.com", "https://www.instagram.com/sadhamayoga/", PROFILE]}] + [event_ld(*d) for d in DATES]
    page('index.html', 'Vipassana Retreat UK: Silent Meditation Retreats near London 2027', 'Silent 7-day vipassana meditation retreats in nature on the River Thames, Oxfordshire, 40 minutes from London. 2027 dates, teaching offered for donation. Beginners welcome.', body, '', 'oak-marquee-dawn', ld)

# ---------- retreats ----------
def build_retreats():
    body = f'''<section class="page-hero">{img("marquee-dawn", ALT["marquee-dawn"], eager=True)}<div class="wrap"><h1>7-Day Insight Vipassana Silent Retreat, 2027</h1>
<p>Hardwick Estate, on the River Thames in South Oxfordshire. Five full days of noble silence. Teaching offered for dāna.</p></div></section>
<section class="band"><div class="wrap"><h2>Choose your dates</h2>{dates_html()}
<p class="muted small" style="margin-top:16px">Booking opens in a secure WeTravel checkout window. You choose your date and accommodation, then pay a £75 deposit to hold your place.</p></div></section>

<section class="band mist"><div class="wrap split"><div><h2>Find inner peace</h2>
<p class="lede">An ancient method of meditation, pristinely simple in principle and profoundly transformative in application.</p>
<p>Live in silence for a few days in a quiet natural place with clean, fresh air, in the Chilterns. Give yourself a digital detox: phone off, a break from the flow of information and endless tasks. Follow a healthy daily rhythm with the sun. Eat nourishing plant-based food, much of it grown organically on the estate. And slow down: plenty of quiet time to listen inwardly.</p>
<p>Silence is kept for five full days. The only exception is the optional personal interviews with the teacher, to clarify anything about the practice.</p></div>
{img("oak-marquee-dawn", ALT["oak-marquee-dawn"], sizes="(max-width:820px) 100vw, 600px")}</div></section>

<section class="band"><div class="wrap grid two" style="align-items:start"><div><h2>What's included</h2><ul class="ticks">
<li><b>Five days of silence</b>, the rare peace of total quiet</li><li><b>Sitting meditation</b>, learning the noting method step by step</li>
<li><b>Walking meditation</b>, the dynamic practice that traditionally accompanies sitting</li><li><b>Daily yoga</b> to prepare the body and ease hips, knees and back</li>
<li><b>Dhamma talks</b> on the nature of mind, with stories from the suttas</li><li><b>Teacher interviews</b> for personal guidance</li>
<li><b>Ayurvedic meals and teas</b>, organic and locally sourced where possible</li><li><b>Riverside sauna</b> on day one and day seven</li>
<li><b>Wild swimming</b> in a clean stretch of the Thames</li><li><b>Campsite ground rent</b>, hot showers and toilets</li></ul></div>
<div><h2>Not included</h2><ul class="ticks"><li>Tent (unless rented at booking), bedding</li><li>Cutlery and crockery: please bring your own</li><li>Yoga mat and a blanket for sitting (a few can be borrowed on request)</li><li>Massage and bodywork with the on-site therapists, at a reduced rate</li></ul>
<h3 style="margin-top:28px">Accommodation</h3><p>Camp in the secluded riverside campsite: bring your own tent, campervan or caravan at no extra cost, or rent a pre-erected tent or a deluxe bell tent with a framed bed at checkout. Tents are single occupancy. No dogs, please.</p>
<p><a href="/articles/what-to-bring-silent-retreat.html">Packing list →</a></p></div></div></section>

<section class="band mist"><div class="wrap grid two" style="align-items:start"><div><h2>A day on retreat</h2><p class="muted">Monastery life: a simple schedule, a bell instead of a clock. Please follow it in full; it is designed for continuity of practice.</p></div>{timetable_html()}</div></section>

<section class="band"><div class="wrap split">{img("riverside-talk", ALT["riverside-talk"], sizes="(max-width:820px) 100vw, 600px")}<div><h2>A generosity-based retreat</h2>
<p><b>1. Organisational fee: £149</b> (deposit £75). Covers the basic costs of accommodation and food.</p>
<p><b>2. Dāna</b> for the teaching itself. It's important for vipassana to be offered for donation, not for private gain. At the end of the retreat, based on what the week gave you, you offer whatever you feel moved to give.</p>
<p>A few <b>seva tickets</b> are available for those who'd like to help the core team, or who can't afford the full fee. Apply through the booking page.</p>
<p><a href="/articles/vipassana-retreat-cost-dana.html">Why we teach for dāna →</a></p></div></div></section>

<section class="band oak"><div class="wrap grid two" style="align-items:start"><div><h2>Getting there</h2>
<p>Hardwick Estate, Whitchurch-on-Thames, RG8 7RA. About 40 minutes by train from London Paddington to Reading or Pangbourne, then a short taxi. By car, 20 minutes from Junction 12 of the M4. London Heathrow is about an hour away.</p>
<p>The retreat is free from drugs, alcohol and intoxicants which cloud the mind.</p></div>
<div><h2>Your teachers and hosts</h2><p><b>Dmitry Glazkov</b> teaches vipassana in the Mahasi tradition, yoga and Ayurveda, here and at the Indriya Retreat Centre in Thailand. <b>Karen Buckland</b> leads the kitchen with plant-based Ayurvedic cooking. <b>Bara Cechova</b> leads yoga, breathwork and bodywork.</p><p><a href="/teacher/">About the teacher →</a></p></div></div></section>

<section class="band"><div class="wrap"><h2>From past retreats</h2>{quotes_html()}
<div style="margin-top:24px"><script src="https://cdn.wetravel.com/widgets/embed_reviews.js" id="wetravel_review_widget" data-env="https://www.wetravel.com" data-version="v0.3" data-userslug="202227" data-uid="202227" data-showstars="true" data-showcount="true" data-name="WeTravel Review Widget"></script></div></div></section>

<section class="band mist"><div class="wrap"><h2>More silent retreats with Dmitry</h2><div class="grid two" style="align-items:start">
<div class="date-card"><span class="yr">Thailand · 7 days</span><span class="when">25–31 January 2027</span><p style="margin:0"><b>Insight Vipassana Silent Retreat, Koh Phangan.</b> The same Mahasi noting practice, at the Indriya Retreat Centre by the sea on Koh Phangan, Thailand. From $350 (deposit $100).</p>{book_btn("Book Thailand", uuid=WT["thai"])}</div>
<div class="date-card"><span class="yr">Hardwick · 4 days of gentle silence</span><span class="when">27–30 August 2027</span><p style="margin:0"><b>Practice of Peace.</b> Gentle meditation, yoga, forest bathing, sauna and plenty of time for yourself over the August bank holiday. A soft first step towards a 7 or 10-day vipassana.</p>{book_btn("Book Practice of Peace", uuid=WT["peace"])}</div>
</div></div></section>

<section class="band"><div class="wrap" style="max-width:860px"><h2>Retreat FAQ</h2>{faq_html(FAQ)}</div></section>'''
    thai = event_ld('2027-01-25', '2027-01-31', 'Thailand January')
    thai.update(name='7-Day Insight Vipassana Silent Meditation Retreat, Koh Phangan, Thailand (January 2027)', location={"@type": "Place", "name": "Indriya Retreat Centre", "address": {"@type": "PostalAddress", "streetAddress": "66/9 Moo 5", "addressLocality": "Koh Phangan", "addressRegion": "Surat Thani", "postalCode": "84280", "addressCountry": "TH"}},
                offers={"@type": "Offer", "price": "350", "priceCurrency": "USD", "url": "https://www.wetravel.com/trips/thailand-vipassana-silent-meditation-retreat-in-koh-phangan-sadhama-rewild-retreats-7915926147", "availability": "https://schema.org/InStock"})
    peace = event_ld('2027-08-27', '2027-08-30', 'August')
    peace.update(name='Practice of Peace: 4-Day Gentle Silent Retreat (August 2027)', description='Four days of gentle silence at Hardwick Estate: simple meditation, yoga, forest bathing, riverside sauna and Ayurvedic food.')
    peace.pop('offers', None)
    ld = [FAQ_LD] + [event_ld(*d) for d in DATES] + [thai, peace]
    page('retreats.html', '7-Day Silent Vipassana Retreat UK 2027: Dates & Booking', 'Book a 7-day silent Insight Vipassana retreat at Hardwick Estate, Oxfordshire, in 2027: 31 May, 26 July or 30 August. £149 organisational fee, teaching for dāna.', body, 'retreats.html', 'marquee-dawn', ld)

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
<p class="muted small" style="margin-top:24px">Translations by Bhikkhu Sujato, from <a href="https://suttacentral.net" rel="noopener">SuttaCentral</a>, CC0 public domain. "Listen" uses your device's built-in voices.</p></div></section>'''
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
.status{font:14px var(--sans);color:var(--soft)}.dl{font:14px var(--sans)}
@media(max-width:900px){.reader{grid-template-columns:minmax(0,1fr)}.toc{position:static;max-height:300px}}</style>'''
    rbody = '''<section class="band" style="padding-top:28px"><div class="wrap">
<nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> › <a href="/library/">Library</a> › <span id="crumb">Reader</span></nav>
<h1 id="bookTitle">Dhamma library</h1><p class="muted" id="bookSub"></p>
<div class="reader"><aside class="toc" aria-label="Contents"><label class="small muted" for="chapter">Chapter</label><select id="chapter"></select><ol id="suttas"></ol></aside>
<div><div class="tools" role="toolbar" aria-label="Reading tools"><button class="play" id="play" type="button">▶ Listen</button><button id="stop" type="button">■ Stop</button>
<select id="rate" aria-label="Reading speed"><option value=".85">Slow</option><option value="1" selected>Normal</option><option value="1.15">Faster</option></select>
<select id="voice" aria-label="Voice"></select><button id="smaller" type="button" aria-label="Smaller text">A−</button><button id="bigger" type="button" aria-label="Larger text">A+</button>
<span class="dl" id="dl"></span><span class="status" id="status"></span></div>
<article class="text" id="text"><p class="muted">Loading…</p></article>
<p class="muted small" style="margin-top:32px">Translated by Bhikkhu Sujato (SuttaCentral), public domain. <span id="tts-note"></span></p></div></div></div></section>'''
    page('read.html', 'Read the Suttas Online | Vipassana Retreat UK', 'Read and listen to the Buddha\'s discourses online in Bhikkhu Sujato\'s public-domain translation.', rbody, 'library.html', 'lily-pond-mist', scripts='<script src="assets/reader.js"></script>', extra_head=reader_head)

def build_seo(arts):
    urls = ['', 'retreats.html', 'articles.html', 'ask-ananda.html', 'library.html', 'teacher.html', 'read.html'] + [f'articles/{a["slug"]}.html' for a in arts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{DOMAIN}/{u}</loc><lastmod>2026-11-27</lastmod></url>\n' for u in urls) + '</urlset>\n'
    (OUT / 'sitemap.xml').write_text(sm)
    (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {DOMAIN}/sitemap.xml\n')

if __name__ == '__main__':
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    for f in ('site.css', 'site.js', 'ananda.js', 'reader.js'):
        shutil.copy(SRC / f, OUT / 'assets' / f)
    arts = load_articles()
    build_home(arts); build_retreats(); build_teacher(); build_articles(arts); build_ananda(); build_library(); build_seo(arts)
    print('built', len(arts), 'articles')
