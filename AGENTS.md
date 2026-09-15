# Website-afspraken — Nijssen Computers

De website is voor klanten. Behoud het bestaande logo, de lichte achtergrond, het groen en de rustige opmaak. Geen nieuw framework of CMS introduceren zonder expliciete opdracht.

## Inhoud en bediening

- De homepage-H1 is exact `Computerhulp aan huis`.
- De homepage beantwoordt zelfstandig: kan Jeroen helpen, waar werkt hij, wat kost het en hoe neem ik contact op?
- Hulpvragen en werkgebied op de homepage zijn gewone tekst. Geen klikbare kaarten, keuzewijzers, nepknoppen of hover-effecten op niet-interactieve inhoud.
- Het zakelijke blok op de homepage is volledig leesbaar zonder door te klikken.
- Houd op alle pagina's hetzelfde echte logo en hetzelfde Nederlandstalige menu in dezelfde volgorde. Gebruik geen `Home` of regio-dropdown.
- Apple/macOS/iPhone/iPad, Windows en Linux zijn gewone onderdelen van de dienstverlening. Geen `Ook Apple kan ik aan`, geen ongefundeerde specialistenclaims.
- Telefoon en WhatsApp zijn echte contactacties; e-mail blijft beschikbaar. Geen nieuwe vensters zonder noodzaak, geen zwevende widgets, pop-ups of FAQ-blokken voor SEO.
- Geen nieuwe plaats × probleem-pagina's zonder aantoonbare unieke klantwaarde. Bestaande URL's niet verwijderen of verplaatsen zonder data en redirects.
- Geen verzonnen certificeringen, adressen, reviews, openingstijden, garanties of beschikbaarheid. De bestaande tarieven en facturatie-eenheden niet wijzigen zonder opdracht.
- De drie overgenomen klantcitaten komen uit de bestaande website. Voeg geen sterren of review-schema toe zonder controleerbare bron.

## Bron en tests

De publieke HTML is statisch en wordt meegeleverd. De gedeelde bron staat in `src/layout.html`, `src/home.html` en `src/pages.json`. Verander de bron, draai `python3 tools/build.py` en controleer met `python3 tools/build.py --check` en `python3 tools/check.py`. Bewerk niet zestien headers afzonderlijk.

Test relevante veranderingen met `tests/browser_checks.py`, inclusief 320–1440 px en vergrote tekst. Apache-regels testen met `tests/http_checks.py` tegen een lokale Apache-server. `tools/serve.py` is alleen een eenvoudige preview, geen volledige Apache-emulatie.

Verberg overflow niet. De titel past op 390 px bij normale tekstgrootte, maar mag bij vergroten doorlopen. De website en navigatie moeten zonder JavaScript bruikbaar blijven. Respecteer verminderde beweging en behoud veilige schermranden op iPhone.

Meet een klik als `contact_click`, niet als een gegarandeerde aanvraag. De GA4-accountinstellingen, toestemming en privacy-informatie zijn aparte controles; deze code is geen verklaring van AVG-conformiteit.

## Publicatie

Gebruik `python3 tools/build.py --deploy ../website-publicatie` voor een nieuwe map met uitsluitend publieke bestanden. Hiervoor moeten het oorspronkelijke `jeroen.png` en de bestaande voorwaarden-PDF in de checkout aanwezig zijn. Publiceer geen audits, klantgegevens, bronmappen, tests of back-ups.

Maak steeds onderscheid tussen lokaal aangepast, naar GitHub gepusht en op de webhost gepubliceerd. Claim geen geslaagde push of livegang zonder afzonderlijke verificatie.
