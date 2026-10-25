#!/usr/bin/env python3
"""Regressie: printerpagina's houden nuttige verschillende inhoud en vaste bedrijfsfeiten."""
from pathlib import Path
from html.parser import HTMLParser
import itertools,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
class MainText(HTMLParser):
    def __init__(self):
        super().__init__(); self.main=False;self.skip=0;self.text=[]
    def handle_starttag(self,tag,attrs):
        if tag=='main':self.main=True
        if tag in ('script','style','nav','footer','header'):self.skip+=1
    def handle_endtag(self,tag):
        if tag=='main':self.main=False
        if tag in ('script','style','nav','footer','header'):self.skip-=1
    def handle_data(self,data):
        if self.main and not self.skip:self.text.append(data)
def shingles(text):
    words=re.findall(r'\b\w+\b',text.lower())
    return set(tuple(words[i:i+5]) for i in range(len(words)-4))
def main():
    pages=json.loads((ROOT/'src/pages.json').read_text()); sets={}; result=[]
    expected={'voorburg':('afdrukwachtrij','proefscan','driver-updater'), 'voorschoten':('AirPrint','gastnetwerk','fabrieksreset'), 'leidschendam':('wachtrij','scanner','printersoftware')}
    for city,terms in expected.items():
        slug='printer-hulp-'+city;p=next(p for p in pages if p['slug']==slug)
        h=(ROOT/(slug+'.html')).read_text();parser=MainText();parser.feed(h)
        text=' '.join(parser.text);sets[slug]=shingles(text)
        assert all(t.casefold() in text.casefold() for t in terms),(slug,terms)
        assert all(t in p['intro'] for t in ('€60','half uur','06\u00a02438\u00a02361')),(slug,'leadfeiten')
        assert p['heading']=='Printerhulp in '+p['city']
        assert 'garantie op herstel' not in p['intro']
    for a,b in itertools.combinations(sorted(sets),2):
        percent=100*len(sets[a]&sets[b])/min(len(sets[a]),len(sets[b]))
        # This is an anti-copy guard, not a ranking target or a word quota.
        assert percent<50,(a,b,percent)
        result.append({'a':a,'b':b,'smaller_set_overlap_pct':round(percent,2),'jaccard_pct':round(100*len(sets[a]&sets[b])/len(sets[a]|sets[b]),2)})
    for name in ['index.html','src/home.html','src/layout.html','style.css','nav.js','analytics-events.js','jeroen.png','jeroen-720.png','.htaccess','_redirects','robots.txt']:
        before=subprocess.check_output(['git','show','7a04315:'+name],cwd=ROOT)
        assert (ROOT/name).read_bytes()==before,('onbedoelde gedeelde wijziging',name)
    print(json.dumps({'passed':True,'pairs':result,'homepage_and_shared_assets_unchanged':True},indent=2))
if __name__=='__main__':main()
