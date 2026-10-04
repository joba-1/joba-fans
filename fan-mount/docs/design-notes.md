# fan-mount — design notes

How the mounts in `../cad/` were derived, why they look the way they do, and how to regenerate
them. The requirements are in [requirements.md](requirements.md), the measured radiator data in
[measurements.md](measurements.md).

## What is in `cad/`

| File | Content | Status |
|---|---|---|
| `RadiatorFanSmall.FCStd` / `.stl` | Mount for radiator **A** (office, 65 mm deep sheet), asymmetric seat | current |
| `RadiatorFanMedium.FCStd` / `.stl` | Mount for radiator **B** (living room, 101 mm), fan centred | current |
| `RadiatorFanLarge.FCStd` / `.stl` | Mount for radiator **C** (dining room, 136 mm), two perforated fields, rib on the centre web | current |
| `RadiatorFanGuard.FCStd` / `.stl` | Finger-guard hood, **one variant for all mounts** (it only depends on the collar, 126.6 mm) | current |
| `ZapfenLarge.stl` | Four pegs for radiator C, printed on their own | current |
| `passprobe.FCStd`, `passprobe_A/B/C.stl` | Fit-test frames: do the measured sheet depths and the edge grip work? | test part |
| `halter_A.stl`, `halter_A_komplett.stl` | First design of the mount for radiator A (mount alone / mount + 6 pegs) | superseded by `RadiatorFanSmall`, kept for reference |
| `radiator_sheets.csv` | Measured perforated-sheet geometry of the three radiators — the source of truth for the spreadsheets | data |

Every `.FCStd` has a spreadsheet **`Masse`** (dimensions) that drives all geometry; a few cells are
formulas (derived values). `Small`, `Medium` and `Large` are the same document with different inputs.

The parts inside are called `Halter` (mount: collar + ribs + baffles), `Zapfen` (pegs), `Schutz`
(guard) and `Zarge` (the collar around the fan).

### Sizes (checked against the STL files)

| | X | Y | Z | Derived from |
|---|---|---|---|---|
| Mount Small / Medium | 226.6 | 126.6 | 28.0 | `z_aussen` + 2 × `blende_b` = 126.6 + 100; `z_hoehe` = 2 + 26 |
| Mount Large | 226.6 | 134.0 | 28.0 | sheet depth 2·16 + 2·40 + 22 = 134 |
| Guard | 131.6 | 131.6 | 14.5 | `z_aussen` + 2 × `schutz_dicke` = 126.6 + 5 |

The fan seat is `z_innen` = 120.6 mm square (120 mm fan + 0.6 mm clearance); the collar is 26 mm
tall above the 2 mm fan rests, so a 25 mm fan sits 1 mm below the rim. The four screw holes use the
standard 105 × 105 mm pattern (`schraub_lk`). The guard's inner size equals the collar's outer size, so
it slips over the collar.

## Glossary of the German names

The spreadsheet aliases and the local variables in the scripts are German. They are stored inside
the `.FCStd` files, so they were not translated:

| Name | Meaning |
|---|---|
| `Masse` | the dimensions spreadsheet |
| `tiefe`, `a_tiefe` … | depth of the perforated sheet (A/B/C) |
| `rand`, `lochfeld`, `stegmitte`, `schlitz`, `steg` | edge strip, perforated field, centre web, slot, web between slots |
| `lueftergroesse`, `luefterhoehe` | fan size (120) and fan thickness (25) |
| `zarge` (`z_innen`, `z_aussen`, `z_dicke`, `z_hoehe`, `zarge_innen`) | the collar: inner/outer size, wall, total height, inner height above the rests |
| `z_auflage`, `z_ecke` | fan rests: thickness (2) and corner length (14) |
| `a_hinten`, `a_vorne`, `a_ueber` | how far the fan projects beyond the sheet: behind (wall side), in front, total |
| `wandabstand`, `wandluft_ist` | distance sheet–wall, resulting air gap to the wall |
| `rippe_b`, `rippe_dy` | rib width and offset |
| `blende_b`, `blende_sd` | baffle width (50) and its screw clearance hole |
| `zapfen_b/l/h/r/sd/spiel` | peg width, length, height, edge radius, core hole, clearance |
| `kern_m2`, `kern_m4` | core-hole diameters for M2 and M4 |
| `trichter_d`, `trichter_t` | funnel diameter and depth at the peg's core hole |
| `kanten_r`, `kehle_r` | edge radius and inner fillet radius |
| `schraub_lk`, `schraub_d` | fan screw hole pattern (105) and hole diameter (6) |
| `schutz_*`, `strebe_*` | guard: wall, skirt, undersize, distance; strut width, pitch, radius, thickness |
| `druckbett`, `bett_rest` | print bed size (230) and what is left of it |
| `plattendicke`, `backentiefe`, `backendicke`, `maulweite`, `blechdicke`, `spiel`, `probelaenge` | fit-test frame: plate, jaw depth and thickness, jaw opening, sheet thickness, clearance, length |

## Regenerating

The scripts in `../scripts/` run inside FreeCAD (View → Panels → Python console), with the
document already open from `fan-mount/cad/`. They write the STL (and, where relevant, the FCStd) next
to the opened document; set the environment variable `FAN_MOUNT_CAD` to write somewhere else.

```python
ZIEL = "RadiatorFanLarge"            # name of the open document
exec(open("<repo>/fan-mount/scripts/build_variante.py").read())   # mount + pegs -> <ZIEL>.stl
exec(open("<repo>/fan-mount/scripts/build_schutz.py").read())     # finger guard -> RadiatorFanGuard.stl
exec(open("<repo>/fan-mount/scripts/build_zapfen.py").read())     # pegs on their own -> ZapfenLarge.stl
```

`passprobe.py` builds the test frames (and the first mount, `halter_A`). To change a dimension,
edit the sheet geometry in `radiator_sheets.csv` **and** in the `Masse` spreadsheet, then run the
script. The depth is a *derived* value (sum of the partial lengths) — if it differs from the
measurement, column E of the spreadsheet shows the difference instead of silently distributing it.

## Fit-test frames (Passproben)

Not a functional part. One print answers four questions:

1. Is the measured depth right?
2. Does the **edge grip** engage over the sheet edge, or does the grid end in a bead / a side panel
   where there is no free edge?
3. Is the **jaw opening** right — does it jam, or wobble?
4. How much does shrinkage distort the width over 141 mm (part C)?

Cross-section, across the wall:

```text
        ┌───────────────────────────────┐   base plate 3 mm
        │                               │
        █ ▁▁                       ▁▁ █     jaw 1.4 mm = sheet 1.0 + clearance 0.4
        █ ██                       ██ █     nose 1.5 mm grips under the sheet
        └──┘                       └──┘     jaw 2.5 mm, outside
          ↑                         ↑
          └──── sheet depth (65/101/136) ────┘
```

The part is **slid onto the sheet edge from the front**. The middle under the sheet is free — it
only clamps at the two edges.

Assumptions to check when you hold it against the radiator:

| Assumption | Value | If wrong |
|---|---|---|
| Sheet thickness | 1.0 mm | change `blechdicke` in the spreadsheet |
| Free sheet edge present | yes | edge grip fails → peg principle needed |
| Jaw depth sufficient | 6 mm | change `backentiefe` |

Print flat (base plate on the bed, noses up) in PLA, 0.2 mm layers, 3 perimeters — then no support
reaches into the jaw. About 60 cm³, a good 3 hours.

The edge grip was later **dropped** from the mounts (it made the part hard to print); the pegs
described below take over the fixing.

## The mount, first design ("Halter A")

`halter_A.stl` — clamp and **collar** (fan seat) in one part, for a 25 mm fan. The fan drops in and
rests on four 2 mm corner rests; there is **no floor** under it, it blows straight onto the sheet. A
base plate with a passage would be a throttle point right at the pressure side — exactly where an axial
fan is most sensitive.

### Ribs instead of a floor

Collar and clamp are joined by **two ribs** that sit on the unperforated edge strips (13 mm at A). A
continuous web across the full sheet depth covered **64 % of the fan outlet** in the first version —
precisely the part above the perforated field, i.e. the only one that does anything. With ribs it is
25 %, all of it collar wall and rests at the edge; **above the perforated field it is 100 % open**.

The script check "field open" tests this at 99 points. It was missing at first, which is why the
floor was only noticed in the picture.

### Asymmetric seat

A 120 mm fan on a 65 mm deep sheet overhangs by 55 mm. With only ~25 mm of wall distance it has to
move forward:

| | mm |
|---|---|
| Total overhang | 55 |
| of which backwards (wall side) | 14 |
| of which forwards (into the room) | 41 |
| Air gap to the wall | 8 |

`a_hinten = z_ecke` — the rear overhang is coupled to the corner length of the rests. As a result
`rippe_dy = 0` and **both ribs lie completely on the unperforated edge strips** of the sheet, while the
front rest continues seamlessly into rib 1.

The wall distance is therefore no longer the governing quantity but a check value:
`wandluft_ist = wandabstand − a_hinten − z_dicke` = 8 mm, requirement at least 5 mm. If the mount is
derived for a radiator with less wall distance, this is the cell where it shows.

### Height

Rest 2 mm + fan 25 mm = 27 mm. With ~55 mm of clear space in the office, **28 mm of intake space**
remain — just under the ~30 mm a 120 mm fan likes, but usable. If it gets too loud, 15 mm slim fans are
the lever; change `luefterhoehe` in the spreadsheet and regenerate.

### Print orientation

`halter_A.stl` is printed **flat, without turning and without special flags** — the part ends at z=0
and every face is supported from below.

**Material: white PETG.** PETG rather than PLA because PLA softens at about 60 °C and the mount sits on a
radiator. White matches the colour of the radiators.

Slicer settings used: 0.2 mm layers, max. speed 60, PETG at 265 °C nozzle / 75 °C bed. 140 layers,
3 h 28 min, 65 g — mount and all six pegs together.

### Collar height and sight screen

`zarge_innen` = 26 mm measured **from the fan rest**, i.e. `z_hoehe` = 28 mm from the sheet. The top
edge of the fan is at 2 + 25 = 27 mm — the black fan disappears completely behind the collar, with 1 mm
to spare.

With `kanten_r` = 1.5 mm the following edges are broken: all vertical outer edges, the upper
circumferential edge of the collar and the **three free top edges of each baffle** (two long sides, one
end).

The fourth baffle edge — the transition to the collar — gets a **fillet** (`kehle_r` = 1.5 mm) instead.
That is an *inner edge*: the rounding runs the other way than on the outer edges and **adds material**
instead of removing it. It stiffens the 2 mm thin baffle exactly where it hangs on the 28 mm high collar
wall. The fillet has to be applied **after** the outer edges: otherwise the lengthwise roundings of the
baffle run through to the transition and eat it away.

The price is intake space. For a 120 mm fan ~30 mm would be ideal:

| | Clear height | above the collar |
|---|---|---|
| A — office | ~55 mm | 27 mm |
| B — living room | 100 mm | 72 mm |
| C — dining room | 50 mm | **22 mm** |

In the dining room it gets tight — the fan is louder there and delivers less. If that bothers,
`zarge_innen` is the adjusting screw.

### Screwing the fan

Four holes **⌀6 mm** in the rest corners, hole spacing **105 × 105 mm** — the standard dimension for 120 mm
fans (hole centre 7.5 mm from every fan edge).

The reference is the fan corner, not the rest: if `z_spiel` or the fan position change, the holes move
along correctly. For other fan sizes `schraub_lk` is the adjusting screw (92 mm for a 92 mm fan, 71.5 mm
for an 80 mm one).

**3.2 mm** remain between the hole edge and the edge of the rest. That is thin — fan screws are normally
M4, for which a 4.5 mm hole would do and leave a 4.0 mm web. At ⌀6 an M4 screw has play; with a washer or
a nut from below that is no problem, for a self-tapping screw directly into PLA 3.5 mm would be right.

### Baffle against short-circuit flow

On the left and right, **50 mm of floor area** each attach (`blende_b`). They cover the neighbouring slots
so the air does not short-circuit back up through them instead of going down through the convector
fins.

The baffle only extends over the sheet depth (y = 0…65), not over the full collar depth — otherwise 62 mm
would hang free in the air. Thickness as the rests, 2 mm.

That makes the part **226.6 mm wide** on a 230 mm usable bed: only 3.4 mm to spare. The cell `bett_rest`
in the spreadsheet accounts for this, and the check "fits the bed" fails before a part that is too wide
reaches the slicer. For radiators B and C, which have wider sheets, the baffle has to be printed in
segments and joined.

### Fixing — pegs (Zapfen; 6× in the complete STL: 2× each M2, M3, M4)

A **solid** block with rounded edges that engages a radiator slot with a **positive fit**. Outer size
7.4 × 39 mm — slot width minus 0.2 mm clearance times the full width of the perforated field. It can
neither turn nor wander.

| | mm |
|---|---|
| Outer | 7.4 × 39.0 |
| Height | 7.0 |
| Edge radius (4 vertical edges) | 2.0 |
| Core hole, self-tapping, through | ⌀1.6 (M2) / 2.5 (M3) / 3.3 (M4) |

**Two pegs per screw size** are printed, because it is only at assembly that it becomes clear which
screws are at hand. Two are installed, the rest is spare. Order on the bed from left to right: M2, M2,
M3, M3, M4, M4. The web next to the hole stays 2.05 mm thick even with M4.

The peg is pushed through the slot from below and screwed into its core hole with **one M3 through the
baffle**.

The two diameters belong together and must not be equal:

| | ⌀ | Function |
|---|---|---|
| Baffle (`blende_sd`) | 3.4 mm | clearance hole — the screw runs through freely |
| Peg (`zapfen_sd`) | 2.5 mm | core hole — the screw cuts its thread |

If the baffle hole were as tight, the screw would cut there too and would not pull the two parts
together.

The core hole goes **through the whole peg**: if the cut thread gives way on one side, the peg is turned
over and the other side is used.

The matching hole in each baffle is centred on the radiator depth (y = 32.5) and in the baffle — the two
line up.

**Assembly vs. printing:** the pegs are mounted under the baffles. For printing they lie loose in the fan
opening in `halter_A_komplett.stl`, where the mount is empty anyway — an STL may contain several separate
solids; the slicer treats them as objects of their own.

The original edge grip (jaws and noses below z=0) was removed: it made the part hard to print, and the
fixing is now done by these two parts.

**To check at the first fitting:** whether 7.4 mm really goes into the slot. Printed outer dimensions in
PLA tend to come out 0.1–0.2 mm too large; `zapfen_spiel` in the spreadsheet is the adjusting screw.

*(The numbers above are those of the first design. The current spreadsheets differ: peg width
`zapfen_b` = slot width − 0.2 mm = 7.4 / 7.5 / 7.8 mm for A / B / C, peg length = width of the perforated
field (39 / 75 / 38.5 mm), core hole `zapfen_sd` = 2.0 mm, baffle hole `blende_sd` = 3.0 mm, funnels of
⌀2.5 mm × 1.2 mm at both ends of the core hole. The principle — core hole smaller than the baffle hole —
is the same.)*

### Possible side effect

The fan touches the sheet through the corner rests and transmits vibration into a large thin sheet. If it
hums: increase `z_auflage` and put a strip of foam rubber underneath.

---

## Printability

Checked on the turned print orientation (`halter_A_gedreht.stl`, a file that is no longer in the
repository). What matters is not the **area** of an overhang but its **span** — and whether it starts free
in the air or bridges between two walls.

| Place | z | Span | Kind |
|---|---|---|---|
| Ribs (2×) | 10.0 mm | **12 mm** | bridge between the collar walls |
| Fan rests (4×) | 10.0 mm | **14 mm** | hang on the collar wall |
| Clamp noses (2×) | 13.4 mm | **2 mm** | bridge |

All below the 20 mm limit, all connected on both sides. **No support material needed**, no face starts
free in the air.

### Why one piece

A two-part variant (collar + slide-on clamps with a dovetail) was calculated and discarded again. The
reason is structural: the collar is 127 mm wide, the sheet only 65 mm. Every connection between the two
bridges 31 mm per side — the bridge does not disappear, it only moves. Separate parts brought **more**
overhang in total (4179 mm² against 2538 mm² for the one-piece part, at a larger span) and an additional
joint.

It stays one piece as long as the spans are below 20 mm. If the collar ever becomes much taller (a thicker
fan), the ribs are the place that becomes critical first.
