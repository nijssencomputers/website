#!/usr/bin/env python3
"""Render the existing 16 public pages. Python 3.9+, no third-party dependencies."""
from pathlib import Path
from string import Template
from html import escape
import argparse
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://www.nijssencomputers.nl'
VERSION = '20260915-audit1'
UPDATED = '2026-09-24'  # Actual content revision; do not replace with today's date on every build.
CONTACT = '''    <section class="section-block contact-section" id="contact">
      <h2>Contact met Jeroen</h2>
      <p>Stuur een WhatsApp-bericht of bel. Vertel kort wat er speelt en in welke plaats u hulp zoekt.</p>
      <div class="contact-options">
        <a href="https://wa.me/31624382361" class="cta-button cta-whatsapp">WhatsApp Jeroen</a>
        <a href="tel:+31624382361" class="cta-button cta-phone">Bel 06 2438 2361</a>
      </div>
      <p class="contact-email">Liever e-mail? <a href="mailto:info@nijssencomputers.nl">info@nijssencomputers.nl</a></p>
    </section>'''


def data_for(page):
    url = BASE + ('/' if not page['slug'] else '/' + page['slug'])
    business = {
        '@type': 'LocalBusiness', '@id': BASE + '/#bedrijf',
        'name': 'Nijssen Computers', 'url': BASE + '/',
        'description': 'Computerhulp en IT-ondersteuning voor particulieren en bedrijven. Apple, Windows en Linux.',
        'telephone': '+31624382361', 'email': 'info@nijssencomputers.nl',
        'founder': {'@type': 'Person', 'name': 'Jeroen Nijssen'}, 'foundingDate': '2008',
        'image': BASE + '/jeroen.png',
        'address': {'@type': 'PostalAddress', 'addressLocality': 'Leidschendam', 'addressCountry': 'NL'},
        'areaServed': ['Leidschendam', 'Voorburg', 'Voorschoten']
    }
    graph = [business,
        {'@type': 'WebSite', '@id': BASE+'/#website', 'name': 'Nijssen Computers', 'url': BASE+'/', 'publisher': {'@id': BASE+'/#bedrijf'}, 'inLanguage': 'nl-NL'},
        {'@type': 'WebPage', '@id': url+'#webpagina', 'url': url, 'name': page['title'], 'description': page['description'], 'inLanguage': 'nl-NL', 'isPartOf': {'@id': BASE+'/#website'}, 'about': {'@id': BASE+'/#bedrijf'}}]
    if page.get('kind'):
        service = {'@type': 'Service', '@id': url+'#dienst', 'name': page['kind'], 'provider': {'@id': BASE+'/#bedrijf'}, 'url': url}
        if page.get('city'): service['areaServed'] = page['city']
        graph.append(service)
    if page.get('faq'):
        graph.append({
            '@type': 'FAQPage',
            '@id': url + '#faq',
            'url': url,
            'inLanguage': 'nl-NL',
            'mainEntity': [{
                '@type': 'Question',
                'name': question,
                'acceptedAnswer': {'@type': 'Answer', 'text': answer}
            } for question, answer in page['faq']]
        })
    return json.dumps({'@context': 'https://schema.org', '@graph': graph}, ensure_ascii=False).replace('<', '\\u003c')


# The three existing homepage quotes. Do not invent extra reviews.
CUSTOMER_QUOTES = (
    ('“Jeroen biedt een ontzettend goede en snelle service. Altijd een vriendelijke lach en denkt goed mee. Al meer dan 15 jaar leunen wij op zijn expertise! Wij willen geen ander meer!”', 'Metselbedrijf Zwaan'),
    ('“Mijn laptop gaf een raar ratelend geluid. Jeroen heeft hem compleet nagekeken, bleek enorm stoffig. Een complete schoonmaak gehad en kon hem de volgende dag alweer ophalen.”', 'Robin Swenne'),
    ('“Fijne en razend snelle service! Mijn laptop was gecrashed (thee), binnen 24 uur was ik weer up en running. Jeroen heeft een nieuwe laptop geregeld en al mijn gegevens teruggevonden.”', 'Mireille van den Dop'),
)


def render_faq(page):
    items = '\n'.join(
        f'      <h3>{escape(question)}</h3>\n      <p>{escape(answer)}</p>'
        for question, answer in page['faq']
    )
    return f'''    <section class="section-block article-section" id="veelgestelde-vragen">
      <h2>Veelgestelde vragen</h2>
{items}
    </section>'''


def render_quotes():
    cards = ''.join(
        f'<blockquote class="review-card"><p>{escape(quote)}</p><footer>{escape(name)}</footer></blockquote>'
        for quote, name in CUSTOMER_QUOTES
    )
    return f'''    <section class="section-block article-section" id="klantreacties">
      <h2>Algemene klantreacties</h2>
      <p>Deze reacties komen van de bestaande website. Het zijn algemene klantervaringen, geen aparte printerbeoordelingen.</p>
      <div class="reviews-grid">{cards}</div>
    </section>'''


def render_body(page):
    parts = [f'''    <nav class="breadcrumb" aria-label="U bent hier"><a href="/">Startpagina</a><span aria-hidden="true">/</span><span>{escape(page['heading'])}</span></nav>
    <section class="hero">
      <h1>{escape(page['heading'])}</h1>
      <p class="tagline">{escape(page['intro'])}</p>
      <div class="hero-actions">
        <a href="https://wa.me/31624382361" class="cta-button cta-whatsapp">WhatsApp Jeroen</a>
        <a href="tel:+31624382361" class="cta-button cta-phone">Bel 06 2438 2361</a>
      </div>
      <p class="hero-note">{escape(page['note'])}</p>
    </section>''']
    for heading, content in page['sections']:
        parts.append(f'    <section class="section-block article-section">\n      <h2>{escape(heading)}</h2>\n      {content}\n    </section>')
    if page.get('faq'):
        parts.append(render_faq(page))
    if page.get('quotes'):
        parts.append(render_quotes())
    parts.append(CONTACT)
    return '\n\n'.join(parts)


def outputs():
    template = Template((ROOT/'src/layout.html').read_text(encoding='utf-8'))
    pages = json.loads((ROOT/'src/pages.json').read_text(encoding='utf-8'))
    pages.insert(0, {'slug': '', 'title': 'Computerhulp aan huis | Nijssen Computers',
        'description': 'Computerhulp aan huis in Leidschendam, Voorburg en Voorschoten. Jeroen helpt met Apple, Windows, Linux, wifi en printers. Particulier €60 per uur.'})
    result = {}
    for page in pages:
        home = not page['slug']
        body = (ROOT/'src/home.html').read_text(encoding='utf-8').rstrip() if home else render_body(page)
        related = ''
        if page.get('related'):
            links = ''.join(f'<a href="/{escape(slug, quote=True)}">{escape(label)}</a>' for slug, label in page['related'])
            related = f'      <div class="related"><p>Verder lezen</p><nav class="related-links" aria-label="Gerelateerde informatie">{links}</nav></div>'
        name = 'index.html' if home else page['slug']+'.html'
        result[name] = template.substitute(title=escape(page['title'], quote=True), description=escape(page['description'], quote=True),
            canonical=BASE+('/' if home else '/'+page['slug']), version=VERSION, body_class='homepage' if home else 'detailpage',
            structured_data=data_for(page), body=body, related=related)
    urls = [BASE+('/' if not p['slug'] else '/'+p['slug']) for p in pages]
    result['sitemap.xml'] = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{escape(url)}</loc><lastmod>{UPDATED}</lastmod></url>\n' for url in urls)+'</urlset>\n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Fail if committed HTML differs from the shared source.')
    parser.add_argument('--deploy', type=Path, help='Copy only public files plus existing image/terms into a new directory.')
    args = parser.parse_args()
    generated = outputs()
    if args.check:
        stale = [p for p, text in generated.items() if not (ROOT/p).exists() or (ROOT/p).read_text(encoding='utf-8') != text]
        if stale:
            print('Run python3 tools/build.py. Stale: '+', '.join(stale), file=sys.stderr)
            return 1
    else:
        for name, text in generated.items(): (ROOT/name).write_text(text, encoding='utf-8')
    if args.deploy:
        target = args.deploy.resolve()
        if target.exists():
            parser.error('Deployment directory must not already exist; this prevents accidental overwrites.')
        assets = ['style.css', 'nav.js', 'analytics-events.js', 'robots.txt', '.htaccess', 'jeroen.png', '_files/ugd/a467e1_485c7f11207647e3a05afcf4b5a87758.pdf']
        missing = [p for p in assets if not (ROOT/p).is_file()]
        if missing:
            parser.error('Unchanged assets must be present in the original checkout: '+', '.join(missing))
        target.mkdir(parents=True)
        for name in list(generated)+assets:
            (target/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, target/name)
        print('Public files only: '+str(target))
    print(f'OK: {len(generated)-1} HTML pages; shared header, metadata and footer; sitemap.')
    return 0

if __name__ == '__main__': raise SystemExit(main())
