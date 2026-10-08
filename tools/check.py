#!/usr/bin/env python3
"""Offline regression checks; no third-party packages and no external network calls."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import datetime
import sys
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter
from build import outputs, BASE, regio_nav_links, head_text
ROOT = Path(__file__).resolve().parents[1]
VOID = set('area base br col embed hr img input link meta param source track wbr'.split())
class Parse(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.errors=[]; self.nodes=[]; self.text=''; self.h1=[]
        self.main_links=[]; self.ids=[]; self.json=[]; self.in_json=False; self.buffer=''
        self.nav=[]; self.in_nav=False; self.nav_text=''; self.current_href=''; self.header=[]; self.in_header=False
    def handle_starttag(self, tag, attrs):
        a=dict(attrs); self.nodes.append((tag,a))
        if 'id' in a: self.ids.append(a['id'])
        if tag=='a' and 'main' in self.stack: self.main_links.append(a.get('href',''))
        if tag=='h1': self.h1.append('')
        if tag=='script' and a.get('type')=='application/ld+json': self.in_json=True; self.buffer=''
        if tag=='nav' and a.get('id')=='site-nav': self.in_nav=True
        if self.in_nav and tag=='a': self.current_href=a.get('href',''); self.nav_text=''
        if tag not in VOID: self.stack.append(tag)
    def handle_endtag(self,tag):
        if self.in_nav and tag=='a': self.nav.append((self.current_href,self.nav_text.strip()))
        if self.in_nav and tag=='nav': self.in_nav=False
        if tag=='script' and self.in_json:
            try:self.json.append(json.loads(self.buffer))
            except ValueError as e:self.errors.append('JSON-LD: '+str(e))
            self.in_json=False
        if tag in VOID: self.errors.append('Closing tag for void element: '+tag); return
        if not self.stack or self.stack[-1]!=tag: self.errors.append('Mismatched closing tag: '+tag+'; stack='+str(self.stack))
        else: self.stack.pop()
    def handle_data(self,data):
        if self.in_json:self.buffer+=data
        if self.in_nav and self.stack and self.stack[-1]=='a':self.nav_text+=data
        if self.stack and self.stack[-1]=='h1':self.h1[-1]+=data
        if not any(t in self.stack for t in ['head','script','style']):self.text+=data


def main():
    failures=[]; parses={}; links=0
    def check(ok,msg):
        if not ok:failures.append(msg)
    expected = outputs()
    htmlfiles=sorted(ROOT.glob('*.html'))
    check(len(htmlfiles)==19, 'Exactly 18 public HTML pages plus 404 expected')
    for f in htmlfiles:
        is_404 = f.name == '404.html'
        text=f.read_text(encoding='utf-8'); p=Parse(); p.feed(text); p.close(); parses['/' if f.name=='index.html' else '/'+f.stem]=p
        check(text==expected.get(f.name),f.name+': generated source is stale')
        check(not p.errors and not p.stack, f.name+': HTML nesting: '+str(p.errors or p.stack))
        check(len(p.h1)==1,f.name+': expected one h1')
        check(not any(n>1 for n in Counter(p.ids).values()),f.name+': duplicate IDs')
        check('contact' in p.ids and 'main-content' in p.ids,f.name+': missing direct contact/skip target')
        check(any(t=='html' and a.get('lang')=='nl' for t,a in p.nodes),f.name+': Dutch language')
        check(any(t=='img' and a.get('class')=='logo-img' and a.get('alt')=='Nijssen Computers' and 'static.wixstatic.com' in a.get('src','') for t,a in p.nodes),f.name+': existing logo must remain')
        check(p.nav==[('/#direct-hulp','Hulp'),('/#tarief','Tarieven'),('/#over-mij','Over mij'),('#contact','Contact'),('/#werkgebied','Regio')]+regio_nav_links(),f.name+': inconsistent navigation')
        check('Home' not in p.text,f.name+': English Home label')
        check(all(label!='Werkgebied' for _,label in p.nav),f.name+': Werkgebied must not be a separate nav item')
        check(any(t=='button' and a.get('class')=='nav-regio-toggle' and a.get('aria-expanded')=='false' and a.get('aria-controls')=='regio-menu' for t,a in p.nodes),f.name+': missing Regio toggle')
        check(sum(1 for t,a in p.nodes if t=='div' and a.get('class')=='nav-regio-group')==3,f.name+': Regio menu needs three town groups')
        check((len(p.json)==0 if is_404 else len(p.json)==1),f.name+': unexpected JSON-LD count')
        if p.json:
            types=[x.get('@type') for x in p.json[0].get('@graph',[])]
            check('LocalBusiness' in types,f.name+': missing LocalBusiness')
            check(types.count('LocalBusiness')==1,f.name+': duplicate LocalBusiness in JSON-LD')
            faq_limits = {
                'printer-hulp-leidschendam': (5, 6),
                'laptop-traag-leidschendam': (5, 8),
                'laptop-traag-voorschoten': (5, 8),
                'computer-laptop-reparatie-leidschendam-voorburg': (6, 8),
                'laptop-traag-voorburg': (6, 8),
                'mkb-it-beheer-leidschendam-voorburg': (6, 10),
                'spoed-computerhulp-leidschendam': (6, 8),
                'wifi-netwerk-hulp-leidschendam': (6, 8),
                'wifi-netwerk-hulp-voorburg': (6, 10),
                'wifi-netwerk-hulp-voorschoten': (6, 8),
                'virus-verwijderen-voorburg': (6, 10),
            }
            related_by_page = {
                'computer-laptop-reparatie-leidschendam-voorburg': ('/computerhulp-aan-huis-leidschendam','/computerhulp-aan-huis-voorburg','/laptop-traag-leidschendam','/laptop-traag-voorburg','/wifi-netwerk-hulp-leidschendam','/wifi-netwerk-hulp-voorburg','/contact','/virus-verwijderen-voorburg'),
                'laptop-traag-voorburg': ('/computerhulp-aan-huis-voorburg','/wifi-netwerk-hulp-voorburg','/computer-laptop-reparatie-leidschendam-voorburg','/laptop-traag-leidschendam','/contact','/virus-verwijderen-voorburg'),
                'mkb-it-beheer-leidschendam-voorburg': ('/computer-laptop-reparatie-leidschendam-voorburg','/wifi-netwerk-hulp-voorburg','/contact'),
                'spoed-computerhulp-leidschendam': ('/computerhulp-aan-huis-leidschendam','/computer-laptop-reparatie-leidschendam-voorburg','/wifi-netwerk-hulp-leidschendam','/laptop-traag-leidschendam','/contact'),
                'wifi-netwerk-hulp-leidschendam': ('/computerhulp-aan-huis-leidschendam','/laptop-traag-leidschendam','/wifi-netwerk-hulp-voorburg','/computer-laptop-reparatie-leidschendam-voorburg','/contact'),
                'wifi-netwerk-hulp-voorschoten': ('/computerhulp-aan-huis-voorschoten','/printer-hulp-voorschoten','/wifi-netwerk-hulp-leidschendam','/wifi-netwerk-hulp-voorburg'),
                'contact': ('/mkb-it-beheer-leidschendam-voorburg','/computer-laptop-reparatie-leidschendam-voorburg','/computerhulp-aan-huis-leidschendam','/computerhulp-aan-huis-voorburg','/laptop-traag-leidschendam','/laptop-traag-voorburg','/wifi-netwerk-hulp-leidschendam','/wifi-netwerk-hulp-voorburg','/spoed-computerhulp-leidschendam','/virus-verwijderen-voorburg'),
                'printer-hulp-leidschendam': (
                    '/computerhulp-aan-huis-leidschendam',
                    '/wifi-netwerk-hulp-leidschendam',
                    '/laptop-traag-leidschendam',
                    '/printer-hulp-voorburg',
                    '/printer-hulp-voorschoten',
                ),
                'wifi-netwerk-hulp-voorburg': (
                    '/wifi-netwerk-hulp-leidschendam',
                    '/wifi-netwerk-hulp-voorschoten',
                    '/computerhulp-aan-huis-voorburg',
                    '/laptop-traag-voorburg',
                    '/contact',
                    '/virus-verwijderen-voorburg',
                ),
                'virus-verwijderen-voorburg': (
                    '/computerhulp-aan-huis-voorburg',
                    '/laptop-traag-voorburg',
                    '/wifi-netwerk-hulp-voorburg',
                    '/computer-laptop-reparatie-leidschendam-voorburg',
                    '/contact',
                ),
                'laptop-traag-leidschendam': (
                    '/computerhulp-aan-huis-leidschendam',
                    '/wifi-netwerk-hulp-leidschendam',
                    '/printer-hulp-leidschendam',
                    '/laptop-traag-voorburg',
                    '/laptop-traag-voorschoten',
                    '/contact',
                ),
                'laptop-traag-voorschoten': (
                    '/computerhulp-aan-huis-voorschoten',
                    '/wifi-netwerk-hulp-voorschoten',
                    '/printer-hulp-voorschoten',
                    '/laptop-traag-leidschendam',
                    '/laptop-traag-voorburg',
                    '/contact',
                ),
            }
            quote_pages = ('printer-hulp-leidschendam', 'wifi-netwerk-hulp-voorburg')
            if f.stem in faq_limits:
                check('FAQPage' in types,f.name+': expected FAQPage schema')
                faq=next((x for x in p.json[0].get('@graph',[]) if x.get('@type')=='FAQPage'),None)
                questions=faq.get('mainEntity') if faq else []
                lo, hi = faq_limits[f.stem]
                check(isinstance(questions,list) and lo<=len(questions)<=hi,f.name+f': FAQPage needs {lo}–{hi} questions')
                for item in questions or []:
                    answer=(item.get('acceptedAnswer') or {})
                    check(item.get('@type')=='Question' and item.get('name') and answer.get('@type')=='Answer' and answer.get('text'),f.name+': invalid FAQ question')
                    check(item.get('name','') in p.text,f.name+': FAQ question not visible: '+item.get('name',''))
                    answer_text=answer.get('text') or ''
                    check(answer_text and answer_text in p.text,f.name+': FAQ answer not visible or does not match JSON-LD')
                if f.stem in quote_pages:
                    for name in ('Metselbedrijf Zwaan','Robin Swenne','Mireille van den Dop'):
                        check(name in p.text,f.name+': missing existing quote '+name)
                check('Veelgestelde vragen' in p.text,f.name+': missing FAQ heading')
                hrefs=[a.get('href') for t,a in p.nodes if t=='a']
                for path in related_by_page[f.stem]:
                    check(path in hrefs,f.name+': missing related '+path)
            else:
                check('FAQPage' not in types,f.name+': unexpected FAQPage')
            schema=json.dumps(p.json)
            check('openingHours' not in schema and 'sameAs' not in schema and 'AggregateRating' not in schema,f.name+': unverified metadata')
        canon=[a['href'] for t,a in p.nodes if t=='link' and a.get('rel')=='canonical']
        wanted=BASE+('/' if f.name=='index.html' else '/'+f.stem)
        check(canon==([] if is_404 else [wanted]),f.name+': incorrect canonical')
        check(any(t=='meta' and a.get('name')=='description' and len(a.get('content',''))>60 for t,a in p.nodes),f.name+': description missing')
        if is_404:
            check(any(t=='meta' and a.get('name')=='robots' and a.get('content')=='noindex' for t,a in p.nodes),'404.html: noindex missing')
            check('Deze pagina bestaat niet (meer)' in p.text,'404.html: missing not-found text')
        hrefs=[a.get('href','') for t,a in p.nodes if t=='a']
        for path in ('/printer-hulp-leidschendam','/computerhulp-aan-huis-voorschoten','/laptop-traag-voorschoten','/wifi-netwerk-hulp-voorschoten','/virus-verwijderen-voorburg'):
            check(path in hrefs,f.name+': footer must link '+path)
        for tag,a in p.nodes:
            if tag in ('a','link'):
                path=urlsplit(a.get('href','')).path
                check(not path.endswith('.html'),f.name+': public URL still uses .html: '+a.get('href',''))
            if tag=='meta' and a.get('property')=='og:url':
                check(not urlsplit(a.get('content','')).path.endswith('.html'),f.name+': og:url uses .html')
        def no_html_urls(obj):
            if isinstance(obj, dict):
                for key,val in obj.items():
                    if key in ('url','@id') and isinstance(val,str):
                        check(not urlsplit(val).path.endswith('.html'),f.name+': JSON-LD .html URL '+val)
                    no_html_urls(val)
            elif isinstance(obj, list):
                for item in obj: no_html_urls(item)
        if p.json: no_html_urls(p.json[0])
        titles={
            'computerhulp-aan-huis-leidschendam':'Computer reparatie & hulp aan huis Leidschendam | Nijssen',
            'laptop-traag-leidschendam':'Laptop traag of reparatie Leidschendam | Aan huis | Nijssen',
            'laptop-traag-voorschoten':'Laptop traag in Voorschoten | Nijssen Computers',
            'computerhulp-aan-huis-voorburg':'Computerhulp aan huis Voorburg | Snel & lokaal | Nijssen',
            'virus-verwijderen-voorburg':'Virus verwijderen Voorburg | Aan huis | Nijssen',
            'wifi-netwerk-hulp-voorburg':'Wifi problemen Voorburg | Hulp aan huis | Nijssen',
        }
        if f.stem in titles:
            check(f'<title>{titles[f.stem].replace("&","&amp;")}</title>' in text,f.name+': unexpected title')
        if f.stem=='laptop-traag-leidschendam':
            start=text.find('<p class="tagline">')
            end=text.find('</p>', start) if start!=-1 else -1
            lead=text[start:end] if start!=-1 and end!=-1 else ''
            for term in ('Leidschendam','thuis','opschonen','opstarten','updates','schijf','€60','half uur','06 2438 2361','WhatsApp'):
                check(term in lead,f.name+': citeerbare lead mist '+term)
            check('Ook Apple kan ik aan' not in text,f.name+': forbidden Apple claim')
            check(p.h1==['Laptop traag of reparatie in Leidschendam'],f.name+': H1 intent changed')
        if f.stem=='virus-verwijderen-voorburg':
            start=text.find('<p class="tagline">')
            end=text.find('</p>', start) if start!=-1 else -1
            lead_raw=text[start:end] if start!=-1 and end!=-1 else ''
            lead=lead_raw.replace('\u00a0',' ')
            for term in ('Voorburg','thuis','virus','2008','€60','half uur','06 2438 2361','WhatsApp'):
                check(term in lead,f.name+': citeerbare lead mist '+term)
            check('06\u00a02438\u00a02361' in lead_raw,f.name+': telefoon in de lead moet niet-afbreekbare spaties hebben')
            check('in Voorburg, en in' not in lead,f.name+': clumsy place list in lead')
            check('Ook Apple kan ik aan' not in text,f.name+': forbidden Apple claim')
            check('binnen 24 uur' not in text,f.name+': geen response-time belofte')
            check(p.h1==['Virus verwijderen aan huis in Voorburg'],f.name+': H1 intent changed')
            check('Apple Mac' in p.text,f.name+': missing Apple Mac wording')
            title=[a.get('content','') for t,a in p.nodes if t=='meta' and a.get('property')=='og:title']
            desc=[a.get('content','') for t,a in p.nodes if t=='meta' and a.get('name')=='description']
            check(title and len(title[0])<=60,f.name+': title longer than 60 characters')
            check(desc and 60<len(desc[0])<=155,f.name+': meta description must be 61–155 characters')
            service=next((x for x in p.json[0].get('@graph',[]) if x.get('@type')=='Service'),None)
            check(service and service.get('areaServed')=='Voorburg',f.name+': Service areaServed must be Voorburg')
        if f.stem=='laptop-traag-voorschoten':
            start=text.find('<p class="tagline">')
            end=text.find('</p>', start) if start!=-1 else -1
            lead=text[start:end] if start!=-1 and end!=-1 else ''
            for term in ('Voorschoten','thuis','2008','€60','half uur','06 2438 2361'):
                check(term in lead,f.name+': citeerbare lead mist '+term)
            check('Ook Apple kan ik aan' not in text,f.name+': forbidden Apple claim')
            check(p.h1==['Hulp bij een trage laptop in Voorschoten'],f.name+': H1 intent changed')
        if f.stem in ('wifi-netwerk-hulp-leidschendam','wifi-netwerk-hulp-voorschoten'):
            start=text.find('<p class="tagline">')
            end=text.find('</p>', start) if start!=-1 else -1
            lead=text[start:end].replace('\u00a0',' ') if start!=-1 and end!=-1 else ''
            town='Leidschendam' if f.stem.endswith('leidschendam') else 'Voorschoten'
            for term in (town,'thuis','€60','half uur','06 2438 2361','WhatsApp'):
                check(term in lead,f.name+': citeerbare lead mist '+term)
            check('Ook Apple kan ik aan' not in text,f.name+': forbidden Apple claim')
        if f.stem=='wifi-netwerk-hulp-voorburg':
            start=text.find('<p class="tagline">')
            end=text.find('</p>', start) if start!=-1 else -1
            lead_raw=text[start:end] if start!=-1 and end!=-1 else ''
            lead=lead_raw.replace('\u00a0',' ')
            for term in ('Voorburg','thuis','wifi','2008','€60','half uur','06 2438 2361','WhatsApp'):
                check(term in lead,f.name+': citeerbare lead mist '+term)
            check('06\u00a02438\u00a02361' in lead_raw,f.name+': telefoon in de lead moet niet-afbreekbare spaties hebben')
            check('in Voorburg, en in' not in lead,f.name+': clumsy place list in lead')
            check('Ook Apple kan ik aan' not in text,f.name+': forbidden Apple claim')
            check(p.h1==['Wifi-hulp aan huis in Voorburg'],f.name+': H1 intent changed')
            check('Apple Mac' in p.text,f.name+': missing Apple Mac wording')
            title=[a.get('content','') for t,a in p.nodes if t=='meta' and a.get('property')=='og:title']
            desc=[a.get('content','') for t,a in p.nodes if t=='meta' and a.get('name')=='description']
            check(title and len(title[0])<=60,f.name+': title longer than 60 characters')
            check(desc and 60<len(desc[0])<=155,f.name+': meta description must be 61–155 characters')
            service=next((x for x in p.json[0].get('@graph',[]) if x.get('@type')=='Service'),None)
            check(service and service.get('areaServed')=='Voorburg',f.name+': Service areaServed must be Voorburg')
        if f.stem=='computerhulp-aan-huis-leidschendam':
            for path in ('/printer-hulp-leidschendam','/computerhulp-aan-huis-voorschoten','/laptop-traag-voorschoten','/wifi-netwerk-hulp-voorschoten'):
                check(path in hrefs,f.name+': missing related '+path)
    home=parses.get('/')
    if home:
        check(len(home.h1)==1 and home.h1[0].startswith('Computerhulp aan huis'),'Homepage h1 must begin with Computerhulp aan huis')
        check(all(urlsplit(x).scheme in ('tel','mailto') or x=='https://wa.me/31624382361' for x in home.main_links),'Homepage content must not send customers to another article')
        for bad in ('quick-help-card','regio-card','Kies wat','Ook Apple kan ik aan','Meer over zakelijke IT-ondersteuning'):
            check(bad not in (ROOT/'index.html').read_text(), 'Forbidden homepage pattern: '+bad)
        for term in ('Apple','Windows','Linux','iPhone','iPad','Android'):check(term in home.text,'Platform missing: '+term)
    known_assets={'/jeroen.png','/jeroen-720.png','/_files/ugd/a467e1_485c7f11207647e3a05afcf4b5a87758.pdf'}
    graph={k:set() for k in parses}
    for url,p in parses.items():
        for tag,a in p.nodes:
            if tag not in ('a','link','script','img'):continue
            href=a.get('href',a.get('src',''))
            if not href:continue
            split=urlsplit(href)
            if split.scheme or split.netloc:continue
            links+=1
            target=unquote(split.path) or url
            if target in parses:
                graph[url].add(target)
                check(not split.fragment or unquote(split.fragment) in parses[target].ids,url+': missing anchor '+href)
            else:check(target in known_assets or (ROOT/target.lstrip('/')).is_file(),url+': missing asset/page '+href)
    seen=set(); queue=['/']
    while queue:
        x=queue.pop()
        if x in seen:continue
        seen.add(x);queue.extend(graph[x]-seen)
    check(seen==set(parses)-{'/404'},'Orphan pages: '+str(set(parses)-seen-{'/404'}))
    root=ET.parse(ROOT/'sitemap.xml').getroot();urls=[e.text for e in root.findall('{*}url/{*}loc')]
    check(set(urls)=={BASE+p for p in parses if p != '/404'},'Sitemap and canonical pages differ')
    check(len(urls)==len(set(urls))==18,'Sitemap count/duplicates')
    check(all(not urlsplit(u).path.endswith('.html') for u in urls),'Sitemap still lists .html URLs')
    sitemap_entries = root.findall('{*}url')
    check((ROOT/'sitemap.xml').read_text(encoding='utf-8')==expected['sitemap.xml'],
          'sitemap.xml: generated source is stale')
    homepage_entry = next((e for e in sitemap_entries if e.findtext('{*}loc') == BASE + '/'), None)
    check(homepage_entry is not None and homepage_entry.find('{*}lastmod') is None,
          'Homepage must not receive a lastmod from the unchanged homepage output')
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    detail_dates = []
    for entry in sitemap_entries:
        loc = entry.findtext('{*}loc')
        if loc == BASE + '/':
            continue
        filename = str(urlsplit(loc).path).strip('/') + '.html'
        # A page whose generated output differs from the committed version changes in
        # the upcoming commit, so its lastmod is today; an unchanged page keeps the
        # date of the last commit that touched it.
        if head_text(filename) != expected[filename]:
            expected_date = today
        else:
            expected_date = subprocess.run(
                ['git', 'log', '-1', '--format=%cs', '--', filename], cwd=ROOT,
                check=True, capture_output=True, text=True).stdout.strip()
        actual = entry.findtext('{*}lastmod')
        check(actual == expected_date,
              f'{loc}: lastmod must be the latest change to {filename} (expected {expected_date}, found {actual})')
        check(actual is not None, f'{loc}: reliable page-specific lastmod is required')
        detail_dates.append(actual)
    check(all(detail_dates), 'Sitemap detail pages require page-specific lastmod values')
    for filename in ('index.html','style.css'):
        check('overflow-x: hidden' not in (ROOT/filename).read_text(),'Do not mask overflow: '+filename)
    if failures:
        print('\n'.join('FAIL '+f for f in failures), file=sys.stderr);return 1
    print(f'PASS: {len(parses)} HTML pages, {links} internal references, every page reachable, consistent navigation, metadata, JSON-LD and homepage invariants.')
    return 0
if __name__=='__main__':raise SystemExit(main())
