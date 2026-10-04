# Through-hole parts — to be sourced yourself

**Only relevant for an order at JLCPCB.** Their catalogue does not carry these parts; they are removed from
the BOM and CPL there and soldered by hand.

**With PCBWay this list does not apply:** they assemble the through-hole parts too (through-hole
assembly), and `pcbway/` contains them in BOM and CPL, with sourcing details in the Note column. The
ordered run was assembled by PCBWay.

Quantities are given **per board** and for **10 boards** (the run that was ordered). Dimensions come from
the footprints on the board — please check them when buying, above all pitch and drill diameter.

---

## C1 — electrolytic capacitor 220 µF

| | |
|---|---|
| Quantity | 1 per board (10) |
| Capacitance | 220 µF |
| Voltage | **≥ 25 V** (the rail carries 12 V) |
| Package | radial leaded, upright |
| **Pitch** | **3.5 mm** |
| Drill | 0.8 mm |
| Max. diameter | 8 mm |
| Height | not critical, ~11 mm usual |

Search term: "electrolytic 220µF 25V radial 3.5mm pitch 8mm".

Note: JLCPCB had suggested an **SMD** type here (C2941234, 6.3 × 5.8 mm). It does not fit — the board has
leaded pads.

Mind the polarity: the positive terminal is marked on the silkscreen.

---

## J1 — DC barrel jack 5.5 × 2.1 mm

| | |
|---|---|
| Quantity | 1 per board (10) |
| Type | panel-mount jack, **horizontal / right-angle** |
| Centre pin | 2.1 mm |
| Outer diameter | 5.5 mm |
| Terminals | 3 pins (plus, minus, switch/mechanical) |
| Drills | 1.6 mm |
| Pin spacing | 3.0 mm (x), 4.7 mm (y) |
| Current | ≥ 2 A |

Reference type: **CUI PJ-102AH** — the footprint comes from this part. The widely available "DC-005"
jacks with the same pin pattern are compatible; compare the dimension drawing.

The jack overhangs the board edge — intended, so that the plug can be reached from outside (see
[`fan-housing`](../../fan-housing/)).

---

## J2–J5 — fan pin headers 1×4

| | |
|---|---|
| Quantity | 4 per board (**40**) |
| Type | pin header, straight, upright |
| Positions | 1×4 |
| **Pitch** | **2.54 mm** |
| Drill | 1.0 mm |
| Pin length | ≥ 6 mm (usual standard) |

Cheapest as a **40-pin strip to be cut** — 4 strips are enough for 10 boards. Search term: "pin header
1x40 2.54mm straight".

These four connectors take the PC fans (GND, +12 V, tach, PWM). They are **unshrouded** headers without
polarisation — see the warning in the [component README](../README.md#known-issues).

---

## U1 — female headers for the XIAO module

| | |
|---|---|
| Quantity | 2 per board (**20**) |
| Type | female header, straight, upright |
| Positions | 1×7 |
| **Pitch** | **2.54 mm** |
| Drill | 0.89 mm |
| Row spacing | 15.24 mm (0.6") |

Also sensible as a 40-pin strip to be cut — one strip gives 5 pieces of 1×7 (with 5 contacts left over), so
20 pieces need 4 strips; plan **5**. Search term: "female header 1x40 2.54mm straight".

The XIAO module is plugged in here, not soldered in. A contact is usually lost when cutting, hence the
extra strip.

---

## Also to be sourced yourself

**1 Seeed XIAO ESP32-C3 per board.** Not part of the assembly; it is plugged in after the sockets are
soldered. (The XIAO ESP32-C6 is pin-compatible and also works with the firmware.)

---

## Overview

| Pos | Part | Per board | For 10 boards |
|---|---|---|---|
| C1 | electrolytic 220 µF/25 V, 3.5 mm pitch | 1 | 12 |
| J1 | DC jack 5.5×2.1 horizontal | 1 | 12 |
| J2–J5 | pin header 2.54 mm | 4 | 4× 1×40 |
| U1 | female header 2.54 mm | 2 | 5× 1×40 |
| — | XIAO ESP32-C3 | 1 | 10 |

Reichelt, Mouser or AliExpress carry everything; the strips are much cheaper there than pre-cut pieces.

---

## Soldering notes

**35 solder joints per board** in total, all uncritical — 2.54 mm pitch and a barrel jack, no fine pitch:

| Part | Joints |
|---|---|
| C1 | 2 |
| J1 | 3 |
| J2–J5 | 16 |
| U1 sockets | 14 |

Order: first the flat female headers (U1), then the pin headers, last the electrolytic cap and the jack.
Align the sockets with the module plugged in while soldering, so that they line up.
