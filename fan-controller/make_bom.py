#!/usr/bin/env python3
"""Build an assembly-ready BOM from the schematic.

Usage: python3 fan-controller/make_bom.py [schematic.kicad_sch] [out.csv]

kicad-cli's own grouping compares every listed field, so the four fan headers
never merge: their Values are FAN1..FAN4 (which channel each drives) even
though they are one identical part. That reads to an assembler as four
different components. So the raw per-part export is regrouped here on
footprint + part type, keeping the channel names in a separate column.

Columns are the ones PCBWay / JLCPCB / Aisler all accept: Designator, Value,
Footprint, Qty, plus MPN/Supplier left blank for you to fill, and a DNP flag.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

SCH = sys.argv[1] if len(sys.argv) > 1 else "fan-controller/fan-controller.kicad_sch"
OUT = sys.argv[2] if len(sys.argv) > 2 else "fab/fan-controller-bom.csv"

# Parts whose Value names a role rather than a part type. The BOM needs the
# part type for sourcing; the role is kept in a Note column.
ROLE_VALUES = {
    "FAN1": "4-pin PC fan header",
    "FAN2": "4-pin PC fan header",
    "FAN3": "4-pin PC fan header",
    "FAN4": "4-pin PC fan header",
    "DC_Jack_12V": "DC barrel jack 5.5x2.1mm",
}

with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    raw = f.name
try:
    subprocess.run(
        ["kicad-cli", "sch", "export", "bom", "--output", raw,
         "--fields", "Reference,Value,Footprint,${DNP}",
         "--labels", "Designator,Value,Footprint,DNP",
         "--group-by", "",                       # no grouping: one row per part
         SCH],
        capture_output=True, check=True)
    rows = list(csv.DictReader(open(raw)))
finally:
    os.unlink(raw)


def refkey(ref):
    m = re.match(r'([A-Za-z_]+)(\d+)', ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def collapse(refs):
    """R1,R2,R3,R5 -> 'R1-R3, R5'"""
    refs = sorted(refs, key=refkey)
    out, run = [], []
    for r in refs:
        if run and refkey(r)[0] == refkey(run[-1])[0] and refkey(r)[1] == refkey(run[-1])[1] + 1:
            run.append(r)
        else:
            if run:
                out.append(run)
            run = [r]
    if run:
        out.append(run)
    return ", ".join(g[0] if len(g) == 1 else f"{g[0]}-{g[-1]}" for g in out)


groups = {}
for r in rows:
    ref = r["Designator"].strip('"')
    val = r["Value"].strip('"')
    fp = r["Footprint"].strip('"')
    dnp = bool(r.get("DNP", "").strip('"'))
    part = ROLE_VALUES.get(val, val)
    note = val if val in ROLE_VALUES else ""
    key = (fp, part, dnp)
    g = groups.setdefault(key, {"refs": [], "notes": []})
    g["refs"].append(ref)
    if note:
        g["notes"].append(note)

os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
with open(OUT, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["Designator", "Value", "Footprint", "Qty",
                "MPN", "Supplier", "DNP", "Note"])
    for (fp, part, dnp), g in sorted(groups.items(), key=lambda kv: refkey(sorted(kv[1]["refs"], key=refkey)[0])):
        w.writerow([collapse(g["refs"]), part, fp, len(g["refs"]),
                    "", "", "DNP" if dnp else "",
                    "; ".join(g["notes"])])

# The XIAO plugs into sockets, so the female headers are what actually gets
# assembled -- but they have no schematic symbol (the module's footprint
# provides their pads). Add them explicitly or they are simply not fitted.
    w.writerow(["U1 socket", "1x7 female header 2.54mm",
                "Connector_PinSocket_2.54mm:PinSocket_1x07_P2.54mm_Vertical",
                2, "", "", "", "mates with U1 (DNP); 2 pcs per board"])

placed = sum(len(g["refs"]) for (fp, p, dnp), g in groups.items() if not dnp)
skipped = sum(len(g["refs"]) for (fp, p, dnp), g in groups.items() if dnp)
print(f"wrote {OUT}: {len(groups)+1} line items "
      f"(incl. the socket headers, which have no schematic symbol), "
      f"{placed+2} parts to place, {skipped} DNP")
