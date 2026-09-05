#!/usr/bin/env python3
"""BOM und CPL im PCBWay-Format erzeugen.

Aufruf: python3 fan-controller/make_pcbway.py

PCBWay ist beim Format deutlich toleranter als JLCPCB: .xls/.xlsx/.csv,
keine festen Spaltennamen. Verlangt werden Designator, Menge, Gehaeuse und
Teilenummer; bei Widerstaenden und Kondensatoren genuegen Wert und Gehaeuse.
PCBWay empfiehlt ausserdem, PTH und SMD zu kennzeichnen - dafuer gibt es
hier die Spalte Type.

PCBWay bestueckt Durchsteckteile als regulaere Dienstleistung (Through-Hole
Assembly). Anders als bei JLCPCB werden hier deshalb ALLE Teile bestueckt,
und BOM wie CPL enthalten auch die THT-Positionen - ohne CPL-Eintrag wuesste
die Bestueckung nicht, wo sie hingehoeren.

Die Spalte Type unterscheidet PTH und SMD, wie von PCBWay empfohlen: THT
wird von Hand oder im Wellenloetbad gesetzt und getrennt kalkuliert.
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

# Sourcing notes for the through-hole parts. PCBWay assembles them but has
# to buy them first, and the KiCad footprint names are not enough for that.
# Dimensions taken from the board's own footprints. English throughout -
# these lines are read by PCBWay staff.
# Positionen, bei denen ein Footprint mehrere physische Bauteile aufnimmt.
#
# Die Qty-Spalte meint die Stueckzahl PRO PLATINE, nicht die Anzahl der
# Designatoren. Von PCBWay am 2026-09-02 so korrigiert: U1 war mit Qty 1
# eingereicht und wurde als eine Buchsenleiste pro Platine kalkuliert,
# obwohl zwei gebraucht werden. Ein Hinweis im Value-Feld oder in der Note
# reicht nicht - die Kalkulation folgt der Spalte.
QTY_PER_FOOTPRINT = {
    "U1": 2,        # zwei 1x7-Buchsenleisten auf dem XIAO-Footprint
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
    # Stueckzahl steht in der Qty-Spalte und NUR dort - "2x" hier dazu
    # liest sich als vier.
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
        # Bei Positionen mit ausfuehrlicher Sourcing-Note reicht im
        # Value-Feld der reine Teilename - sonst steht alles doppelt.
        if refs[0] in THT_SPEC and " - " in part:
            part = part.split(" - ")[0]
        # Kein "2x" im Value-Feld: die Stueckzahl steht in der Qty-Spalte,
        # sonst liest sich Qty 2 mal "2x ..." als vier Stueck.
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

print(f"{bom_path}: {len(groups)} Positionen (inkl. PTH als Information)")
n_tht = sum(1 for r in pos if r["Ref"] in THT_REFS)
print(f"{cpl_path}: {len(pos)} Bestueckpositionen "
      f"({len(pos)-n_tht} SMD, {n_tht} PTH)")
