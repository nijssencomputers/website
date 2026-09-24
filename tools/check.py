#!/usr/bin/env python3
"""Offline regression checks; no third-party packages and no external network calls."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from build import outputs, BASE, regio_nav_links
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
    check(len(htmlfiles)==16, 'Exactly 16 existing HTML pages expected')
    for f in htmlfiles:
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
        check(len(p.json)==1,f.name+': expected one JSON-LD graph')
        if p.json:
            types=[x.get('@type') for x in p.json[0].get('@graph',[])]
            check('LocalBusiness' in types,f.name+': missing LocalBusiness')
            faq_limits = {
                'printer-hulp-leidschendam': (5, 6),
                'wifi-netwerk-hulp-voorburg': (6, 8),
            }
            related_by_page = {
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
                ),
            }
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
                    snippet=(answer.get('text') or '')[:50]
                    check(snippet and snippet in p.text,f.name+': FAQ answer not visible')
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
        check(canon==[wanted],f.name+': incorrect canonical')
        check(any(t=='meta' and a.get('name')=='description' and len(a.get('content',''))>60 for t,a in p.nodes),f.name+': description missing')
        hrefs=[a.get('href','') for t,a in p.nodes if t=='a']
        for path in ('/printer-hulp-leidschendam','/computerhulp-aan-huis-voorschoten','/laptop-traag-voorschoten','/wifi-netwerk-hulp-voorschoten'):
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
            'computerhulp-aan-huis-voorburg':'Computerhulp aan huis Voorburg | Snel & lokaal | Nijssen',
        }
        if f.stem in titles:
            check(f'<title>{titles[f.stem].replace("&","&amp;")}</title>' in text,f.name+': unexpected title')
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
    check(seen==set(parses),'Orphan pages: '+str(set(parses)-seen))
    root=ET.parse(ROOT/'sitemap.xml').getroot();urls=[e.text for e in root.findall('{*}url/{*}loc')]
    check(set(urls)=={BASE+p for p in parses},'Sitemap and canonical pages differ')
    check(len(urls)==len(set(urls))==16,'Sitemap count/duplicates')
    check(all(not urlsplit(u).path.endswith('.html') for u in urls),'Sitemap still lists .html URLs')
    for filename in ('index.html','style.css'):
        check('overflow-x: hidden' not in (ROOT/filename).read_text(),'Do not mask overflow: '+filename)
    if failures:
        print('\n'.join('FAIL '+f for f in failures), file=sys.stderr);return 1
    print(f'PASS: {len(parses)} HTML pages, {links} internal references, every page reachable, consistent navigation, metadata, JSON-LD and homepage invariants.')
    return 0
if __name__=='__main__':raise SystemExit(main())
