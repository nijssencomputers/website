#!/usr/bin/env python3
"""Test the actual Apache rules on localhost; does not call the production site."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError
from urllib.parse import urlsplit

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',default='http://127.0.0.1:8765')
    ap.add_argument('--output',type=Path,default=Path('/tmp/nijssen-http-results.json'))
    args=ap.parse_args()
    if urlsplit(args.base).hostname not in ('localhost','127.0.0.1'):ap.error('Use a local Apache server.')
    root=Path(__file__).resolve().parents[1]
    opener=build_opener(NoRedirect())
    results=[]
    def verify(path,status,location=None):
        try:r=opener.open(Request(args.base+path),timeout=5)
        except HTTPError as e:r=e
        actual_location=r.headers.get('Location','')
        actual_path=urlsplit(actual_location).path
        if urlsplit(actual_location).query:actual_path+='?'+urlsplit(actual_location).query
        if urlsplit(actual_location).fragment:actual_path+='#'+urlsplit(actual_location).fragment
        ok=r.status==status and (location is None or actual_path==location)
        results.append({'path':path,'expected_status':status,'status':r.status,'expected_location':location,'location':actual_location,'passed':ok})
        r.close()
    for f in sorted(root.glob('*.html')):
        canonical='/' if f.name=='index.html' else '/'+f.stem
        verify(canonical,200)
        verify('/'+f.name,301,canonical)
        verify('/'+f.name+'?utm_source=test',301,canonical+'?utm_source=test')
    for path,location in {'/index':'/','/copy-of-contact':'/contact','/copy-of-diensten':'/#diensten','/copy-of-tarieven':'/#tarief','/copy-of-zakelijk':'/mkb-it-beheer-leidschendam-voorburg','/kopie-van-home':'/'}.items():verify(path,301,location)
    verify('/niet-bestaande-pagina.html',301,'/niet-bestaande-pagina')
    for path in ['/style.css?v=20260924-home1','/nav.js?v=20260924-home1','/analytics-events.js?v=20260924-home1','/robots.txt','/sitemap.xml']:verify(path,200)
    for path in ['/src/pages.json','/tools/build.py','/tests/browser_checks.py','/.git/config']:verify(path,403)
    verify('/niet-bestaande-pagina',404)
    report={'server':'Local Apache with the delivered .htaccess','cases':len(results),'passed':all(r['passed'] for r in results),'results':results,'not_tested':'Live hosting/Cloudflare/TLS, remote logo, unchanged original photo and terms PDF.'}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'cases':report['cases'],'passed':report['passed'],'failures':[r for r in results if not r['passed']]},ensure_ascii=False,indent=2))
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
