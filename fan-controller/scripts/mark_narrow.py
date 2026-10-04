#!/usr/bin/env python3
"""Mark power/ground tracks that are below their target width.

Usage:
    python3 mark_narrow.py [board.kicad_pcb] [--skip-benign]

Markers go on User.Eco1: visible in the PCB editor, and kept out of fab
output as long as gerbers are exported with an explicit --layers list (a
bare `kicad-cli pcb export gerbers` writes every layer, Eco1 included).

Each marker is a circle at the segment midpoint plus a label reading
"net actual/target". Large circles are the 12V rail and ground return,
small ones the low-current 5V/3V3 rails.

Re-running clears the previous set first, so the markers always describe the
current board. Remove them with unmark.py.

--skip-benign omits segments where width is not the real limit: sub-0.5mm
joint fragments, and GND runs sitting directly over the B.Cu ground plane
(the plane carries that current in parallel).

Target widths from IPC-2152, 1oz external copper, 10C rise:
    1.0mm -> 2.39A    0.6mm -> 1.65A    0.2mm -> 0.74A
"""
import os
import sys

import pcbnew

args = [a for a in sys.argv[1:] if not a.startswith("--")]
PATH = args[0] if args else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "fan-controller.kicad_pcb")
SKIP_BENIGN = "--skip-benign" in sys.argv[1:]

LAYER = pcbnew.Eco1_User
TARGET = {"+12V_IN": 1.0, "+12V_FUSED": 1.0, "+12V_PROT": 1.0, "GND": 1.0,
          "+5V": 0.6, "+3V3": 0.6}
CRITICAL = {"+12V_IN", "+12V_FUSED", "+12V_PROT", "GND"}
STUB_LEN = 0.5

b = pcbnew.LoadBoard(PATH)
mm = pcbnew.ToMM
MM = pcbnew.FromMM

zones = [b.GetArea(i) for i in range(b.GetAreaCount())
         if not b.GetArea(i).GetIsRuleArea()]
gnd_poly = zones[0].GetFilledPolysList(pcbnew.B_Cu) if zones else None


def plane_backed(layer, a, c):
    """True if a ground plane runs alongside this segment for most of its length."""
    if gnd_poly is None or layer != pcbnew.B_Cu:
        return False
    hit = 0
    for i in range(11):
        x = a[0] + (c[0] - a[0]) * i / 10.0
        y = a[1] + (c[1] - a[1]) * i / 10.0
        if gnd_poly.Contains(pcbnew.VECTOR2I(MM(x), MM(y))):
            hit += 1
    return hit / 11.0 >= 0.7


# Collect geometry before mutating: removing drawings invalidates the board's
# iterators, so a later GetTracks() would raise.
tracks = []
for t in b.GetTracks():
    if t.GetClass() != "PCB_TRACK":
        continue
    s, e = t.GetStart(), t.GetEnd()
    tracks.append((t.GetNetname().lstrip('/'), round(mm(t.GetWidth()), 2),
                   (mm(s.x), mm(s.y)), (mm(e.x), mm(e.y)), t.GetLayer()))

old = 0
for d in list(b.GetDrawings()):
    if d.GetLayer() == LAYER:
        b.Remove(d)
        old += 1

marks, skipped = [], []
for net, w, a, c, layer in tracks:
    tgt = TARGET.get(net)
    if tgt is None or w >= tgt:
        continue
    length = ((c[0] - a[0]) ** 2 + (c[1] - a[1]) ** 2) ** 0.5
    mid = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
    if SKIP_BENIGN:
        if length < STUB_LEN:
            skipped.append((net, w, tgt, mid, f"stub, {length:.2f}mm"))
            continue
        if net == "GND" and plane_backed(layer, a, c):
            skipped.append((net, w, tgt, mid, "parallel to GND plane"))
            continue
    note = ""
    if length < STUB_LEN:
        note = "stub"
    elif net == "GND" and plane_backed(layer, a, c):
        note = "plane-backed"
    marks.append((net, w, tgt, mid, net in CRITICAL, length, note))

for net, w, tgt, (cx, cy), crit, length, note in marks:
    r = 1.2 if crit else 0.7
    shape = pcbnew.PCB_SHAPE(b)
    shape.SetShape(pcbnew.SHAPE_T_CIRCLE)
    shape.SetCenter(pcbnew.VECTOR2I(MM(cx), MM(cy)))
    shape.SetEnd(pcbnew.VECTOR2I(MM(cx + r), MM(cy)))
    shape.SetLayer(LAYER)
    shape.SetWidth(MM(0.15 if crit else 0.1))
    shape.SetFilled(False)
    b.Add(shape)

    txt = pcbnew.PCB_TEXT(b)
    txt.SetText(f"{net} {w}/{tgt}" + (f" ({note})" if note else ""))
    txt.SetPosition(pcbnew.VECTOR2I(MM(cx), MM(cy - r - 0.6)))
    txt.SetLayer(LAYER)
    txt.SetTextSize(pcbnew.VECTOR2I(MM(0.6), MM(0.6)))
    txt.SetTextThickness(MM(0.1))
    b.Add(txt)

b.Save(PATH)

print(f"cleared {old} old marker item(s)")
print(f"marked {len(marks)} segment(s) below target:")
for net, w, tgt, mid, crit, length, note in sorted(marks, key=lambda m: (not m[4], m[0])):
    tag = "!!" if crit else "  "
    extra = f"  [{note}]" if note else ""
    print(f"   {tag} {net:11} {w:.2f}/{tgt:.1f}mm  len {length:5.2f}mm  "
          f"at ({mid[0]:.2f},{mid[1]:.2f}){extra}")
if skipped:
    print(f"\nskipped {len(skipped)} (width not the limit):")
    for net, w, tgt, mid, why in skipped:
        print(f"      {net:11} {w:.2f}/{tgt:.1f}mm at ({mid[0]:.2f},{mid[1]:.2f})  {why}")
