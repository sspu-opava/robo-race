# Etapa 3 – Bezpečný jazyk RoboScript

[Předchozí](02-svet-a-robot.md) · [Obsah](00-obsah-a-priprava.md) · [Další](04-interpret-a-pohon.md)

## Cíl

Přijmout hráčův text, převést ho na přesně šest povolených instrukcí a zamítnout všechno ostatní. Neexistuje žádné `eval`, `exec` ani spuštění Pythonu z textu hráče.

## 1. Sepiš přesnou gramatiku

Každý neprázdný řádek obsahuje jeden příkaz. Komentář začíná `#`. Název je velkými písmeny; desetinný oddělovač je tečka.

| Příkaz | Parametry | Rozsah |
|---|---|---|
| `PLYN(p)` | výkon | 0–100 % |
| `DOPREDU(t)` | čas vpřed | 0,05–5,00 s |
| `DOZADU(t)` | čas vzad | 0,05–5,00 s |
| `VLEVO(k, t)` | intenzita, čas | 0–100 %; 0,05–5,00 s |
| `VPRAVO(k, t)` | intenzita, čas | 0–100 %; 0,05–5,00 s |
| `BRZDA(t)` | čas brzdění | 0,05–5,00 s |

Příklad platného programu:

```text
# Zkus mírně ubrat před zatáčkou.
PLYN(45)
DOPREDU(1.2)
VLEVO(60, 0.8)
BRZDA(0.4)
```

## 2. Reprezentuj příkaz jako data

V [`language.py`](../../controllers/roborace_controller/language.py) je neměnný záznam:

```python
@dataclass(frozen=True)
class Instruction:
    opcode: str
    args: tuple[float, ...]
    source_line: int

    @property
    def duration(self) -> float:
        return self.args[-1] if self.opcode != "PLYN" else 0.0
```

`source_line` umožní zvýraznit chybný nebo právě prováděný řádek v editoru. `PLYN` mění nastavení okamžitě, a proto nepřispívá k délce programu.

## 3. Parsuj pomocí celé shody

```python
_NUMBER = r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)"
_COMMAND = re.compile(
    rf"^([A-Z]+)\s*\(\s*({_NUMBER})(?:\s*,\s*({_NUMBER}))?\s*\)$"
)

for line_number, raw_line in enumerate(source.splitlines(), start=1):
    line = raw_line.split("#", 1)[0].strip()
    if not line:
        continue
    match = _COMMAND.fullmatch(line)
    if not match:
        raise ParseError(line_number, "Použij jeden příkaz ve tvaru NÁZEV(čísla).")
```

`fullmatch` zabrání přidat za platný příkaz další text. Výraz přijímá nezáporná desetinná čísla zapsaná tečkou; `1,2` se považuje za dva argumenty, nikoli desetinné číslo. Samotný regex ještě nehlídá název, počet parametrů ani rozsah. Ty kontroluj zvlášť.

## 4. Ověř sémantiku a limity

Po shodě s regexem zkontroluj, zda `opcode` patří do množiny šesti příkazů. Pro `VLEVO` a `VPRAVO` požaduj dva argumenty, pro ostatní jeden. Potom použij číselné hranice. Současný parser také hlídá maximálně 10 000 znaků zdroje, 40 instrukcí a 32 s součtu časovaných povelů.

```python
instruction = Instruction(opcode, values, line_number)
instructions.append(instruction)
total_duration += instruction.duration
if len(instructions) > MAX_INSTRUCTIONS:
    raise ParseError(line_number, "Program je příliš dlouhý.")
if total_duration > MAX_TOTAL_DURATION + 1e-9:
    raise ParseError(line_number, "Součet dob překročil 32 s.")
```

U `PLYN(0)` vrať varování: další pohybové příkazy sice běží, ale cílová rychlost je nula. Prázdný program odmítni. Na serverové validaci trvej i tehdy, když panel dříve zobrazil „Ověřit“; uživatel může poslat WWI zprávu přímo.

## 5. Přidej chybu s číslem řádku

```python
class ParseError(ValueError):
    def __init__(self, line: int, message: str):
        self.line = line
        self.message = message
        super().__init__(f"Řádek {line}: {message}")
```

Controller pak může odeslat `{"type":"validation_result","valid":false,"line":3,"message":"..."}`. Panel zvýrazní přesný řádek.

## 6. Kontrolní bod

Vyzkoušej `parse_program("PLYN(40)\nDOPREDU(1.0)")` a ověř dvě instrukce s původními řádky 1 a 2. Potom zkus `VLEVO(101, 0.5)`, `DOPREDU(0)`, malé `plyn(40)`, dva příkazy na jednom řádku a 41 instrukcí. Všechny neplatné varianty musí skončit `ParseError`, nikoli spuštěním či tichým přeskočením.

