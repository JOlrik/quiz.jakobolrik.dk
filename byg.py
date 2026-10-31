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
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

HER = Path(__file__).resolve().parent
UD = HER / 'site'
CACHE = HER / 'medier-cache'
IND = json.loads((HER / 'indstillinger.json').read_text())
DATA = json.loads((HER / 'data' / 'quizzer.json').read_text())
MEDIER = json.loads((HER / 'data' / 'medier.json').read_text())
TEKSTSVAR = json.loads((HER / 'data' / 'tekstsvar.json').read_text())

# Nye tekster til spørgsmål, hvor svarene stod på et billede, der er gået tabt. Pointene er uændrede.
for _z in DATA:
    for _q in _z['questions']:
        _ret = TEKSTSVAR.get(str(_q['id']))
        if _ret:
            _q['title'] = _ret.get('titel', _q['title'])
            _q['description'] = _ret.get('beskrivelse', _q['description'])
            for _a in _q['answers']:
                _a['title'] = _ret.get('svar', {}).get(str(_a['id']), _a['title'])
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


# ---------- billeder og videoer fra den gamle platform ----------

def medie(art, id_):
    """Webudgave af et originalt billede/video fra den gamle platform (data/medier.json → originaler/)."""
    rel = MEDIER.get(art, {}).get(str(id_))
    return medie_fil(HER / rel) if rel else None


def foto(id_):
    """Foto fra Jakobs egen fotoserie (fotos/), valgt pr. quiz i indstillinger.json."""
    navn = IND.get('fotos', {}).get(str(id_))
    return medie_fil(HER / 'fotos' / f'{navn}.jpg') if navn else None


def medie_fil(kilde):
    """Lægger en webudgave af kilden i site/medier/. Giver (sti, 'billede'|'video') eller None.

    De nedskalerede udgaver gemmes i medier-cache/, så videoerne kun konverteres én gang.
    """
    if not kilde.exists():
        return None
    CACHE.mkdir(exist_ok=True)
    if kilde.suffix.lower() in ('.jpg', '.jpeg', '.png'):
        navn, slags = f'{kilde.stem}.jpg', 'billede'
        if not (CACHE / navn).exists():
            im = ImageOps.exif_transpose(Image.open(kilde)).convert('RGB')
            im.thumbnail((1400, 1400))
            im.save(CACHE / navn, 'JPEG', quality=80, optimize=True, progressive=True)
    elif kilde.suffix.lower() in ('.mp4', '.mov', '.m4v'):
        navn, slags = f'{kilde.stem}.mp4', 'video'
        if not (CACHE / navn).exists():
            subprocess.run(['avconvert', '-p', 'Preset960x540', '-s', str(kilde), '-o', str(CACHE / navn)],
                           check=True, capture_output=True)
    else:
        return None
    (UD / 'medier').mkdir(exist_ok=True)
    if not (UD / 'medier' / navn).exists():
        shutil.copy(CACHE / navn, UD / 'medier' / navn)
    return f'medier/{navn}', slags


def medie_html(m, rod, klasse):
    if not m:
        return ''
    sti, slags = m
    if slags == 'video':
        return f'<video class="{klasse}" src="{rod}{sti}" controls playsinline preload="metadata"></video>'
    return f'<img class="{klasse}" src="{rod}{sti}" alt="" loading="lazy">'


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


def billede(sti, etiket, overskrift, undertekst, foto=None):
    W, H, M = 1200, 630, 80
    img = Image.new('RGB', (W, H), '#171816')
    bredde = W - 2 * M
    if foto and foto[1] == 'billede':
        # fotoet i højre side, glidende over i den mørke flade bag teksten
        X, B = 620, 160
        img.paste(ImageOps.fit(Image.open(UD / foto[0]).convert('RGB'), (W - X, H)), (X, 0))
        maske = Image.linear_gradient('L').rotate(-90).resize((B, H))
        img.paste(Image.new('RGB', (B, H), '#171816'), (X, 0), maske)
        bredde = X - M
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill='#B76F51')
    d.text((M, 72), etiket.upper(), font=sans(24), fill='#CB9174')
    # største skrift, hvor overskriften kan stå på højst 3 linjer
    for str_ in (104, 92, 82, 72, 64, 56, 50):
        f = ImageFont.truetype(SERIF, str_)
        linjer = ombryd(d, overskrift, f, bredde)
        if len(linjer) <= 3:
            break
    y = 140 + (3 - len(linjer)) * str_ * 0.35
    for l in linjer[:3]:
        d.text((M, y), l, font=f, fill='#EAE8E2')
        y += str_ * 1.08
    if undertekst:
        f2 = sans(28)
        u = ombryd(d, undertekst, f2, bredde)[:2]
        uy = H - 72 - 40 * (len(u) - 1)
        for l in u:
            d.text((M, uy), l, font=f2, fill='#B7B5AC', anchor='ls')
            uy += 40
    if bredde == W - 2 * M:
        d.text((W - M, H - 72), 'jakobolrik.dk', font=sans(24), fill='#B7B5AC', anchor='rs')
    else:
        d.text((M + d.textlength(etiket.upper(), font=sans(24)) + 16, 72), '· JAKOBOLRIK.DK', font=sans(24), fill='#B7B5AC')
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
        # spørgsmål, hvis svar står på et billede, kommer først med, når billedet findes
        sprunget = [q['title'] for q in z['questions'] if kraever_billede(q) and not medie('spoergsmaal', q['id'])]
        z = dict(z, questions=[q for q in z['questions'] if not kraever_billede(q) or medie('spoergsmaal', q['id'])])
        if z['id'] in udeladt or len(z['questions']) < 4 or len(z['results']) < 2:
            continue
        if sprunget:
            print(f"  {z['title']}: sprunget over, mangler billede: {sprunget}")
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
            resultater.append({'id': str(r['id']), 'slug': rs, 'titel': r['title'].strip(), 'tekst': r['description'],
                               'medie': medie('resultater', r['id'])})

        def spm_medie(q):
            m = medie('spoergsmaal', q['id'])
            return {'sti': '../' + m[0], 'slags': m[1]} if m else None

        quizdata = {
            'resultater': [{'id': r['id'], 'slug': r['slug']} for r in resultater],
            'spoergsmaal': [{
                'titel': q['title'].strip(),
                'beskrivelse': (q['description'] or '').strip(),
                'medie': spm_medie(q),
                'svar': [{'titel': a['title'].strip(), 'point': a['points']} for a in sortér_svar(q['answers'])],
            } for q in z['questions']],
        }
        beskr = ' '.join((z['description'] or '').split()) or f'Tag testen og bliv klogere på dig selv. {len(z["questions"])} spørgsmål.'
        minutter = max(1, round(len(z['questions']) * 12 / 60))
        forside = medie('quiz', z['id']) or foto(z['id'])

        billede(UD / 'billeder' / f'{s}.png', 'Test dig selv', z['title'].strip(), kursus['navn'], forside)
        indhold = f'''<section class="quiz"><div class="wrap"><div class="smal">
  <div id="intro" class="intro">
    {medie_html(forside, '../', 'quiz-billede')}
    <p class="etiket">Test · {e(kursus['navn'])}</p>
    <h1>{e(z['title'].strip())}</h1>
    {f'<p class="lead">{e(beskr)}</p>' if z['description'] else ''}
    <p class="meta">{len(z['questions'])} spørgsmål · ca. {minutter} min.</p>
    <div class="knapper"><button id="start" class="knap" type="button">Start testen</button></div>
  </div>
  <div id="spm" class="spoergsmaal skjult">
    <div class="fremdrift"><span id="spm-bar"></span></div>
    <div class="taeller"><span id="spm-taeller"></span><button id="spm-tilbage" class="tilbage skjult" type="button">← Tilbage</button></div>
    <div id="spm-medie"></div>
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
            billede(UD / 'billeder' / bnavn, 'Mit resultat', r['titel'], z['title'].strip(),
                    r['medie'] if r['medie'] and r['medie'][1] == 'billede' else forside)
            rurl = f"{url}{r['slug']}/"
            fb = 'https://www.facebook.com/sharer/sharer.php?u=' + html.escape(rurl, quote=True)
            rabat = (f'<p>Brug koden <span class="kode">{e(kursus["rabatkode"])}</span> og få rabat på kurset.</p>'
                     if kursus.get('rabatkode') else f'<p>Bliv klogere på dig selv i onlinekurset {e(kursus["navn"])}.</p>')
            rindhold = f'''<section class="resultat"><div class="wrap"><div class="smal">
  <p class="etiket"><span class="mit-tekst skjult">Dit resultat · </span>{e(z['title'].strip())}</p>
  <h1>{e(r['titel'])}</h1>
  {medie_html(r['medie'], '../../', 'resultat-medie')}
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

        oversigt.append((z, s, beskr, kursus, forside))

    # forside med de synlige quizzer
    kort = '\n'.join(f'''  <a class="kort" href="{s}/">
    {medie_html(f, '', 'kort-billede')}
    <p class="etiket">{e(k['navn'])}</p>
    <h3>{e(z['title'].strip())}</h3>
    <p>{e(kort_tekst(b, 120))}</p>
    <span class="mere">Tag testen →</span>
  </a>''' for z, s, b, k, f in oversigt if z['id'] not in skjult)
    forside = f'''<section class="hero"><div class="wrap">
  <p class="etiket">Test dig selv</p>
  <h1>Hvem er du, når det gælder kærlighed og sex?</h1>
  <p class="lead">Små tests fra sexolog Jakob Olrik. Svar på spørgsmålene, få dit resultat, og del det med dine venner.</p>
</div></section>
<section><div class="wrap"><div class="gitter">
{kort}
</div></div></section>'''
    billede(UD / 'billeder' / 'forside.png', 'Test dig selv', 'Hvem er du, når det gælder kærlighed og sex?', 'Små tests fra sexolog Jakob Olrik',
            medie_fil(HER / 'fotos' / f"{IND['forside_foto']}.jpg") if IND.get('forside_foto') else None)
    (UD / 'index.html').write_text(side('Test dig selv – Jakob Olrik', 'Små tests om kærlighed, dating og sex fra sexolog Jakob Olrik.',
                                        f'{ADR}/', f'{ADR}/billeder/forside.png', forside, 0))
    (UD / '404.html').write_text(side('Siden findes ikke – Jakob Olrik', '', f'{ADR}/', f'{ADR}/billeder/forside.png',
                                      '<section class="hero"><div class="wrap"><h1>Siden findes ikke</h1>'
                                      '<div class="knapper"><a class="knap" href="/">Se alle tests</a></div></div></section>', 0))

    synlige = sum(1 for z, *_ in oversigt if z['id'] not in skjult)
    print(f'{len(oversigt)} quizzer bygget ({synlige} på forsiden) i {UD}')
    for z, s, *_ in oversigt:
        print(f"  {'   ' if z['id'] not in skjult else 'skj'} /{s}/")


def kraever_billede(q):
    if str(q['id']) in TEKSTSVAR:
        return False
    # svarene er bare bogstaver (A., B., ...), eller spørgsmålet henviser til billeder
    kun_bogstaver = q['answers'] and all(re.fullmatch(r'[A-ZÆØÅ][\W_]*', a['title'].strip()) for a in q['answers'])
    return bool(kun_bogstaver) or 'billede' in q['title'].lower() or q['title'].strip() == '?'


def sortér_svar(svar):
    # svar med bogstaver (A., B., ...) i bogstavrækkefølge, ellers i oprettelsesrækkefølge
    if svar and all(re.match(r'^[A-ZÆØÅ][.)]', a['title'].strip()) for a in svar):
        return sorted(svar, key=lambda a: a['title'].strip())
    return svar


if __name__ == '__main__':
    main()
