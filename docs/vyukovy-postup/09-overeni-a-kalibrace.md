# Etapa 9 – Ověření, fyzikální kalibrace a předání

[Předchozí](08-uzivatelske-rozhrani.md) · [Obsah](00-obsah-a-priprava.md)

## Cíl

Oddělit rychlé kontroly čisté logiky od fyzikálního ověření ve Webots. Výsledek pro děti musí být opakovatelný: správné znaménko pohonu, konzistentní brány, překážky na dráze a férový žebříček.

## 1. Spusť čisté Python testy

Z kořene projektu:

```powershell
python -m unittest discover -s tests -v
```

Testy v `tests/test_language.py`, `test_interpreter.py`, `test_drivetrain.py`, `test_race.py`, `test_collisions.py`, `test_protocol.py` a `test_leaderboard.py` kontrolují logiku bez běžícího Webots. Zaměř se zejména na:

- parser přijímá jen šest povelů a správně hlásí řádek chyby;
- levá zatáčka znamená kladnou změnu orientace vpřed i vzad;
- rampa nikdy nepřekročí povolenou změnu za krok;
- brány se počítají jen ve správném směru, v šířce a pořadí;
- každý kužel se penalizuje pouze jednou;
- JSON zpráva s češtinou se nepřeruší;
- neplatný výsledek se nedostane do žebříčku.

Tato sada neověřuje dotyk pneumatik s terénem ani skutečný průjezd trasou.

## 2. Otevři hlavní svět

Ve Webots R2025a otevři `worlds/roborace.wbt`, stiskni **Run** a otevři Robot Window. Zkontroluj:

1. controller startuje bez chyby a panel dostane `ready`;
2. výchozí kamera zabírá dráhu a **Zobrazit dráhu** ji obnoví;
3. kladné otáčky všech kol posunou auto k jeho lokálnímu +X;
4. `VLEVO` vytváří kladný yaw vpřed i při couvání;
5. reset vrátí karoserii, kužely a pohyblivé bariéry na výchozí pozice;
6. po přepnutí úrovně jsou vidět jen prvky dané trasy;
7. kontakty s kužely přidají správnou penalizaci, brány fungují v pořadí;
8. opakované pokusy nezanechávají starý stav.

Tyto body nelze pravdivě označit za splněné jen na základě unit testů.

## 3. Spusť izolovanou integraci

[`tests/run_webots_integration.py`](../../tests/run_webots_integration.py) vytvoří oddělený svět v `tests/webots/worlds/` a spustí nainstalovaný Webots v režimu `fast` a `batch`:

```powershell
python tests/run_webots_integration.py
```

Případně použij `--webots` pro cestu k programu a `--port` při obsazeném portu. Výsledky se zapisují do `tests/webots/reports/integration.json`, nikoli do soutěžního `data/`. Aktuální implementace runneru očekává **21 případů**; při budoucí změně kontroluj počet přímo v jeho zdroji. Součástí jsou opakované jízdy vzorového programu. Deset shodných jízd je minimum před tvrzením, že je ukázka reprodukovatelná.

## 4. Ověř WWI samostatně

Při otevřeném hlavním světě a spuštěné simulaci lze použít:

```powershell
node tests/robot_window_smoke.mjs 1234
```

Port uprav podle Webots. Tento nástroj cvičí produkčního WWI klienta, validaci, obnovu kamery, dokončení, reconnect a reset. Nekontroluje vizuální rozložení HTML. Pro kontrolu pohledu na úzký panel je nutné skutečně otevřít Robot Window nebo místní adresu přes Webots a prohlédnout jej v prohlížeči.

## 5. Kalibruj fyziku v pevném pořadí

Nejdříve se ujisti, že osy kloubů a kol mají správná znaménka. Pak ladíš tření `tire/track`, `maxTorque`, hmotnost a těžiště, rychlostní rampu. Teprve poté dolaď šířku koridoru, průjezdové brány a časy ukázkového RoboScriptu. Jinak by úprava fyziky znehodnotila dříve naladěný program.

Pro každou úroveň zapisuj při zkušební jízdě: čas, dosažené brány, důvod DNF, kontakty s kužely, místo vyjetí a náklon. Opravuj konkrétní příčinu. Zvlášť prohlédni všechny kužely, hrboly a bariéry, zda leží uvnitř fyzického jízdního pruhu a nejsou ve vzduchu nebo pod podlahou.

## 6. Udrž identitu konfigurace

Když se změní dráha nebo pohyb robota, změň `LEVEL_CONFIG_IDS` pro zasaženou úroveň. Výsledky staré geometrie nepřipojuj k novému žebříčku. Pravidla v `README.md`, v nápovědě panelu a v této výuce musí odpovídat skutečnému controlleru. Po každé změně projdi zejména limity 16 ms, 14 rad/s, 0,72 m, 35 s, 2 s za kužel, 40 instrukcí a 32 s programu.

## 7. Závěrečný kontrolní seznam

Nezávislost na internetu kontroluje `node tests/offline_assets.mjs`. Kontrola ověřuje místní odkazy na assety, importy PROTO a JavaScriptu, Content Security Policy, přijetí loopback adres, odmítnutí vzdálených adres ještě před vytvořením socketu a platnost místních odkazů mezi etapami výuky. Používá náhradní WebSocket, proto neposílá síťové požadavky. Skutečné místní spojení následně ověř pomocí WWI smoke runneru.

- Svět se načte a úvodní kamera ukáže trať.
- Robot projede všechna kola v očekávaném směru bez teleportace během jízdy.
- Každá ze čtyř tras má vlastní geometrii, ukázkový program a ID konfigurace.
- Průjezd checkpointy odpovídá viditelným značkám a fyzické silnici.
- Výběr trasy, editor, nápověda a akční tlačítka jsou dostupné v panelu do 400 px.
- Testovací jízda se nezapisuje; platná oficiální jízda ano; DNF ne.
- Po resetu a reconnectu je panel v souladu se stavem Supervisoru.
- V reportu je uvedeno, které kontroly skutečně běžely ve Webots a které byly pouze logické nebo vizuální.

