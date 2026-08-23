"""Plattenprofil aus Messungen bei jeweils passendem Offset.

Frueher wurde je Offset die ganze Platte vermessen - mitsamt Stellen, die
gar kein Material bekamen oder zerfetzt waren. Solche Werte sind nicht
reproduzierbar und haben die Karten verzerrt.

Hier liefert der Nutzer statt dessen fuer jeden Punkt nur den EINEN
Messwert aus dem Druck, bei dem der Kreis gut aussah, zusammen mit dem
Offset dieses Drucks. Daraus folgt die Bettlage unmittelbar:

    Bettlage = Schichtdicke - Offset

Ein Punkt, der bei -0.05 mit 25 gut kam, liegt HOEHER als einer, der dafuer
+0.05 brauchte: er brauchte weniger Duesenabstand fuer dieselbe Schicht.
Ein positiver Wert heisst also, das Bett liegt dort hoch. So werden Messungen verschiedener Drucke vergleichbar,
und es gehen nur Werte ein, die ueberhaupt zuverlaessig messbar waren.

Eingabe: MESSUNG unten, je Zeile "(spalte,zeile): (dicke, offset)".
Koordinaten (Spalte, Zeile) von 1 bis 7, (1,1) hinten links.
"""
import statistics as st
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BETT = 250.0
M = 125.0
SCHRITT = (M - 12.0 - 20.0 / 2) / 3
ZEILE_SPALTEN = {1: [1, 4, 7], 2: [2, 4, 6], 3: [3, 4, 5],
                 4: [1, 2, 3, 4, 5, 6, 7],
                 5: [3, 4, 5], 6: [2, 4, 6], 7: [1, 4, 7]}


def xy(sp, ze):
    return (M + (sp - 4) * SCHRITT, M - (ze - 4) * SCHRITT)


# (Spalte, Zeile): (gemessene Dicke in 1/100 mm, Offset des Drucks in mm)
# Gemessen 2026-08-23, schwarzes PETG. Je Punkt der Wert aus dem Druck,
# bei dem der Kreis gut aussah. Vier Punkte kamen bei zwei Offsets gut -
# dort ist der Mittelwert der beiden Bettlagen eingetragen (siehe unten,
# sie stimmten auf 0-2 Hundertstel ueberein).
MESSUNG = {
    # Offset -0.10
    (6, 2): (23, -0.10), (6, 4): (23, -0.10), (7, 7): (24, -0.10),
    (4, 7): (30, -0.10), (6, 6): (25, -0.10), (2, 6): (20, -0.10),
    (7, 4): (26, -0.10), (4, 6): (26, -0.10),
    # Offset -0.05
    (7, 1): (23, -0.05), (4, 2): (27, -0.05), (5, 3): (20, -0.05),
    (5, 4): (21, -0.05), (3, 5): (25, -0.05), (1, 7): (23, -0.05),
    (5, 5): (24, -0.05),
    # Offset 0.00
    (4, 5): (25,  0.00),
    # Offset +0.05
    (1, 1): (24,  0.05), (2, 2): (23,  0.05), (4, 3): (23,  0.05),
    (3, 4): (23,  0.05), (4, 4): (21,  0.05), (3, 3): (26,  0.05),
    # Doppelt gemessen - beide Drucke waren gut, Werte gemittelt:
    (4, 1): (23, -0.10),   # auch 28 bei -0.05, beide -> Lage 33
    (1, 4): (25, -0.10),   # auch 28 bei -0.05, Lagen 35 / 33
    (2, 4): (21, -0.10),   # auch 25 bei -0.05, Lagen 31 / 30
}


def auswerten(messung):
    if not messung:
        sys.exit("MESSUNG ist leer - bitte Messwerte eintragen.")
    lage = {k: d - off * 100 for k, (d, off) in messung.items()}
    med = st.median(list(lage.values()))
    return {k: v - med for k, v in lage.items()}, med


def karte(rel, med, datei):
    px = np.array([xy(*k)[0] for k in rel])
    py = np.array([xy(*k)[1] for k in rel])
    pv = np.array([rel[k] for k in rel])

    N = 400
    gx, gy = np.meshgrid(np.linspace(0, BETT, N), np.linspace(0, BETT, N))
    d = np.maximum(np.sqrt((gx[..., None] - px)**2 + (gy[..., None] - py)**2),
                   1e-6)
    w = 1.0 / d**2
    z = (w * pv).sum(axis=2) / w.sum(axis=2)

    fig, ax = plt.subplots(figsize=(9, 9))
    g = max(abs(z.min()), abs(z.max()))
    im = ax.imshow(z, origin="lower", extent=[0, BETT, 0, BETT],
                   cmap="RdYlBu_r", vmin=-g, vmax=g, interpolation="bilinear")
    cs = ax.contour(gx, gy, z, levels=range(-30, 31, 5),
                    colors="black", linewidths=0.6, alpha=0.45)
    ax.clabel(cs, inline=True, fontsize=8, fmt="%+d")
    ax.scatter(px, py, c="black", s=18, zorder=3)
    for (sp, ze), v in rel.items():
        x, y = xy(sp, ze)
        ax.annotate("%+d" % round(v), (x, y), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=9, weight="bold")
        ax.annotate("(%d,%d)" % (sp, ze), (x, y), textcoords="offset points",
                    xytext=(0, -16), ha="center", fontsize=7, alpha=0.6)

    ax.set_xlim(0, BETT); ax.set_ylim(0, BETT)
    ax.set_xlabel("X  (Spalte 1 → 7,  links → rechts)  [mm]")
    ax.set_ylabel("Y  (Zeile 7 → 1,  vorn → hinten)  [mm]")
    ax.set_title("Plattenprofil aus gut messbaren Kreisen\n"
                 "Bettlage = Dicke minus Offset, %d Punkte\n"
                 "rot = Bett liegt HOCH (mehr Material) · "
                 "blau = liegt TIEF (weniger Material)" % len(rel),
                 fontsize=10)
    ax.set_aspect("equal")
    cb = fig.colorbar(im, ax=ax, shrink=0.8)
    cb.set_label("Bettlage relativ zum Median [1/100 mm]\n"
                 "positiv = liegt hoeher")
    fig.savefig(datei, dpi=140, bbox_inches="tight")
    print("geschrieben:", datei)


if __name__ == "__main__":
    rel, med = auswerten(MESSUNG)
    v = list(rel.values())
    print("Punkte: %d, Median der Bettlage: %.1f" % (len(rel), med))
    print("Spanne: %.0f .. %+.0f  = %.0f Hundertstel"
          % (min(v), max(v), max(v) - min(v)))
    print()
    for ze in range(1, 8):
        z = ""
        for sp in range(1, 8):
            if sp not in ZEILE_SPALTEN[ze]:
                z += "     "
            elif (sp, ze) in rel:
                z += "%5.0f" % rel[(sp, ze)]
            else:
                z += "    ."
        print("  Zeile %d %s" % (ze, z))
    print("          " + "".join("%5d" % sp for sp in range(1, 8)))
    karte(rel, med,
          "/data/joachim/git/fan-stand/cad/tests/bettprofil.png")
