# Etapa 7 – WWI protokol, reconnect a trvalý žebříček

[Předchozí](06-supervisor-a-zavod.md) · [Obsah](00-obsah-a-priprava.md) · [Další](08-uzivatelske-rozhrani.md)

## Cíl

Přenášet zprávy mezi lokálním panelem a Webots, po obnovení spojení vrátit aktuální stav a bezpečně zapisovat jen platné oficiální výsledky.

## 1. Definuj typy zpráv

[`protocol.py`](../../controllers/roborace_controller/protocol.py) připouští od klienta `hello`, `restore_view`, `set_level`, `validate`, `start`, `reset`, `new_competitor` a `admin_reset`. Panel posílá například:

```json
{"type":"start","mode":"test","source":"PLYN(40)\nDOPREDU(1.0)","request_id":"rr-123"}
```

Dekodér nejprve zavolá `json.loads`, pak ověří objekt, známý typ a formát `request_id`. Délka ID je nejvýše 80 znaků. Kontrola typu zprávy není náhrada za kontrolu jejích parametrů; `_handle` znovu validuje číslo úrovně, režim jízdy i zdroj programu.

## 2. Ošetři kódování češtiny

Webots R2025a v Python vazbě `wwiSendText` může měřit počet znaků místo počtu bajtů. Surová čeština v UTF-8 by mohla zprávu useknout. Proto posílej JSON s escape sekvencemi:

```python
def encode_message(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))
```

Na klientské straně se po `JSON.parse` český text opět zobrazí správně. Zpracování uživatelského textu jako JSON zároveň neznamená jeho vykonání.

## 3. Připoj lokální WebSocket

[`wwi_client.js`](../../plugins/robot_windows/roborace/wwi_client.js) odvodí místní server z URL otevřeného Webots Robot Window a přečte jméno robota z query parametru `name`. Při otevření spojení pošle inicializační zprávu Webots a potom aplikační pozdrav:

Ještě před vytvořením WebSocketu klient ověří protokol HTTP/HTTPS a hostitele `localhost`, `127.0.0.1` nebo `[::1]`. Vzdálené adresy a URL s přihlašovacími údaji odmítne. Toto spojení je omezené na vlastní počítač; není potřeba internet ani server v místní síti.

```javascript
this.socket.addEventListener('open', () => {
  this.connectionChanged(true);
  this.send('init robot window');
  this.send(JSON.stringify({type: 'hello'}));
});
```

Webots spotřebuje `init robot window` sám. Proto musí samostatné `hello` vyžádat `ready` i tehdy, když se panel otevře až po spuštění simulace. Po přerušení spojení klient zkouší reconnect a controller po `hello` odešle aktuální stav i poslední výsledek.

Zprávy posílané do Webots mají obálku `robot:<jméno>:<obsah>`. Controller sleduje posledních 256 `request_id`, aby opakovaná zpráva nespustila stejný požadavek dvakrát.

## 4. Ulož data odděleně podle úrovně

[`Leaderboard`](../../controllers/roborace_controller/leaderboard.py) používá pro úroveň 1 `data/leaderboard.json`; další úrovně mají `data/leaderboard-level-N.json`. Každý soubor má `competition_config_id`, který se musí rovnat příslušné hodnotě v `LEVEL_CONFIG_IDS`.

```json
{
  "schema_version": 1,
  "competition_config_id": "junior-track-v2-level-1",
  "entries": []
}
```

Výsledek obsahuje přezdívku, UTC čas zápisu, původní čas, počet penalizací, penalizační sekundy, výsledný čas, zdrojový program a ID konfigurace. Přezdívka se normalizuje a omezuje na 20 tisknutelných znaků. Pro stejného hráče zůstává v pořadí jeho nejlepší čas a záznamy jednotlivých oficiálních jízd se ukládají do `official_runs`.

## 5. Zapisuj atomicky

Nezapisuj přímo do finálního JSON souboru. Vytvoř dočasný soubor ve stejném adresáři, zapiš JSON, `flush`, `fsync` a nahraď původní soubor pomocí `os.replace`. Před nahrazením validního starého souboru vytvoř stejně bezpečně zálohu `.bak`.

```python
fd, temp_name = tempfile.mkstemp(
    prefix="leaderboard-", suffix=".tmp", dir=self.path.parent
)
with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as target:
    json.dump(self.data, target, ensure_ascii=False, indent=2)
    target.write("\n")
    target.flush()
    os.fsync(target.fileno())
os.replace(temp_name, self.path)
```

Při čtení poškozeného souboru zkus platnou zálohu. Pokud ID konfigurace nesouhlasí, zobraz varování a začni prázdným žebříčkem pro aktuální trať.

## 6. Oficiální pokusy a správa

Controller sleduje nejvýše dva oficiální pokusy pro dvojici `(úroveň, přezdívka)` v jedné relaci. Testovací jízdy tento čítač nemění. `new_competitor` vynuluje lokální počítadlo zadané přezdívky; nejde o ověření identity. `admin_reset` vyžaduje `confirm: true` a maže žebříček aktuální úrovně. Rozhraní tuto akci potvrzuje uživatelským dialogem.

## 7. Kontrolní bod

Odpoj a znovu připoj panel: musí přijít `ready`, případná běžící telemetrie a poslední výsledek. Zkus dvakrát stejné `request_id` a ověř, že se soutěžní pokus nezapočítá dvakrát. Po platné oficiální jízdě otevři správný JSON soubor; po testovací nebo neplatné jízdě musí zůstat pořadí beze změny.

