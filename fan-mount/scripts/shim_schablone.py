"""Massstabsgetreue PDF-Schnittschablonen fuer Shims unter die PEI-Platte.

Aus den gemittelten Messreihen wird das Bettprofil interpoliert und in
Hoehenstufen zerlegt. Fuer jede Stufe entsteht eine Umrisslinie: alle
Flaechen, die mindestens so tief liegen, dass dort n Lagen Folie noetig
sind. Man schneidet Stufe n aus, legt sie auf, dann Stufe n-1 darueber,
usw. - so entsteht eine Treppe, die die Senke auffuellt.

Wichtig: gedruckt werden muss OHNE Skalierung ("Tatsaechliche Groesse",
nicht "An Seite anpassen"), sonst stimmen die Masse nicht. Jede Seite
traegt dafuer eine 100-mm-Kontrollstrecke.
"""
import statistics as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

BETT = 250.0
M = 125.0
S = (M - 12.0 - 20.0 / 2) / 3
xs = [M - 3*S, M - 2*S, M - S, M, M + S, M + 2*S, M + 3*S]
ys = [M + 3*S, M + 2*S, M + S, M, M - S, M - 2*S, M - 3*S]
SP = {0: [0, 3, 6], 1: [1, 3, 5], 2: [2, 3, 4],
      4: [2, 3, 4], 5: [1, 3, 5], 6: [0, 3, 6]}
REIHEN = [
    "0,24,17, 7,24,25, 0,0,18, 28,24,9,0,11,28,30, 14,10,17, 24,22,26, 18,22,24",
    "28,55,33, 14,50,45, 30,33,45, 43,45,35,30,34,45,48, 42,42,41, 44,46,48, 46,50,48",
    "26,50,39, 9,44,35, 26,27,34, 35,34,27,31,34,49,39, 33,28,35, 41,36,39, 23,40,40",
]
FOLIE = 1.0     # Dicke einer Lage in 1/100 mm (0,01 mm Alufolie)


def lade(roh):
    g = {}
    for r, grp in enumerate(roh.split(", ")):
        vals = [int(v) for v in grp.strip().split(",")]
        cols = list(range(7)) if r == 3 else SP[r]
        for c, v in zip(cols, vals):
            g[(r, c)] = v
    return g


G = [lade(x) for x in REIHEN]
med = [st.median(list(g.values())) for g in G]
prof = {k: sum(g[k] - m for g, m in zip(G, med)) / 3.0 for k in G[0]}

px = np.array([xs[c] for (r, c) in prof])
py = np.array([ys[r] for (r, c) in prof])
pv = np.array([prof[k] for k in prof])

N = 500
gx, gy = np.meshgrid(np.linspace(0, BETT, N), np.linspace(0, BETT, N))
d = np.maximum(np.sqrt((gx[..., None] - px)**2 + (gy[..., None] - py)**2), 1e-6)
w = 1.0 / d**2
z = (w * pv).sum(axis=2) / w.sum(axis=2)

# Ziel: alles auf Medianniveau (0) anheben. Hoeher liegende Stellen
# bleiben unberuehrt - sie abzutragen ginge ohnehin nicht.
noetig = np.maximum(-z, 0) / FOLIE            # Lagen, kontinuierlich

# Nicht jede einzelne Lage bekommt eine Schablone: 22 Stufen waeren 22
# auszuschneidende Teile, und so fein ist weder die Messung (Rauschen
# 3 Hundertstel) noch die Folie (Haushaltsfolie schwankt um 0,001 mm).
# Zusammengefasst zu Stufen von je STUFENHOEHE Lagen.
STUFENHOEHE = 4
stufen_lagen = list(range(STUFENHOEHE, int(np.ceil(noetig.max())) + 1,
                          STUFENHOEHE))
if not stufen_lagen:
    stufen_lagen = [int(np.ceil(noetig.max()))]
STUFEN = len(stufen_lagen)

out = "/data/joachim/git/fan-stand/cad/tests/shim-schablonen.pdf"
with PdfPages(out) as pdf:
    # Uebersicht
    fig = plt.figure(figsize=(8.27, 11.69))           # A4 hoch
    ax = fig.add_axes([0.13, 0.34, 0.72, 0.44])
    im = ax.contourf(gx, gy, noetig, levels=[0] + stufen_lagen + [99],
                     cmap="YlOrRd")
    ax.contour(gx, gy, noetig, levels=stufen_lagen,
               colors="black", linewidths=0.5)
    ax.scatter(px, py, c="black", s=10)
    ax.set_aspect("equal")
    ax.set_xlim(0, BETT); ax.set_ylim(0, BETT)
    ax.set_title("Uebersicht: noetige Lagen Alufolie (0,01 mm)\n"
                 "Blick von OBEN auf das Hotbed, PEI-Platte abgenommen",
                 fontsize=11)
    ax.set_xlabel("X [mm]   (links → rechts)")
    ax.set_ylabel("Y [mm]   (vorn → hinten)")
    fig.colorbar(im, ax=ax, shrink=0.6, label="Lagen")
    fig.text(0.5, 0.20,
             "%d Schablonen (Stufen zu je %d Lagen), maximal %.0f Lagen = %.2f mm"
             % (STUFEN, STUFENHOEHE, noetig.max(), noetig.max() * FOLIE / 100),
             ha="center", fontsize=10)
    pdf.savefig(fig, bbox_inches=None); plt.close(fig)

    # Je Stufe eine massstabsgetreue Seite
    # Die ganze Platte (250 mm) passt nicht auf A4. Sie muss aber auch
    # nicht: Folie bekommt nur die Senke, und die liegt in einer Ecke.
    # Also nur den belegten Ausschnitt zeigen, auf 10 mm gerundet und mit
    # etwas Rand - das passt 1:1 auf A4 hoch.
    m = noetig >= stufen_lagen[0]
    AX0 = max(0.0, np.floor((gx[m].min() - 8) / 10) * 10)
    AX1 = min(BETT, np.ceil((gx[m].max() + 8) / 10) * 10)
    AY0 = max(0.0, np.floor((gy[m].min() - 8) / 10) * 10)
    AY1 = min(BETT, np.ceil((gy[m].max() + 8) / 10) * 10)
    AW, AH = AX1 - AX0, AY1 - AY0

    A4B, A4H = 210.0, 297.0
    for nr, lage in enumerate(stufen_lagen, start=1):
        fig = plt.figure(figsize=(A4B/25.4, A4H/25.4))
        ax = fig.add_axes([(A4B/2 - AW/2)/A4B, 42.0/A4H, AW/A4B, AH/A4H])
        ax.contour(gx, gy, noetig, levels=[lage], colors="black", linewidths=1.5)
        ax.contourf(gx, gy, noetig, levels=[lage, 99], colors=["#00000012"])
        # Plattenrand als Passmarke - er liegt teilweise im Ausschnitt und
        # ist beim Auflegen die einzige verlaessliche Referenz.
        ax.plot([0, BETT, BETT, 0, 0], [0, 0, BETT, BETT, 0],
                color="black", linewidth=1.2)
        for lx, ly, txt in ((0, BETT, "Ecke hinten links"),
                            (0, 0, "Ecke vorn links")):
            if AX0 <= lx <= AX1 and AY0 <= ly <= AY1:
                ax.plot([lx], [ly], marker="+", ms=14, mew=1.5, color="black")
                ax.annotate(txt, (lx, ly), textcoords="offset points",
                            xytext=(6, -12 if ly > AY0 + 10 else 8),
                            fontsize=8, style="italic")
        ax.set_aspect("equal")
        ax.set_xlim(AX0, AX1); ax.set_ylim(AY0, AY1)
        ax.set_xticks(range(int(AX0), int(AX1) + 1, 20))
        ax.set_yticks(range(int(AY0), int(AY1) + 1, 20))
        ax.tick_params(labelsize=7)
        ax.grid(True, linewidth=0.3, alpha=0.3)
        fig.text(0.5, 0.975,
                 "Shim-Schablone %d von %d  —  %d Lagen Folie  (1:1 ausdrucken)"
                 % (nr, STUFEN, lage), ha="center", fontsize=12, weight="bold")
        fig.text(0.5, 0.945,
                 "Umrandete Flaeche %dx ausschneiden und aufeinander auf das "
                 "Hotbed legen (kleinste Flaeche zuunterst).\n"
                 "Ausschnitt X %.0f-%.0f, Y %.0f-%.0f mm — Blick von OBEN, "
                 "PEI-Platte abgenommen." % (STUFENHOEHE, AX0, AX1, AY0, AY1),
                 ha="center", fontsize=9)
        # Kontrollstrecke: 100 mm in Datenkoordinaten
        kx = AX0 + (AW - 100) / 2
        ax.annotate("", xy=(kx, AY0 - AH*0.055), xytext=(kx + 100, AY0 - AH*0.055),
                    xycoords="data", textcoords="data",
                    arrowprops=dict(arrowstyle="|-|", linewidth=1.0),
                    annotation_clip=False)
        ax.text(kx + 50, AY0 - AH*0.085, "Kontrollstrecke 100 mm — nachmessen!",
                ha="center", va="top", fontsize=8, clip_on=False)
        pdf.savefig(fig, bbox_inches=None); plt.close(fig)

print("geschrieben:", out)
print("Stufen: %d, maximal %.0f Lagen (%.2f mm)" % (STUFEN, noetig.max(),
                                                    noetig.max()*FOLIE/100))
