#!/usr/bin/env python3
"""Erstlagen-Testmuster in Form eines Muehlebretts.

Zweck: an 25 ueber die Platte verteilten Stellen zugleich zeigen, ob
  * die Duese schmiert (gefuellte Kreisflaeche),
  * benachbarte Bahnen verschmelzen (dieselbe Flaeche, 14 mm),
  * enge Kurven bei Druckgeschwindigkeit haften (Kreisring 20 mm),
  * scharfe Ecken haften (die zwoelf 90-Grad-Ecken der drei Ringe).

Aufbau: drei verschachtelte Quadrate mit je 8 Punkten (Ecken und
Kantenmitten) plus einem Kreis im Zentrum. Die Abstaende auf den
Mittellinien sind gleich; auf den Diagonalen sind sie zwangslaeufig
groesser - das laesst sich bei einem Quadratraster nicht vermeiden.

Alles mit einer Geschwindigkeit, damit ein Fehler dem ORT zugeordnet
werden kann und nicht dem Tempo.

Erzeugt fuer jeden z-Offset eine eigene Datei.
"""
import math, os, sys

BETT   = 250.0
RAND   = 12.0            # Abstand des aeusseren Rings vom Bettrand
KREIS_D  = 20.0          # Aussendurchmesser der Kreise
FUELL_D  = 14.0          # gefuellter Kern
LINIEN   = 2             # Verbindungen aus zwei Bahnen
BREITE   = 0.42          # Extrusionsbreite
HOEHE    = 0.20          # Lagenhoehe
SPEED    = 60 * 60       # 60 mm/s
TEMP_N, TEMP_B = 265, 75 # PETG weiss
FLOW_KOEFF = BREITE * HOEHE / (math.pi * (1.75/2)**2)

M = BETT / 2
# Der aeussere Ring traegt Kreise, die um ihren Radius nach aussen ragen.
# RAND meint den Abstand des AEUSSERSTEN Materials vom Bettrand.
SCHRITT = (M - RAND - KREIS_D / 2) / 3


def punkte():
    """25 Mittelpunkte: drei Ringe a 8 Punkte, dazu das Zentrum."""
    p = []
    for ring in (3, 2, 1):
        h = ring * SCHRITT
        for dx, dy in ((-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)):
            p.append((M + dx*h, M + dy*h))
    p.append((M, M))
    return p


class Bahn:
    def __init__(self):
        self.g = []
        self.x = self.y = None

    def nach(self, x, y, extrudieren=True):
        if self.x is None or not extrudieren:
            self.g.append("G1 X%.3f Y%.3f F9000" % (x, y))
        else:
            d = math.hypot(x - self.x, y - self.y)
            self.g.append("G1 X%.3f Y%.3f E%.5f F%d"
                          % (x, y, d * FLOW_KOEFF, SPEED))
        self.x, self.y = x, y

    def kreis(self, cx, cy, r, segmente=72):
        self.nach(cx + r, cy, False)
        for i in range(1, segmente + 1):
            w = 2 * math.pi * i / segmente
            self.nach(cx + r * math.cos(w), cy + r * math.sin(w))

    def strecke(self, x0, y0, x1, y1):
        self.nach(x0, y0, False)
        self.nach(x1, y1)


def muster(z):
    b = Bahn()
    b.g += ["; Bett-Testmuster, Muehlebrett, z=%.3f" % z,
            "M201 X20000 Y20000 Z1000 E20000", "M203 X600 Y600 Z15 E600",
            "M204 P20000 R20000 T20000", "M205 X15 Y15 Z15 E15",
            "M106 S0", "M106 P2 S0",
            "G9111 bedTemp=%d extruderTemp=%d" % (TEMP_B, TEMP_N),
            "M117", "G90", "G21", "M83", "M900 K0.04",
            "; PURGE LINE", "M204 P500",
            "SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=9",
            "G1 Z%.3f F900" % (z + 0.3), "G1 X89.365 Y255 F18000",
            "G1 Z%.3f F900" % z, "G1 E0.8 F2400", "G1 E0.6 F2400", "G1 F3000",
            "G1 X158.835 Y255 E3.72454", "G1 X158.835 Y255.45 E.0252",
            "G1 X89.365 Y255.45 E3.72454", "G1 X89.365 Y255.02 E.02305",
            "G1 Z%.3f F600" % (z + 0.3),
            ";LAYER_CHANGE", ";Z:%.2f" % HOEHE,
            "G1 Z%.3f F600" % z, "M204 P5000"]

    # die drei Ringe - ihre Ecken sind die echten 90-Grad-Wechsel
    for ring in (3, 2, 1):
        h = ring * SCHRITT
        for i in range(LINIEN):
            o = i * BREITE
            ecken = [(M-h+o, M-h+o), (M+h-o, M-h+o),
                     (M+h-o, M+h-o), (M-h+o, M+h-o), (M-h+o, M-h+o)]
            b.nach(*ecken[0], extrudieren=False)
            for e in ecken[1:]:
                b.nach(*e)

    # Speichen: vom Zentrum nach aussen ueber die Kantenmitten
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        for i in range(LINIEN):
            o = (i - (LINIEN-1)/2) * BREITE
            qx, qy = (0, o) if dx else (o, 0)
            b.strecke(M + qx, M + qy,
                      M + dx*3*SCHRITT + qx, M + dy*3*SCHRITT + qy)

    # Kreise: Aussenring und gefuellter Kern
    for cx, cy in punkte():
        b.kreis(cx, cy, KREIS_D/2)
        r = FUELL_D/2
        while r > BREITE/2:
            b.kreis(cx, cy, r)
            r -= BREITE

    b.g += ["G1 E-2 F3000", "G1 Z20 F900", "G1 X44 Y270 F12000",
            "M140 S0", "M104 S0", "M106 S0", "M84"]
    return "\n".join(b.g) + "\n"


ziel = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(ziel, exist_ok=True)
print("Muehlebrett-Testmuster, %d Kreise, Schritt %.2f mm\n" % (len(punkte()), SCHRITT))
n = 0
for i in range(9):
    off = -0.10 + i * 0.05
    z = HOEHE + off
    name = "bedtest_z%+.2f.gcode" % off
    open(os.path.join(ziel, name), "w").write(muster(z))
    print("  %-24s Duese %.3f mm" % (name, z))
    n += 1
print("\n%d Dateien in %s" % (n, ziel))
