#!/usr/bin/env python3
"""Build an assembly-ready BOM from the schematic.

Usage: python3 fan-controller/make_bom.py [schematic.kicad_sch] [out.csv]

kicad-cli's own grouping compares every listed field, so the four fan headers
never merge: their Values are FAN1..FAN4 (which channel each drives) even
though they are one identical part. That reads to an assembler as four
different components. So the raw per-part export is regrouped here on
footprint + part type, keeping the channel names in a separate column.

Ausgabeformat sind JLCPCBs vier Spalten: Comment, Designator, Footprint,
LCSC Part #. Deren Import lehnt abweichende Kopfzeilen ab (wie schon bei der
CPL). "LCSC Part #" bleibt leer - entweder selbst ausfuellen oder den
Bestuecker aus seinem Lager substituieren lassen.

DNP-Teile werden weggelassen statt markiert: U1 (das XIAO-Modul) wird
gesockelt und von dir beigestellt. Die Fassungen selbst muessen dagegen
bestueckt werden und stehen daher drin.
"""
import csv
import os
import re
import subprocess
import sys
import tempfile

SCH = sys.argv[1] if len(sys.argv) > 1 else "fan-controller/fan-controller.kicad_sch"
OUT = sys.argv[2] if len(sys.argv) > 2 else "fab/fan-controller-bom.csv"

# Durchsteckteile werden selbst beschafft und geloetet - JLCPCBs Katalog
# fuehrt sie nicht. Sie muessen aus BOM UND CPL raus, sonst meldet der
# Import wieder fehlende Designatoren. Liste: fab/THT-BESTELLLISTE.md
THT_REFS = {"C1", "J1", "J2", "J3", "J4", "J5", "U1"}

# Parts whose Value names a role rather than a part type. The BOM needs the
# part type for sourcing; the role is kept in a Note column.
# LCSC-Teilenummern. Ohne diese raet JLCPCBs Zuordnung, und THT-Teile
# findet sie meist gar nicht ("No matches").
#
# Bestaetigt - von JLCPCBs eigener BOM-Zuordnung geliefert:
LCSC = {
    "C2":  "C440198",    # 10uF 0805, Murata GRM21BR61H106KE43L, Basic
    "D1":  "C8678",      # SS34 SMA, MDD, Basic
    "U2":  "C6187",      # AMS1117-5.0 SOT-223, AMS, Basic
    "R1":  "C25804",     # 10k 0603 1%, Uniroyal, Basic
    "R5":  "C21190",     # 1k  0603 1%, Uniroyal, Basic
    "R9":  "C23138",     # 330 0603 1%, Uniroyal, Basic
    # Recherchiert, NICHT von JLCPCB bestaetigt - vor dem Bestellen im
    # Katalog gegenpruefen (Bauform, Spannung, Lagerbestand):
    "F1":  "C209713",    # SMD1812P150TF/24, 1.5A 24V 1812. Die /8-Variante
                         #   (C209721) waere mit 8V zu wenig fuer 12V.
    "U1":  "C5303",      # 2.54mm Buchsenleiste 1x40, zum Ablaengen auf 1x7
    # Nicht gefunden - J1 (Hohlbuchse 5.5x2.1) und J2-J5 (Stiftleiste 1x4)
    # bleiben leer und muessen im Web-Interface gewaehlt werden.
}

ROLE_VALUES = {
    "FAN1": "4-pin PC fan header",
    "FAN2": "4-pin PC fan header",
    "FAN3": "4-pin PC fan header",
    "FAN4": "4-pin PC fan header",
    "DC_Jack_12V": "DC barrel jack 5.5x2.1mm",
    # U1 ist im Schaltplan das XIAO-Modul, auf der Platine aber die
    # Fassungsposition: die 14 Durchsteckpads des Modul-Footprints sind
    # die Loecher fuer zwei 1x7-Buchsenleisten. Das Modul selbst wird
    # gesteckt, nicht bestueckt. Die Fassungen haben kein eigenes
    # Schaltplan-Symbol, also muessen sie hier haengen - sonst stehen sie
    # in keiner CPL und JLCPCB weist die BOM-Zeile zurueck.
    "XIAO ESP32-C3": "1x7 female header 2.54mm - 2 pcs per board - "
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
    """Alle Designatoren als Kommaliste: R1,R2,R3,R4

    Keine Bereichsschreibweise ("R1-R4"): JLCPCB gleicht BOM und CPL
    designatorweise ab und meldet sonst "designators don't exist in the
    CPL file". Ohne Leerzeichen nach dem Komma, damit der Parser die
    Namen nicht mit Leerraum liest.
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
            continue          # U1: gesockelt, vom Kunden beigestellt
        comment = part
        # Rollenbezeichnungen anhaengen (FAN1..FAN4), aber nicht bei
        # Positionen, deren Comment die Rolle ohnehin schon beschreibt.
        notes = [n for n in g["notes"] if n not in ROLE_VALUES]
        if notes:
            comment += " - " + " ".join(notes)
        refs = sorted(g["refs"], key=refkey)
        w.writerow([comment, collapse(g["refs"]), fp,
                    LCSC.get(refs[0], "")])

placed = sum(len(g["refs"]) for (fp, p, dnp), g in groups.items() if not dnp)
skipped = sum(len(g["refs"]) for (fp, p, dnp), g in groups.items() if dnp)
print(f"{OUT}: {len([k for k in groups if not k[2]])} Positionen im "
      f"JLCPCB-Format, {placed} Teile zu bestuecken, "
      f"{skipped} DNP weggelassen")
