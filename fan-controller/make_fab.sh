#!/bin/sh
# Regenerate the fabrication package.
#
# Run from the repo root:  fan-controller/make_fab.sh
#
# The explicit --layers list is not optional: a bare
# `kicad-cli pcb export gerbers` writes every layer, including the
# User.Eco1 scratch layer used for review markers during layout.
set -e

PCB=fan-controller/fan-controller.kicad_pcb
SCH=fan-controller/fan-controller.kicad_sch
OUT=fab

LAYERS="F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"

rm -rf "$OUT/gerbers"
mkdir -p "$OUT/gerbers"

kicad-cli pcb export gerbers --output "$OUT/gerbers" --layers "$LAYERS" "$PCB"

kicad-cli pcb export drill --output "$OUT/gerbers/" \
    --format excellon --drill-origin plot --excellon-units mm \
    --generate-map --map-format gerberx2 "$PCB"

# CPL im JLCPCB-Spaltenformat. Nicht kicad-cli direkt: dessen Kopfzeile
# (Ref,Val,Package,PosX,PosY,Rot,Side) wird von JLCPCB abgelehnt.
python3 fan-controller/make_cpl.py "$PCB" "$OUT/fan-controller-cpl.csv"

python3 fan-controller/make_bom.py "$SCH" "$OUT/fan-controller-bom.csv"

# PCBWay-Variante: tolerantes Format, eigene Spalten, PTH mitgelistet
python3 fan-controller/make_pcbway.py

# python's zipfile rather than zip(1), which is not installed everywhere
python3 - "$OUT" <<'EOF'
import os, sys, zipfile
out = sys.argv[1]
zp = os.path.join(out, "fan-controller-fab.zip")
if os.path.exists(zp):
    os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for name in ("fan-controller-bom.csv", "fan-controller-cpl.csv",
                 "README.md", "THT-BESTELLLISTE.md", "ROTATION-WARNUNG.md"):
        z.write(os.path.join(out, name), name)
    for f in sorted(os.listdir(os.path.join(out, "pcbway"))):
        z.write(os.path.join(out, "pcbway", f), os.path.join("pcbway", f))
    for f in sorted(os.listdir(os.path.join(out, "gerbers"))):
        z.write(os.path.join(out, "gerbers", f), os.path.join("gerbers", f))
EOF

echo
echo "package: $OUT/fan-controller-fab.zip"
ls -la "$OUT/fan-controller-fab.zip"
