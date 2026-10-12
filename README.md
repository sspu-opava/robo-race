# RoboRace Junior

Podrobný návod k vytvoření celé aplikace je rozdělen do devíti navazujících etap v [obsahu výukového postupu](docs/vyukovy-postup/00-obsah-a-priprava.md).

Závěrečný audit, místní provoz a aktuální výsledky kontrol jsou v [protokolu závěrečné kontroly](docs/zaverecna-kontrola.md).

Lokální soutěžní simulace pro Webots: žáci píší krátké programy v RoboScriptu a řídí fyzikální čtyřkolový robot na čtyřech úrovních tratí. Každá má tři checkpointy a vlastní žebříček.

## Spuštění ve Windows

1. Nainstalujte Webots R2025a nebo kompatibilní vydání s Python 3 controller API. Projekt byl načten ve Webots R2025a; běh přes Robot Window je popsaný níže.
2. Otevřete Webots a zvolte **File → Open World…**.
3. Otevřete `worlds/roborace.wbt` z této složky. Projekt nevyžaduje stažení balíčků ani připojení ke cloudu.
4. Spusťte simulaci tlačítkem **Run**. Robot Window se otevře dvojklikem na robota nebo přes **Show Robot Window** v kontextové nabídce robota. V závislosti na nastavení Webots se panel zobrazí ve webovém prohlížeči.
5. V panelu vyberte obtížnost trasy. Změna načte ukázkový program pro danou úroveň; pro vlastní program můžete použít příklady **Rovinka** nebo **Zatáčka**. Nápovědu otevřete tlačítkem **?**. Stiskněte **Ověřit**, potom **Testovat**. Po úpravě textu můžete test opakovat bez omezení.
6. Pro soutěžní pokus vyplňte přezdívku a stiskněte **Soutěžit**. Výsledky se ukládají odděleně podle trasy: úroveň 1 do `data/leaderboard.json`, další úrovně do souborů `data/leaderboard-level-2.json` až `data/leaderboard-level-4.json`.

Po otevření světa je celá dráha vidět z vyvýšené kamery. Ovládací Robot Window používejte vedle 3D okna Webots. Pokud pohled omylem posunete, tlačítko **Zobrazit dráhu** v panelu obnoví přehled celé arény; ve Webots lze také použít **View → Restore Viewpoint**. Po úpravě projektu znovu načtěte `worlds/roborace.wbt`, aby se použily opravené PROTO a kamera.

Úroveň 1 zachovává základní okruh. Úroveň 2 přidává fyzické vlny. Úroveň 3 obsahuje slalom a bariéry uvnitř jízdního pruhu. Úroveň 4 vede delší serpentinu do stoupání a přidává překážky i různě velké hrboly. Každá úroveň má vlastní ukázkový program a konfiguraci žebříčku. Dosavadní fyzikální zkoušky úrovní 1 a 3 jsou popsané v [protokolu ověření](docs/overeni-webots.md).

Závodní čas vychází ze simulačního času Webots. Panel komunikuje s controllerem přes místní Webots Robot Window / WWI WebSocket. HTML, CSS, JavaScript a Python jsou součástí projektu.

## Provoz bez internetu

Po instalaci Webots a Pythonu aplikace nepotřebuje internet, účet, npm ani pip balíčky. Modely, tratě, fonty systému, nápověda, skripty a výsledky jsou místní. Panel otevřete přes Webots na `localhost`, `127.0.0.1` nebo `[::1]`; toto spojení uvnitř počítače funguje i bez připojení k síti. Vzdálené hostitele klient odmítá a Content Security Policy panelu blokuje externí zdroje. Samostatné otevření HTML přes `file://` není způsob spuštění simulace.

Kontrolu místních souborů a omezení WWI lze spustit bez serveru nebo síťových požadavků:

```powershell
node tests/offline_assets.mjs
```

Node.js je potřebný pouze pro tyto vývojové kontroly. Odkazy na oficiální zdroje v původním zadání a historickém protokolu jsou volitelné bibliografické odkazy; aplikace je nenačítá.

## RoboScript

Každý řádek obsahuje jeden velkými písmeny zapsaný příkaz. Komentář začíná `#`. Desetinný oddělovač je tečka a argumenty odděluje čárka.

```text
PLYN(45)
DOPREDU(1.2)
VLEVO(55, 0.8)
BRZDA(0.4)
```

Jediných šest povelů je `PLYN(p)`, `DOPREDU(t)`, `DOZADU(t)`, `VLEVO(k, t)`, `VPRAVO(k, t)` a `BRZDA(t)`. Plyn nastavuje cílovou rychlost. Robot zrychluje postupně; v zatáčce se projevuje setrvačnost a smyk. Vyšší plyn tedy nemusí znamenat rychlejší platný čas.

Maximálně 40 instrukcí, 32 sekund celkové délky časovaných instrukcí, 5 sekund na jeden pohybový příkaz a 35 sekund soutěžního času. Tato pravidla ověřuje Python controller.

## Soutěž a pořadatel

- Platné oficiální jízdy zapisují přezdívku, UTC datum, neupravený čas, penalizace, výsledný čas, zdrojový RoboScript a `competition_config_id` do JSON.
- Náraz na každý jedinečný kužel přidá 2 sekundy. Neplatné dokončení (DNF) se do tabulky neukládá.
- Výchozí limit je dva oficiální pokusy na přezdívku v jedné relaci Webots. **Nový soutěžící** vynuluje lokální počítadlo této přezdívky. Jde o provozní pomůcku, nikoli ověření identity.
- Tlačítko **Správa** nabízí potvrzené vymazání místního žebříčku. Jde o jednoduchý lokální pořadatelský režim bez autentizace.
- Každá úroveň používá vlastní ID z `LEVEL_CONFIG_IDS` v `controllers/roborace_controller/courses.py`, aby se výsledky různých tratí neslučovaly. Změna fyziky nebo geometrie vyžaduje aktualizovat odpovídající ID.

## Ověření logiky

Testy standardní knihovny Pythonu spustíte z kořene projektu:

```powershell
python -m unittest discover -s tests -v
```

Tato sada ověřuje parser, výpočet povelů kol, stavový automat, checkpointy, kolize, protokol a JSON žebříček. Volitelný end-to-end smoke runner `tests/webots_smoke.mjs` pošle ukázkový program do běžící simulace přes místní WWI a vrátí výsledek jízdy. Otevřete svět, stiskněte **Run** a spusťte `node tests/webots_smoke.mjs 1234` v druhém terminálu (port upravte podle nastavení Webots). Tím ověříte propojení WWI a ukázkovou jízdu. Před veřejnou soutěží proveďte také opakované vizuální a fyzikální jízdy.

Úplnou fyzikální kontrolu spustíte příkazem `python tests/run_webots_integration.py`. Runner vytvoří oddělený testovací svět z aktuální tratě, ověří pohyb a zatáčení v obou směrech, kontakt s kuželem, DNF mimo koridor, deset opakování ukázky úrovně 1, ukázky nových úrovní a zápis oficiálního výsledku. Testovací výsledky ukládá pouze do `tests/webots/reports/`. Cestu k Webots lze zadat přes `--webots`; port přes `--port`.

Klienta používaného panelem lze zkontrolovat proti běžící simulaci pomocí `node tests/robot_window_smoke.mjs 1234`. Ověřuje české texty, validaci, obnovení kamery, dokončenou jízdu, opětovné připojení a reset. Samotná kontrola nepoužívá prohlížeč a neposuzuje rozložení HTML.

## Soubory

- `worlds/roborace.wbt` – aréna, mantinely, checkpointy, kužely a Robot.
- `protos/RoboRaceCar.proto` – čtyřkolový fyzikální model s HingeJoint a RotationalMotor.
- `protos/CourseRoad.proto` a `protos/CourseGate.proto` – fyzické díly vyvýšené čtvrté trasy a její značky checkpointů.
- `controllers/roborace_controller/` – parser, interpret, drivetrain, závodní logika, WWI protokol a žebříček.
- `plugins/robot_windows/roborace/` – lokální český panel a WWI WebSocket klient bez CDN.
- `docs/zackova-napoveda.md` – stručná pomůcka pro žáka.
- `tests/` – logické Python testy a volitelný Webots smoke runner.
- `tests/run_webots_integration.py` – opakovatelné fyzikální kontroly v odděleném světě Webots.
