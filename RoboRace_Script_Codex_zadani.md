# RoboRace Script – kompletní zadání pro Codex

**Projekt:** RoboRace Challenge / režim Junior  
**Prostředí:** Webots, Python 3, HTML/CSS/JavaScript  
**Primární platforma:** Windows 10/11  
**Cílová skupina:** žáci základních škol přibližně 10–15 let  
**Účel:** krátká veřejná soutěž v programování pohybu fyzikálního robota

> **Hlavní úkol pro Codex:** Vytvoř skutečně spustitelný projekt Webots, nikoliv jen koncept, pseudokód či ukázku UI. Implementuj 3D překážkovou trať, fyzikálně řízeného čtyřkolového robota, bezpečný interpret níže definovaného mini-jazyka, měření času, penalizace, reset, testovací i soutěžní režim a trvalý žebříček. Nejprve dokonči funkční minimální verzi a teprve potom rozšiřuj vzhled.

## 1. Charakter a hlavní princip

RoboRace je krátká závodní výzva: návštěvník dostane připraveného robota a textový editor, upraví několik instrukcí a pokusí se robota co nejrychleji provést dráhou se zatáčkami a překážkami. Robot **nemá autonomní navigaci ani automatické vyhýbání**; během soutěžní jízdy pouze postupně provádí instrukce hráče. Fyzikální engine Webots určuje skutečný pohyb, smyk, brzdnou dráhu a případné převrácení.

Přibližná délka účasti: 2–4 minuty. Jedna jízda má mít časový limit 35 sekund *simulačního* času. Soutěžící může před ostrým pokusem využít testovací jízdu. Hlavním výsledkem je čas platného dokončení trati včetně penalizací. Neplatné dokončení se do žebříčku nezapisuje.

Základní pedagogické cíle: posloupnost příkazů, argumenty funkcí, ladění programu, fyzika zrychlování a brzdění, kompromis mezi rychlostí a stabilitou.

## 2. Technologické a provozní požadavky

- Webots R2025a nebo již nainstalovaná kompatibilní verze: nejprve zjisti dostupnou verzi, ověř odpovídající API a zdokumentuj ji. Výchozí návrh testuj proti R2025a.
- Controller v Pythonu 3; rozhraní v lokálních HTML/CSS/JavaScript souborech. Preferuj nativní **Robot Window** s WWI komunikací podle ukázky `custom_robot_window_simple.wbt`.
- Používej zdokumentované Webots API, zejména `Motor.setPosition(float('inf'))`, `Motor.setVelocity(...)`, `Robot.wwiSendText`, `Robot.wwiReceiveText`, `Supervisor.getFromDef`, `Node.getPosition`, `Node.getOrientation`, `Node.resetPhysics` a související metody; ověř jejich konkrétní podpisy pro nainstalovanou verzi.
- Nejjednodušší vhodná architektura: **jediný Robot se `supervisor TRUE`**, který ve svém Python controlleru řídí vlastní čtyři motory, čte stav soutěže, měří kontrolní body, resetuje model a obsluhuje Robot Window. Pokud to způsobí technické problémy, rozděl do robot controlleru a samostatného Supervisor controlleru s přesně definovanou komunikací.
- Vše běží lokálně bez cloudu a internetového připojení. Nepoužívej velké frameworky ani běhové stahování souborů.
- Výsledky ukládej do JSON souboru; umožni export do CSV jako nepovinné rozšíření.
- Čeština ve všech soutěžních textech a chybách. Zdrojové identifikátory mohou být anglicky.
- Fyzika musí používat skutečná spojení, kola, tření a fyzikální tělesa, **nikoliv přepisování souřadnic robota při závodu**.

## 3. Vizuální koncept a geometrie světa

Vytvoř moderní závodní scénu s výraznou, ale čistou grafikou: tmavý podklad, světlá závodní dráha, tyrkysové označení startu, zelené označení cíle, oranžové překážky, čísla checkpointů, dekorativní LED pásky. Scéna má být dobře čitelná na 24–32palcovém monitoru i z dálky.

Základní trať pro MVP:

- Délka pomyslné střednice cca 7–10 m; šířka koridoru přibližně 1,2–1,6 m.
- Startovní rovinka, **dvě jasně čitelné zatáčky** (např. levá a pravá) a cílová rovinka.
- Tři kužely nebo podobné pevné fyzikální překážky (jednoznačně označené ID).
- Dvě nebo tři průjezdové brány/checkpointy v pořadí a cílová čára.
- Dost prostoru kolem zatáček pro smyk, vyjetí a viditelnou havárii; žádné netriviální bludiště.
- Neprůjezdné okraje nebo mantinely, které zabrání zkrácení trati; kolize s mantinelem mohou být diskvalifikační, ale nastav chování tak, aby nebyly pro děti příliš frustrující.
- Základní svět Webots ENU: X a Y představují horizontální rovinu, Z výšku. Všechny pozice a průjezdové testy odvozuj z tohoto předpokladu.

Kamera staticky z šikmého nadhledu zabírá většinu okruhu; volitelně nabídni druhý pohled sledující robota. Prioritou je přehlednost a stabilní framerate, ne přehnané vizuální efekty. Základní modely sestav z primitiv Webots bez externích aktiv.

## 4. Robotický model a fyzikální stabilita

Vytvoř kompaktní čtyřkolový závodní robot s pohonem dvou stran (skid/differential steering): levá přední a zadní kola dostávají stejný příkaz; pravá přední a zadní kola také. Model musí mít:

- vizuálně zřetelné tělo, čtyři kola a orientační označení předku;
- dynamické `Physics`, reálné kolizní tvary `boundingObject`, poháněné `HingeJoint` / `RotationalMotor`;
- rozumnou hmotnost, nízko umístěné těžiště, dostatečný rozchod a rozvor;
- kontakt pneumatik s podložkou s kalibrovaným třením;
- omezenou maximální úhlovou rychlost motorů, zrychlení, točivý moment a brzdný účinek;
- kontakt kol s terénem skutečně ovlivňující zatáčení, prokluz a stabilitu.

Nevynucuj náklon animací. Při přehnaně vysoké rychlosti v zatáčce má robot fyzikálně projevit přetáčivost, smyk, vyjetí z dráhy nebo při dostatečně extrémním manévru převrácení. Běžné povely však mají být stabilní. Pokud se čtyřkolové smykové řízení kvůli kontaktům v ODE chová nestabilně, nejprve oprav kolizní geometrii, kontakty a rozložení hmotnosti; případně zdůvodni jednodušší variantu s dvěma hnacími koly a dvěma pasivními oporami.

Vyhodnocování stability: při překročení náklonu (roll/pitch) přibližně 50° po 0,25 s označ jízdu jako převrácení. Hodnotu konfigurovat; orientaci odvozuj korektně z orientační matice a globální vertikály, ne z neověřených indexů vektoru rotace. Vyjetí z trati pozná Supervisor podle povolené oblasti, nikoli podle vizuální barvy podložky.

### Pohon a fyzikální reakce

`Motor.setVelocity` určuje **požadovanou** úhlovou rychlost kola, nikoliv okamžitou rychlost pohybu vozidla. Před aplikací změn používej fyzikálně omezenou akceleraci (volitelně vlastní rampování požadavku pro předvídatelnou hratelnost). Brzdění realizuj jako odpovídající motorickou regulaci směrem k nule, případně s odlišným, ale konečným brzdným omezením. Nepřepisuj rychlost tělesa pomocí Supervisor API během jízdy.

## 5. Mini-jazyk RoboScript 1.0 – ZÁVAZNÁ SPECIFIKACE

**Každý příkaz má jednoslovný název, následovaný závorkami s parametry.** Žádné víceslovné povely, žádný Python, žádné příkazy obsahující mezery, žádné implicitní příkazy oddělené středníkem.

Přípustných je přesně **šest příkazů**:

| Příkaz | Parametry | Význam |
|---|---|---|
| `PLYN(p)` | `p`: 0–100 % | Nastaví požadovanou míru pohonu, bez simulovaného času; přetrvává do dalšího `PLYN` |
| `DOPREDU(t)` | `t`: 0,05–5,00 s | Po dobu `t` žádá přímý pohyb vpřed při aktuálním plynu |
| `DOZADU(t)` | `t`: 0,05–5,00 s | Po dobu `t` žádá přímý pohyb vzad při aktuálním plynu |
| `VLEVO(k, t)` | `k`: 0–100 %; `t`: 0,05–5,00 s | Po dobu `t` zatáčí doleva intenzitou `k` při aktuálním plynu |
| `VPRAVO(k, t)` | `k`: 0–100 %; `t`: 0,05–5,00 s | Po dobu `t` zatáčí doprava intenzitou `k` při aktuálním plynu |
| `BRZDA(t)` | `t`: 0,05–5,00 s | Po dobu `t` aktivně zpomaluje až k zastavení a udržuje požadavek nulové rychlosti |

**Důležité a jednoznačné sémantické podmínky:**

1. `PLYN(p)` mění pouze cíl pohonu. Neposune robota a nemá časové trvání. `PLYN(100)` nepřepne robota okamžitě na maximální skutečnou rychlost.
2. `DOPREDU` / `DOZADU` po danou dobu řídí kola pro přímou jízdu. Parametr je **čas**, nikoliv vzdálenost. Po jejich dokončení zůstane zapamatován **směr poslední jízdy**.
3. `VLEVO` / `VPRAVO` jsou **časově trvající oblouky** při současném pohonu, nikoliv okamžitá změna úhlu ani otočení na místě. `k` určuje rozdíl požadovaných rychlostí levé a pravé strany. `t` je čas tohoto povelu. V zatáčce zůstává aktivní poslední směr jízdy (vpřed/vzad); výchozí směr je vpřed. Slova vlevo/vpravo určují změnu orientace **v souřadnicích robota**, a to i při couvání.
4. `BRZDA(t)` přebije pohon požadavkem nulové rychlosti obou stran a aktivně brzdí po dobu `t`; původní hodnota plynu a poslední směr se pamatují pro další instrukce. Je-li čas brzdy krátký, robot se nemusí plně zastavit.
5. Po uplynutí doby jedné pohybové instrukce následuje bez umělé pauzy další instrukce. Hmotnost a setrvačnost tělesa se zachovávají. Pokud program skončí před cílem, řízení začne bezpečně brzdit a běží krátká dojezdová fáze maximálně 2 s; pokud robot během ní správně projede cílem, může být jízda platná. Jinak skončí jako nedokončená.
6. Zpomalení, prokluz, skutečný poloměr zatáčky a míra změny směru vznikají z fyziky. Příkaz `VLEVO(70, 0.8)` **nezaručuje** otočení o konkrétní počet stupňů.
7. Při `PLYN(0)` se další pohybové instrukce vykonávají po zadaný čas s nulovou cílovou rychlostí; nabídni varování, že robot zřejmě nepojede.
8. Obnovování stavu před každou jízdou resetuje výchozí plyn na 40 % a směr na „vpřed“, aby se nastavení nepřenášelo mezi pokusy. Požaduj ale v dodaném ukázkovém programu explicitní `PLYN(...)`.

**Mapování zatáčení na kola**: Zaveď konfigurovatelnou základní úhlovou rychlost motorů `base = (p/100) * MAX_WHEEL_SPEED` a asymetrii `delta = (k/100) * MAX_STEER_DIFFERENCE * base`. Pro jízdu vpřed a levé zatáčení počítej cíle `left = base - delta`, `right = base + delta`; pro pravé obráceně. Při jízdě vzad použij záporný základ a uprav asymetrii tak, aby `VLEVO` stále znamenalo požadovaný levý **yaw robota**, nikoli automaticky opačnou orientaci vlivem couvání. Při překročení limitu některé strany obě rychlosti **proporcionálně normalizuj**, aby zůstal zachován poměr a žádný motor nepřekročil limity. Používej stejné cíle pro obě kola jedné strany. Model ověř jednotkovými testy znamének i jízdou ve Webots.

### Příklad pro editaci soutěžícím

```text
# RoboRace – zkus projet trať rychleji!
PLYN(45)
DOPREDU(1.2)
VLEVO(60, 0.8)
DOPREDU(0.9)
BRZDA(0.3)
VPRAVO(55, 0.7)
PLYN(70)
DOPREDU(1.7)
BRZDA(0.8)
```

Toto je **příklad syntaxe**, nikoli zaručený vítězný program. Vytvoř navíc **kalibrovaný výchozí program**, který ve skutečně dodané aréně spolehlivě dojede do cíle, ale nezajistí špičkový čas. Ověř jej opakovanými integračními jízdami, je-li Webots dostupný.

### Textová pravidla

- Jeden příkaz na jeden řádek; prázdné řádky povol.
- Komentář začíná `#` a sahá do konce řádku, i za příkazem.
- Pouze velká písmena v povelových názvech. Volitelně v editoru automaticky převáděj malá na velká, ale chování zdokumentuj.
- Mezery kolem parametrů a za čárkou mohou být libovolné: `VLEVO(60, 0.8)`.
- Desetinným oddělovačem je **tečka**; v UI výslovně vysvětli rozdíl od české desetinné čárky. Oddělovačem argumentů je **čárka**.
- Nepovol proměnné, výrazy, bloky, `for`, `while`, importy, libovolné funkce ani eval.
- Neznámý příkaz, chybějící závorka, chybný počet argumentů nebo překročený rozsah = viditelná diagnostika s číslem řádku a přesným důvodem.

Omez program na **40 instrukcí**, součet trvání všech časovaných instrukcí na maximálně **32 s** a jednu časovanou instrukci na maximálně 5 s. Tato omezení uplatni serverově/v Pythonu, nikoliv jen v HTML.

### Bezpečné parsování

Vytvoř vlastní parser se striktní gramatikou: `IDENTIFIER '(' NUMBER (',' NUMBER)* ')'`, po odstranění povolených komentářů. Nikdy nepoužívej `eval`, `exec`, `ast.literal_eval` na neověřené konstrukce jako náhradu za explicitní gramatiku ani shellové volání. Vytvoř datový typ `Instruction(opcode, args, source_line)`; výsledkem parsování je seznam validovaných instrukcí. Odmítej `NaN`, `Infinity`, exponenty (není-li výslovně podporováno), záporný čas, neuzavřené závorky a více instrukcí na řádku.

## 6. Vykonávání instrukcí

Použij **neblokující stavový automat nad simulačními kroky**, žádné `sleep()` a žádné dlouhé blokující smyčky uvnitř jedné instrukce. V každém kroku Webots:

1. Načti případné zprávy UI.
2. Pokud běží závod, vykonej jeden simulační krok aktuální instrukce a aktualizuj požadované rychlosti kol.
3. Aktualizuj čas instrukce ze simulačního času nebo pevného `basicTimeStep`.
4. Sleduj polohu, checkpointy, hranice tratě, kolize, převrácení a případný cíl.
5. Po dokončení instrukce přejdi na další bez resetu rychlosti a polohy robota.
6. Po skončení programu nebo při havárii aktivuj bezpečný stav motorů a vyhodnoť jízdu.
7. Odesílej UI stav, aktuální řádek, čas a výsledek; telemetry neposílej častěji, než je potřeba pro plynulou odezvu (např. 5–10 Hz).

Soutěžní stavy např. `IDLE`, `VALIDATED`, `COUNTDOWN`, `RUNNING`, `FINISHED`, `FAILED`, `RESULT`. Při `COUNTDOWN` robot stojí a časomíra neběží. Během jízdy není možné měnit program, restartovat jen určité části fyziky ani opakovaně spustit stejný pokus klikáním.

## 7. Měření času, checkpointy a výsledek

- Měř **simulační čas** od prvního vykonávaného fyzikálního kroku ostré jízdy do korektního překročení cílové čáry. Nepoužívej `time.time()` či rychlost vykreslování jako zdroj soutěžního času.
- Pro každou bránu definuj orientovanou konečnou úsečku v rovině XY a povolený směr průjezdu. Průjezd počítej na základě přechodu středu robota mezi stranami segmentu při správném pořadí a uvnitř šířky brány; chraň se proti vícenásobnému započtení při kmitání.
- Cíl lze uznat pouze po průjezdu **všech checkpointů ve správném pořadí** a pokud nedošlo k diskvalifikaci. Zvaž souvislost průjezdu jednotlivými checkpointy s povoleným koridorem, aby nebylo možné obejít překážky mimo trať.
- Pokud robot opustí povolený koridor, převrátí se, překročí limit 35 s nebo je jinak nezpůsobilý pokračovat, jízda je `DNF` a do žebříčku se nezapisuje.
- Po nárazu do každého **jedinečného** kužele přičti **+2,00 s**. Při opakovaném kontaktu se stejným kuželem už penalizaci nezvyšuj; při kontaktu s různými kužely se penalizace sčítají.
- Kolizi identifikuj pokud možno skutečnými kontakty přes Webots Supervisor `Node.getContactPoints(includeDescendants=...)` a ID dotčených uzlů. Ověř prakticky, že se nezaměňují kontakty s podlahou a kuželem. Pokud tato metoda není pro konkrétní model spolehlivá, použij výslovně zdokumentovanou geometrickou aproximaci skutečného průniku kolizních objemů; pouhá blízkost před nárazem se **nesmí** bodovat jako kontakt.
- Penalizace jsou přičteny ke konečnému měřenému času, nikoli k průběhu fyzikální simulace.

**Oficiální výsledek:** `vysledny_cas = namereny_cas + 2.0 * pocet_zasazenych_unikatnich_kuzelu`.

Zobraz naměřený čas na setiny sekundy (interně ponech vyšší přesnost pro řazení), počet penalizací, výsledný čas a status. Pořadí v žebříčku: nejnižší výsledný čas, při rovnosti nejnižší neupravený čas, pak dřívější dosažení výsledku. Každému hráči ponech nejlepší platný oficiální pokus.

## 8. Testovací a soutěžní režim

V rozhraní jasně odliš:

**TESTOVAT:** neukládá do žebříčku; umožní experimentovat a vrátí diagnostiku, přesný čas, místo selhání, řádek posledního prováděného příkazu a počet dotyků kuželů.

**SOUTĚŽIT:** po zadání přezdívky spustí oficiálně hodnocený pokus. Po skončení validní jízdy uloží čas do žebříčku. Výchozí pravidlo: nejvýše **dvě oficiální jízdy na hráče v rámci jedné lokální soutěžní relace**, testovací jízdy bez limitu; pravidlo musí být konfigurovatelné pořadatelem. Protože přezdívky nejsou identitní důkaz, neslibuj technicky neprolomitelnou kontrolu počtu pokusů.

Ve veřejném režimu ukazuj aktuální TOP 10 a motivující příklady změn programu, nikoli řešení nejlepší trasy. Účastník musí být schopen začít z připravené šablony jediným kliknutím a do 20 sekund uskutečnit první test.

## 9. Uživatelské rozhraní

Vytvoř ergonomický panel pro použití vedle 3D pohledu Webots, ideálně při 1920×1080 px:

**Levý panel / editor:** název RoboRace, jednoznačně označený editor jednoduchého kódu s číslováním řádků, zvýrazněním právě prováděného řádku, tlačítky `OVĚŘIT`, `TESTOVAT`, `SOUTĚŽIT`, `RESET`, stručnou kartou šesti příkazů a diagnostikou. Pokud externí editorová knihovna vyžaduje CDN, nepoužívej ji; základní lokální textarea je přijatelná, ale zajisti přehlednou typografii a funkční synchronizované číslování řádků.

**Pravý panel / simulační plocha:** skutečná 3D scéna Webots. Tlačítka v HTML nesmí zobrazovat falešný video náhled; používají skutečný běh simulace.

**Horní/spodní stavový pás:** simulační čas, stav robota, pořadí checkpointu, penalizace, nejlepší čas dne. Po skončení jízdy karta `VÝSLEDEK`, případně `NEPLATNÝ POKUS` s konkrétní příčinou.

**Nápověda:** krátké srozumitelné popisy v češtině (např. „`VLEVO(60, 0.8)` = zatáčej vlevo s intenzitou 60 % po dobu 0,8 sekundy“). Zahrň 2–3 malé ukázkové programy a vysvětlení, že rychlost a zatáčení nejsou okamžité kvůli fyzice.

**Vzhled:** výrazné názvy a vysoký kontrast, tmavé antracitové/modré pozadí, tyrkysový akcent, velká tlačítka, čitelný monospace kód. Připrav rozumné zobrazení i na menším panelu.

## 10. Komunikace mezi Webots a panelem

Používej jednoduchý protokol JSON zpráv přes Webots Robot Window / WWI. Příklady:

```json
{"type":"validate","request_id":"r1","source":"PLYN(50)\nDOPREDU(1.2)"}
```

```json
{"type":"start","request_id":"r2","mode":"test","source":"PLYN(50)\nDOPREDU(1.2)"}
```

```json
{"type":"start","request_id":"r3","mode":"official","nickname":"Rychlik42","source":"PLYN(50)\nDOPREDU(1.2)"}
```

```json
{"type":"execution","state":"RUNNING","source_line":2,"elapsed":1.23,"checkpoint":1,"checkpoint_total":3,"penalties":0}
```

```json
{"type":"result","state":"FINISHED","raw_time":14.28,"penalty_seconds":2.0,"final_time":16.28,"mode":"official"}
```

Doplň zprávy `validation_result`, `error`, `leaderboard`, `ready`, `reset`. Zprávy ověřuj v Pythonu proti schématu, neznámé typy ignoruj se zdokumentovaným upozorněním. `request_id` použij na ochranu před duplicitními požadavky. Udržuj oddělené funkce pro příjem, validaci, změnu stavu a publikování výsledků.

## 11. Ukládání žebříčku a férovost

Používej lokální JSON (`data/leaderboard.json`) s datem/časem UTC, přezdívkou, výsledky oficiálních jízd, nejlepším časem, penalizacemi a základním identifikátorem verze trati a fyzikální konfigurace. Ulož i zdrojový text nejlepšího soutěžního programu, aby bylo možné výsledek později reprodukovat (nikdy jej nespouštěj přes Python `exec`).

Přezdívka nejvýše 20 znaků, bez HTML, ovládaných znaků a nepřiměřeně dlouhých vstupů. Pokud není vyplněna, použij `Hrac-001` a podobně. Při zobrazování vždy používej textové HTML API, nikoli `innerHTML` s uživatelským textem.

Používej atomický zápis přes dočasný soubor v témž adresáři a `os.replace`; uchovávej poslední platnou zálohu. Poškozený soubor nesmí způsobit pád celé akce. Odděl administrátorské mazání žebříčku s potvrzením a jednoduchým lokálním pořadatelským režimem (bez nepravdivých tvrzení o silné autentizaci).

**Zásadní:** Pokud pořadatel změní trať, velikost kol, parametry tření nebo maximální výkon, změň `competition_config_id`; výsledky s různou konfigurací neslučuj do jedné soutěžní tabulky.

## 12. Reset, opakovatelnost a výkon

Po každé jízdě:

1. Zastav cíle motorů, ukonči stávající časovače a uzamkni záznam výsledku.
2. Vrať robota na uloženou startovní pozici a rotaci. Obnov fyziku pomocí vhodných Supervisor metod, mimo závod.
3. Obnov případně převržené nebo posunuté kužely na přesně stejné výchozí pozice a fyzikální stav.
4. Vynuluj checkpointy, penalizace, čas, seznam vykonaných instrukcí a směr/plyn.
5. Před novým startem nech proběhnout krátké ustálení fyziky, pokud je nutné; nezapočítávej je do měřeného času.
6. Neprováděj `simulationReset()` po každém pokusu, pokud by resetoval controller nebo ztrácel herní stav.

Při stejném zdrojovém programu, identických počátečních stavech a konfiguraci očekávej výsledky dostatečně podobné pro spravedlivou soutěž. Vytvoř integrační opakovací test nejméně 10 identických jízd. Zachyť a zdokumentuj případný rozptyl časů a důvody; neslibuj absolutní determinismus bez měření.

Přednost dej stabilní simulaci při doporučeném `basicTimeStep` (například 16 nebo 32 ms podle fyzikální kalibrace) před příliš efektní grafikou. K měření jízdy nepoužívej reálný čas CPU.

## 13. Doporučená struktura projektu

```text
roborace/
├── worlds/
│   └── roborace.wbt
├── protos/
│   └── RoboRaceCar.proto                # pouze pokud dává smysl
├── controllers/
│   └── roborace_controller/
│       ├── roborace_controller.py
│       ├── config.py
│       ├── language.py                  # parser, validace, datové typy
│       ├── interpreter.py               # vykonávání po krocích
│       ├── drivetrain.py                # mapování na motory, limity
│       ├── race.py                      # stavy, checkpointy, DNF
│       ├── collisions.py                # kontakty a penalizace
│       ├── leaderboard.py               # JSON a řazení
│       └── protocol.py                  # WWI zprávy
├── plugins/
│   └── robot_windows/
│       └── roborace/
│           ├── roborace.html
│           ├── roborace.js
│           └── style.css
├── data/
│   └── leaderboard.json
├── tests/
│   ├── test_language.py
│   ├── test_interpreter.py
│   ├── test_drivetrain.py
│   ├── test_checkpoints.py
│   ├── test_race.py
│   └── test_leaderboard.py
├── README.md
├── AGENTS.md
└── requirements-dev.txt
```

Uprav umístění komponent podle skutečných konvencí Webots. Udržuj moduly importovatelné a čistou Python logiku testovatelnou bez spuštěného Webots. Ověř cesty a schopnost načítat lokální soubory z relativní pracovní složky controlleru.

## 14. Testy a akceptační kritéria

### Automatické jednotkové testy

- Správné rozpoznání šesti instrukcí, počtu argumentů a mezí.
- Povolování komentářů, prázdných řádků, mezer a desetinné tečky.
- Odmítání `VLEVO 60 0.8`, `VLEVO(60)`, `PLYN(200)`, `DOPREDU(-1)`, `DOPREDU(1,5)` (dva argumenty), `PYTHON(...)`, závorek navíc, nekonečných čísel, více povelů na řádku, neznámých znaků.
- Ochrana proti `eval`, neomezeně dlouhým programům a nekonečnému vykonávání.
- Plynulý přechod mezi instrukcemi bez vynucené nulové rychlosti; korektní funkce brzdy a couvání.
- Směrová konvence `VLEVO` a `VPRAVO` pro jízdu vpřed i vzad.
- Kontrola průjezdu branou dopředu, mimo bránu, opačným směrem a špatným pořadím.
- Přičtení penalizace právě jednou za dotčený kužel.
- Převrácení, vyjetí, timeout, dokončení a zápis jen platného oficiálního času.
- JSON záznam, řazení, nejlepší pokus, ochrana před rozbitým JSON a oddělení konfigurací.

### Integrační testy v Webots

1. Otevření světa bez chybového nebo chybějícího uzlu.
2. Skutečné otáčení kol a pohyb robota při `DOPREDU`.
3. Skutečné couvání při `DOZADU`.
4. Rozlišitelné zatáčení vlevo/vpravo a reakce na změnu intenzity.
5. Plynulá odezva plynu a měřitelná brzdná dráha při `BRZDA`.
6. Nižší stabilita při extrémní rychlosti v zatáčce, bez zbytečně náhodných havárií.
7. Jeden validní vzorový program skutečně dorazí do cíle přes checkpointy.
8. Kolize s kuželem způsobí fyzikický kontakt a jedinou penalizaci.
9. Vyjetí mimo dráhu a převrácení způsobí DNF.
10. Reset opakovaně navrací robota a překážky do totožných podmínek.
11. Testovací jízda nemění žebříček, soutěžní platný pokus ano.
12. Žebříček se zachová po vypnutí a opětovném spuštění Webots.
13. Deset opakování shodného programu je dostatečně reprodukovatelných.
14. Celý soutěžní cyklus lze opakovat bez restartování aplikace.

### Přijetí výsledku

Za hotové považuj pouze skutečně běžící `.wbt` projekt s funkčním panelem, parserem, fyzikou, časy, penalizacemi, resetem, oficiálními výsledky a dokumentací. Pokud nemáš Webots v prostředí k dispozici, ověř dostupné Python testy a výslovně vyjmenuj funkce, které bez běhu Webots nebylo možné zkontrolovat. **Nikdy nevydávej neprovedený integrační test za úspěšný.**

## 15. Pracovní postup pro Codex

Pracuj inkrementálně a po každé etapě otestuj dostupné funkce:

**Etapa A – svět a fyzika:** postav zjednodušenou trať a robota, zprovozni motory, fyziku a stabilní reset. Vypusť předem naprogramovanou testovací sekvenci.

**Etapa B – RoboScript:** implementuj parser, diagnostiku, časované vykonávání a mapování na kola. Doplň čisté unit testy.

**Etapa C – závod:** kontrolní body, cíl, časomíra, tresty, DNF, reset po havárii; integrační demonstrace dokončení celé trati.

**Etapa D – UI:** český editor, nápověda, validace, testování, live zvýraznění řádku a výsledky; integrace skutečného Robot Window.

**Etapa E – žebříček:** režim soutěžní jízdy, ukládání, TOP 10, konfigurace soutěže.

**Etapa F – vyladění:** výchozí hratelný program, fyzikální kalibrace, vizuální efekty, opakované běhy, dokumentace.

Po dokončení uveď seznam vytvořených souborů, spouštěcí postup ve Windows, úspěšné a neprovedené testy, známá omezení a doporučená další rozšíření.

## 16. Dokumentace pro pořadatele a žáka

V `README.md` vysvětli přesné otevření světa ve Webots, otevření Robot Window, spuštění simulace, vyzkoušení ukázkového programu a umístění JSON žebříčku. Přidej krátkou **jednostránkovou nápovědu pro žáka** s příklady šesti povelů a vysvětlením, proč vysoká rychlost při zatáčení nemusí přinést lepší čas. Přidej režim „Nový soutěžící“ a administrátorský reset výsledků s potvrzením. Do `AGENTS.md` uveď architekturu, příkazy pro testování, stabilní konvenci os, konstanty fyziky a postup kalibrace.

### Výchozí zdroje pro ověření Webots API

- Oficiální ukázka HTML/JS/Python robot window: `https://github.com/cyberbotics/webots/tree/master/projects/samples/howto/custom_robot_window_simple`
- Dokumentace Motor: `https://cyberbotics.com/doc/reference/motor`
- Dokumentace Supervisor: `https://cyberbotics.com/doc/reference/supervisor`
- Dokumentace WorldInfo: `https://cyberbotics.com/doc/reference/worldinfo`
- Tutoriál čtyřkolového robota: `https://cyberbotics.com/doc/guide/tutorial-6-4-wheels-robot`

**Závěrečný požadavek:** Vytvoř jednoduchou, opakovatelnou a soutěžně férovou robotickou simulaci. Začni na fungujícím fyzikálním prototypu, důsledně dodrž jednoslovnou závorkovou syntaxi RoboScript a dokonči celý provozní řetězec od editace programu až po zápis platného času do žebříčku.
