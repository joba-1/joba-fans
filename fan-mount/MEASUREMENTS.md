# Radiator measurements

Fill this in per radiator. These feed the FreeCAD spreadsheet directly.
Photos of the top slot (looking down into it) and the bottom edge are worth
more than most of these numbers — add them to `doc/` if you take some.

## Radiator 1 — <room name>

| Key | Value | Notes |
|-----|-------|-------|
| `type` | | 11 / 21 / 22 / 33 |
| `manufacturer` | | e.g. Kermi, Buderus, Purmo |
| `length` | mm | overall, along the wall |
| `height` | mm | overall |
| `depth` | mm | front face to back face (not to the wall) |
| `slot_width` | mm | width of the opening in the top grille |
| `channel_gap` | mm | clear gap between the fin packs, measured *inside* the radiator |
| `top_lip` | mm | thickness/profile of the top edge the hanger hooks over |
| `grille_removable` | yes/no | |
| `side_covers_removable` | yes/no | |
| `headroom` | mm | radiator top → windowsill (or ∞ if no sill) |
| `floor_clearance` | mm | floor → bottom edge of radiator |
| `wall_standoff` | mm | wall → back face of radiator |
| `fan_count` | | ≈ length / 275, rounded |

## Radiator 2 — <room name>

(copy the table)

---

## How to measure `channel_gap`

This is the critical one for P1. Look down through the top slot: on a Type 22
you see two fin packs facing each other with a gap between them. That gap is
what the fan blows into, and it sets the maximum width of the mount's duct
section. Measure the *clear* distance between the fin tips, not the slot in the
sheet metal above it — they are usually different.

If the top grille lifts off, measure with it removed and note both values.
