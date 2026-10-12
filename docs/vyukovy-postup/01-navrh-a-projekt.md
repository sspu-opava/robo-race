# Etapa 1 – Návrh a založení projektu

[Obsah](00-obsah-a-priprava.md) · [Další: svět a robot](02-svet-a-robot.md)

## Cíl

Oddělit části, které lze ladit bez simulátoru, od části závislé na Webots. Současně založit svět, který je možné otevřít dříve, než vznikne plná závodní logika.

## 1. Nakresli tok dat

```text
RoboScript v panelu
  → WWI JSON → Supervisor → parser → interpret → omezení motorů
                                      ↓
                            Webots fyzikální simulace
                                      ↓
                         poloha, brány, kolize, čas
                                      ↓
                        výsledek → JSON žebříček
                                      ↓
                      WWI zprávy → panel hráče
```

Parser nikdy nespouští uživatelský text jako Python. Interpret vrací jen požadované rychlosti levé a pravé strany. Fyzický pohyb počítá Webots. Supervisor čte skutečnou polohu a rozhoduje o platnosti jízdy. Díky tomu lze parser, interpret, pohon a geometrii kontrolovat samostatně.

## 2. Vytvoř adresáře

V kořeni projektu založ `worlds`, `protos`, `controllers/roborace_controller`, `plugins/robot_windows/roborace`, `data`, `tests` a `docs`. Název controlleru v uzlu robota musí odpovídat názvu adresáře. Hodnota `window "roborace"` musí odpovídat adresáři Robot Window.

Základ budoucího modelu je:

```vrml
Robot {
  controller "roborace_controller"
  window "roborace"
  supervisor TRUE
}
```

V hotové aplikaci je uzel `Robot` uzavřen do `protos/RoboRaceCar.proto`, aby se model nepřepisoval přímo ve světě.

## 3. Urči jednotky a osy

Do `WorldInfo` zapiš `coordinateSystem "ENU"` a `basicTimeStep 16`. Světové X/Y jsou rovina tratě, Z je nahoru. Robotův lokální +X je předek a lokální +Y je levá strana. Souřadnice bran, kuželů a koridoru proto ukládej ve světovém XY. Pozor: aktuální lokální orientaci robota je nutné převést pomocí orientační matice.

```vrml
WorldInfo {
  basicTimeStep 16
  coordinateSystem "ENU"
  gravity 9.81
}
```

Časový krok v Pythonu pak vypočteš jako `dt = robot.getBasicTimeStep() / 1000.0`. Hodnota `dt` určuje, o kolik se při jednom `robot.step(...)` zkrátí právě vykonávaný příkaz.

## 4. Založ malé samostatné moduly

Před hlavním controllerem vytvoř soubory `language.py`, `drivetrain.py`, `interpreter.py`, `race.py`, `collisions.py`, `courses.py`, `protocol.py` a `leaderboard.py`. Neimportuj v nich `controller.Supervisor`. Hlavní soubor `roborace_controller.py` bude jejich klientem a jediným místem, které používá Webots API.

Zvol jednoduchou hranici: `parse_program(source)` vrací seznam instrukcí; `Interpreter.step(dt)` vrací požadované rychlosti; `RouteTracker.update(previous, current)` upraví postup bran; `Leaderboard.add_result(...)` uloží platný oficiální výsledek.

## 5. Kontrolní bod

Ve Webots otevři zatím prázdnou arénu s kamerou a robotem. Ověř, že konzola nehlásí chybějící controller a že souřadnice X/Y/Z odpovídají tomu, co sis zapsal. Ještě nehodnoť čas ani brány; ty přijdou v dalších etapách.

