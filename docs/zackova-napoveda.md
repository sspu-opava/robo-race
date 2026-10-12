# RoboRace – rychlá nápověda

## Cíl

Dostaň robota přes brány 1, 2 a 3 do cíle. Kužely jsou překážky: každý zasažený kužel přidá k výslednému času 2 sekundy. Robot se řídí přesně podle tvých příkazů. Sám neuhýbá.

## Obtížnost tratí

- **Úroveň 1:** rovná trať se dvěma zatáčkami.
- **Úroveň 2:** stejný okruh s fyzickými vlnami.
- **Úroveň 3:** slalom, vlny a bariéry přímo v jízdním pruhu.
- **Úroveň 4:** delší horská serpentina se stoupáním, bariérami a hrboly různých tvarů.

## Šest příkazů

| Příkaz | Co dělá |
|---|---|
| `PLYN(45)` | Nastaví plyn na 45 %. Sám o sobě robota neposune. |
| `DOPREDU(1.2)` | Jede vpřed 1,2 sekundy. |
| `DOZADU(0.5)` | Couvá půl sekundy. |
| `VLEVO(60, 0.8)` | Zatáčí vlevo intenzitou 60 % po dobu 0,8 sekundy. |
| `VPRAVO(40, 0.7)` | Zatáčí vpravo intenzitou 40 % po dobu 0,7 sekundy. |
| `BRZDA(0.6)` | Aktivně brzdí 0,6 sekundy. |

```text
PLYN(40)
DOPREDU(1.5)
VLEVO(50, 0.8)
DOPREDU(1.0)
BRZDA(0.5)
```

Piš jeden příkaz na řádek. Za `#` můžeš přidat poznámku. Desetinná čísla piš s **tečkou** (`0.8`), čárka odděluje parametry (`VLEVO(60, 0.8)`). Používej velká písmena v názvu příkazu.

## Jak postupovat

1. Načti příklad **Rovinka + brzda**.
2. Stiskni **Ověřit**, pak **Testovat**.
3. Sleduj číslo právě prováděného řádku a checkpointy.
4. Uprav jeden čas nebo intenzitu a test zopakuj.
5. Až budeš připravený, zadej přezdívku a zkus **Soutěžit**.

Plyn a zatáčení nepůsobí okamžitě. Kola potřebují čas na roztočení a těžší robot pokračuje setrvačností i po změně příkazu. Vysoký plyn v zatáčce proto může způsobit smyk nebo náraz. Kratší a pomalejší zatáčka někdy vyjde rychleji než prudké zatočení.
