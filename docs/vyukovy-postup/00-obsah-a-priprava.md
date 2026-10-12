# RoboRace Junior: obsah výukového postupu

Tento postup ukazuje, jak krok za krokem sestavit současnou aplikaci RoboRace Junior. Je určen čtenáři, který zná základy Pythonu, HTML a JavaScriptu, ale Webots teprve poznává. Ukázky kódu jsou vybrané výřezy skutečné implementace. Pro celý kontext vždy otevři odkazovaný zdrojový soubor.

## Co vznikne

Fyzikální čtyřkolový robot ve Webots projíždí jednu ze čtyř tratí podle textového programu RoboScript. Supervisor kontroluje brány, koridor, převrácení a kontakty s kužely. Lokální Robot Window nabízí editor, testovací a oficiální jízdu, telemetrii a žebříček. Aplikace nepotřebuje cloud ani externí JavaScriptové knihovny.

## Pořadí etap

1. [01 – Návrh a založení projektu](01-navrh-a-projekt.md): hranice modulů, datový tok, souřadnice a první spustitelný svět.
2. [02 – Svět a fyzikální robot](02-svet-a-robot.md): aréna, kamera, kontakty, PROTO karoserie a čtyři klouby.
3. [03 – Jazyk RoboScript](03-jazyk-roboscript.md): přesná gramatika, datový model instrukce, chyby a limity.
4. [04 – Interpret a pohon](04-interpret-a-pohon.md): časované příkazy, mapování na kola, omezení změny rychlosti.
5. [05 – Trasy, brány a překážky](05-trasy-a-vyhodnoceni.md): čtyři úrovně, stoupající cesta, detekce bran a kolizí.
6. [06 – Supervisor a stav závodu](06-supervisor-a-zavod.md): běhová smyčka, reset, telemetrie a výsledek.
7. [07 – Protokol a žebříček](07-protokol-a-zebricek.md): WWI zprávy, obnova spojení a atomický JSON.
8. [08 – Uživatelské rozhraní](08-uzivatelske-rozhrani.md): úzký panel, editor, CSS, modální nápověda.
9. [09 – Ověření a kalibrace](09-overeni-a-kalibrace.md): čisté testy, fyzikální kontroly a ladění tratí.

## Příprava prostředí

Použij Webots R2025a, Python 3 a volitelně Node.js pro klientské smoke kontroly. Ve Windows otevři PowerShell v kořeni projektu. Základní struktura je:

```text
robo-race/
├── worlds/roborace.wbt
├── protos/RoboRaceCar.proto
├── protos/CourseRoad.proto
├── protos/CourseGate.proto
├── controllers/roborace_controller/
│   ├── roborace_controller.py
│   ├── language.py, interpreter.py, drivetrain.py
│   ├── courses.py, race.py, collisions.py
│   └── protocol.py, leaderboard.py
├── plugins/robot_windows/roborace/
│   ├── roborace.html, style.css, roborace.js
│   └── wwi_client.js
├── data/
└── tests/
```

Otevři `worlds/roborace.wbt` přímo ve Webots a spusť simulaci tlačítkem **Run**. Většina modulů v `controllers/roborace_controller/` funguje i bez Webots; výjimkou je hlavní controller, který importuje `Supervisor`.

## Pravidlo práce s ukázkami

Každá etapa obsahuje **cíl**, **konkrétní kroky**, **ukázku**, **vysvětlení** a **kontrolní bod**. Výřezy někdy vynechávají importy nebo okolní větve; proto je nevkládej slepě za sebe do jednoho souboru. Postup staví funkce v pedagogickém pořadí. Hotový repozitář už obsahuje finální podobu a je zdrojem přesných souřadnic i všech okrajových případů.

## Pevné hodnoty této verze

Svět používá ENU: vodorovné osy X/Y, výšku Z. Simulační krok je 16 ms. Poloměr kola je 0,08 m, limit otáčení 14 rad/s, koridor má poloviční šířku 0,72 m, limit jízdy je 35 s, kužel dává 2 s penalizace, program má nejvýše 40 instrukcí a 32 s časovaných příkazů. Když se změní geometrie či fyzika, musí se změnit také odpovídající položka `LEVEL_CONFIG_IDS` v `courses.py`.

