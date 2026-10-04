# fan-mount — 3D printed fan mounts for radiator cooling assist: requirements

This is the original requirements and concept document (started 2026-08-15). It is kept
as written; what has actually been built since is summarised in the status table in the
[component README](../README.md#status), and the design details are in
[design-notes.md](design-notes.md). Where this document says "magnets", the built parts
use printed pegs in the radiator slots and screws instead (see design-notes.md).

## 1. Problem

Heat pump runs in cooling mode over the existing wet radiator circuit (panel
radiators). The heat pump's **minimum cooling capacity is larger than what the
radiators can dissipate into the rooms**, so the return water never warms up
enough. Result: the heat pump satisfies its target quickly, shuts off, and
short-cycles.

Root cause on the room side: panel radiators are mounted **low on the wall**.
That placement is optimal for *heating* — the radiator warms air, the warm air
rises, and the resulting chimney draft through the convector fins is
self-sustaining and drives room-scale mixing.

In *cooling* the same geometry works against us:

- Cooled air is **denser** and sinks. The radiator is already at the floor, so
  the buoyancy column is ~0 cm tall. There is essentially no driving head.
- Air-side heat transfer collapses to near-still-air free convection. The
  air side is by far the dominant thermal resistance, so the whole radiator
  capacity collapses with it.
- The cold air **puddles on the floor** around the radiator. The radiator then
  re-inhales its own cold exhaust (short-circuit), which kills the air-to-water
  temperature difference and therefore the capacity a second time.
- The room stratifies: cold at the floor, warm at the ceiling. Comfort is bad
  *and* the warm air that we actually want to cool never reaches the radiator.

Rule of thumb: a panel radiator in cooling delivers roughly **10–15 % of its
nominal heating output**. Forced air over the fins typically recovers a factor
of **3–4×** of that, because it attacks the dominant resistance directly.

## 2. Goals

G1. **Raise cooling capacity per radiator** enough that the heat pump can run
    continuously at its minimum modulation instead of short-cycling.
    Mechanism: forced convection over the convector fins (air-side `h` up).

G2. **Feed the radiator the warmest air available in the room** — maximise the
    air-to-water temperature difference, and avoid re-inhaling the cold puddle.

G3. **Destratify the room**: drive a room-scale circulation loop so the warm
    ceiling air is continuously brought back down to the radiator. This serves
    G1 and G2 (warmer intake air) *and* comfort (uniform room temperature) at
    the same time — they are the same objective seen from two ends.

G4. **Quiet.** These run continuously in living rooms. Target: inaudible at
    2 m, i.e. fans undervolted / PWM-limited, no resonance transmitted into the
    radiator sheet metal.

G5. **Non-destructive, reversible mounting.** No drilling, no adhesive, no
    modification of the radiator. The parts stay on year-round (C4), but must
    still come off by hand for cleaning inside the radiator, and must leave the
    radiator's heating performance intact in winter (C5).

## 3. Airflow decision — where does the fan go, and which way?

**Decision: fans sit on TOP of the radiator and blow DOWNWARD through the
convector channel. Discharge at the bottom is turned horizontally into the room
by a deflector.**

### Rationale

Buoyancy inside the radiator channel is irrelevant once a fan is involved.
Over a 0.6 m panel at ΔT = 5 K the buoyant head is
`Δp = ρ·g·h·ΔT/T ≈ 1.2 · 9.81 · 0.6 · 5/295 ≈ 0.12 Pa`,
against 20–50 Pa of fan static pressure. So "fighting gravity" is a non-issue
in either direction, and the decision is made purely on **intake air
temperature** and **room air pattern**.

| | Top intake, blow down (chosen) | Bottom intake, blow up |
|---|---|---|
| Intake air | Warmest air in the room reaches the radiator top | Coldest air — the floor puddle |
| Short-circuit risk | Low: intake and exhaust are maximally separated along the stratification axis | High: exhaust cools, sinks, is re-inhaled |
| Window interaction | Intercepts the warm downdraught/updraught at the glass — cools the heat gain at its source | Ignores it |
| Room loop | Floor jet → across room → up at far wall → back along ceiling → into the top intake. Closed, self-reinforcing loop. | Cold plume thrown up, mixes at ceiling, then falls back to intake — also mixes, but starves its own intake |
| Comfort risk | Cold draught at ankle level | Cold air thrown at seated head height |

The chosen direction wins on G2 decisively, and its room loop (G3) has the
useful property that the **return leg of the loop terminates at the fan
intake** — the warm ceiling air is actively pulled down and consumed, rather
than left to find its own way.

The ankle-draught risk is the one real drawback and is handled by the discharge
deflector: aim the jet horizontally out into the room rather than straight down
at the floor, and keep the discharge velocity moderate. Note also that the water
in this system is deliberately *not* very cold (see C1), so the jet is cool, not
icy.

### Consequences for the parts

- The top opening of the radiator must be **sealed except at the fans**,
  otherwise most of the air spills back out of the top slot instead of going
  down the channel. Blanking plates are as important as the fan mounts.
- Fan spacing must give reasonably even coverage over the radiator length —
  target roughly **one 120 mm fan per 250–300 mm of radiator length**.

## 4. Sizing estimate (to be checked against the real radiator)

For a target of ~700 W per radiator:

```
V̇ = Q / (ρ · cp · ΔT_air)
   = 700 W / (1.2 kg/m³ · 1005 J/kgK · 8 K) · 3600
   ≈ 260 m³/h
```

At an *installed* (not free-air) delivery of ~50–60 m³/h per 120 mm fan through
the fin pack, that is **4–5 fans** per radiator. Numbers are estimates and need
to be validated by measurement (see §8).

Implication for fan selection: the fins are a real pressure drop, so pick
**static-pressure** fans (e.g. Arctic P12, Noctua NF-F12 class), not
high-airflow/low-pressure case fans. Power is negligible: ~1.5 W per fan
undervolted, ~6–8 W per radiator, versus several hundred W of recovered
capacity.

## 5. Constraints

C1. **Condensation — already handled by the heat pump control.** The heat pump
    reads room temperature and humidity and raises the coolant temperature to
    keep the surfaces above dew point, so dripping is designed out at system
    level. Nothing in this project may defeat that.
    Two residual notes, not open risks:
    - Forcing air over the fins does not meaningfully lower the fin surface
      temperature (the water-side resistance is small either way, so the metal
      sits near water temperature regardless). The existing control input is
      therefore still the right one after fans are added.
    - What fans *do* change is the deposition rate if the margin is ever thin,
      and the coldest spot is the flow-inlet end of the radiator. Worth one
      look at the actual dew point margin under fan operation (§8) — if the
      control already holds a couple of K, there is nothing to do.

C2. No modification of the radiator (G5). Mounting is by magnets onto the steel
    panels (§6), backed up by hooking over the existing top slot and bottom
    edge where a magnet alone cannot locate the part precisely enough.

C3. Radiators sit under windows in most rooms — a windowsill limits the
    vertical space available above the radiator. The top mount must stay low
    profile. Available headroom is a key dimension (see §8).

C4. **Parts stay mounted year-round** (decided). They therefore see radiator
    surface temperatures in the heating season, where PLA creeps and softens
    (~55–60 °C). → Print in **PETG or ASA**. The hook and clamp geometry needs
    extra clearance for thermal expansion, and must not rely on a press-fit
    that would relax when warm.

C5. **Heating-season bypass.** Because the parts stay on year-round (C4), the
    blanking tiles (P2) that seal the top slot against fan bypass would also
    block the natural convection chimney in winter, when it is exactly what
    makes the radiator work. Must be resolved by one of:
    1. tiles separately removable from the fan mounts (seasonal chore);
    2. tiles as gravity/pressure flaps — pressed shut by downward fan flow,
       falling open when the fans stop (self-managing, more parts);
    3. **turn the fans over in winter** so they blow *upward*, assisting the
       chimney instead of blocking it. Raises heating output, which permits a
       lower flow temperature and a better COP — turns the project into a
       year-round gain.
    → Preferred: 3, with 1 as fallback. Consequence for the design: the duct
    geometry must not be so optimised for downflow that it chokes upflow.

    **Not by reversing polarity.** PC fans are brushless DC motors: the driver
    IC and Hall sensor sit inside the hub, and the direction of rotation comes
    from the order in which that IC energises the coils — not from the supply
    polarity. Swapping +12 V and GND does not reverse the fan, it reverse-feeds
    a driver IC that usually has no protection. The blades are aerofoils with a
    defined leading edge and the frame has an inlet radius on one side and the
    struts on the other, so even a genuinely reversed impeller would move far
    less air.

    **Physically turning the fan over is what works**, and the existing mount
    already allows it: the surround is a 120.6 mm square open at the top, and
    the M4 hole pattern sits at `(120 − 105) / 2 = 7.5 mm` from every edge —
    point-symmetric, so the fan drops onto the same pegs either way up. The
    seasonal chore is lifting it out, flipping it, putting it back.

C6. Fans are standard 120 × 120 × 25 mm with the standard 105 mm mounting hole
    pattern, M4/self-tapping screws or press-fit pins.

C7. Cabling: fans daisy-chained per radiator to a single 12 V supply.
    Ideally switched from the heat pump's cooling signal so they only run when
    cooling is active.

## 6. Material strategy — print only what must be printed

Printing is the right tool for **interfaces**: things that must match the
radiator's exact profile, hold a fan at an exact position, or clip onto an
edge. It is the wrong tool for **large flat areas and long shallow curves** —
those print slowly, warp in PETG, eat filament, and a sheet of stock material
does the job better and cheaper.

So the rule for this project: *printed clips and brackets carrying cut sheet
stock.* Standard materials to use:

| Material | Where | Why |
|---|---|---|
| **Neodymium magnets** (10×3 mm discs, in printed pockets) | mounting P1/P2/P3 to the radiator | The radiator is painted steel. Magnets give a strong, zero-force, non-destructive, instantly removable mount — this satisfies G5 and C2 almost for free, and removes most of the clamping geometry from the design. Face them with felt or foam tape so they cannot scratch the paint, and keep them off the hottest zones (N-grade magnets lose strength above ~80 °C; radiator surface stays well below that, but use N42SH or similar if in doubt). |
| **PVC foam board** (Forex/Kapa, 3–5 mm) or thin aluminium sheet | blanking tiles P2, deflector P3 body | Cuts with a knife, stiff, flat, cheap, bends to a curve (aluminium) or scores and snaps (PVC). Replaces the largest printed areas entirely. |
| **Self-adhesive foam weatherstrip** (EPDM, D- or P-profile) | every printed-part-to-metal contact | Does three jobs at once: seals the shroud so air cannot bypass, takes up manufacturing tolerance between the print and the real radiator, and decouples fan vibration from the radiator sheet metal — which is the main noise path (G4). Cheap and it makes the printed parts far less dimension-critical. |
| **Silicone fan mounting pins** (standard PC part) | fan → bracket | Vibration isolation at the source, and no screws. Directly serves G4. |
| **Aluminium tape** | sealing seams between tiles | Faster than designing overlapping joints. |
| **Fan grills / finger guards** (standard 120 mm wire guards) | intake side | Safety, off the shelf, no reason to print one. |
| **12 V PSU, PWM controller, fan splitters/hub** | electrics | All standard PC parts. |

Consequence: the printed parts get *smaller and more numerous* — end caps,
edge clips, magnet carriers, fan shrouds — rather than a few big shells. That
is also what prints reliably in PETG.

## 7. Parts to design (draft list)

| # | Part | Printed portion | Stock portion |
|---|------|-----------------|---------------|
| P1 | **Fan hanger / top mount** — holds one 120 mm fan over the convector channel, sealed to the top slot | bracket, fan seat with silicone-pin holes, magnet pockets, duct collar down into the slot | foam weatherstrip seal, silicone pins, wire guard |
| P2 | **Blanking tile** — closes the top slot between the fans so air cannot bypass (§3), must not defeat winter chimney (C5) | end clips / magnet carriers only | PVC foam or aluminium sheet cut to length |
| P3 | **Discharge deflector** — turns the downward flow into a horizontal jet into the room; sets the room loop (G3), defuses the ankle draught | end caps and intermediate edge clips that hold the sheet at the right angle | bent aluminium or PVC foam sheet |
| P4 | **Cable clip / daisy-chain holder** | all of it, trivial | — |

Design order: P1 first (it fixes all interface dimensions), then P2 (shares
the magnet/clip geometry with P1), then P3, then P4.

All dimensions driven from a **FreeCAD spreadsheet** so the same model
re-generates for the different radiator types in the house (several types
confirmed — see measurements.md).

## 8. Open questions / to measure

Needed before P1 can be modelled — see measurements.md:

- Radiator type (11 / 21 / 22 / 33) and manufacturer
- Height, length, depth (front face to wall face)
- Width of the **top slot** and its internal clear gap between the fin packs
- Is the top grille removable? Are the side covers removable?
- Clear headroom above the radiator to the windowsill
- Floor clearance under the radiator, and wall standoff
- Number of radiators to equip, and their sizes

To validate afterwards:

- Return water temperature rise, before vs. after (the actual success metric —
  it is what stops the short-cycling)
- Heat pump runtime / cycles per hour, before vs. after
- Room temperature at floor vs. ceiling, before vs. after (destratification, G3)
- Room humidity and dew point margin (C1)

## 9. Note on scope

Fans on the radiators raise the emitter capacity, which is the correct lever for
"minimum cooling output exceeds the emitter capacity". The alternative levers —
a buffer volume to absorb the excess, or raising the flow temperature — are
system-side and out of scope here, but worth keeping in mind if the fans alone
do not close the gap.
