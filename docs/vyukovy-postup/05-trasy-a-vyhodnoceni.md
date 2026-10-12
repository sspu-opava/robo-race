# Etapa 5 – Trasy, brány, koridor a překážky

[Předchozí](04-interpret-a-pohon.md) · [Obsah](00-obsah-a-priprava.md) · [Další](06-supervisor-a-zavod.md)

## Cíl

Popsat čtyři obtížnosti jako data, vytvořit fyzické prvky vybrané trasy a rozhodovat o průjezdu branami podle skutečné polohy robota.

## 1. Ulož trať do datového modelu

[`Course`](../../controllers/roborace_controller/courses.py) sdružuje název, popis, střednici, tři checkpointy, cíl, hrboly, bariéry, ukázkový program a volitelné trojrozměrné segmenty silnice. Základní střednice:

```python
_BASE_SEGMENTS = (
    ((-3.8, -1.5), (0.0, -1.5)),
    ((0.0, -1.5), (0.0, 1.5)),
    ((0.0, 1.5), (3.8, 1.5)),
)
```

Úroveň 1 používá jednoduchý okruh. Úroveň 2 přidává dvě fyzické vlny. Úroveň 3 má klikatější střednici, čtyři vlny a čtyři bariéry. Úroveň 4 má tři dlouhé řady spojené dvěma obrátkami, převýšení 0,45 m, čtyři odlišné hrboly a čtyři bariéry. Přesné souřadnice jsou v `COURSES`.

## 2. Odděl povrch od pravidel

Vizuální pruh ještě neurčuje, zda je jízda platná. Supervisor počítá vzdálenost středu robota od všech úseček `track_segments`; nejbližší musí být nejvýše 0,72 m.

```python
if min(distance_to_segment(current_xy, start, end)
       for start, end in self.course.track_segments) > TRACK_HALF_WIDTH:
    self._finish(False, elapsed, "Robot opustil povolený koridor.")
```

`distance_to_segment` promítá bod na úsečku s parametrem omezeným do intervalu `[0, 1]`. Proto nejbližší místo neleží za koncem úsečky. Při návrhu nové trasy slaď tuto matematickou střednici s viditelným jízdním pruhem a mantinely.

## 3. Definuj směrovou konečnou bránu

[`Gate`](../../controllers/roborace_controller/race.py) má bod `(x, y)`, normálu `(nx, ny)` v povoleném směru, polovinu šířky a popisek.

```python
Gate(-2.4, -1.5, 1.0, 0.0, 0.62, "1")
```

Pro předchozí a aktuální pozici spočti jejich podepsané vzdálenosti od roviny brány. Průjezd vpřed nastává při přechodu z `s0 <= 0` na `s1 > 0`. Potom dopočti bod průsečíku a otestuj jeho vzdálenost v tečném směru:

```python
ratio = s0 / (s0 - s1)
px = x0 + ratio * (x1 - x0)
py = y0 + ratio * (y1 - y0)
tangent = -gate.ny * px + gate.nx * py
in_bounds = abs(tangent) <= gate.half_width
```

Opačný směr je chyba. `RouteTracker` přijímá checkpointy jen v pořadí 1 → 2 → 3 → cíl. Při přeskočení brány vrátí důvod DNF.

## 4. Přidej penalizaci kuželů

Každý ze tří kuželů má stabilní `DEF` identifikátor. [`car_cone_overlap`](../../controllers/roborace_controller/collisions.py) aproximuje překryv orientované karoserie a čtyř kol s válcovým kolizním tvarem kužele. Nestačí porovnat jen vzdálenost středů: kolo může kužel trefit, i když střed auta projede dál.

```python
if car_cone_overlap(car_position, orientation, node.getPosition()):
    self.cone_penalties.contact(name)
```

`ConePenaltyLedger` ukládá zasažená ID do množiny. Opakovaný dotek stejného kužele se tedy neúčtuje znovu. Výsledná penalizace je `2.0 * len(hit_ids)` sekund. Reset jízdy množinu vyprázdní.

## 5. Založ vyvýšenou silnici pro úroveň 4

[`CourseRoad.proto`](../../protos/CourseRoad.proto) je `Solid` s viditelným povrchem a stejně velkým `boundingObject`. Úroveň 4 ukládá cestu jako trojice `(x, y, z)`. Supervisor umístí jeden silniční díl mezi dvě po sobě jdoucí trojice a nastaví jeho délku, rotaci a výšku. Změna Z z `0` na `0.45` vytvoří skutečnou rampu. Šířka dílu je 1,40 m.

```python
dx, dy, dz = (end[i] - start[i] for i in range(3))
length = math.sqrt(dx * dx + dy * dy + dz * dz)
tile_size = [length + 0.05, ROAD_WIDTH, ROAD_THICKNESS]
node.getField("size").setSFVec3f(tile_size)
```

Úplný výpočet osy a úhlu rotace je v metodě `_place_road_tile`. Pouhé nastavení délky bez natočení by fungovalo na rovině, ale stoupající úsek by byl fyzikálně špatně. Značky bran pro horskou trasu vytváří [`CourseGate.proto`](../../protos/CourseGate.proto).

## 6. Umísťuj překážky podle vybrané trasy

Nevyužité objekty jsou připravené ve světě na `z = -50`. Při přepnutí úrovně Supervisor všechny vrátí mimo arénu a teprve potom vybrané přemístí. U hrbolu upraví stejný rozměr viditelného `Box` i `boundingObject`:

```python
dimensions = [size_x, size_y, half_height * 2.0]
shape.getField("geometry").getSFNode().getField("size").setSFVec3f(dimensions)
node.getField("boundingObject").getSFNode().getField("size").setSFVec3f(dimensions)
node.getField("translation").setSFVec3f([x, y, road_z + half_height])
```

U pohyblivých bariér a kuželů po změně polohy zavolej `resetPhysics()`. Výšku překážky na vyvýšené cestě počítej vzhledem k povrchu silnice. Při návrhu ověř zvlášť souřadnice každého kužele, hrbolu i bariéry uvnitř zvolené cesty.

## 7. Konfigurace výsledků

`LEVEL_CONFIG_IDS` dává každé úrovni samostatnou identitu žebříčku. Když změníš polohu brány, šířku, fyziku nebo překážku, změň ID dané úrovně. Jinak by výsledky ze dvou různých tratí vypadaly srovnatelně, ač nejsou.

## 8. Kontrolní bod

Při přepnutí úrovně sleduj silnici, hrboly, kužely a bariéry z kamery. Zkontroluj, že všechny leží na povrchu vybrané trasy a předchozí prvky zmizely. Projeď každou bránu oběma směry a zkus průjezd mimo její konečnou šířku; jen správný průjezd ve správném pořadí se smí započítat.

