#!/usr/bin/env python3
"""Gehaeuse-Parameter aus der Platine ziehen.

Aufruf: python3 enclosure/extract_geometry.py

Schreibt enclosure/board_params.scad. Alle Masse kommen aus pcbnew, nicht
aus dem Textformat der .kicad_pcb: die Footprint-Rotationen von Hand zu
transformieren hat in diesem Projekt schon einmal zwei Verdrahtungen
gekostet, und ein um 90 Grad gespiegelter Stecker faellt am fertigen Druck
auf, nicht vorher.

Koordinaten: Ursprung linke untere Ecke des Platinenumrisses, X nach
rechts, Y nach oben - also so, wie man die bestueckte Seite ansieht.
"""
import pcbnew

PCB = "fan-controller/fan-controller.kicad_pcb"
OUT = "enclosure/board_params.scad"
LW = 0.05            # halbe Linienbreite von Edge.Cuts, steckt in der BBox

# Bauteile, deren Grundflaeche das Gehaeuse braucht
WANTED = ["U1", "J1", "J2", "J3", "J4", "J5", "C1", "U2"]

board = pcbnew.LoadBoard(PCB)
box = board.GetBoardEdgesBoundingBox()
x0, ytop = box.GetLeft(), box.GetBottom()
mm = lambda v: round(v / 1e6, 3)

L = mm(box.GetWidth()) - 2 * LW
W = mm(box.GetHeight()) - 2 * LW

def bbox(ref):
    for f in board.GetFootprints():
        if f.GetReference() != ref:
            continue
        cy = f.GetCourtyard(pcbnew.F_CrtYd).BBox()
        if cy.GetWidth() == 0:
            cy = f.GetBoundingBox(False, False)
        return (mm(cy.GetLeft() - x0) - LW, mm(cy.GetRight() - x0) - LW,
                mm(ytop - cy.GetBottom()) - LW, mm(ytop - cy.GetTop()) - LW)
    raise KeyError(ref)

# Antennen-Sperrflaeche: Zonen stehen in absoluten Koordinaten, hier ist
# keine Rotation im Spiel
ant = None
for i in range(board.GetAreaCount()):
    z = board.GetArea(i)
    if not z.GetIsRuleArea():
        continue
    b = z.GetBoundingBox()
    ant = (mm(b.GetLeft() - x0) - LW, mm(b.GetRight() - x0) - LW,
           mm(ytop - b.GetBottom()) - LW, mm(ytop - b.GetTop()) - LW)

with open(OUT, "w") as f:
    f.write("// AUTOMATISCH ERZEUGT von enclosure/extract_geometry.py\n"
            "// Nicht von Hand aendern - Aenderungen an der Platine hier\n"
            "// durch erneuten Aufruf nachziehen.\n\n")
    f.write(f"board_l = {L};   // X, Laengsrichtung\n")
    f.write(f"board_w = {W};   // Y, Querrichtung\n\n")
    for ref in WANTED:
        xa, xb, ya, yb = bbox(ref)
        f.write(f"{ref}_x = [{xa}, {xb}];  {ref}_y = [{ya}, {yb}];\n")
    if ant:
        f.write(f"\nantenna_x = [{ant[0]}, {ant[1]}];  "
                f"antenna_y = [{ant[2]}, {ant[3]}];\n")

print(f"{OUT} geschrieben:  Platine {L} x {W} mm")
for ref in WANTED:
    xa, xb, ya, yb = bbox(ref)
    print(f"  {ref:3}  X {xa:6.2f}..{xb:6.2f}   Y {ya:6.2f}..{yb:6.2f}")
if ant:
    print(f"  Antennenzone  X {ant[0]:.2f}..{ant[1]:.2f}  Y {ant[2]:.2f}..{ant[3]:.2f}")
