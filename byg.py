#!/usr/bin/env python3
"""Bygger quiz-sitet til mappen site/.

    python3 byg.py

Læser data/quizzer.json (hentet fra den gamle GoOnlive-database) og
indstillinger.json (adresse, kursuslinks, rabatkoder, skjulte quizzer).
Laver en side pr. quiz, en side pr. resultat (den deles på Facebook)
og et delebillede i 1200 x 630 til hver af dem.
"""
import html
import json
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HER = Path(__file__).resolve().parent
UD = HER / 'site'
IND = json.loads((HER / 'indstillinger.json').read_text())
DATA = json.loads((HER / 'data' / 'quizzer.json').read_text())
ADR = IND['adresse'].rstrip('/')

FB_IKON = ('<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M24 12.07C24 5.4 18.63 0 12 0S0 5.4 0 12.07C0 18.1 '
           '4.39 23.1 10.13 24v-8.44H7.08v-3.49h3.05V9.41c0-3.02 1.79-4.69 4.53-4.69 1.31 0 2.68.24 2.68.24v2.96h-1.51c-1.49 0-1.96.93-1.96 '
           '1.89v2.26h3.33l-.53 3.49h-2.8V24C19.61 23.1 24 18.1 24 12.07z"/></svg>')


# ---------- hjælpere ----------

def slug(tekst):
    t = tekst.lower()
    for a, b in (('æ', 'ae'), ('ø', 'oe'), ('å', 'aa'), ('é', 'e'), ('ü', 'u')):
        t = t.replace(a, b)
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t[:60].rstrip('-') or 'quiz'


def e(t):
    return html.escape(t or '', quote=True)


def afsnit(t):
    linjer = [l.strip() for l in (t or '').replace('\r', '').split('\n')]
    return '\n'.join(f'<p>{e(l)}</p>' for l in linjer if l)


def kort_tekst(t, n=155):
    t = ' '.join((t or '').split())
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0] + ' …'


def side(titel, beskrivelse, url, billede, indhold, dybde, script=''):
    rod = '../' * dybde
    return f'''<!doctype html>
<html lang="da">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titel)}</title>
<meta name="description" content="{e(beskrivelse)}">
<link rel="canonical" href="{e(url)}">
<meta property="og:type" content="website">
<meta property="og:locale" content="da_DK">
<meta property="og:site_name" content="Jakob Olrik">
<meta property="og:title" content="{e(titel)}">
<meta property="og:description" content="{e(beskrivelse)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{e(billede)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{rod}favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400;9..40,500&family=Instrument+Serif&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rod}style.css">
</head>
<body>
<header class="top"><div class="wrap">
  <a class="logo" href="{e(IND['hjemmeside'])}">Jakob Olrik</a>
  <nav><a href="{rod}">Alle tests</a></nav>
</div></header>
<main>
{indhold}
</main>
<footer class="bund"><div class="wrap">
  <a href="{e(IND['hjemmeside'])}">jakobolrik.dk</a> · <a href="{e(IND['hjemmeside'])}/onlinekurser">Onlinekurser</a>
</div></footer>
{script}
</body>
</html>
'''


# ---------- delebilleder ----------

SERIF = str(HER / 'fonts' / 'InstrumentSerif-Regular.ttf')
SANS = str(HER / 'fonts' / 'DMSans.ttf')


def sans(str_):
    f = ImageFont.truetype(SANS, str_)
    try:
        f.set_variation_by_axes([14, 500])
    except Exception:
        pass
    return f


def ombryd(draw, tekst, font, bredde):
    linjer, linje = [], ''
    for ord_ in tekst.split():
        proeve = (linje + ' ' + ord_).strip()
        if draw.textlength(proeve, font=font) <= bredde:
            linje = proeve
        else:
            if linje:
                linjer.append(linje)
            linje = ord_
    if linje:
        linjer.append(linje)
    return linjer


def billede(sti, etiket, overskrift, undertekst):
    W, H, M = 1200, 630, 80
    img = Image.new('RGB', (W, H), '#171816')
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill='#B76F51')
    d.text((M, 72), etiket.upper(), font=sans(24), fill='#CB9174')
    # største skrift, hvor overskriften kan stå på højst 3 linjer
    for str_ in (104, 92, 82, 72, 64, 56, 50):
        f = ImageFont.truetype(SERIF, str_)
        linjer = ombryd(d, overskrift, f, W - 2 * M)
        if len(linjer) <= 3:
            break
    y = 140 + (3 - len(linjer)) * str_ * 0.35
    for l in linjer[:3]:
        d.text((M, y), l, font=f, fill='#EAE8E2')
        y += str_ * 1.08
    if undertekst:
        f2 = sans(28)
        u = ombryd(d, undertekst, f2, W - 2 * M)[:2]
        uy = H - 72 - 40 * (len(u) - 1)
        for l in u:
            d.text((M, uy), l, font=f2, fill='#B7B5AC', anchor='ls')
            uy += 40
    d.text((W - M, H - 72), 'jakobolrik.dk', font=sans(24), fill='#B7B5AC', anchor='rs')
    img.save(sti, optimize=True)


# ---------- byg ----------

def main():
    if UD.exists():
        shutil.rmtree(UD)
    (UD / 'billeder').mkdir(parents=True)
    shutil.copy(HER / 'skabelon' / 'style.css', UD / 'style.css')
    shutil.copy(HER / 'skabelon' / 'quiz.js', UD / 'quiz.js')
    (UD / 'CNAME').write_text(ADR.split('://', 1)[1] + '\n')
    (UD / '.nojekyll').write_text('')
    (UD / 'favicon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="4" fill="#171816"/>'
                                    '<text x="16" y="24" text-anchor="middle" font-family="Georgia,serif" font-size="22" fill="#CB9174">J</text></svg>')

    udeladt = {int(k) for k in IND['udeladt']}
    skjult = set(IND['skjult'])
    brugte = set()
    oversigt = []

    for z in DATA:
        if z['id'] in udeladt or len(z['questions']) < 4 or len(z['results']) < 2:
            continue
        kursus = IND['kurser'][str(z['course_id'])]
        s = slug(z['title'])
        while s in brugte:
            s += '-2'
        brugte.add(s)
        mappe = UD / s
        mappe.mkdir()

        # resultater med egne adresser
        rslugs = set()
        resultater = []
        for r in z['results']:
            rs = slug(r['title'])
            n = 2
            while rs in rslugs:
                rs = f"{slug(r['title'])}-{n}"
                n += 1
            rslugs.add(rs)
            resultater.append({'id': str(r['id']), 'slug': rs, 'titel': r['title'].strip(), 'tekst': r['description']})

        quizdata = {
            'resultater': [{'id': r['id'], 'slug': r['slug']} for r in resultater],
            'spoergsmaal': [{
                'titel': q['title'].strip(),
                'beskrivelse': (q['description'] or '').strip(),
                'svar': [{'titel': a['title'].strip(), 'point': a['points']} for a in sortér_svar(q['answers'])],
            } for q in z['questions']],
        }
        beskr = ' '.join((z['description'] or '').split()) or f'Tag testen og bliv klogere på dig selv. {len(z["questions"])} spørgsmål.'
        minutter = max(1, round(len(z['questions']) * 12 / 60))

        billede(UD / 'billeder' / f'{s}.png', 'Test dig selv', z['title'].strip(), kursus['navn'])
        indhold = f'''<section class="quiz"><div class="wrap"><div class="smal">
  <div id="intro" class="intro">
    <p class="etiket">Test · {e(kursus['navn'])}</p>
    <h1>{e(z['title'].strip())}</h1>
    {f'<p class="lead">{e(beskr)}</p>' if z['description'] else ''}
    <p class="meta">{len(z['questions'])} spørgsmål · ca. {minutter} min.</p>
    <div class="knapper"><button id="start" class="knap" type="button">Start testen</button></div>
  </div>
  <div id="spm" class="spoergsmaal skjult">
    <div class="fremdrift"><span id="spm-bar"></span></div>
    <div class="taeller"><span id="spm-taeller"></span><button id="spm-tilbage" class="tilbage skjult" type="button">← Tilbage</button></div>
    <h2 id="spm-titel"></h2>
    <p id="spm-beskrivelse" class="beskrivelse"></p>
    <ul id="spm-svar" class="svar"></ul>
  </div>
</div></div></section>'''
        quizjson = json.dumps(quizdata, ensure_ascii=False).replace('</', '<\\/')
        script = (f'<script type="application/json" id="quiz-data">{quizjson}</script>\n'
                  '<script src="../quiz.js"></script>')
        url = f'{ADR}/{s}/'
        (mappe / 'index.html').write_text(side(z['title'].strip(), beskr, url, f'{ADR}/billeder/{s}.png', indhold, 1, script))

        for r in resultater:
            rmappe = mappe / r['slug']
            rmappe.mkdir()
            bnavn = f"{s}--{r['slug']}.png"
            billede(UD / 'billeder' / bnavn, 'Mit resultat', r['titel'], z['title'].strip())
            rurl = f"{url}{r['slug']}/"
            fb = 'https://www.facebook.com/sharer/sharer.php?u=' + html.escape(rurl, quote=True)
            rabat = (f'<p>Brug koden <span class="kode">{e(kursus["rabatkode"])}</span> og få rabat på kurset.</p>'
                     if kursus.get('rabatkode') else f'<p>Bliv klogere på dig selv i onlinekurset {e(kursus["navn"])}.</p>')
            rindhold = f'''<section class="resultat"><div class="wrap"><div class="smal">
  <p class="etiket"><span class="mit-tekst skjult">Dit resultat · </span>{e(z['title'].strip())}</p>
  <h1>{e(r['titel'])}</h1>
  <div class="tekst">{afsnit(r['tekst'])}</div>
  <div class="knapper mit skjult">
    <a class="knap fb" href="{fb}" target="_blank" rel="noopener">{FB_IKON}Del på Facebook</a>
    <button class="knap sekundaer" type="button" id="del">Kopiér link</button>
    <a class="knap sekundaer" href="../">Tag testen igen</a>
  </div>
  <p class="besked mit skjult" id="besked" aria-live="polite"></p>
  <div class="knapper andres">
    <a class="knap" href="../">Tag testen selv</a>
  </div>
  <div class="boks">
    <h3>{e(kursus['navn'])}</h3>
    {rabat}
    <div class="knapper"><a class="knap" href="{e(kursus['url'])}">Se kurset</a></div>
  </div>
</div></div></section>'''
            rscript = f'''<script>
(function () {{
  if (!/[?&]mit=1/.test(location.search)) return;
  document.querySelectorAll('.mit, .mit-tekst').forEach(function (el) {{ el.classList.remove('skjult'); }});
  document.querySelector('.andres').classList.add('skjult');
  var url = {json.dumps(rurl)};
  document.getElementById('del').addEventListener('click', function () {{
    var besked = document.getElementById('besked');
    if (navigator.share) {{ navigator.share({{ url: url, title: document.title }}).catch(function () {{}}); return; }}
    navigator.clipboard.writeText(url).then(function () {{ besked.textContent = 'Linket er kopieret.'; }},
      function () {{ besked.textContent = url; }});
  }});
}})();
</script>'''
            rtitel = f"{r['titel']} – {z['title'].strip()}"
            (rmappe / 'index.html').write_text(side(rtitel, kort_tekst(r['tekst']), rurl, f'{ADR}/billeder/{bnavn}', rindhold, 2, rscript))

        oversigt.append((z, s, beskr, kursus))

    # forside med de synlige quizzer
    kort = '\n'.join(f'''  <a class="kort" href="{s}/">
    <p class="etiket">{e(k['navn'])}</p>
    <h3>{e(z['title'].strip())}</h3>
    <p>{e(kort_tekst(b, 120))}</p>
    <span class="mere">Tag testen →</span>
  </a>''' for z, s, b, k in oversigt if z['id'] not in skjult)
    forside = f'''<section class="hero"><div class="wrap">
  <p class="etiket">Test dig selv</p>
  <h1>Hvem er du, når det gælder kærlighed og sex?</h1>
  <p class="lead">Små tests fra sexolog Jakob Olrik. Svar på spørgsmålene, få dit resultat, og del det med dine venner.</p>
</div></section>
<section><div class="wrap"><div class="gitter">
{kort}
</div></div></section>'''
    billede(UD / 'billeder' / 'forside.png', 'Test dig selv', 'Hvem er du, når det gælder kærlighed og sex?', 'Små tests fra sexolog Jakob Olrik')
    (UD / 'index.html').write_text(side('Test dig selv – Jakob Olrik', 'Små tests om kærlighed, dating og sex fra sexolog Jakob Olrik.',
                                        f'{ADR}/', f'{ADR}/billeder/forside.png', forside, 0))
    (UD / '404.html').write_text(side('Siden findes ikke – Jakob Olrik', '', f'{ADR}/', f'{ADR}/billeder/forside.png',
                                      '<section class="hero"><div class="wrap"><h1>Siden findes ikke</h1>'
                                      '<div class="knapper"><a class="knap" href="/">Se alle tests</a></div></div></section>', 0))

    synlige = sum(1 for z, *_ in oversigt if z['id'] not in skjult)
    print(f'{len(oversigt)} quizzer bygget ({synlige} på forsiden) i {UD}')
    for z, s, *_ in oversigt:
        print(f"  {'   ' if z['id'] not in skjult else 'skj'} /{s}/")


def sortér_svar(svar):
    # svar med bogstaver (A., B., ...) i bogstavrækkefølge, ellers i oprettelsesrækkefølge
    if svar and all(re.match(r'^[A-ZÆØÅ][.)]', a['title'].strip()) for a in svar):
        return sorted(svar, key=lambda a: a['title'].strip())
    return svar


if __name__ == '__main__':
    main()
