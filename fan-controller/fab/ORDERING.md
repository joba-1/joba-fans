# Ordering options

Board: 72.9 × 25.0 mm, 2 layers. Target quantity 20.

Per board: **16 SMD parts** (12× 0603 resistors, 0805 cap, SMA diode, 1812
polyfuse, SOT-223 regulator) and **8 through-hole** (4 fan headers, 2 socket
headers, barrel jack, radial cap) — 24 placements, 68 solder joints.

U1 (the XIAO) is DNP everywhere: it is socketed and you supply it.

---

## Option A — assembled, ~€95 / ~€4.70 per board

Send `fan-controller-fab.zip` to JLCPCB (or PCBWay / Aisler) for a
20-off assembled run.

Estimated from JLCPCB's published rates — **verify at order time, these
move**:

| | USD |
|---|---|
| Setup | 8.00 |
| Stencil | 1.50 |
| SMT placement (660 joints) | 1.12 |
| Hand-solder THT (700 joints) | 15.61 |
| Bare PCBs | 15–25 |
| Components, 20 sets | 25–40 |
| Shipping to DE | 20–30 |
| **Total** | **~103 USD ≈ 95 EUR** |

The through-hole line dominates: JLCPCB charges a $3.50 hand-soldering fee
plus $0.0173 per joint, and this board has 35 THT joints each. That single
item is about half the labour cost. Reducing THT count is the main lever if
the quote comes back high.

**Effort: none.** Boards arrive ready; plug in the XIAO modules.

---

## Option B — bare PCBs panelised, ~€5 + shipping

Exploits the standard "5 boards ≤ 100×100 mm, dirt cheap" deal by putting
several circuits on one panel with cut lines between them.

**The arithmetic is tight.** Four boards stacked is 4 × 25.0 = exactly
100.0 mm with *zero* gap — most fabs will not accept that, and it leaves
nothing for panel rails. A 3-across-plus-1-on-top arrangement is
75 × 97.9 mm before gaps, which also exceeds 100 mm on one axis once
routing gaps are added.

The board cannot be made shorter without rerouting: the `+12V_PROT` traces
already sit at exactly 0.5 mm from both edges, the design-rule minimum, so
there is **zero slack** in the current layout. Bigger resistors would not
help — the height is set by trace routing, not part size.

**What does fit: 3-up.** 75 × 72.9 mm, comfortable gaps, no design changes.
A 5-panel order yields **15 boards**.

**Effort: substantial.** Hand-assembling 15–20 boards means ~240 0603
resistors, 15–20 each of SOT-223 regulator, SMA diode, 1812 polyfuse, plus
all the connectors. Several evenings.

Also: you own the panel's correctness. A mistake multiplies across every
copy, and some fabs charge a panelisation fee that eats the saving.

---

## Recommendation

Get a real quote for Option A before committing to B. The estimate above
puts assembled at ~€4.70/board — if that holds, the saving from Option B is
perhaps €60–70 in exchange for several evenings of soldering and the risk of
panelising it yourself.

If the quote comes back much higher than estimated, the fallback that keeps
Option A viable is reducing the through-hole count, since that is what
drives the labour cost.

---

## Before ordering either way

1. **Fill in MPN / Supplier in the BOM**, or let the assembler substitute
   from stock — everything except the barrel jack and the AMS1117 is a
   generic jellybean part.
2. **Source 20 XIAO ESP32-C3 modules** if you do not have enough.
3. Sanity-check the gerbers in an online viewer before paying.
