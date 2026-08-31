# Fabrication package — 4-channel ESP32-C3 PC fan controller

Generated from `fan-controller.kicad_pcb` / `.kicad_sch` with KiCad 10.0.5.
Regenerate with `fan-controller/make_fab.sh`.

## Board

| | |
|---|---|
| Size | 72.9 × 25.0 mm |
| Layers | 2 (F.Cu / B.Cu), 1 oz copper |
| Min track / clearance | 0.2 mm / 0.2 mm |
| Min drill | 0.3 mm |
| Finished thickness | 1.6 mm (standard) |
| Surface finish | HASL or ENIG, either is fine |
| Solder mask / silkscreen | any colour |
| Castellated / edge plating | no |

Quantity: **20 pcs**, assembled.

## Contents

```
gerbers/            RS-274X gerbers + Excellon drill (mm, absolute origin)
  *-F_Cu.gtl          top copper
  *-B_Cu.gbl          bottom copper (ground plane)
  *-F_Mask.gts        top solder mask
  *-B_Mask.gbs        bottom solder mask
  *-F_Paste.gtp       top paste stencil
  *-B_Paste.gbp       bottom paste stencil
  *-F_Silkscreen.gto  top silkscreen
  *-B_Silkscreen.gbo  bottom silkscreen
  *-Edge_Cuts.gm1     board outline
  *.drl               drill file
  *-drl_map.gbr       drill map (reference only, do not fabricate)
  *-job.gbrjob        gerber job file
fan-controller-bom.csv   BOM, JLCPCB-Spalten (Comment, Designator,
                         Footprint, LCSC Part #)
fan-controller-cpl.csv   Pick-and-place, JLCPCB-Spalten (Designator,
                         Mid X, Mid Y, Layer, Rotation); nur Oberseite,
                         DNP ausgenommen
```

Origin for both drill and placement files is the board's **bottom-left
corner**.

## Assembly notes

**U1 ist die Fassungsposition, nicht das Modul.** Dort gehoeren zwei
**1×7-Buchsenleisten** hin; das XIAO-Modul selbst wird spaeter gesteckt und
ist nicht Teil der Bestueckung.

Der Grund fuer diese Verdrehung: die Fassungen haben kein eigenes
Schaltplan-Symbol — ihre Loecher sind die 14 Durchsteckpads des
Modul-Footprints. Als eigene BOM-Zeile mit erfundenen Designatoren
(U1-SKT1/2) haetten sie keinen CPL-Eintrag, und JLCPCB weist BOM-Zeilen
ohne passenden CPL-Eintrag zurueck. Darum laeuft die Position unter U1,
mit der Fassung als Comment.

All parts are on the top side. J1 (barrel jack) overhangs the right board
edge by 3.5 mm by design — its flange seats on the edge so the socket is
reachable from outside an enclosure.

Die Spalte **LCSC Part #** in der BOM ist leer. Entweder selbst ausfuellen
oder den Bestuecker aus seinem Lager substituieren lassen — ausser der
Hohlbuchse und dem AMS1117 ist alles Standardware.

BOM und CPL stehen in **JLCPCBs Spaltenformat**. kicad-cli exportiert eigene
Kopfzeilen (`Ref,Val,Package,PosX,PosY,Rot,Side` bzw. `Value` statt
`Comment`), die der Import dort ablehnt — daher erzeugen `make_bom.py` und
`make_cpl.py` die Dateien um. Fuer PCBWay oder Aisler sind beide Formate in
der Regel unproblematisch.

JLCPCB gleicht **BOM und CPL designatorweise** ab. Deshalb stehen in der BOM
vollstaendige Kommalisten (`R1,R2,R3,R4`) statt Bereichen (`R1-R4`), und
jeder Designator existiert in beiden Dateien. Aktuell 23 auf beiden Seiten,
deckungsgleich.

## Reproducing

```sh
fan-controller/make_fab.sh
```

Gerbers must be exported with an explicit `--layers` list. A bare
`kicad-cli pcb export gerbers` writes *every* layer, including the
`User.Eco1` scratch layer used during layout for review markers.
