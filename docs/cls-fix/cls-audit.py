import argparse, json, os, subprocess, time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--base',default='https://www.nijssencomputers.nl');p.add_argument('--label',default='before-live');p.add_argument('--repeat',type=int,default=1);a=p.parse_args()
root=Path('/var/lib/hermes/.hermes/profiles/website-builder/cache/scratch/cls-evidence');root.mkdir(exist_ok=True)
chrome='/var/lib/hermes/.hermes/tools/chromium-1208/chrome-linux64/chrome'
summary=[]
for repeat in range(a.repeat):
 for slug,name in [('/', 'home'),('/printer-hulp-leidschendam','printer'),('/laptop-traag-leidschendam','laptop')]:
  for mode in ['mobile','desktop']:
   out=root/f'{a.label}-{name}-{mode}-{repeat+1}'
   cmd=['npm','exec','--yes','--package=lighthouse@13.4.1','--','lighthouse',a.base.rstrip('/')+slug,'--only-categories=performance','--output=json','--output=html',f'--output-path={out}','--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage','--save-assets','--quiet']
   if mode=='desktop':cmd+=['--preset=desktop']
   env=dict(os.environ,CHROME_PATH=chrome)
   r=subprocess.run(cmd,env=env,capture_output=True,text=True)
   if r.returncode:raise RuntimeError(r.stderr)
   d=json.loads(Path(str(out)+'.report.json').read_text());aud=d['audits']
   item={'label':a.label,'page':name,'mode':mode,'repeat':repeat+1,'url':d['finalDisplayedUrl'],'cls':aud['cumulative-layout-shift']['numericValue'],'lcp_ms':aud['largest-contentful-paint']['numericValue'],'score':aud['performance'] if 'performance' in aud else d['categories']['performance']['score'],'warnings':d.get('runWarnings',[]),'culprits':aud.get('cls-culprits-insight',{}).get('details'),'layout_shift_elements':aud.get('layout-shifts',{}).get('details')}
   summary.append(item);(root/f'{a.label}-summary.json').write_text(json.dumps(summary,indent=2))
   print(json.dumps({k:v for k,v in item.items() if k not in ['culprits','layout_shift_elements']}),flush=True)
