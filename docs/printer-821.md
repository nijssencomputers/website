# Printerinhoud — reviewpakket 821

Aparte branch vanaf 7a04315; geen publicatie vóór Lieke's review. Homepage, gedeeld template, assets, stijl, navigatie, tracking en actieve instellingen zijn byte-identiek aan dat terugdraaipunt.

Voorburg legt wachtrijen, printerkeuze, software en proefscans uit. Voorschoten verklaart draadloos printen, AirPrint-ondersteuning, gastnetwerken en routerwissels. De pagina's zeggen expliciet dat dit geen ander lokaal aanbod is; geen wijken, cases, serviceverschillen of nieuwe claims verzonnen. Leidschendam behoudt het bestaande overzicht en krijgt een concrete lead. URL's, H1's, titles, canonical en bestaand schema blijven staan; sitemap alleen voor deze drie pagina's bijgewerkt.

Vijfwoordreeksoverlap, hoofdinhoud zonder nav/header/footer/script/style, gedeeld door kleinste unieke verzameling: Voorburg/Voorschoten lokaal 89,08% naar 8,41%, Leidschendam/Voorburg 83,84% naar 9,78%, Leidschendam/Voorschoten 54,15% naar 8,24%. Geen rankingwinst gemeten. tests/printer_checks.py bewaakt onderscheidende uitleg, tarieven, leadnummer en homepage/gedeelde invarianten; baseline-kopie is als negatieve controle aangetoond.

Groen: build --check, tools/check.py (19 HTML, 977 interne verwijzingen), printer_checks.py, browser_checks.py (133 normale/57 vergrote layouts en 19 no-JS), CLS-test met echte assets (alle CLS 0), 74 echte Apache-HTTP-regressies. Zelfgemaakte CDP-screenshots van alle drie pagina's op 1440 en 390 px, echte assets volledig geladen, geen horizontale overflow, telefoonnummers niet opgebroken. Browsertests hebben fixtures; echte assets zijn aanvullend afzonderlijk getest.

Lighthouse Voorburg desktop/mobiel performance 100/100 vóór en na; CLS 0. LCP 445->502 ms desktop en 1416->1537 ms mobiel. Dit is meer inhoud, niet een snelheidsclaim. Analytics tijdens labtests geblokkeerd.

Uitgebreid verslag, voor/na, bronmetingen en fouten letterlijk: /var/lib/hermes/.hermes/profiles/website-builder/cache/821/verslag.pdf en verslag.txt. Backup: /srv/scratch/backups/20261019-guusje-website-821, README met herstel en mag-wegdatum 2026-11-18. Herstel met een normale revert van deze inhoudscommit; homepage is niet betrokken.

De twee losse lokale conceptbranches website/821-shared-proposal en website/821-headers-proposal zijn géén onderdeel van deze inhoudswijziging en mogen niet mergen/publiceren zonder afzonderlijk akkoord. Lieke reviewt eerst; live nameting na een eventuele goedgekeurde publicatie.
