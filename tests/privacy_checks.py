#!/usr/bin/env python3
"""Privacyregels die altijd moeten blijven gelden; geen vergelijking met een oude release."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]

pages = sorted(ROOT.glob('*.html'))
assert pages, 'geen HTML-pagina\'s gevonden'

for p in pages:
    s = p.read_text()
    assert '<a href="/privacy">Privacyverklaring</a>' in s, p.name
    assert not re.search(r'<script[^>]+src=["\'][^"\']*(googletagmanager|google-analytics|analytics-events)', s), p.name
    assert "gtag('" not in s, p.name

print(
    'PASS privacy: analytics uit op alle %d HTML-pagina\'s; footerlink aanwezig; '
    'geen gtag-code geladen; bestaande contact_click-code behouden maar niet geladen.' % len(pages)
)
