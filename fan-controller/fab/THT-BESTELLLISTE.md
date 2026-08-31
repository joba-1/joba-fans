# Durchsteckteile — selbst zu beschaffen

**Nur relevant bei einer Bestellung über JLCPCB.** Deren Katalog führt diese
Teile nicht; sie sind dort aus BOM und CPL entfernt und werden von Hand
gelötet.

**Bei PCBWay entfällt diese Liste:** dort werden die Durchsteckteile
mitbestückt (Through-Hole Assembly), und `fab/pcbway/` enthält sie in BOM
und CPL, samt Beschaffungsangaben in der Note-Spalte.

Mengen für **20 Platinen**, Maße aus den Footprints der Platine — bitte beim
Kauf gegenprüfen, vor allem Rastermaß und Bohrungsdurchmesser.

---

## C1 — Elektrolytkondensator 220 µF

| | |
|---|---|
| Menge | 20 |
| Kapazität | 220 µF |
| Spannung | **≥ 25 V** (Schiene führt 12 V) |
| Bauform | radial bedrahtet, stehend |
| **Rastermaß** | **3,5 mm** |
| Bohrung | 0,8 mm |
| max. Durchmesser | 8 mm |
| Bauhöhe | unkritisch, ~11 mm üblich |

Suchbegriff: „Elko 220µF 25V radial RM 3,5mm 8mm".

Achtung: JLCPCB hatte hier einen **SMD**-Typ vorgeschlagen (C2941234,
6,3 × 5,8 mm). Der passt nicht — die Platine hat bedrahtete Pads.

Polarität beachten: Pluspol ist auf dem Bestückungsdruck markiert.

---

## J1 — DC-Hohlbuchse 5,5 × 2,1 mm

| | |
|---|---|
| Menge | 20 |
| Typ | Einbaubuchse, **horizontal / gewinkelt** |
| Innenstift | 2,1 mm |
| Außendurchmesser | 5,5 mm |
| Anschlüsse | 3 Pins (Plus, Minus, Schalter/Mechanik) |
| Bohrungen | 1,6 mm |
| Pin-Abstände | 3,0 mm (x), 4,7 mm (y) |
| Strom | ≥ 2 A |

Referenztyp: **CUI PJ-102AH** — der Footprint stammt von diesem Teil.
Kompatibel sind die weit verbreiteten „DC-005"-Buchsen mit gleichem
Pinbild; bitte Maßbild vergleichen.

Die Buchse steht 3,5 mm über die Platinenkante hinaus — so gewollt, damit
der Stecker von außen erreichbar ist.

---

## J2–J5 — Lüfter-Stiftleisten 1×4

| | |
|---|---|
| Menge | **80 Stück** (4 pro Platine) |
| Typ | Stiftleiste, gerade, stehend |
| Polzahl | 1×4 |
| **Rastermaß** | **2,54 mm** |
| Bohrung | 1,0 mm |
| Pinlänge | ≥ 6 mm (üblicher Standard) |

Am günstigsten als **40-polige Leiste zum Ablängen** — 8 Stück reichen für
alle 20 Platinen. Suchbegriff: „Stiftleiste 1x40 RM 2,54 gerade".

Diese vier Stecker nehmen die PC-Lüfter auf (GND, +12 V, Tacho, PWM).

---

## U1 — Buchsenleisten für das XIAO-Modul

| | |
|---|---|
| Menge | **40 Stück** (2 pro Platine) |
| Typ | Buchsenleiste, gerade, stehend |
| Polzahl | 1×7 |
| **Rastermaß** | **2,54 mm** |
| Bohrung | 0,89 mm |
| Reihenabstand | 15,24 mm (0,6") |

Ebenfalls als 40-polige Leiste zum Ablängen sinnvoll — 7 Stück genügen.
Suchbegriff: „Buchsenleiste 1x40 RM 2,54 gerade".

Hier wird das XIAO-Modul eingesteckt, nicht eingelötet. Beim Ablängen: 1×40
ergibt 5× 1×7 mit Rest, also lieber eine Leiste mehr einplanen — beim
Trennen geht meist ein Kontakt verloren.

---

## Ebenfalls selbst zu beschaffen

**20× Seeed XIAO ESP32-C3.** Nicht Teil der Bestückung; wird nach dem Löten
der Fassungen gesteckt.

---

## Übersicht

| Pos | Teil | Stück | Sinnvolle Bestellmenge |
|---|---|---|---|
| C1 | Elko 220 µF/25 V, RM 3,5 mm | 20 | 25 |
| J1 | DC-Buchse 5,5×2,1 horizontal | 20 | 25 |
| J2–J5 | Stiftleiste 2,54 mm | 80 | 8× 1×40 |
| U1 | Buchsenleiste 2,54 mm | 40 | 7× 1×40 |
| — | XIAO ESP32-C3 | 20 | 20 |

Reichelt, Mouser oder AliExpress führen alles; die Leisten sind dort
deutlich billiger als einzeln konfektioniert.

---

## Löthinweise

Insgesamt **35 Lötstellen pro Platine**, alle unkritisch — 2,54-mm-Raster
und Hohlbuchse, kein Feinpitch:

| Teil | Lötstellen |
|---|---|
| C1 | 2 |
| J1 | 3 |
| J2–J5 | 16 |
| U1-Fassungen | 14 |

Reihenfolge: erst die flachen Buchsenleisten (U1), dann die Stiftleisten,
zuletzt Elko und Hohlbuchse. Die Fassungen beim Löten mit dem gesteckten
Modul ausrichten, damit sie fluchten.
