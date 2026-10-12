# Etapa 4 – Interpret příkazů a pohon kol

[Předchozí](03-jazyk-roboscript.md) · [Obsah](00-obsah-a-priprava.md) · [Další](05-trasy-a-vyhodnoceni.md)

## Cíl

Proměnit instrukce v požadované rychlosti motorů bez blokujícího čekání. Jeden krok interpretu odpovídá jednomu simulačnímu kroku Webots.

## 1. Udržuj stav interpretu

[`Interpreter`](../../controllers/roborace_controller/interpreter.py) si pamatuje index dalšího příkazu, právě vykonávaný příkaz, jeho zbývající čas, aktuální plyn a poslední směr. Výchozí plyn je 40 % a směr vpřed. Nová jízda vždy vytvoří nový `Interpreter`, takže staré nastavení nepřeteče do dalšího pokusu.

```python
self.index = 0
self.current = None
self.remaining = 0.0
self.throttle = 40.0
self.direction = 1
self.coast_remaining = None
```

`PLYN` nemá trvání: při `step(dt)` ho zpracuj ve smyčce a pokračuj k následujícímu časovanému příkazu bez umělé pauzy. Doba časovaného příkazu se v každém kroku sníží o `dt`.

```python
while self.current is None and self.index < len(self.instructions):
    instruction = self.instructions[self.index]
    if instruction.opcode == "PLYN":
        self.throttle = instruction.args[0]
        self.index += 1
        continue
    self.current = instruction
    self.remaining = instruction.duration
```

## 2. Přelož povel na levou a pravou stranu

[`wheel_targets`](../../controllers/roborace_controller/drivetrain.py) používá 14 rad/s jako strop a `0.72` jako největší asymetrii stran.

```python
base = direction * (throttle / 100.0) * max_speed
delta = (steer / 100.0) * max_difference * abs(base)
if turn == "left":
    left, right = base - delta, base + delta
elif turn == "right":
    left, right = base + delta, base - delta
else:
    left = right = base
```

Použití `abs(base)` je důležité: `VLEVO` má zvýšit levé natočení robota i při couvání. Kdyby se rozdíl počítal přímo ze záporného `base`, význam vlevo/vpravo by se v obrátil.

Jestli některá strana překročí 14 rad/s, vyděl obě rychlosti stejným poměrem:

```python
peak = max(abs(left), abs(right))
if peak > max_speed:
    factor = max_speed / peak
    left, right = left * factor, right * factor
```

Tím zachováš poměr potřebný pro zatáčku.

## 3. Vytvoř vykonávací krok

Pro `DOPREDU` nastav `direction = 1`, pro `DOZADU` `-1`; u zatáček ponech poslední směr. `BRZDA` vyžaduje nulu na obou stranách a příznak `braking=True`. Návratový `DriveStep` nese i číslo zdrojového řádku pro telemetrii.

```python
@dataclass(frozen=True)
class DriveStep:
    left: float
    right: float
    source_line: int | None
    braking: bool = False
    program_finished: bool = False
```

Po posledním příkazu následuje nejvýše dvousekundový dojezd s brzděním. Pokud robot během něj projede cílem, dokončení se stále uzná. Jinak interpret označí program za skončený a Supervisor vyhlásí DNF.

## 4. Omez změnu cíle motorů

Požadovanou rychlost nenasazuj skokem. `RateLimitedDrive.step` přiblíží každou stranu k cíli nejvýše o `rate × dt`: 24 rad/s² při jízdě a 38 rad/s² při brzdění.

```python
rate = BRAKE_ACCELERATION if braking else MAX_ACCELERATION
limit = rate * max(0.0, dt)
self.left = _approach(self.left, target_left, limit)
self.right = _approach(self.right, target_right, limit)
```

Při `dt = 0.016` s je největší běžná změna cíle `0.384 rad/s` za krok. Motor má navíc vlastní fyzikální reakci a omezený moment. Rampa tedy mění požadavek, nepřepisuje rychlost těla.

## 5. Připoj obě strany ke čtyřem motorům

V hlavním controlleru jsou první dva motory levé a druhé dva pravé:

```python
def _set_wheels(self, left: float, right: float) -> None:
    for motor in self.motors[:2]:
        motor.setVelocity(left)
    for motor in self.motors[2:]:
        motor.setVelocity(right)
```

Před tím v inicializaci nastav všem motorům `setPosition(float("inf"))` a nulovou rychlost. Každý simulační krok volá `interpreter.step(dt)`, potom rampu a nakonec `_set_wheels`.

## 6. Kontrolní bod

Pro `wheel_targets(50)` očekávej stejné kladné rychlosti. `wheel_targets(50, 100, turn="left")` má dát pravé straně vyšší cíl. Totéž ověř při `direction=-1` podle výsledného yaw ve Webots. Při `BRZDA` sleduj postupný pokles; okamžité zastavení fyzikálního těla by bylo chybou modelu.

