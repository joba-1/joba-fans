"""Bettkarte nur aus gut messbaren Kreisen.

Sehr dicke oder sehr duenne Kreise lassen sich mit dem Messschieber
schlecht erfassen: bei welligem oder klumpigem Material streut der Wert
an ein und demselben Kreis um mehrere Hundertstel. Verlaesslich sind die
Kreise mittlerer Dicke.

Diese Auswertung nimmt daher pro Rasterpunkt nur die Messungen, die im
Band LO..HI liegen, und rechnet den jeweiligen z-Offset heraus:

    Bettlage = Schichtdicke - Offset

Eine duenne Lage bei hohem Offset bedeutet, dass das Bett dort hoch
liegt; eine dicke Lage bei niedrigem Offset, dass es tief liegt. So
werden Messungen verschiedener Offsets auf eine gemeinsame Skala
gebracht - unabhaengig davon, mit welchem Offset sie entstanden sind.

Aufruf:  python3 bettkarte_gut.py [LO] [HI]      (Vorgabe 14 36)
"""
import sys
import statistics as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BETT = 250.0
M = 125.0
S = (M - 12.0 - 20.0 / 2) / 3
xs = [M - 3*S, M - 2*S, M - S, M, M + S, M + 2*S, M + 3*S]
ys = [M + 3*S, M + 2*S, M + S, M, M - S, M - 2*S, M - 3*S]
SP = {0: [0, 3, 6], 1: [1, 3, 5], 2: [2, 3, 4],
      4: [2, 3, 4], 5: [1, 3, 5], 6: [0, 3, 6]}


def lade(roh):
    g = {}
    for r, grp in enumerate(roh.split(", ")):
        vals = [int(v) for v in grp.strip().split(",")]
        cols = list(range(7)) if r == 3 else SP[r]
        for c, v in zip(cols, vals):
            g[(r, c)] = v
    return g


REIHEN = [
    (0.00, "weiss",  "0,24,17, 7,24,25, 0,0,18, 28,24,9,0,11,28,30, 14,10,17, 24,22,26, 18,22,24"),
    (0.20, "weiss",  "28,55,33, 14,50,45, 30,33,45, 43,45,35,30,34,45,48, 42,42,41, 44,46,48, 46,50,48"),
    (0.02, "schwarz","26,50,39, 9,44,35, 26,27,34, 35,34,27,31,34,49,39, 33,28,35, 41,36,39, 23,40,40"),
]
DATEN = [(off, lade(roh)) for off, _, roh in REIHEN]

LO = int(sys.argv[1]) if len(sys.argv) > 2 else 14
HI = int(sys.argv[2]) if len(sys.argv) > 2 else 36

punkte = sorted(DATEN[0][1].keys())
lage, anzahl = {}, {}
for k in punkte:
    w = [g[k] - off * 100 for off, g in DATEN if LO <= g[k] <= HI]
    if w:
        lage[k] = sum(w) / len(w)
        anzahl[k] = len(w)

# Wo nur EINE Messung im Band liegt, kann die Filterung genau den
# Ausreisser behalten und zwei uebereinstimmende Werte verwerfen. Solche
# Punkte werden gemeldet, damit man sie nicht fuer bare Muenze nimmt.
verdaechtig = []
for k in lage:
    if anzahl[k] != 1:
        continue
    raus = [g[k] - off * 100 for off, g in DATEN if not LO <= g[k] <= HI]
    if len(raus) == 2 and abs(raus[0] - raus[1]) <= 5:
        if abs(lage[k] - sum(raus) / 2) > 10:
            verdaechtig.append((k, lage[k], raus))
if verdaechtig:
    print("ACHTUNG: %d Punkt(e) beruhen auf einer einzigen Messung, waehrend"
          % len(verdaechtig))
    print("die verworfenen Werte untereinander einig sind:")
    for k, v, raus in verdaechtig:
        print("   Zeile %d Spalte %d: behalten %+.0f, verworfen %s"
              % (k[0], k[1], v, ["%+.0f" % x for x in raus]))

if len(lage) < len(punkte):
    fehlt = [k for k in punkte if k not in lage]
    print("WARNUNG: %d Punkte ohne Wert im Band %d..%d: %s"
          % (len(fehlt), LO, HI, fehlt))

med = st.median(list(lage.values()))
px = np.array([xs[c] for (r, c) in lage])
py = np.array([ys[r] for (r, c) in lage])
pv = np.array([lage[k] - med for k in lage])
pn = np.array([anzahl[k] for k in lage])

N = 500
gx, gy = np.meshgrid(np.linspace(0, BETT, N), np.linspace(0, BETT, N))
d = np.maximum(np.sqrt((gx[..., None] - px)**2 + (gy[..., None] - py)**2), 1e-6)
w = 1.0 / d**2
z = (w * pv).sum(axis=2) / w.sum(axis=2)

fig, ax = plt.subplots(figsize=(9, 9))
g = max(abs(z.min()), abs(z.max()))
im = ax.imshow(z, origin="lower", extent=[0, BETT, 0, BETT],
               cmap="RdYlBu_r", vmin=-g, vmax=g, interpolation="bilinear")
cs = ax.contour(gx, gy, z, levels=[-20, -15, -10, -5, 0, 5],
                colors="black", linewidths=0.6, alpha=0.45)
ax.clabel(cs, inline=True, fontsize=8, fmt="%+d")

# Punkte: Groesse zeigt, auf wie vielen Messungen der Wert beruht
for x, y, v, n in zip(px, py, pv, pn):
    ax.scatter([x], [y], c="black", s=14 + 16 * (n - 1), zorder=3)
    ax.annotate("%+d" % round(v), (x, y), textcoords="offset points",
                xytext=(0, 8), ha="center", fontsize=9, weight="bold")

ax.set_xlim(0, BETT); ax.set_ylim(0, BETT)
ax.set_xlabel("X  (links → rechts)  [mm]")
ax.set_ylabel("Y  (vorn → hinten)  [mm]")
ax.set_title("Bettlage nur aus gut messbaren Kreisen (%d..%d/100 mm)\n"
             "Schichtdicke minus z-Offset · rot = Bett liegt tief · "
             "blau = liegt hoch\nPunktgröße = Anzahl verwendeter Messungen"
             % (LO, HI), fontsize=10)
ax.set_aspect("equal")
cb = fig.colorbar(im, ax=ax, shrink=0.8)
cb.set_label("Abweichung vom Median [1/100 mm]")

out = "/data/joachim/git/fan-stand/cad/tests/bettkarte-gut-%d-%d.png" % (LO, HI)
fig.savefig(out, dpi=140, bbox_inches="tight")
print("geschrieben:", out)
print("Punkte: %d, Spanne %.0f Hundertstel" % (len(lage), pv.max() - pv.min()))
