"""Ueberlagerung aller drei Messreihen zu einem Bettprofil.

Einzelne Kreise sind bei welligem oder klumpigem Material schlecht
reproduzierbar - ob an derselben Stelle 40 oder 50 herauskommt, ist
teilweise Zufall. Ueber drei Drucke gemittelt bleibt die Tendenz uebrig.

Zwei Karten:
  mittel     - schlichter Mittelwert der drei Messungen
  profil     - jede Reihe zuerst auf ihren eigenen Median normiert, dann
               gemittelt. Das ist die eigentliche Bettform, unabhaengig
               davon, auf welcher Hoehe die jeweilige Reihe insgesamt lag.
"""
import sys
import statistics as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BETT = 250.0
M = 125.0
S = (M - 12.0 - 20.0 / 2) / 3
xs = [M - 3*S, M - 2*S, M - S, M, M + S, M + 2*S, M + 3*S]
ys = [M + 3*S, M + 2*S, M + S, M, M - S, M - 2*S, M - 3*S]
SPALTEN = {0: [0, 3, 6], 1: [1, 3, 5], 2: [2, 3, 4],
           4: [2, 3, 4], 5: [1, 3, 5], 6: [0, 3, 6]}

REIHEN = [
    ("0.00 weiss", "0,24,17, 7,24,25, 0,0,18, 28,24,9,0,11,28,30, 14,10,17, 24,22,26, 18,22,24"),
    ("0.20 weiss", "28,55,33, 14,50,45, 30,33,45, 43,45,35,30,34,45,48, 42,42,41, 44,46,48, 46,50,48"),
    ("0.02 schwarz", "26,50,39, 9,44,35, 26,27,34, 35,34,27,31,34,49,39, 33,28,35, 41,36,39, 23,40,40"),
]


def lade(roh):
    p = []
    for r, grp in enumerate(roh.split(", ")):
        vals = [int(v) for v in grp.strip().split(",")]
        cols = list(range(7)) if r == 3 else SPALTEN[r]
        for c, v in zip(cols, vals):
            p.append((xs[c], ys[r], v))
    return p


saetze = [lade(r) for _, r in REIHEN]
px = np.array([p[0] for p in saetze[0]])
py = np.array([p[1] for p in saetze[0]])
werte = [np.array([p[2] for p in s], dtype=float) for s in saetze]

MODUS = sys.argv[1] if len(sys.argv) > 1 else "profil"
if MODUS == "mittel":
    pv = sum(werte) / len(werte)
    VMAX = 55
    ANKER = [(0, "#d02020"), (10, "#e8d020"), (20, "#20a040"),
             (30, "#2050d0"), (40, "#7020c0"), (50, "#e020a0")]
    titel = ("Mittel aus drei Messreihen — Höhe in 1/100 mm\n"
             "rot 0 · gelb 10 · grün 20 · blau 30 · violett 40 · magenta 50")
    cblabel = "mittlere Höhe der ersten Lage [1/100 mm]"
else:
    # jede Reihe auf ihren Median normiert: uebrig bleibt die Bettform
    pv = sum(w - np.median(w) for w in werte) / len(werte)
    VMAX = None
    titel = ("Bettprofil — Mittel aus drei Reihen, je auf ihren Median normiert\n"
             "blau = liegt höher als der Rest der Platte · rot = liegt tiefer")
    cblabel = "Abweichung vom Median der Platte [1/100 mm]"

N = 400
gx, gy = np.meshgrid(np.linspace(0, BETT, N), np.linspace(0, BETT, N))
d = np.maximum(np.sqrt((gx[..., None] - px)**2 + (gy[..., None] - py)**2), 1e-6)
w = 1.0 / d**2
z = (w * pv).sum(axis=2) / w.sum(axis=2)

fig, ax = plt.subplots(figsize=(9, 9))
if MODUS == "mittel":
    stops = [(min(v / VMAX, 1.0), c) for v, c in ANKER if v <= VMAX]
    if stops[-1][0] < 1.0:          # Skala bis 1.0 fortsetzen
        stops.append((1.0, stops[-1][1]))
    cmap = LinearSegmentedColormap.from_list("bett", stops)
    im = ax.imshow(z, origin="lower", extent=[0, BETT, 0, BETT],
                   cmap=cmap, vmin=0, vmax=VMAX, interpolation="bilinear")
    lev = [10, 20, 30, 40, 50]
    fmt = "%d"
else:
    g = max(abs(z.min()), abs(z.max()))
    im = ax.imshow(z, origin="lower", extent=[0, BETT, 0, BETT],
                   cmap="RdYlBu", vmin=-g, vmax=g, interpolation="bilinear")
    lev = [-20, -15, -10, -5, 0, 5, 10]
    fmt = "%+d"

cs = ax.contour(gx, gy, z, levels=lev, colors="black", linewidths=0.6, alpha=0.45)
ax.clabel(cs, inline=True, fontsize=8, fmt=fmt)
ax.scatter(px, py, c="black", s=18, zorder=3)
for x, y, v in zip(px, py, pv):
    ax.annotate(fmt % round(v), (x, y), textcoords="offset points",
                xytext=(0, 7), ha="center", fontsize=9, weight="bold")

# Die groesste ebene Rechteckflaeche (Spanne <= 12 Hundertstel), gesucht
# ueber alle achsparallelen Rechtecke des Messrasters.
if MODUS == "profil":
    import matplotlib.patches as mp
    ax.add_patch(mp.Rectangle((22, 22), 206, 69, fill=False,
                              edgecolor="black", linewidth=2.0, linestyle="--"))
    ax.annotate("ebene Zone 206 x 69 mm, Spanne 11/100 mm",
                (125, 96), ha="center", va="bottom", fontsize=9, weight="bold")

ax.set_xlim(0, BETT); ax.set_ylim(0, BETT)
ax.set_xlabel("X  (links → rechts)  [mm]")
ax.set_ylabel("Y  (vorn → hinten)  [mm]")
ax.set_title(titel, fontsize=10)
ax.set_aspect("equal")
cb = fig.colorbar(im, ax=ax, shrink=0.8)
cb.set_label(cblabel)

out = "/data/joachim/git/fan-stand/cad/tests/bettkarte-%s.png" % MODUS
fig.savefig(out, dpi=140, bbox_inches="tight")
print("geschrieben:", out)
