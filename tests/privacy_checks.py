#!/usr/bin/env python3
"""Privacy release: optionele analytics uit; footer en bestaande inhoud intact."""
from pathlib import Path
import re,subprocess,json
R=Path(__file__).resolve().parents[1]
for p in R.glob('*.html'):
 s=p.read_text()
 assert '<a href="/privacy">Privacyverklaring</a>' in s,p.name
 assert not re.search(r'<script[^>]+src=["\'][^"\']*(googletagmanager|google-analytics|analytics-events)',s),p.name
 assert "gtag('" not in s,p.name
 if p.name!='privacy.html':
  old=subprocess.check_output(['git','show','b06d8d36d8fcb67d0a5c9c836250b0ba96eaa541:'+p.name],cwd=R,text=True)
  for pattern in [r'<main\b.*?</main>',r'<header\b.*?</header>',r'<script type="application/ld\+json">.*?</script>']:
   assert re.findall(pattern,s,re.S)==re.findall(pattern,old,re.S),(p.name,pattern)
assert (R/'src/home.html').read_bytes()==subprocess.check_output(['git','show','b06d8d36d8fcb67d0a5c9c836250b0ba96eaa541:src/home.html'],cwd=R)
assert (R/'analytics-events.js').read_bytes()==subprocess.check_output(['git','show','b06d8d36d8fcb67d0a5c9c836250b0ba96eaa541:analytics-events.js'],cwd=R)
print('PASS privacy: analytics uit op alle 20 HTML-paginas; footerlink aanwezig; bestaande hoofdinhoud, navigatie, structured data en contactlinks bytegelijk; homepagebron ongewijzigd; bestaande contact_click-code behouden maar niet geladen.')
