#!/usr/bin/env python3
"""Generate the BOM and CPL in PCBWay format.

Usage: python3 make_pcbway.py

PCBWay is much more tolerant about the format than JLCPCB: .xls/.xlsx/.csv,
no fixed column names. It asks for designator, quantity, package and part
number; for resistors and capacitors, value and package are enough. PCBWay
also recommends marking PTH and SMD - the Type column is for that.

PCBWay assembles through-hole parts as a regular service (through-hole
assembly). Unlike with JLCPCB, ALL parts are therefore assembled here, and
BOM and CPL include the THT positions too - without a CPL entry the
assembly would not know where they belong.

The Type column distinguishes PTH and SMD, as PCBWay recommends: THT is
placed by hand or in a wave-solder bath and priced separately.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = os.path.join(HERE, "..", "fan-controller.kicad_sch")
PCB = os.path.join(HERE, "..", "fan-controller.kicad_pcb")
OUT = os.path.join(HERE, "..", "fab", "pcbway")

sys.path.insert(0, HERE)
from make_bom import LCSC, ROLE_VALUES, THT_REFS, collapse, refkey  # noqa: E402

# Sourcing notes for the through-hole parts. PCBWay assembles them but has
# to buy them first, and the KiCad footprint names are not enough for that.
# Dimensions taken from the board's own footprints. English throughout -
# these lines are read by PCBWay staff.
# Positions where one footprint takes several physical parts.
#
# The Qty column means the number of pieces PER BOARD, not the number of
# designators. PCBWay corrected this on 2026-09-02: U1 had been submitted
# with Qty 1 and was priced as one female header per board, although two are
# needed. A hint in the Value field or in the note is not enough - the
# calculation follows the column.
QTY_PER_FOOTPRINT = {
    "U1": 2,        # two 1x7 female headers on the XIAO footprint
}

THT_SPEC = {
    "C1": ("electrolytic cap 220uF 25V radial, 3.5mm pitch, "
           "max 8mm diameter, THROUGH-HOLE (not SMD)"),
    "J1": ("DC barrel jack 5.5x2.1mm, horizontal/right-angle, 3 pins, "
           "CUI PJ-102AH or DC-005 compatible"),
    "J2": "pin header 1x4 straight, 2.54mm pitch",
    # U1 is the socket position: the footprint is the XIAO module, but what
    # goes there is TWO 1x7 female headers. The module itself is not
    # assembled - the customer plugs it in later.
    # The count lives in the Qty column and ONLY there - adding "2x" here
    # reads as four.
    "U1": ("female header 1x7 straight, 2.54mm pitch, row spacing "
           "15.24mm - do NOT fit the module itself"),
}

os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- BOM
with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    raw = f.name
try:
    subprocess.run(
        ["kicad-cli", "sch", "export", "bom", "--output", raw,
         "--fields", "Reference,Value,Footprint",
         "--labels", "Designator,Value,Footprint",
         "--group-by", "", SCH],
        capture_output=True, check=True)
    rows = list(csv.DictReader(open(raw)))
finally:
    os.unlink(raw)

groups = {}
for r in rows:
    ref = r["Designator"].strip('"')
    val = r["Value"].strip('"')
    fp = r["Footprint"].strip('"')
    part = ROLE_VALUES.get(val, val)
    note = val if val in ROLE_VALUES else ""
    key = (fp, part)
    g = groups.setdefault(key, {"refs": [], "notes": []})
    g["refs"].append(ref)
    if note:
        g["notes"].append(note)

bom_path = os.path.join(OUT, "fan-controller-bom-pcbway.csv")
with open(bom_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Item", "Designator", "Qty", "Value", "Package",
                "Type", "LCSC Part #", "Note"])
    for i, ((fp, part), g) in enumerate(
            sorted(groups.items(), key=lambda kv: refkey(sorted(kv[1]["refs"], key=refkey)[0])), 1):
        refs = sorted(g["refs"], key=refkey)
        is_tht = refs[0] in THT_REFS
        pkg = fp.split(":")[-1]
        # For positions with a detailed sourcing note, the Value field only
        # needs the plain part name - otherwise everything is stated twice.
        if refs[0] in THT_SPEC and " - " in part:
            part = part.split(" - ")[0]
        # No "2x" in the Value field: the count is in the Qty column,
        # otherwise Qty 2 with "2x ..." reads as four pieces.
        qty = len(refs) * QTY_PER_FOOTPRINT.get(refs[0], 1)
        notes = [n for n in g["notes"] if n not in ROLE_VALUES]
        note = " ".join(notes)
        if is_tht:
            spec = THT_SPEC.get(refs[0], "")
            note = "; ".join(x for x in ("PTH - hand/wave solder",
                                         spec, note) if x)
        w.writerow([i, collapse(refs), qty, part, pkg,
                    "PTH" if is_tht else "SMD",
                    LCSC.get(refs[0], ""), note])

# ---------------------------------------------------------------- CPL
with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    raw = f.name
try:
    subprocess.run(
        ["kicad-cli", "pcb", "export", "pos", "--output", raw,
         "--format", "csv", "--units", "mm", "--side", "both",
         "--use-drill-file-origin", "--exclude-dnp", PCB],
        capture_output=True, check=True)
    pos = list(csv.DictReader(open(raw)))
finally:
    os.unlink(raw)

cpl_path = os.path.join(OUT, "fan-controller-cpl-pcbway.csv")
with open(cpl_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Mid X (mm)", "Mid Y (mm)",
                "Layer", "Rotation", "Type"])
    for r in pos:
        w.writerow([r["Ref"],
                    f'{float(r["PosX"]):.4f}',
                    f'{float(r["PosY"]):.4f}',
                    "Top" if r["Side"].strip().lower() == "top" else "Bottom",
                    f'{float(r["Rot"]):.2f}',
                    "PTH" if r["Ref"] in THT_REFS else "SMD"])

print(f"{bom_path}: {len(groups)} lines (including PTH for information)")
n_tht = sum(1 for r in pos if r["Ref"] in THT_REFS)
print(f"{cpl_path}: {len(pos)} placements "
      f"({len(pos)-n_tht} SMD, {n_tht} PTH)")
