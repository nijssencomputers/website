#!/usr/bin/env python3
"""Chromium regression checks. Run against a local preview/Apache server, never a customer session."""
import argparse
import json
import re
import base64
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
WIDTHS=[320,360,375,390,414,768,1440]

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base',default='http://127.0.0.1:8765')
    ap.add_argument('--output',type=Path,default=Path('/tmp/nijssen-browser-results'))
    ap.add_argument('--chromium',default=None)
    ap.add_argument('--in-memory',action='store_true',help='Render source HTML with inlined CSS/JS and labelled asset fixtures; test HTTP separately.')
    args=ap.parse_args()
    if urlsplit(args.base).hostname not in ('localhost','127.0.0.1'):
        ap.error('Only local test servers are supported; this suite must not send analytics to production.')
    args.output.mkdir(parents=True,exist_ok=True)
    slugs=['/' if p.name=='index.html' else '/'+p.stem for p in sorted(ROOT.glob('*.html'))]
    result={'engine':'Chromium','widths':WIDTHS,'normal_layout_cases':0,'enlarged_text_cases':0,'failures':[],
        'asset_note':'External requests are stubbed. Existing logo and portrait are replaced by clearly labelled layout fixtures. Actual asset appearance and live network loading are not verified.',
        'checks':[], 'render_mode':'in-memory HTML; HTTP tested separately' if args.in_memory else 'local HTTP'}
    def check(ok,msg):
        if not ok:result['failures'].append(msg)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.chromium,headless=True,args=['--no-sandbox'])
        result['browser_version']=browser.version
        context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
        def route_request(route):
            url=route.request.url
            if 'static.wixstatic.com' in url:
                # Not a reproduction of the logo: explicit fixture for offline layout checks.
                svg='<svg xmlns="http://www.w3.org/2000/svg" width="280" height="66"><rect width="280" height="66" fill="#eeeeea"/><text x="12" y="39" fill="#2d5a3d" font-size="20" font-family="sans-serif">Bestaand logo (test)</text></svg>'
                route.fulfill(status=200,content_type='image/svg+xml',body=svg)
            elif url.endswith('/jeroen.png') or '/jeroen-720.' in url:
                svg='<svg xmlns="http://www.w3.org/2000/svg" width="160" height="160"><rect width="160" height="160" fill="#eeeeea"/><text x="12" y="82" fill="#566168" font-size="15" font-family="sans-serif">Bestaande foto</text><text x="12" y="106" fill="#566168" font-size="15" font-family="sans-serif">(test)</text></svg>'
                route.fulfill(status=200,content_type='image/svg+xml',body=svg)
            elif '/favicon.ico' in url:route.fulfill(status=204,body='')
            elif url.startswith(args.base):route.continue_()
            else:route.fulfill(status=200,content_type='application/javascript',body='/* External request suppressed for offline tests. */')
        context.route('**/*',route_request)
        def load_page(page,slug):
            if not args.in_memory:
                return page.goto(args.base+slug,wait_until='load')
            name='index.html' if slug=='/' else slug.lstrip('/')+'.html'
            html=(ROOT/name).read_text()
            html=re.sub(r'<link[^>]+rel="stylesheet"[^>]*>',lambda _: '<style>'+(ROOT/'style.css').read_text()+'</style>',html)
            html=re.sub(r'<script[^>]+src="([^"]+)"[^>]*>.*?</script>',lambda m: '<script>'+(ROOT/urlsplit(m[1]).path.lstrip('/')).read_text()+'</script>' if urlsplit(m[1]).path.lstrip('/') in ('nav.js','analytics-events.js') else '',html,flags=re.S)
            # Execute scripts after the document body exists (the originals use defer).
            local_scripts=''.join('<script>'+(ROOT/n).read_text()+'</script>' for n in ('nav.js','analytics-events.js'))
            for n in ('nav.js','analytics-events.js'):
                html=html.replace('<script>'+(ROOT/n).read_text()+'</script>','')
            html=html.replace('</body>',local_scripts+'</body>')
            def fixture(m):
                portrait='jeroen.png' in m[0] or 'jeroen-720' in m[0]
                w,h=(160,160) if portrait else (280,66)
                label='Bestaande foto (test)' if portrait else 'Bestaand logo (test)'
                svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="#eee"/><text x="8" y="{h//2}" font-family="sans-serif" font-size="14">{label}</text></svg>'
                uri='data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
                return re.sub(r'src="[^"]*"','src="'+uri+'"',m[0])
            html=re.sub(r'<img\b[^>]*>',fixture,html)
            page.set_content(html,wait_until='load')
            return None
        page=context.new_page()
        page.on('pageerror',lambda err:result['failures'].append('JavaScript exception: '+str(err)))
        for slug in slugs:
            for width in WIDTHS:
                page.set_viewport_size({'width':width,'height':900 if width>760 else 844})
                response=load_page(page,slug)
                if response:check(response.status==200,f'{slug} {width}: HTTP {response.status}')
                data=page.evaluate('''() => {
                    const h=document.querySelector('h1');
                    return {width:document.documentElement.clientWidth, scroll:document.documentElement.scrollWidth,
                      h1Height:h.getBoundingClientRect().height, line:parseFloat(getComputedStyle(h).lineHeight),
                      targets:Array.from(document.querySelectorAll('.cta-button')).map(x=>({w:x.getBoundingClientRect().width,h:x.getBoundingClientRect().height})),
                      offscreen:Array.from(document.querySelectorAll('main *, .site-header-inner, .footer-inner')).filter(x=>{
                        const r=x.getBoundingClientRect(); return r.width>0 && (r.right>innerWidth+1||r.left< -1);
                      }).slice(0,4).map(x=>x.tagName+'.'+x.className)
                    };
                }''')
                check(data['scroll']<=data['width']+1,f'{slug} {width}: horizontal overflow {data}')
                check(not data['offscreen'],f'{slug} {width}: clipped elements {data["offscreen"]}')
                check(all(x['w']>=44 and x['h']>=44 for x in data['targets']),f'{slug} {width}: contact targets below 44px')
                if slug=='/' and width==390:
                    check(data['h1Height']<=data['line']*1.1,'Homepage at 390px: H1 does not fit one line at default text size')
                    page.screenshot(path=str(args.output/'layout-mobile-390-testassets.png'),full_page=True)
                    result['home_390_h1_height']=data['h1Height'];result['home_390_h1_line_height']=data['line']
                if slug=='/' and width==1440:page.screenshot(path=str(args.output/'layout-desktop-1440-testassets.png'),full_page=True)
                if slug=='/mkb-it-beheer-leidschendam-voorburg' and width==390:page.screenshot(path=str(args.output/'layout-zakelijk-390-testassets.png'),full_page=True)
                result['normal_layout_cases']+=1
            for width in [320,390,768]:
                page.set_viewport_size({'width':width,'height':844})
                load_page(page,slug)
                page.evaluate("document.documentElement.style.fontSize='200%'")
                size=page.evaluate('({scroll:document.documentElement.scrollWidth,width:document.documentElement.clientWidth})')
                check(size['scroll']<=size['width']+1,f'{slug} {width} 200% text: horizontal overflow {size}')
                result['enlarged_text_cases']+=1
        # Disclosure navigation: keyboard, escape, same-page focus and resize.
        page.set_viewport_size({'width':390,'height':844})
        load_page(page,'/')
        btn=page.locator('.nav-toggle')
        check(btn.is_visible(),'Mobile menu control missing')
        check(not page.locator('#site-nav').is_visible(),'Mobile menu should start closed')
        btn.focus();page.keyboard.press('Space')
        check(btn.get_attribute('aria-expanded')=='true' and page.locator('#site-nav').is_visible(),'Space does not open menu')
        page.keyboard.press('Tab')
        check(page.evaluate('document.activeElement.textContent.trim()')=='Hulp','Tab does not enter navigation predictably')
        page.keyboard.press('Escape')
        check(btn.get_attribute('aria-expanded')=='false' and btn.evaluate('(el)=>document.activeElement===el'),'Escape does not close menu and restore focus')
        btn.click();page.locator('#site-nav a[href="#contact"]').click()
        check(btn.get_attribute('aria-expanded')=='false','Contact link does not close menu')
        check(page.evaluate('document.activeElement.id')=='contact','Contact target does not receive keyboard focus')
        load_page(page,'/');btn.click();page.set_viewport_size({'width':1440,'height':900})
        check(page.locator('#site-nav').is_visible(),'Desktop menu not visible after resize')
        page.locator('#site-nav a').first.focus();page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100)
        check(btn.evaluate('(el)=>document.activeElement===el'),'Breakpoint leaves focus in hidden navigation')
        result['checks'].append('Mobile menu: Space, Tab, Escape, anchor focus, desktop/mobile resize')
        # Regio: desktop mega menu and mobile accordion.
        page.set_viewport_size({'width':1440,'height':900})
        load_page(page,'/')
        regio=page.locator('.nav-regio-toggle')
        check(regio.is_visible(),'Desktop Regio control missing')
        check(regio.get_attribute('aria-expanded')=='false','Regio should start closed')
        regio.focus();page.keyboard.press('Enter')
        check(regio.get_attribute('aria-expanded')=='true' and page.locator('.nav-regio-menu').is_visible(),'Enter does not open Regio')
        check(page.locator('.nav-regio-group').count()==3,'Regio should have three town groups')
        check(page.locator('.nav-regio-overview').is_visible() and page.locator('.nav-regio-overview').get_attribute('href')=='/#werkgebied','Werkgebied overview missing from Regio panel')
        check(page.locator('.nav-regio-hub').first.inner_text()=='Leidschendam','Town hub is not the first group heading')
        check(page.locator('#site-nav > *').evaluate_all("els=>els.map(e=>e.classList.contains('nav-regio')?'Regio':e.textContent.trim())")==['Hulp','Tarieven','Over mij','Contact','Regio'],'Top-level nav order changed')
        box=page.locator('.nav-regio-menu').bounding_box()
        check(box and box['x']>=-1 and box['x']+box['width']<=1441,f'Regio panel leaves 1440 viewport {box}')
        page.keyboard.press('Escape')
        check(regio.get_attribute('aria-expanded')=='false' and regio.evaluate('(el)=>document.activeElement===el'),'Escape does not close Regio and restore focus')
        page.set_viewport_size({'width':1024,'height':900})
        regio.click()
        box=page.locator('.nav-regio-menu').bounding_box()
        check(box and box['x']>=-1 and box['x']+box['width']<=1025,f'Regio panel leaves 1024 viewport {box}')
        check(page.locator('.nav-regio-group').count()==3 and page.locator('.nav-regio-overview').is_visible(),'Regio panel incomplete at 1024')
        page.keyboard.press('Escape')
        page.set_viewport_size({'width':390,'height':844})
        load_page(page,'/')
        page.locator('.nav-toggle').click()
        check(regio.is_visible() and regio.get_attribute('aria-expanded')=='false','Mobile Regio control missing or open')
        regio.click()
        check(regio.get_attribute('aria-expanded')=='true' and page.locator('.nav-regio-overview').is_visible(),'Mobile Regio panel does not open')
        town=page.locator('.nav-town-toggle').first
        check(town.is_visible() and town.get_attribute('aria-expanded')=='false','Town accordion control missing or open')
        check(page.locator('.nav-regio-hub').first.is_visible(),'Town hub hidden while accordion is collapsed')
        check(not page.locator('#regio-town-leidschendam').is_visible(),'Town services should start collapsed on mobile')
        town.click()
        check(town.get_attribute('aria-expanded')=='true' and page.locator('#regio-town-leidschendam').is_visible(),'Town accordion does not open')
        check(page.locator('#regio-town-leidschendam a').count()>=4,'Leidschendam services missing from accordion')
        result['checks'].append('Regio menu: desktop keyboard, three town groups, mobile accordion')
        # Homepage help and area are not controls disguised as text.
        load_page(page,'/')
        check(page.locator('#direct-hulp a, #direct-hulp button, #direct-hulp [tabindex], #werkgebied a, #voor-wie a').count()==0,'Homepage choices are still interactive')
        result['checks'].append('No interactive help choices, city tiles, or business detour in homepage content')
        # Click exactly once; prevent navigation and inspect dataLayer without external GA.
        page.evaluate("document.addEventListener('click', e=>e.preventDefault());window.dataLayer=[]")
        for selector,method in [('.hero .cta-whatsapp','whatsapp'),('.hero .cta-phone','phone'),('.contact-email a','email')]:
            page.locator(selector).click()
            events=page.evaluate("Array.from(window.dataLayer).filter(x=>x[0]==='event').map(x=>({name:x[1],method:x[2].method}))")
            check(events==[{'name':'contact_click','method':method}],f'Contact event duplicate or wrong type: {method} {events}')
            page.evaluate('window.dataLayer=[]')
        result['checks'].append('One contact_click per WhatsApp, telephone and email click; no automatic generate_lead')
        # Reduced motion removes smooth scrolling.
        page.emulate_media(reduced_motion='reduce')
        check(page.evaluate("getComputedStyle(document.documentElement).scrollBehavior")=='auto','Reduced motion ignored')
        result['checks'].append('Reduced-motion preference')
        context.close()
        # No-JS fallback: links and contact do not depend on client rendering.
        nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
        nojs.route('**/*',route_request)
        q=nojs.new_page()
        for slug in slugs:
            load_page(q,slug)
            check(q.locator('#site-nav').is_visible(),slug+': no-JS menu hidden')
            check(q.locator('h1').is_visible() and q.locator('a[href="tel:+31624382361"]').first.is_visible(),slug+': no-JS content/contact absent')
        result['no_js_pages']=len(slugs)
        nojs.close();browser.close()
    result['passed']=not result['failures']
    (args.output/'browser-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
