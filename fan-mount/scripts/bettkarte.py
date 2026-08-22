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

ROH = "0,24,17, 7,24,25, 0,0,18, 28,24,9,0,11,28,30, 14,10,17, 24,22,26, 18,22,24"
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

cmap = LinearSegmentedColormap.from_list(
    "bett", [(0.0, "#d02020"), (1/3, "#e8d020"), (2/3, "#20a040"), (1.0, "#2050d0")])

fig, ax = plt.subplots(figsize=(9, 9))
im = ax.imshow(z, origin="lower", extent=[0, BETT, 0, BETT],
               cmap=cmap, vmin=0, vmax=30, interpolation="bilinear")

cs = ax.contour(gx, gy, z, levels=[5, 10, 15, 20, 25],
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
ax.set_title("Erste Lage bei z-Offset 0.00 — Höhe in 1/100 mm\n"
             "grün = Soll 20 · rot = Düse zu tief · blau = zu hoch",
             fontsize=11)
ax.set_aspect("equal")

cb = fig.colorbar(im, ax=ax, shrink=0.8, ticks=[0, 10, 20, 30])
cb.set_label("Höhe der ersten Lage [1/100 mm]")

out = "/data/joachim/git/fan-stand/cad/tests/bettkarte-z000.png"
fig.savefig(out, dpi=140, bbox_inches="tight")
print("geschrieben:", out)
print("Wertebereich interpoliert: %.1f .. %.1f" % (z.min(), z.max()))
