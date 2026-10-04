#!/usr/bin/env python3
"""Build an assembly-ready BOM from the schematic.

Usage: python3 make_bom.py [schematic.kicad_sch] [out.csv]

kicad-cli's own grouping compares every listed field, so the four fan headers
never merge: their Values are FAN1..FAN4 (which channel each drives) even
though they are one identical part. That reads to an assembler as four
different components. So the raw per-part export is regrouped here on
footprint + part type, keeping the channel names in a separate column.

The output format is JLCPCB's four columns: Comment, Designator, Footprint,
LCSC Part #. Their import rejects other headers (as it already does for the
CPL). "LCSC Part #" stays empty where no number is known - either fill it in
yourself or let the assembler substitute from stock.

DNP parts are left out rather than marked: U1 (the XIAO module) is socketed
and supplied by the customer. The sockets themselves do have to be fitted
and are therefore included.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "fan-controller.kicad_sch")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "fab", "fan-controller-bom.csv")

# Through-hole parts are sourced and soldered by hand - JLCPCB's catalogue
# does not carry them. They must be removed from the BOM AND the CPL, or the
# import again complains about missing designators. List: fab/THT-ORDER-LIST.md
THT_REFS = {"C1", "J1", "J2", "J3", "J4", "J5", "U1"}

# LCSC part numbers. Without them JLCPCB's matching guesses, and it usually
# does not find THT parts at all ("No matches").
#
# Confirmed - supplied by JLCPCB's own BOM matching:
LCSC = {
    "C2":  "C440198",    # 10uF 0805, Murata GRM21BR61H106KE43L, Basic
    "D1":  "C8678",      # SS34 SMA, MDD, Basic
    "U2":  "C6187",      # AMS1117-5.0 SOT-223, AMS, Basic
    "R1":  "C25804",     # 10k 0603 1%, Uniroyal, Basic
    "R5":  "C21190",     # 1k  0603 1%, Uniroyal, Basic
    "R9":  "C23138",     # 330 0603 1%, Uniroyal, Basic
    # Researched, NOT confirmed by JLCPCB - check against the catalogue
    # before ordering (package, voltage, stock):
    "F1":  "C209713",    # SMD1812P150TF/24, 1.5A 24V 1812. The /8 variant
                         #   (C209721) is only 8V, too little for 12V.
    "U1":  "C5303",      # 2.54mm female header 1x40, to be cut to 1x7
    # Not found - J1 (barrel jack 5.5x2.1) and J2-J5 (pin header 1x4)
    # stay empty and have to be chosen in the web interface.
}

# Parts whose Value names a role rather than a part type. The BOM needs the
# part type for sourcing; the role is kept in a Note column.
ROLE_VALUES = {
    "FAN1": "4-pin PC fan header",
    "FAN2": "4-pin PC fan header",
    "FAN3": "4-pin PC fan header",
    "FAN4": "4-pin PC fan header",
    "DC_Jack_12V": "DC barrel jack 5.5x2.1mm",
    # U1 is the XIAO module in the schematic, but on the board it is the
    # socket position: the 14 through-hole pads of the module footprint are
    # the holes for two 1x7 female headers. The module itself is plugged in,
    # not assembled. The sockets have no schematic symbol of their own, so
    # they have to hang here - otherwise they are in no CPL and JLCPCB
    # rejects the BOM line.
    "XIAO ESP32-C3": "1x7 female header 2.54mm - "
                     "module is plugged in later, do not fit",
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
    """All designators as a comma list: R1,R2,R3,R4

    No range notation ("R1-R4"): JLCPCB matches BOM and CPL designator by
    designator and otherwise reports "designators don't exist in the CPL
    file". No space after the comma, so the parser does not read the names
    with whitespace.
    """
    return ",".join(sorted(refs, key=refkey))


groups = {}
for r in rows:
    ref = r["Designator"].strip('"')
    if ref in THT_REFS:
        continue
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
    w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
    for (fp, part, dnp), g in sorted(groups.items(), key=lambda kv: refkey(sorted(kv[1]["refs"], key=refkey)[0])):
        if dnp:
            continue          # U1: socketed, supplied by the customer
        comment = part
        # Append the role names (FAN1..FAN4), but not for positions whose
        # comment already describes the role.
        notes = [n for n in g["notes"] if n not in ROLE_VALUES]
        if notes:
            comment += " - " + " ".join(notes)
        refs = sorted(g["refs"], key=refkey)
        w.writerow([comment, collapse(g["refs"]), fp,
                    LCSC.get(refs[0], "")])

placed = sum(len(g["refs"]) for (fp, p, dnp), g in groups.items() if not dnp)
skipped = sum(len(g["refs"]) for (fp, p, dnp), g in groups.items() if dnp)
print(f"{OUT}: {len([k for k in groups if not k[2]])} lines in "
      f"JLCPCB format, {placed} parts to assemble, "
      f"{skipped} DNP left out")
