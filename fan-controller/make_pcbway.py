#!/usr/bin/env python3
"""BOM und CPL im PCBWay-Format erzeugen.

Aufruf: python3 fan-controller/make_pcbway.py

PCBWay ist beim Format deutlich toleranter als JLCPCB: .xls/.xlsx/.csv,
keine festen Spaltennamen. Verlangt werden Designator, Menge, Gehaeuse und
Teilenummer; bei Widerstaenden und Kondensatoren genuegen Wert und Gehaeuse.
PCBWay empfiehlt ausserdem, PTH und SMD zu kennzeichnen - dafuer gibt es
hier die Spalte Type.

Die BOM listet anders als bei JLCPCB *alle* Teile, auch die
Durchsteckteile, damit die Stueckliste vollstaendig ist. Sie sind als PTH
markiert und mit dem Hinweis versehen, dass sie selbst beschafft werden.
Die CPL enthaelt dagegen nur SMD - PCBWay erlaubt ausdruecklich, THT dort
wegzulassen.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

SCH = "fan-controller/fan-controller.kicad_sch"
PCB = "fan-controller/fan-controller.kicad_pcb"
OUT = "fab/pcbway"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_bom import LCSC, ROLE_VALUES, THT_REFS, collapse, refkey  # noqa: E402

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
        notes = [n for n in g["notes"] if n not in ROLE_VALUES]
        note = " ".join(notes)
        if is_tht:
            note = ("vom Kunden beigestellt - nicht bestuecken; "
                    + note).strip("; ")
        # Bei beigestellten Teilen keine Teilenummer: sie werden nicht
        # beschafft, eine Nummer waere hier irrefuehrend.
        w.writerow([i, collapse(refs), len(refs), part, pkg,
                    "PTH" if is_tht else "SMD",
                    "" if is_tht else LCSC.get(refs[0], ""), note])

# ---------------------------------------------------------------- CPL
with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    raw = f.name
try:
    subprocess.run(
        ["kicad-cli", "pcb", "export", "pos", "--output", raw,
         "--format", "csv", "--units", "mm", "--side", "both",
         "--use-drill-file-origin", "--exclude-dnp", "--exclude-fp-th", PCB],
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
                    "SMD"])

print(f"{bom_path}: {len(groups)} Positionen (inkl. PTH als Information)")
print(f"{cpl_path}: {len(pos)} SMD-Bestueckpositionen")
