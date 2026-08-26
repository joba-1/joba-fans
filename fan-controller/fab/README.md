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
fan-controller-bom.csv   bill of materials
fan-controller-cpl.csv   pick-and-place (top side only, DNP excluded)
```

Origin for both drill and placement files is the board's **bottom-left
corner**.

## Assembly notes

**U1 (XIAO ESP32-C3) is DNP — do not fit.** The module is socketed and
supplied by the customer. What *does* need fitting is the pair of **1×7
female headers** it plugs into; these are the last line of the BOM. They
have no schematic symbol, since the module's own footprint provides their
pads, so they are easy to miss.

All parts are on the top side. J1 (barrel jack) overhangs the right board
edge by 3.5 mm by design — its flange seats on the edge so the socket is
reachable from outside an enclosure.

The BOM has empty **MPN** and **Supplier** columns. Fill these in, or ask
the assembler to substitute from their own stock — every part is a generic
jellybean except the barrel jack and the AMS1117.

## Reproducing

```sh
fan-controller/make_fab.sh
```

Gerbers must be exported with an explicit `--layers` list. A bare
`kicad-cli pcb export gerbers` writes *every* layer, including the
`User.Eco1` scratch layer used during layout for review markers.
