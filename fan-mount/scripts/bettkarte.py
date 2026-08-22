"""Farbkarte der ersten Lage aus den Messwerten des Testmusters.

Interpoliert die 25 Messpunkte per inverser Distanzgewichtung ueber die
ganze Platte. Farbskala nach Vorgabe: 0 rot, 10 gelb, 20 gruen, 30 blau -
also gruen = Sollhoehe, rot = Duese zu tief (kein Material).
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BETT = 250.0
M = 125.0
RAND = 12.0
KREIS_D = 20.0
S = (M - RAND - KREIS_D / 2) / 3

xs = [M - 3*S, M - 2*S, M - S, M, M + S, M + 2*S, M + 3*S]
ys = [M + 3*S, M + 2*S, M + S, M, M - S, M - 2*S, M - 3*S]   # Zeile 1 = hinten

import sys
DATEN = {
    "z000": ("0,24,17, 7,24,25, 0,0,18, 28,24,9,0,11,28,30, 14,10,17, 24,22,26, 18,22,24",
             0.00, 30),
    "z020": ("28,55,33, 14,50,45, 30,33,45, 43,45,35,30,34,45,48, 42,42,41, 44,46,48, 46,50,48",
             0.20, 55),
    # ab hier SCHWARZES PETG - nicht direkt mit den Weiss-Messungen
    # vergleichbar, das Material traegt bei gleichem Offset mehr auf.
    "z002s": ("26,50,39, 9,44,35, 26,27,34, 35,34,27,31,34,49,39, 33,28,35, 41,36,39, 23,40,40",
              0.02, 55),
}
WAHL = sys.argv[1] if len(sys.argv) > 1 else "z000"
ROH, OFFSET, VMAX = DATEN[WAHL]
SPALTEN = {0: [0, 3, 6], 1: [1, 3, 5], 2: [2, 3, 4],
           4: [2, 3, 4], 5: [1, 3, 5], 6: [0, 3, 6]}

pkt = []
for r, grp in enumerate(ROH.split(", ")):
    vals = [int(v) for v in grp.strip().split(",")]
    cols = list(range(7)) if r == 3 else SPALTEN[r]
    for c, v in zip(cols, vals):
        pkt.append((xs[c], ys[r], v))

px = np.array([p[0] for p in pkt])
py = np.array([p[1] for p in pkt])
pv = np.array([p[2] for p in pkt], dtype=float)

# Inverse Distanzgewichtung (scipy ist nicht installiert und wird hier
# auch nicht gebraucht - 25 Stuetzstellen sind wenig).
N = 400
gx, gy = np.meshgrid(np.linspace(0, BETT, N), np.linspace(0, BETT, N))
d = np.sqrt((gx[..., None] - px)**2 + (gy[..., None] - py)**2)
d = np.maximum(d, 1e-6)
w = 1.0 / d**2
z = (w * pv).sum(axis=2) / w.sum(axis=2)

# Farbskala nach Nutzervorgabe, feste Zuordnung Wert -> Farbe, damit
# Karten verschiedener Offsets direkt vergleichbar sind:
#   0 rot . 10 gelb . 20 gruen (Soll) . 30 blau . 40 blauviolett . 50 magenta
# Der Nutzer hat die Stufen am gedruckten Teil geeicht (2026-08-22):
#   14 gequetscht . 28 perfekt . 30 leicht zu hoch (Luecken) . >40 zerfetzt
ANKER = [(0, "#d02020"), (10, "#e8d020"), (20, "#20a040"),
         (30, "#2050d0"), (40, "#7020c0"), (50, "#e020a0")]
stops = [(min(v / VMAX, 1.0), c) for v, c in ANKER if v <= VMAX]
if stops[-1][0] < 1.0:
    stops.append((1.0, stops[-1][1]))
cmap = LinearSegmentedColormap.from_list("bett", stops)

fig, ax = plt.subplots(figsize=(9, 9))
im = ax.imshow(z, origin="lower", extent=[0, BETT, 0, BETT],
               cmap=cmap, vmin=0, vmax=VMAX, interpolation="bilinear")

cs = ax.contour(gx, gy, z, levels=[l for l in (5,10,15,20,25,30,35,40,45,50) if l < VMAX],
                colors="black", linewidths=0.6, alpha=0.45)
ax.clabel(cs, inline=True, fontsize=8, fmt="%d")

ax.scatter(px, py, c="black", s=18, zorder=3)
for x, y, v in pkt:
    ax.annotate("%d" % v, (x, y), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=9, weight="bold",
                color="white",
                path_effects=[])
    ax.annotate("%d" % v, (x, y), textcoords="offset points", xytext=(0, 7),
                ha="center", fontsize=9, weight="bold", color="black")

ax.set_xlim(0, BETT); ax.set_ylim(0, BETT)
ax.set_xlabel("X  (links → rechts)  [mm]")
ax.set_ylabel("Y  (vorn → hinten)  [mm]")
ax.set_title("Erste Lage bei z-Offset %.2f — Höhe in 1/100 mm\n" % OFFSET +
             "rot 0 · gelb 10 · grün 20 (Soll) · blau 30 · violett 40 · magenta 50\n"
             "am Teil geeicht: 14 gequetscht · 28 perfekt · 30 Lücken · ab 40 zerfetzt",
             fontsize=10)
ax.set_aspect("equal")

cb = fig.colorbar(im, ax=ax, shrink=0.8, ticks=[t for t in (0,10,20,30,40,50,60) if t <= VMAX])
cb.set_label("Höhe der ersten Lage [1/100 mm]")

out = "/data/joachim/git/fan-stand/cad/tests/bettkarte-%s.png" % WAHL
fig.savefig(out, dpi=140, bbox_inches="tight")
print("geschrieben:", out)
print("Wertebereich interpoliert: %.1f .. %.1f" % (z.min(), z.max()))
