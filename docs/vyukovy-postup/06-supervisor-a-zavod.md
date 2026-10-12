# Etapa 6 – Supervisor a životní cyklus závodu

[Předchozí](05-trasy-a-vyhodnoceni.md) · [Obsah](00-obsah-a-priprava.md) · [Další](07-protokol-a-zebricek.md)

## Cíl

Spojit nezávislé moduly do jednoho Webots controlleru. Jeden robot se `supervisor TRUE` ovládá vlastní čtyři motory, čte polohu, měří čas a komunikuje s panelem.

## 1. Inicializuj zařízení a uzly

V [`roborace_controller.py`](../../controllers/roborace_controller/roborace_controller.py) vytvoř `Supervisor`, zjisti délku kroku a najdi motory podle přesných jmen v PROTO. Vyhledej také `DEF ROBORACE_CAR`, kameru `COURSE_VIEW`, kužely, hrboly, bariéry, silniční díly a značky. Pokud některý povinný uzel chybí, skonči s jasnou chybou; bez něj by závod dával zavádějící výsledek.

```python
self.robot = Supervisor()
self.step_ms = int(self.robot.getBasicTimeStep())
self.dt = self.step_ms / 1000.0
self.motors = [self.robot.getDevice(name) for name in (
    "left_front", "left_rear", "right_front", "right_rear"
)]
for motor in self.motors:
    motor.setPosition(float("inf"))
    motor.setVelocity(0.0)
self.car = self.robot.getFromDef("ROBORACE_CAR")
```

Výchozí stav je `IDLE`, úroveň 1, žádný interpret a žádná aktivní trasa. `_restore_scene()` přesune auto na start, vybrané překážky na místo a nevyužité mimo svět.

## 2. Sestav neblokující hlavní smyčku

```python
while self.robot.step(self.step_ms) != -1:
    now = self.robot.getTime()
    self._receive_messages()
    self._advance(now)
    self._publish(now)
```

Nepoužívej `time.sleep()` k vykonávání příkazů. Každé `robot.step` posune fyziku, controller čte zprávy, vyhodnotí závod a podle potřeby publikuje telemetrii. `robot.getTime()` je simulační čas pro výsledek, zatímco `time.monotonic()` slouží jen k omezení četnosti zpráv do panelu.

## 3. Navrhni stavy

| Stav | Co probíhá | Možný přechod |
|---|---|---|
| `IDLE` | čekání na program | `start` → `COUNTDOWN` |
| `COUNTDOWN` | jednosekundový odpočet, kola stojí | čas → `RUNNING` |
| `RUNNING` | vykonávání programu a vyhodnocení | cíl/chyba/limit → `RESULT` |
| `RESULT` | zobrazený výsledek | nový start nebo reset |

Při startu nejprve znovu zavolej serverový parser, obnov scénu a stav rampy, založ nový `Interpreter` a `RouteTracker`, vymaž penalizace a teprve pak potvrď zprávu `accepted`. Režim `official` předtím zkontroluje počet pokusů.

## 4. Vyhodnoť jeden běhový krok

V `_advance(now)` při `RUNNING` spočti `elapsed = now - started_at`. Zkontroluj koridor, dlouhodobý náklon, průjezd branou, kontakty s kužely, dokončení a limit 35 s. Teprve potom aplikuj další instrukci.

```python
if self.route.finished:
    self._finish(True, elapsed, "Cíl projet.")
    return
if elapsed >= TIME_LIMIT:
    self._finish(False, elapsed, "Vypršel limit 35 sekund.")
    return
self._apply_next_instruction(elapsed)
```

Náklon odvoď z lokálního „nahoru“ v orientační matici auta. Ve Webots je matice v řádkovém pořadí a třetí sloupec je lokální Z. Úhel k světové vertikále získáš z prvku `matrix[8]`:

```python
vertical_alignment = max(-1.0, min(1.0, float(matrix[8])))
tilt = math.degrees(math.acos(vertical_alignment))
```

Překročení 50° musí trvat alespoň 0,25 s; krátký náraz tak sám neukončí jízdu.

## 5. Dokonči výsledek přes jednu funkci

`_finish(success, raw_time, reason)` zastaví motory, spočítá penalizace, vytvoří zprávu `result` a v oficiálním platném režimu uloží žebříček. Neplatná jízda má `final_time = None` a do pořadí nepatří. Čas platné jízdy je `raw_time + penalty_seconds`.

```python
penalty_seconds = self.cone_penalties.seconds
final_time = raw_time + penalty_seconds if success else None
if success and self.mode == "official":
    self.leaderboard.add_result(
        self.nickname, raw_time, len(self.cone_penalties.hit_ids),
        penalty_seconds, self.source
    )
```

Výsledek ulož do `self.result` pro opětovné odeslání po reconnectu. Pozici pro zprávu odečti před resetem scény. Následně vrať auto na start a udrž stav `RESULT`, dokud hráč nespustí další jízdu nebo reset.

## 6. Telemetrie a reset

`_publish` posílá typ `execution` s časem, checkpointem, penalizacemi, režimem, zdrojovým řádkem a XY polohou přibližně po 0,12 s reálného času. Reset musí zastavit motory, obnovit fyzikální uzly a vyčistit běhový stav. Po přepnutí úrovně obnov i vybraný žebříček a její ukázkový program.

## 7. Kontrolní bod

V simulaci sleduj pořadí `IDLE → COUNTDOWN → RUNNING → RESULT`. Ověř, že reset funguje před startem, během odpočtu, při jízdě i po výsledku. Zkus pustit dva požadavky `start` rychle po sobě; druhý nesmí založit souběžnou jízdu. Simulační čas nesmí záviset na rychlosti vykreslování panelu.

