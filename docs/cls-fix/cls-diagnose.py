import argparse, json, time
from pathlib import Path
from playwright.sync_api import sync_playwright
p=argparse.ArgumentParser();p.add_argument('--base',default='https://www.nijssencomputers.nl');p.add_argument('--label',default='before-live');p.add_argument('--variant',choices=['normal','delay-nav','block-nav','early-ready','block-portrait'],default='normal');a=p.parse_args()
out=Path('/var/lib/hermes/.hermes/profiles/website-builder/cache/scratch/cls-evidence');out.mkdir(exist_ok=True)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/var/lib/hermes/.hermes/tools/chromium-1208/chrome-linux64/chrome',headless=True,args=['--no-sandbox'])
 results=[]
 for mode,w,h in [('mobile',412,823),('desktop',1350,940)]:
  c=b.new_context(viewport={'width':w,'height':h},device_scale_factor=1)
  page=c.new_page();cdp=c.new_cdp_session(page);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
  cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':1638.4*1024/8,'uploadThroughput':750*1024/8})
  page.add_init_script('''window.probe={shifts:[],events:[]};
  const geometry=()=>({time:performance.now(),ready:document.documentElement.className,header:document.querySelector('header')?.getBoundingClientRect().toJSON(),main:document.querySelector('main')?.getBoundingClientRect().toJSON(),portrait:document.querySelector('.about-img')?.getBoundingClientRect().toJSON()});
  new PerformanceObserver(list=>{for(const e of list.getEntries())window.probe.shifts.push({time:e.startTime,value:e.value,input:e.hadRecentInput,sources:e.sources.map(s=>({node:s.node?.tagName+'#'+s.node?.id+'.'+s.node?.className,previous:s.previousRect.toJSON(),current:s.currentRect.toJSON()})),geometry:geometry()})}).observe({type:'layout-shift',buffered:true});
  new MutationObserver(()=>window.probe.events.push(geometry())).observe(document.documentElement,{attributes:true,attributeFilter:['class']});
  document.addEventListener('DOMContentLoaded',()=>window.probe.events.push({event:'DOMContentLoaded',...geometry()}));
  ''')
  if a.variant=='delay-nav':
   def delay(route):
    time.sleep(2);route.continue_()
   page.route('**/nav.js*',delay)
  if a.variant=='block-nav':page.route('**/nav.js*',lambda r:r.abort())
  if a.variant=='block-portrait':page.route('**/jeroen-720.png',lambda r:r.abort())
  if a.variant=='early-ready':
   def early(route):
    response=route.fetch();html=response.text().replace('<head>','<head><script>document.documentElement.classList.add("nav-ready")</script>')
    route.fulfill(response=response,body=html)
   page.route(a.base+'/',early)
  page.goto(a.base+'/',wait_until='load');page.wait_for_timeout(1500)
  probe=page.evaluate('window.probe');probe['resources']=page.evaluate("performance.getEntriesByType('resource').map(r=>({name:r.name,start:r.startTime,end:r.responseEnd}))")
  probe['portrait']=page.locator('.about-img').evaluate('(e)=>({width:e.width,height:e.height,naturalWidth:e.naturalWidth,naturalHeight:e.naturalHeight,complete:e.complete,aspect:getComputedStyle(e).aspectRatio})')
  # Screenshots taken directly through CDP, real production/local assets.
  import base64
  for full in [False,True]:
   dims=cdp.send('Page.getLayoutMetrics')['cssContentSize'];params={'format':'png','captureBeyondViewport':full,'fromSurface':True}
   if full:params['clip']={'x':0,'y':0,'width':w,'height':dims['height'],'scale':1}
   data=cdp.send('Page.captureScreenshot',params)['data'];(out/f'{a.label}-{a.variant}-{mode}-{("full" if full else "viewport")}.png').write_bytes(base64.b64decode(data))
  item={'label':a.label,'variant':a.variant,'mode':mode,**probe};results.append(item)
  print(json.dumps({'mode':mode,'variant':a.variant,'shifts':probe['shifts'],'events':probe['events'],'portrait':probe['portrait']}),flush=True)
  c.close()
 b.close();(out/f'{a.label}-{a.variant}-diagnose.json').write_text(json.dumps(results,indent=2))
