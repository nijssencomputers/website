# Nijssen Computers — statische website

De website behoudt de bestaande 16 publieke pagina's. De homepage is zelfstandig bruikbaar; hulpvragen en werkgebied zijn geen klikbare kaarten. Alle pagina's hebben dezelfde kop en hetzelfde Nederlandstalige menu. HTML, CSS en twee kleine scripts zijn voldoende op de webhost; Python is daar niet nodig.

## Bewerken

Bronbestanden:

- `src/home.html`: inhoud van de homepage.
- `src/pages.json`: inhoud van de bestaande vervolgpagina's.
- `src/layout.html`: gedeelde kop, menu, metadata en voettekst.
- `style.css`: vormgeving.
- `nav.js`: alleen het mobiele menu.
- `analytics-events.js`: één `contact_click` per contactactie; een klik is geen bevestigde aanvraag.

Na een wijziging, vanuit de repository:

```sh
python3 tools/build.py
python3 tools/build.py --check
python3 tools/check.py
```

Dit vereist Python 3.9 of hoger en geen extra Python-pakketten. De geproduceerde HTML blijft in de repository staan. De webhost heeft geen build-stap nodig.

## Lokaal bekijken en testen

```sh
python3 tools/serve.py
```

Open de getoonde lokale URL. Dit is een eenvoudige previewserver; hij test geen Apache-redirects.

Browsertests vereisen afzonderlijk Playwright en Chromium. Installatie van testgereedschap is niet nodig voor de website zelf. Gebruik een lokaal testadres, nooit een echte klantsessie:

```sh
python3 tests/browser_checks.py --base http://127.0.0.1:8765 --output /tmp/nijssen-browser-results
python3 tests/http_checks.py --base http://127.0.0.1:8765
```

De tweede test vereist een echte lokale Apache-server met deze `.htaccess`. De browsertest blokkeert externe analytics en gebruikt expliciet gelabelde testafbeeldingen. `--in-memory` kan HTML/CSS/JS-layout testen zonder browsernavigatie; HTTP moet dan apart worden getest. `--chromium /pad/naar/chromium` kiest een aanwezig Chromium-programma.

## Publieke uploadmap maken

Pas het wijzigingspakket eerst toe op de bestaande checkout. Behoud `jeroen.png` en de bestaande PDF in `_files/ugd/`; deze ongewijzigde binaire bestanden zitten niet in het wijzigingspakket.

```sh
python3 tools/build.py --check
python3 tools/build.py --deploy ../website-publicatie
```

De doelmap moet nog niet bestaan. Zij bevat alle 16 HTML-pagina's, CSS, scripts, sitemap, robots.txt, `.htaccess`, de foto en voorwaarden. Upload alleen de inhoud van die map via de bestaande veilige publicatiemethode. Neem `.htaccess` mee. Wis niet zomaar andere bestanden van de host.

Bronmappen, audits, tests en back-ups mogen niet naar de publieke webroot. De Apache-configuratie is bedoeld voor een website in de domeinroot. HTTPS, voorkeursdomein en Cloudflare-instellingen blijven onder de bestaande hostingconfiguratie; deze worden hier niet geraden of gewijzigd.

## Controle na publicatie

Controleer op de live site de homepage, mobiele menu, telefoon/WhatsApp/e-mail, zakelijke pagina, foto, logo en voorwaarden. Controleer alle extensionless URL's, redirects en een echte 404. Test Safari op iPhone. Controleer daarna Search Console, eventuele firewallblokkades voor crawlers en GA4 DebugView. Druk voor tests geen echte klantaanvragen door.

De site behoudt het bestaande GA4-meet-ID. Advertentiepersonalisatie en Google signals zijn in de paginacode uitgeschakeld. Toestemming, accountinstellingen en privacy-informatie moeten afzonderlijk worden beoordeeld; dit is geen volledige privacy-audit.

Lees ook `AGENTS.md` voordat een volgende agent wijzigingen maakt.
