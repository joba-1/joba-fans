"""Klebeschablonen fuer Kapton-Shims unter der PEI-Platte.

Aus dem gemessenen Plattenprofil werden Hoehenstufen abgeleitet und je
Stufe eine massstabsgetreue Vorlage gezeichnet: die Umrisslinie der
Flaeche plus die Bahnen des Klebebands, damit beim Verlegen klar ist,
wo die Stoesse liegen.

Warum Kapton und nicht Alufolie: an den tiefen Stellen liegt die Platte
ohnehin nicht auf - dort ist ein Luftspalt. Luft leitet mit 0,026
W/(m*K) rund fuenfmal schlechter als Kapton mit 0,12. Das Band fuellt
also einen Isolator, statt einen Waermeleiter zu ersetzen: der
Temperaturabfall an diesen Stellen sinkt von grob 10 K auf 2 K. Alu
waere thermisch noch besser, haelt aber nicht von selbst.

Die Bahnen werden mit LUECKE Abstand gezeichnet, nicht auf Stoss:
ueberlappt das Band, traegt es dort doppelt auf und macht die Stelle
schlimmer als vorher. Eine schmale Luecke ist harmlos.

    python3 kapton_schablone.py [bandbreite_mm]
"""
import statistics as st
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mp

BETT = 250.0
M = 125.0
SCHRITT = (M - 12.0 - 20.0 / 2) / 3
DICKE = 6.0             # Hundertstel mm je Bahn Kapton
LUECKE = 0.5            # mm Abstand zwischen zwei Bahnen
SCHWELLEN = (4, -2, -8)  # Stufengrenzen, ermittelt fuer DICKE=6

# Plattenprofil: (Spalte, Zeile) -> (gemessene Dicke, Offset des Drucks)
MESSUNG = {
    (6, 2): (23, -0.10), (6, 4): (23, -0.10), (7, 7): (24, -0.10),
    (4, 7): (30, -0.10), (6, 6): (25, -0.10), (2, 6): (20, -0.10),
    (7, 4): (26, -0.10), (4, 6): (26, -0.10), (4, 1): (23, -0.10),
    (1, 4): (25, -0.10), (2, 4): (21, -0.10),
    (7, 1): (23, -0.05), (4, 2): (27, -0.05), (5, 3): (20, -0.05),
    (5, 4): (21, -0.05), (3, 5): (25, -0.05), (1, 7): (23, -0.05),
    (5, 5): (24, -0.05),
    (4, 5): (25, 0.00),
    (1, 1): (24, 0.05), (2, 2): (23, 0.05), (4, 3): (23, 0.05),
    (3, 4): (23, 0.05), (4, 4): (21, 0.05), (3, 3): (26, 0.05),
}


def xy(sp, ze):
    return (M + (sp - 4) * SCHRITT, M - (ze - 4) * SCHRITT)


def profil(n=600):
    lage = {k: d - o * 100 for k, (d, o) in MESSUNG.items()}
    med = st.median(lage.values())
    rel = {k: v - med for k, v in lage.items()}
    px = np.array([xy(*k)[0] for k in rel])
    py = np.array([xy(*k)[1] for k in rel])
    pv = np.array([rel[k] for k in rel])
    gx, gy = np.meshgrid(np.linspace(0, BETT, n), np.linspace(0, BETT, n))
    d = np.maximum(np.sqrt((gx[..., None] - px)**2 + (gy[..., None] - py)**2),
                   1e-6)
    w = 1.0 / d**2
    return gx, gy, (w * pv).sum(axis=2) / w.sum(axis=2), rel


def zeichne(ax, gx, gy, z, schwelle, band, nr, gesamt):
    m = z < schwelle
    ax.contourf(gx, gy, m.astype(float), levels=[0.5, 1.5], colors=["#00000018"])
    ax.contour(gx, gy, z, levels=[schwelle], colors="black", linewidths=1.8)

    # Bahnen: waagrecht, von unten nach oben, mit Luecke dazwischen
    y = 0.0
    n = 0
    while y < BETT:
        ax.add_patch(mp.Rectangle((0, y), BETT, band, fill=False,
                                  edgecolor="#c02020", linewidth=0.5,
                                  linestyle=(0, (4, 3))))
        n += 1
        y += band + LUECKE
    ax.plot([0, BETT, BETT, 0, 0], [0, 0, BETT, BETT, 0],
            color="black", linewidth=1.0)
    ax.plot([0], [BETT], marker="+", ms=14, mew=1.5, color="black")
    ax.annotate("Ecke hinten links", (0, BETT), textcoords="offset points",
                xytext=(6, -12), fontsize=8, style="italic")
    ax.set_xlim(0, BETT); ax.set_ylim(0, BETT)
    ax.set_xticks(range(0, 251, 50)); ax.set_yticks(range(0, 251, 50))
    ax.tick_params(labelsize=7)
    ax.set_aspect("equal")
    return n, m


def main(band=40.0):
    gx, gy, z, rel = profil()
    out = "/data/joachim/git/fan-stand/cad/tests/kapton-schablonen-%dmm.pdf" % band
    with PdfPages(out) as pdf:
        # Uebersicht
        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_axes([0.13, 0.34, 0.72, 0.44])
        im = ax.contourf(gx, gy, z, levels=20, cmap="RdYlBu_r")
        ax.contour(gx, gy, z, levels=sorted(SCHWELLEN), colors="black",
                   linewidths=1.5)
        for (sp, ze), v in rel.items():
            x, y = xy(sp, ze)
            ax.annotate("%+d" % round(v), (x, y), ha="center",
                        fontsize=7, weight="bold")
        ax.set_aspect("equal"); ax.set_xlim(0, BETT); ax.set_ylim(0, BETT)
        ax.set_title("Plattenprofil und Stufengrenzen\n"
                     "Blick von OBEN auf das Hotbed, PEI-Platte abgenommen",
                     fontsize=11)
        ax.set_xlabel("X [mm]  links → rechts")
        ax.set_ylabel("Y [mm]  vorn → hinten")
        fig.colorbar(im, ax=ax, shrink=0.6, label="Bettlage [1/100 mm]")
        korr = np.zeros_like(z)
        for i, s in enumerate(SCHWELLEN, start=1):
            korr = np.where(z < s, i * DICKE, korr)
        neu = z + korr
        fig.text(0.5, 0.22,
                 "%d Lagen Kapton a %.2f mm, Band %.0f mm breit, %.1f mm Luecke\n"
                 "Spanne vorher %.0f, nachher %.0f Hundertstel mm"
                 % (len(SCHWELLEN), DICKE / 100, band, LUECKE,
                    z.max() - z.min(), neu.max() - neu.min()),
                 ha="center", fontsize=10)
        pdf.savefig(fig); plt.close(fig)

        # Je Stufe eine Seite, 1:1 auf A4 hoch
        # 250 mm passen nicht 1:1 auf A4 (210 mm breit). Statt die
        # Zeichnung abzuschneiden wird sie verkleinert und der Massstab
        # angeschrieben - die Kontrollstrecke unten macht ihn pruefbar.
        A4B, A4H = 210.0, 297.0
        RAND = 12.0
        BREITE = A4B - 2 * RAND
        MASSSTAB = BREITE / BETT
        for nr, s in enumerate(SCHWELLEN, start=1):
            fig = plt.figure(figsize=(A4B / 25.4, A4H / 25.4))
            ax = fig.add_axes([RAND / A4B, 40.0 / A4H,
                               BREITE / A4B, BREITE / A4H])
            n, m = zeichne(ax, gx, gy, z, s, band, nr, len(SCHWELLEN))
            fig.text(0.5, 0.965,
                     "Kapton-Lage %d von %d  —  Bereich unter %+d/100 mm"
                     % (nr, len(SCHWELLEN), s),
                     ha="center", fontsize=12, weight="bold")
            fig.text(0.5, 0.94,
                     "Graue Flaeche mit Band belegen. Rote Linien = Bahnen "
                     "%.0f mm mit %.1f mm Luecke.\n"
                     "NICHT ueberlappen - dort traegt es doppelt auf."
                     % (band, LUECKE), ha="center", fontsize=8)
            kx = (BETT - 100) / 2
            ax.annotate("", xy=(kx, -18), xytext=(kx + 100, -18),
                        annotation_clip=False,
                        arrowprops=dict(arrowstyle="|-|", linewidth=1.0))
            ax.text(kx + 50, -26,
                    "100 mm auf der Platte = %.1f mm auf dem Papier "
                    "(Massstab 1:%.3f) — nachmessen!"
                    % (100 * MASSSTAB, 1 / MASSSTAB),
                    ha="center", va="top", fontsize=8, clip_on=False)
            pdf.savefig(fig); plt.close(fig)
    print("geschrieben:", out)
    print("Restspanne nach %d Lagen: %.0f Hundertstel (vorher %.0f)"
          % (len(SCHWELLEN), neu.max() - neu.min(), z.max() - z.min()))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 40.0)
