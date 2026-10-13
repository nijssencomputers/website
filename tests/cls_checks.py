#!/usr/bin/env python3
"""Cold-load CLS regression with real assets; local preview/Apache only."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--base', default='http://127.0.0.1:8765')
    ap.add_argument('--chromium', required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    if urlsplit(args.base).hostname not in ('localhost', '127.0.0.1'):
        ap.error('Use a local server.')
    cases = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=args.chromium, args=['--no-sandbox'])
        for width, height in [(412, 823), (1350, 940)]:
            for slug in ['/', '/printer-hulp-leidschendam', '/laptop-traag-leidschendam']:
                context = browser.new_context(viewport={'width': width, 'height': height})
                page = context.new_page()
                cdp = context.new_cdp_session(page)
                cdp.send('Network.enable')
                cdp.send('Network.setCacheDisabled', {'cacheDisabled': True})
                cdp.send('Network.emulateNetworkConditions', {
                    'offline': False, 'latency': 150,
                    'downloadThroughput': 1638.4 * 1024 / 8,
                    'uploadThroughput': 750 * 1024 / 8,
                })
                page.add_init_script("""window.clsEntries=[];
                    new PerformanceObserver(list=>list.getEntries().forEach(e=>{
                      if(!e.hadRecentInput)window.clsEntries.push({time:e.startTime,value:e.value});
                    })).observe({type:'layout-shift',buffered:true});""")
                page.goto(args.base + slug, wait_until='networkidle')
                page.wait_for_timeout(1000)
                entries = page.evaluate('window.clsEntries')
                # Sum is a stricter bound than the maximum CLS session window.
                cls = sum(e['value'] for e in entries)
                cases.append({'width': width, 'page': slug, 'cls_upper_bound': cls,
                              'shifts': entries, 'passed': cls < 0.1})
                if slug == '/':
                    portrait = page.locator('.about-img').evaluate('(e)=>({w:e.width,h:e.height,nw:e.naturalWidth,nh:e.naturalHeight})')
                    cases.append({'width': width, 'portrait': portrait,
                                  'passed': portrait['nw'] == 720 and portrait['nh'] == 816 and portrait['w'] > 0})
                context.close()
            context = browser.new_context(viewport={'width': width, 'height': height})
            page = context.new_page()
            page.route('**/nav.js*', lambda r: r.abort())
            page.goto(args.base + '/', wait_until='networkidle')
            cases.append({'width': width, 'case': 'nav download failed',
                          'passed': page.locator('#site-nav').is_visible()
                          and page.locator('.nav-regio-fallback').is_visible()
                          and page.locator('a[href="tel:+31624382361"]').first.is_visible()})
            context.close()
        browser.close()
    result = {'passed': all(c['passed'] for c in cases), 'cases': cases}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
