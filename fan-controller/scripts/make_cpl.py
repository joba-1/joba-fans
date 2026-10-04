#!/usr/bin/env python3
"""Generate the CPL (pick and place) file in JLCPCB format.

Usage: python3 make_cpl.py [board.kicad_pcb] [out.csv]

kicad-cli exports the columns Ref,Val,Package,PosX,PosY,Rot,Side.
JLCPCB wants Designator,Mid X,Mid Y,Layer,Rotation - different names,
a different order, and "Side" is called "Layer" there, with the values
Top/Bottom instead of top/bottom. If the KiCad file is uploaded unchanged,
JLCPCB rejects it.

The coordinates themselves are already right: the origin is the lower left
corner of the board (aux origin), unit mm.

--exclude-fp-th leaves out the through-hole parts: JLCPCB's catalogue does
not carry them, they are sourced separately and soldered by hand. See
fab/THT-ORDER-LIST.md.
"""
import csv
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "fan-controller.kicad_pcb")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "fab", "fan-controller-cpl.csv")

with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    raw = f.name
try:
    subprocess.run(
        ["kicad-cli", "pcb", "export", "pos", "--output", raw,
         "--format", "csv", "--units", "mm", "--side", "both",
         "--use-drill-file-origin", "--exclude-dnp",
         "--exclude-fp-th",        # THT is fitted by hand
         PCB],
        capture_output=True, check=True)
    rows = list(csv.DictReader(open(raw)))
finally:
    os.unlink(raw)

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for r in rows:
        # JLCPCB wants Top/Bottom capitalised, and dimensions with a unit.
        layer = "Top" if r["Side"].strip().lower() == "top" else "Bottom"
        w.writerow([r["Ref"],
                    f'{float(r["PosX"]):.4f}mm',
                    f'{float(r["PosY"]):.4f}mm',
                    layer,
                    f'{float(r["Rot"]):.2f}'])

print(f"{OUT}: {len(rows)} placements in JLCPCB format")
