# fan-mount — radiator fan mounts

3D-printed mounts that hold 120 mm PC fans on top of a panel radiator and blow down through its
convector channel. They are the "load" of the [`fan-controller`](../fan-controller/) board: the
fans sitting in these mounts are what the board drives.

**Why:** a heat pump that cools through wall-hung panel radiators short-cycles, because a radiator
mounted low on the wall hardly emits any cooling power by free convection (cold air sinks and
puddles around it). Forced air over the fins recovers a factor of roughly 3–4. The full reasoning,
the airflow decision and the sizing are in [docs/requirements.md](docs/requirements.md).

## Status

| Part | State |
|---|---|
| P1 fan mount (collar, ribs, baffles, pegs), variants **Small / Medium / Large** for three radiator types | modelled, trial prints made; STLs in `cad/` |
| Finger-guard hood, one variant for all mounts | modelled; STL in `cad/` |
| P2 blanking tiles, P3 discharge deflector, P4 cable clip | **not built** (concept only, see requirements) |
| Fixing | printed **pegs in the radiator slots**, screwed to the baffles — not the magnets of the original concept |
| 4th radiator (guest WC), tube and sectional radiators | not measured / out of scope for now |

The radiator measurements are partly still `open`; see [docs/measurements.md](docs/measurements.md).

## The three variants

Each fits one measured radiator sheet. The mount is a square collar for a 120 × 25 mm fan with four
corner rests, ribs on the unperforated edge strips, 50 mm baffles left and right, and pegs that
engage the radiator's top slots.

| STL | Radiator | Sheet depth | Fan seat |
|---|---|---|---|
| `cad/RadiatorFanSmall.stl` | A — office | 65 mm | asymmetric: the fan overhangs 41 mm to the front |
| `cad/RadiatorFanMedium.stl` | B — living room | 101 mm | centred |
| `cad/RadiatorFanLarge.stl` | C — dining room | 136 mm | centred, rib on the centre web, two perforated fields |
| `cad/RadiatorFanGuard.stl` | all | — | finger guard, slips over the collar |

The mounts are 226.6 mm wide (230 mm bed) and 28 mm tall; print flat, no support.
**Material: PETG** (or ASA) — PLA softens at around 60 °C, and the mounts sit on a heating radiator.
`cad/ZapfenLarge.stl` is a set of four spare pegs for radiator C.

## How it fits the rest of the system

* **Fans:** standard 120 × 120 × 25 mm, 105 mm screw pattern, 4-pin PWM. The collar is 120.6 mm
  inside, the fan sits 1 mm below its rim; the four ⌀6 mm holes take M4 screws with a washer.
  15 mm slim fans also fit and leave more intake space where the sill is low.
* **Controller:** each fan plugs into one of the four 4-pin headers of
  [`fan-controller`](../fan-controller/) (pin order GND, +12 V, tach, PWM). A radiator needs several
  fans (one per 250–300 mm of length), more than a board has channels, so the rule is **at most 2 fans per channel**, joined with a PWM
  splitter cable: the pair runs at the same speed and only one fan's tach is read back (not yet tried
  on the real board). That makes **8 fans per board at most**; a radiator that needs more (the living
  room, 7–9) gets a second board. Keep the *total* current of all fans on a board below the 1.5 A
  polyfuse — about 0.18 A per fan with 8 fans.
* **Control:** [`fan-remote`](../fan-remote/) sets the speeds (web page, MQTT, Home Assistant). The
  mounts do not depend on it.

## Files

| Path | Content |
|---|---|
| `cad/` | FreeCAD documents (`.FCStd`, dimensions in the `Masse` spreadsheet), the print-ready STLs, `radiator_sheets.csv` |
| `scripts/` | FreeCAD scripts that build the parts from the spreadsheet |
| `docs/design-notes.md` | how the mounts were derived, print notes, glossary of the German parameter names, how to regenerate |
| `docs/requirements.md` | the original requirements and concept |
| `docs/measurements.md` | radiator measurements and the measurement checklist |
| `docs/primer.html` | illustrated primer for the concept (open in a browser) |

Not in the repository: the original photos (40 MB of phone HEIC) and G-code (regenerable from the
STLs).

## Regenerating a part

Open the `.FCStd` in FreeCAD, then in the Python console:

```python
ZIEL = "RadiatorFanLarge"
exec(open("<repo>/fan-mount/scripts/build_variante.py").read())
```

Details in [docs/design-notes.md](docs/design-notes.md). Parameter names inside the files are
German (`zarge`, `blende`, `zapfen` …); the glossary is there too.

## Known gaps

* Printed fit is only partly confirmed — the peg-in-slot fit (7.4–7.8 mm) is the first thing to check
  on the radiator; `zapfen_spiel` is the adjusting screw.
* The STLs are checked against the spreadsheet dimensions (sizes above), but were not regenerated
  from the scripts when the repository was assembled.
* Without a P2 blanking tile the top slot between fans is open, so part of the air spills back out;
  and in the heating season the fans should be turned over (see requirements C5).
