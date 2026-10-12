# Etapa 8 – Úzký panel Robot Window

[Předchozí](07-protokol-a-zebricek.md) · [Obsah](00-obsah-a-priprava.md) · [Další](09-overeni-a-kalibrace.md)

## Cíl

Postavit český panel, v němž jsou všechny ovládací prvky v jednom sloupci širokém nejvýše 400 px. Panel se otevře jako lokální Webots Robot Window a nevyžaduje externí fonty, CDN ani framework.

## 1. Propoj HTML, CSS a JavaScript

V [`roborace.html`](../../plugins/robot_windows/roborace/roborace.html) používej relativní lokální odkazy. Parametr verze pomáhá obnovit soubory v prohlížeči po změně vzhledu:

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./style.css?v=panel-3">
<script type="module" src="./roborace.js?v=panel-3"></script>
```

Po změně CSS či JS verzi zvyš. Když panel působí jako bez stylů, nejdříve v prohlížeči ověř, zda se stylesheet skutečně načetl a kolik obsahuje pravidel. Při této aplikaci se URL souboru vracela, ale stará otevřená stránka měla 0 pravidel; nová verze odkazu vynutila čerstvé načtení.

HTML navíc obsahuje Content Security Policy: výchozí zdroje jsou zakázané, skripty a styly mohou pocházet pouze ze stejného místního serveru a spojení WS/WSS pouze z loopback adres. Přehled pravidel najdeš v `meta[http-equiv="Content-Security-Policy"]`. Při rozšiřování panelu nepřidávej CDN, vzdálené fonty, obrázky ani analytiku; soubory musí být součástí projektu.

## 2. Uspořádej obsah podle práce hráče

Pořadí v HTML je: hlavička a připojení; obtížnost trasy; pět metrik; editor programu s příklady; soutěžící a akce; telemetrie; žebříček; patička. Prvky používají stabilní ID, na která se váže [`roborace.js`](../../plugins/robot_windows/roborace/roborace.js). Například:

```html
<select id="courseLevel" disabled>
  <option value="1">Úroveň 1 · Základní zatáčky</option>
  <option value="4">Úroveň 4 · Horská serpentina</option>
</select>
<textarea id="source" aria-label="Editor RoboScript"></textarea>
<button id="test" type="button">Testovat</button>
```

`disabled` u výběru trasy je počáteční stav. Po zprávě `ready` klient zavolá `setBusy(false)` a výběr povolí. Během jízdy ho opět dočasně zakáže.

## 3. Nastav šířku a vizuální systém

[`style.css`](../../plugins/robot_windows/roborace/style.css) používá tmavou grafitovou paletu, jemné rámečky, menší písmo a úzké ovládací prvky. Klíčové je, že kořen aplikace nemá více sloupců vedle sebe:

```css
.app-shell {
  width: 100%;
  max-width: 400px;
  margin: 0 auto;
  padding: 12px 10px 18px;
}
.panel {
  margin-bottom: 8px;
  padding: 11px;
  min-width: 0;
}
```

Uvnitř panelu mohou být menší mřížky metrik, příkladů a tlačítek; všechny zůstávají v jednom vnějším sloupci. `min-width: 0` brání obsahu s dlouhým textem roztahovat grid. Při šířce 320 px se čtyři akce rozdělí do dvou řad.

## 4. Vytvoř editor se zvýrazněním

Editor tvoří tři synchronizované vrstvy: číslování řádků, neinteraktivní `pre#codeHighlight` a průhledná `textarea#source`. Skutečný zápis probíhá jen do `textarea`; `pre` vykresluje komentáře a aktivní řádek.

```javascript
const rows = source.value.split('\n');
rows.forEach((row, index) => {
  const gutterRow = document.createElement('span');
  gutterRow.textContent = String(index + 1);
  lineNumbers.append(gutterRow);
  const codeRow = document.createElement('span');
  // Komentář od # vlož jako samostatný span.
  codeHighlight.append(codeRow, document.createTextNode('\n'));
});
```

Při posunu editoru synchronizuj `scrollTop` a `scrollLeft`. Viditelný text vždy nastavuj přes `textContent` a textové uzly, nikoli přes `innerHTML` z hráčova programu. Tím se obsah editoru neinterpretuje jako HTML.

## 5. Napoj ovládání na protokol

Tlačítka posílají `validate`, `start` s režimem `test` nebo `official`, `reset`, `restore_view` a `set_level`. Funkce `send` přidává jedinečné `request_id`:

```javascript
$('#test').addEventListener('click', () =>
  send({type: 'start', mode: 'test', source: source.value})
);
$('#courseLevel').addEventListener('change', event =>
  send({type: 'set_level', level: Number(event.target.value)})
);
```

V `onMessage` zpracuj `ready`, `validation_result`, `accepted`, `execution`, `result`, `level_changed`, `reset`, `leaderboard` a `error`. Jeden zdroj pravdy o závodu je controller; panel jen zobrazuje jeho zprávy. Po reconnectu se stav obnoví z nového `ready`.

## 6. Přesuň nápovědu do dialogu

Otazník v hlavičce a odkaz `Příkazy ?` u editoru otevírají stejné nativní `dialog`. Obsah uvádí postup jízdy, všech šest povelů a pravidlo setrvačnosti.

```html
<button id="helpButton" type="button" aria-label="Nápověda k ovládání a RoboScriptu">?</button>
<dialog id="helpDialog" aria-labelledby="helpTitle">
  <h2 id="helpTitle">Ovládání hry</h2>
  <button id="closeHelp" type="button" aria-label="Zavřít nápovědu">×</button>
</dialog>
```

```javascript
for (const trigger of [$('#helpButton'), $('#editorHelp')]) {
  trigger.addEventListener('click', () => helpDialog.showModal());
}
$('#closeHelp').addEventListener('click', () => helpDialog.close());
```

`showModal()` přesune dialog do horní vrstvy a prohlížeč podporuje klávesu Escape. V aktuální implementaci se zavře i kliknutím na pozadí dialogu.

## 7. Kontrolní bod

Otevři Robot Window přes běžící Webots, nikoli jako samostatný soubor `file://`; klient potřebuje lokální Webots URL. Ověř načtení CSS, maximální šířku 400 px, absenci vodorovného přetečení ovládacích prvků, čitelnost editoru, povolení výběru trasy po `ready`, funkci všech akcí a otevření/zavření nápovědy. Při nové verzi assetů obnov panel.

