#!/usr/bin/env python3
"""CPL/Pick-and-Place im JLCPCB-Format erzeugen.

Aufruf: python3 fan-controller/make_cpl.py [board.kicad_pcb] [out.csv]

kicad-cli exportiert die Spalten Ref,Val,Package,PosX,PosY,Rot,Side.
JLCPCB verlangt Designator,Mid X,Mid Y,Layer,Rotation - andere Namen,
andere Reihenfolge, und "Side" heisst dort "Layer" mit den Werten
Top/Bottom statt top/bottom. Wird die KiCad-Datei unveraendert
hochgeladen, weist JLCPCB sie zurueck.

Die Koordinaten selbst sind bereits richtig: Ursprung ist die linke
untere Platinenecke (aux origin), Einheit mm.

--exclude-fp-th laesst die Durchsteckteile weg: JLCPCBs Katalog fuehrt sie
nicht, sie werden separat beschafft und von Hand geloetet. Siehe
fab/THT-BESTELLLISTE.md.
"""
import csv
import os
import subprocess
import sys
import tempfile

PCB = sys.argv[1] if len(sys.argv) > 1 else "fan-controller/fan-controller.kicad_pcb"
OUT = sys.argv[2] if len(sys.argv) > 2 else "fab/fan-controller-cpl.csv"

with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
    raw = f.name
try:
    subprocess.run(
        ["kicad-cli", "pcb", "export", "pos", "--output", raw,
         "--format", "csv", "--units", "mm", "--side", "both",
         "--use-drill-file-origin", "--exclude-dnp",
         "--exclude-fp-th",        # THT wird selbst bestueckt
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
        # JLCPCB will Top/Bottom gross geschrieben, und Masse mit Einheit.
        layer = "Top" if r["Side"].strip().lower() == "top" else "Bottom"
        w.writerow([r["Ref"],
                    f'{float(r["PosX"]):.4f}mm',
                    f'{float(r["PosY"]):.4f}mm',
                    layer,
                    f'{float(r["Rot"]):.2f}'])

print(f"{OUT}: {len(rows)} Bestueckpositionen im JLCPCB-Format")
