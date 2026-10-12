# Závěrečná kontrola RoboRace

Datum: 12. 10. 2026. Prostředí: Windows, Webots R2025a, Python 3, Node.js 24.

## Nezávislost na internetu

Aplikace po instalaci Webots a Pythonu používá pouze soubory projektu, standardní knihovnu Pythonu, Webots API a systémové fonty. Nejsou potřeba npm ani pip balíčky, účet nebo cloud. Svět importuje pouze tři místní PROTO; neobsahuje vzdálené modely, textury ani zvukové soubory.

Robot Window potřebuje HTTP a WebSocket server místního procesu Webots. Používá pouze `localhost`, `127.0.0.1` nebo `[::1]`, tedy spojení uvnitř stejného počítače. Klient vzdáleného hostitele odmítne ještě před vytvořením WebSocketu. Content Security Policy povoluje místní skripty a styly a omezuje WS/WSS na stejné loopback adresy; ostatní zdroje jsou zakázané.

Wi-Fi, ethernet ani přístup na internet nejsou běhovou závislostí. Při této kontrole se systémové síťové připojení počítače nevypínalo. Nezávislost byla ověřena auditem assetů, kontrolou povolených adres bez skutečné sítě a skutečným spojením výhradně s místním Webots. Případné aktualizační funkce samotného Webots nebo rozšíření prohlížeče nejsou součástí aplikace.

Dokumentace výuky je kompletně místní. Původní zadání a historický protokol mají volitelné odkazy na oficiální zdroje; žádná funkce aplikace je neotevírá ani nestahuje.

## Provedené opravy

- Klient WWI ověřuje protokol a loopback hostitele; odmítá vzdálené URL i vložené přihlašovací údaje.
- Panel má Content Security Policy a novou verzi odkazů na CSS a JavaScript.
- Chybová zpráva výběru trasy správně uvádí čtyři úrovně.
- Silniční díly horské trasy mají jedinečná jména, takže Webots nehlásí jejich duplicity.
- README popisuje místní provoz a aktuální názvy tlačítek.
- Výukové etapy obsahují aktuální odkazy na assety a popis ověření nezávislosti na internetu.

## Výsledky kontrol

| Kontrola | Výsledek |
|---|---|
| Python logika | 22/22 prošlo |
| Audit místních assetů a omezení WWI | Prošel, bez síťových požadavků |
| Místní odkazy výukových etap a bloky kódu | Prošly |
| Skutečný panel v Chrome | 119 CSS pravidel, šířka 400 px |
| Modální nápověda při aktivní CSP | Otevření a zavření prošlo |
| Panel proti místnímu Webots | Připojení a povolení výběru trasy prošlo |
| Produkční klient WWI | Čtyři úrovně, validace, kamera, základní jízda 20,368 s, reconnect a reset prošly |
| Fyzikální integrační sada Webots | 20/21 prošlo |
| Základní ukázka | 10/10 platných jízd, 20,368 s, bez penalizací |
| Ukázka úrovně 2 | Platná jízda 20,384 s, bez penalizací |
| Ukázka úrovně 3 | Neprošla: první kužel v dráze vyvolal převrácení |

Fyzikální kontrola byla skutečně spuštěna v odděleném testovacím světě. Soutěžní žebříčky se při integrační sadě nepoužívají. WWI smoke běžel pouze v testovacím režimu. Historický protokol `overeni-webots.md` popisuje starší rozmístění překážek; jeho dřívější 21/21 není výsledkem současné geometrie.

## Zbývající problém mimo síťové závislosti

Třetí trasa potřebuje novou kalibraci ukázkového programu a rozmístění překážek. Současná ukázka narazí do prvního kužele a po 3,344 s skončí jako převrácení. Úroveň 4 se v této fyzikální sadě neprojíždí do cíle; smoke kontrola ověřila její přepnutí a výběr. Nelze proto označit všechny čtyři ukázkové jízdy za reprodukovatelně ověřené. Při změně geometrie třetí či čtvrté trasy je nutné změnit odpovídající `LEVEL_CONFIG_IDS`.

## Opakování

```powershell
python -m unittest discover -s tests -v
node tests/offline_assets.mjs
python tests/run_webots_integration.py --port 1252
```

Pro kontrolu WWI otevři `worlds/roborace.wbt`, spusť simulaci a použij její místní port:

```powershell
node tests/robot_window_smoke.mjs 1253
```

Aktuální strojově čitelné fyzikální výsledky jsou v `tests/webots/reports/integration.json`. Plný runner očekává 21 případů; jediná neúspěšná úroveň 3 správně způsobí nenulový návratový kód.
