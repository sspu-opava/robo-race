# Etapa 2 – Svět, kamera a fyzikální robot

[Předchozí](01-navrh-a-projekt.md) · [Obsah](00-obsah-a-priprava.md) · [Další](03-jazyk-roboscript.md)

## Cíl

Postavit čitelnou arénu a skutečný čtyřkolový robot. Pohyb musí vznikat otáčením kol a kontaktem s podložkou, ne přepisováním pozice vozidla během jízdy.

## 1. Založ svět

Soubor [`worlds/roborace.wbt`](../../worlds/roborace.wbt) začíná hlavičkou `#VRML_SIM R2025a utf8` a importy PROTO. Kamera má vlastní `DEF`, aby ji Supervisor mohl obnovit.

```vrml
EXTERNPROTO "../protos/RoboRaceCar.proto"
EXTERNPROTO "../protos/CourseRoad.proto"
EXTERNPROTO "../protos/CourseGate.proto"

WorldInfo {
  basicTimeStep 16
  coordinateSystem "ENU"
}
DEF COURSE_VIEW Viewpoint {
  orientation -0.413223395 0.413223395 0.811475725 1.778194113
  position 0 -8 11
  fieldOfView 0.9
}
```

Viewpoint v ENU hledí podél svého lokálního +X. Uvedená orientace míří ze souřadnic `(0, -8, 11)` do středu arény. Při změně kamery aktualizuj i akci `restore_view` v hlavním controlleru.

## 2. Dej pod arénu pevné těleso

Na tmavou podlahu použij `Solid` s vizuální `Shape` a odpovídajícím `boundingObject`. Samotná barva tvaru není kolizní plocha. Traťové značení může být jen plochý vizuální `Transform`, zatímco podklad nese fyzickou kolizi.

```vrml
Solid {
  translation 0 0 -0.06
  children [
    Shape {
      appearance PBRAppearance { baseColor 0.035 0.055 0.075 roughness 0.92 }
      geometry Box { size 12.0 7.2 0.12 }
    }
  ]
  contactMaterial "track"
  boundingObject Box { size 12.0 7.2 0.12 }
}
```

Spodní plocha končí v `z = -0.12`, horní v `z = 0`. Barevné pruhy dráhy kresli těsně nad nulou, aby nebyly skryté v podlaze. Pro mantinely přidej další `Solid` s `boundingObject`; vizuální čára sama robota nezastaví.

## 3. Nastav kontakt pneumatik

V `WorldInfo.contactProperties` spoj materiály `tire` a `track`:

```vrml
ContactProperties {
  material1 "tire"
  material2 "track"
  coulombFriction 1.7
  bounce 0
}
```

Stejné názvy musí být uvedené u příslušných fyzikálních uzlů. Tření, hmotnost a moment motorů společně rozhodují o skutečném chování. Nevyvozuj z `Motor.setVelocity`, že se karoserie bude pohybovat předepsanou rychlostí.

## 4. Vytvoř karoserii v PROTO

Soubor [`protos/RoboRaceCar.proto`](../../protos/RoboRaceCar.proto) nabízí pole pro polohu, natočení a název controlleru. Uvnitř je jediný `Robot` se čtyřmi `HingeJoint`. Základ těla má rozměr `0.50 × 0.34 × 0.13 m`, hmotnost `1.8 kg` a nízké těžiště.

```vrml
Robot {
  translation IS translation
  rotation IS rotation
  controller IS controller
  window IS window
  supervisor IS supervisor
  boundingObject Box { size 0.50 0.34 0.13 }
  physics Physics {
    density -1
    mass 1.8
    centerOfMass [ -0.02 0 -0.025 ]
  }
}
```

Lokální +X označ odlišnou barvou nebo tvarem, aby hráč viděl, kam auto míří.

## 5. Připoj každé kolo kloubem

Přední levé kolo je na `(+0.17, +0.22, -0.08)`. Pravé používá záporné Y a zadní záporné X. Ukázka jednoho ze čtyř kloubů:

```vrml
HingeJoint {
  jointParameters HingeJointParameters {
    anchor 0.17 0.22 -0.08
    axis 0 1 0
  }
  device [
    RotationalMotor {
      name "left_front"
      maxVelocity 14
      maxTorque 0.65
    }
  ]
  endPoint Solid {
    translation 0.17 0.22 -0.08
    rotation 1 0 0 -1.5707963267948966
    children [
      Shape { geometry Cylinder { height 0.07 radius 0.08 } }
    ]
    contactMaterial "tire"
    boundingObject Cylinder { height 0.07 radius 0.08 }
    physics Physics { density -1 mass 0.12 }
  }
}
```

V R2025a má primitivum `Cylinder` vlastní osu Z. Rotace `-π/2` kolem X ji zarovná s lokálním +Y, tedy s osou kloubu. Rotaci použij na `Solid` kola, aby stejně směřoval i jeho kolizní tvar. Všechny čtyři `HingeJoint` používají osu `0 1 0`; kladná rychlost pak pohání auto k lokálnímu +X.

## 6. Kontrolní bod

Ve Webots zobraz robot z boku a ověř, že kola skutečně dosedají na podlahu. V kontroleru dočasně nastav všem motorům malou kladnou rychlost; auto musí jet dopředu. Po kontrole pomocný příkaz odstraň. Pak ověř opačný směr a rozdílné rychlosti levé a pravé strany. Ladění této fyziky rozebírá závěrečná etapa.

