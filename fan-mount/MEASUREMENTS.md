# Radiator measurements

One table per radiator. These feed the FreeCAD spreadsheet directly.

Values already known are filled in. The **Status** column says how much to trust
each one:

| Status | Meaning |
|--------|---------|
| `measured` | Measured at the wall. Usable as a design input. |
| `photo` | Scaled off the steel rule in a photo. Indicative only — re-measure before it drives geometry. |
| `open` | Not yet determined. |

Photo references are the `doc/` originals (`IMG_####.HEIC`, gitignored — see
`doc/primer.html` for the annotated version of what each one shows).

Seven radiators, three families. Only the four panel radiators can take P1 as
conceived; see §"Non-panel radiators" below for the other three.

---

## Radiator 1 — Dining room

Long, low unit under a large window with a stone sill. Plants and lamps stand on
the sill directly above it. Photos: `IMG_7172`–`IMG_7177`.

| Key | Value | Status | Notes |
|-----|-------|--------|-------|
| `type` | 22 or 33 | `photo` | Two fin banks visible (7174). 135 mm depth is deep for a 22 |
| `manufacturer` | | `open` | Look for a label on the end cap or behind the front panel |
| `length` | 1800–2200 mm | `photo` | Proportion against the window opening only (7172) |
| `height` | 220–230 mm | `photo` | Rule spans the full front face, both edges readable (7177) |
| `depth` | **135 mm** | `measured` | Confirms the photo estimate (7176) |
| `slot_width` | | `open` | |
| `channel_gap` | | `open` | Critical — see below |
| `top_lip` | | `open` | |
| `grille_removable` | | `open` | **Priority 1** — see checklist |
| `side_covers_removable` | | `open` | |
| `headroom` | **50 mm** | `measured` | To underside of the stone sill |
| `floor_clearance` | | `open` | Looks small in 7172; may rule out P3 |
| `wall_standoff` | | `open` | |
| `fan_count` | 7–8 | derived | At one per 275 mm, pending real length |

**Fan fit:** 120 mm fan sits fully on the top face — the only radiator in the
house where it does. But 50 mm headroom leaves only 10–15 mm of intake plenum,
so use 15 mm slim fans and drop the finger guard.

---

## Radiator 2 — Living room

Long, low unit under a window with a stone sill. A floor fan already parked
beside it. Photos: `IMG_7178`–`IMG_7181`.

| Key | Value | Status | Notes |
|-----|-------|--------|-------|
| `type` | 22 or 33 | `photo` | Two fin banks with a central gap (7181) |
| `manufacturer` | | `open` | |
| `length` | 2000–2400 mm | `photo` | Proportion against the window (7178) |
| `height` | 360–380 mm | `photo` | Rule shorter than the face, scaled by ratio (7179) |
| `depth` | **100 mm** | `measured` | |
| `slot_width` | | `open` | Grille bar pitch is 5–6 mm (`photo`, 7180) |
| `channel_gap` | 10–15 mm | `photo` | Rule crosses both fin banks, edges soft (7181) |
| `top_lip` | | `open` | |
| `grille_removable` | | `open` | **Priority 1** |
| `side_covers_removable` | | `open` | |
| `headroom` | **100 mm** | `measured` | To underside of the sill |
| `floor_clearance` | | `open` | Looks small in 7178/7179 |
| `wall_standoff` | | `open` | |
| `fan_count` | 7–9 | derived | Pending real length |

**Fan fit:** 120 mm fan overhangs ~10 mm each side. Let it overhang towards the
room, and add a short tapered plenum to gather the discharge onto the grille —
100 mm of headroom pays for that comfortably.

---

## Radiator 3 — Office

Panel radiator under a window with a stone sill. Boxes and a desk pushed against
it — access is poor. Photos: `IMG_7161`–`IMG_7164`.

| Key | Value | Status | Notes |
|-----|-------|--------|-------|
| `type` | | `open` | Fin pack visible down the slot in 7164 but not countable |
| `manufacturer` | | `open` | |
| `length` | ~2000 mm | `photo` | Very rough (7161) |
| `height` | | `open` | |
| `depth` | **60 mm** | `measured` | Shallowest of the four |
| `slot_width` | | `open` | |
| `channel_gap` | | `open` | May not have one — 60 mm is thin for a Type 22 |
| `top_lip` | | `open` | |
| `grille_removable` | | `open` | |
| `side_covers_removable` | | `open` | |
| `headroom` | 40–70 mm | `photo` | Rule was in a different plane — unreliable (7161) |
| `floor_clearance` | | `open` | |
| `wall_standoff` | | `open` | |
| `fan_count` | | `open` | |

**Fan fit — problem case.** A 120 mm fan is twice as wide as this radiator is
deep; roughly two thirds of its discharge would miss the grille. Either drop to
60 mm fans (noisy for the air they move) or use a tangential blower, whose
roller is naturally 60–80 mm across and the right shape for a long narrow slot.
Decide this before designing a P1 variant for this room.

---

## Radiator 4 — Guest WC

Small panel radiator on the tiled wall behind the toilet, valve bottom right.
No windowsill above it. Photos: `IMG_7165`–`IMG_7167`.

| Key | Value | Status | Notes |
|-----|-------|--------|-------|
| `type` | 11 or 21 | `photo` | Only one fin bank visible down the slot (7167) |
| `manufacturer` | | `open` | |
| `length` | ~600 mm | `photo` | Counted against wall tiles of assumed size (7165) |
| `height` | ~500 mm | `photo` | Same method — low confidence |
| `depth` | | `open` | **The one depth still completely unknown** |
| `slot_width` | | `open` | Grille slot pitch 11–12 mm (`photo`, 7166) |
| `channel_gap` | | `open` | If Type 11, there is no channel |
| `top_lip` | | `open` | |
| `grille_removable` | | `open` | |
| `side_covers_removable` | | `open` | |
| `headroom` | | `open` | Probably unlimited — no sill seen in 7165 |
| `floor_clearance` | n/a | — | Wall-hung, well above the floor |
| `wall_standoff` | | `open` | |
| `fan_count` | 2 | derived | At one per 275 mm, pending real length |

**Fan fit:** unknown until depth is measured. At ~600 mm long this is the
smallest job in the house and a good candidate for the first prototype — if the
depth allows a 120 mm fan.

---

## Non-panel radiators

These three have no top slot and no convector fins. P1 does not apply; they need
a different part family, and it is a live question whether they stay in scope at
all. Only fill these in if they do.

### Radiator 5 — Main bathroom, towel rail

Horizontal round tubes on two vertical side collectors. Usually covered in
towels, which will block most of any forced airflow. Photos: `IMG_7156`–`IMG_7160`.

| Key | Value | Status |
|-----|-------|--------|
| `tube_diameter` | | `open` |
| `tube_pitch` | | `open` (centre to centre) |
| `collector_spacing` | | `open` |
| `length` / `height` | | `open` |
| `wall_standoff` | | `open` |

**Concept:** fan turned on its side on a clip-on bracket gripping two tubes,
blowing horizontally through the gaps. See FIG 8 in `doc/primer.html`.

### Radiator 6 — Second bathroom, vertical tube radiator

Tall, narrow two-column radiator beside the mirror and sink.
Photos: `IMG_7168`–`IMG_7169`.

| Key | Value | Status |
|-----|-------|--------|
| `tube_diameter` | | `open` |
| `tube_pitch` | | `open` |
| `length` / `height` | | `open` |
| `wall_standoff` | | `open` |

### Radiator 7 — Old sectional radiator

Cast-style ribbed sections with corrosion at the section joints. Tight niche.
Photos: `IMG_7170`–`IMG_7171`.

| Key | Value | Status |
|-----|-------|--------|
| `section_pitch` | | `open` |
| `section_count` | | `open` |
| `top_profile_height` | | `open` (hump to valley) |
| `height` | | `open` |
| `wall_standoff` | | `open` |

**Concept:** a saddle bracket straddling the humped top, feet in the valleys,
blowing down the gaps between sections. Downdraft still works here — the top is
just not flat. Note the corrosion before investing effort in this one.

---

# Measurement checklist

In priority order. Items 1 and 2 can still change what the parts are, so do them
first.

- [ ] **1. Does the top grille or front cover lift off?**
      Dining room and living room. Try lifting the full-length grille, then
      pulling the front panel forward off its clips. If either comes away, fans
      can sit *inside* the casing blowing up through the grille — which removes
      the headroom and intake-plenum problems entirely and changes P1 from a
      collar into an internal cradle. Also settles whether these are panel
      radiators or convector casings.

- [ ] **2. `channel_gap`, all four panel radiators.**
      Caliper jaws down through the top slot until they touch the fin tips on
      both sides. *Not* the sheet-metal slot above it — they differ. In
      `IMG_7181` this is the dark band running between the two rows of wavy
      fins. Decides whether P1 ducts into the channel or seals flat on the
      grille face.

- [ ] **3. `depth` — guest WC.**
      Rule flat across the end cap, front face to back face. The shot in
      `IMG_7176` is the right technique. Depth decides fan diameter, so this is
      a real gap.

- [ ] **4. `headroom` — office and guest WC.**
      Rule standing on the radiator top, hard against the wall; read where the
      underside of the sill crosses it. Do it at one end and again in the
      middle — sills are rarely level. The guest WC may have no sill at all, in
      which case it is unlimited.

- [ ] **5. `slot_width`, all four.**
      Rule flat across the top, measuring the opening in the pressed steel —
      the feature seen edge-on in `IMG_7163` and `IMG_7166`. Sets the collar
      footprint if the seal-on-grille approach wins.

- [ ] **6. `length` and `height`, all four.**
      Tape along the wall, and floor to top edge. These drive fan count and the
      P2 tile lengths. Millimetre precision not needed.

- [ ] **7. `floor_clearance`, all four.**
      Floor to bottom edge. In `IMG_7178` and `IMG_7179` the units look like
      they nearly reach the skirting, which would rule out a bottom-mounted
      deflector (P3) as well as any fallback to upward flow.

- [ ] **8. `wall_standoff`, all four.**
      Back face to wall. Sets how far the magnet skirt can reach round.

- [ ] **9. `top_lip`, all four.**
      Thickness and profile of the top edge the hanger hooks over.

- [ ] **10. Tube diameter and pitch — the two bathrooms.**
      Only if the tube radiators stay in scope. Caliper across one tube, then
      centre to centre between two adjacent ones.

---

# How to measure the awkward ones

## `channel_gap`

The critical one for P1. Look down through the top slot: on a Type 22 you see
two fin packs facing each other with a gap between them. That gap is what the
fan blows into, and it sets the maximum width of the mount's duct section.
Measure the *clear* distance between the fin tips, not the slot in the sheet
metal above it — they are usually different.

If the top grille lifts off, measure with it removed and note both values.

Current best estimate is 10–15 mm (living room, `IMG_7181`). If that holds, a
duct collar reaching down into the channel is not buildable and P1 seals flat on
the grille face instead.

## `headroom`

Stand the rule on the radiator's top surface, hard against the wall, and read
where the underside of the sill crosses it. Not the sill's front edge — the
overhang is not what limits the fan.

What actually matters is not the total gap but what is left above the fan once
the stack is in: fan body + collar + compressed seal. An axial fan wants roughly
a quarter of its diameter of free space on the suction side to draw evenly —
about 30 mm for a 120 mm fan. Below that it loses flow and starts to whistle.

## `depth` and fan diameter

Depth sets the width of the top face, which is all the area available to accept
the fan's discharge. If the fan is wider than the radiator is deep, the surplus
blows at the sill and the wall and does no work.

Rough rule: fan diameter ≤ depth for a direct fit; up to about 1.2 × depth if
there is headroom for a tapered plenum; beyond that, change fan size or switch
to a tangential blower.

## Photographing instead of measuring

Only worth it if the rule lies flat against the feature with its zero mark and
the far edge both in frame and in focus. Most of the `doc/` photos fail that
test, which is why so much here is still `open`. Shoot straight on, not at an
angle. For a fine scale, crop tight to the feature *before* resizing — cropping
preserves detail that downscaling destroys.
