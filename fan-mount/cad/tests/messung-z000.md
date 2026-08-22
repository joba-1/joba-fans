# Erste Lage, gemessen — Testmuster bei z-Offset 0.00

Gemessen 2026-08-22 mit Messschieber am gedruckten Muster
(`bedtest_z+0.00`, 225 mm, eine Lage, Sollhöhe 0,20 mm).
Werte in 1/100 mm, Ablesung hinten-links nach vorne-rechts.

```
            links ------------------> rechts
hinten       0    ·    ·   24    ·    ·   17
             ·    7    ·   24    ·   25    ·
             ·    ·    0    0   18    ·    ·
MITTE       28   24    9    0   11   28   30
             ·    ·   14   10   17    ·    ·
             ·   24    ·   22    ·   26    ·
vorn        18    ·    ·   22    ·    ·   24
```

## Auswertung

| Zone | Mittelwert |
|---|---|
| Zentrum (r < 40 mm) | **10** |
| Rand (r > 70 mm) | **22** |
| links (x < 125) | 18 |
| rechts (x > 125) | 22 |

Vier Kreise um die Plattenmitte kamen mit **0** heraus — dort steht die
Düse so tief, dass gar kein Material austritt; sie liessen sich nicht
ablösen und nicht messen. Die Randmitten erreichen dagegen 28–30, also
*über* dem Sollwert.

**Das Bett hat eine Delle in der Mitte, keine Kuppel.** Die frühere
gegenteilige Annahme stammte von einem 132 mm breiten Teil, das den
echten Plattenrand nie erreicht hat.

Folge für die Justage: Die drei Schrauben unter dem Bett können die
leichte Schräglage nach links beheben, **nicht aber die Delle** — drei
Punkte definieren eine Ebene, keine Wölbung. Dagegen hilft Unterlegen
in der Mitte, oder ein Offset hoch genug, dass die Mitte noch trägt.

Der Wert 0 bei hinten-links (x=22, y=228) passt nicht ins Bild — die
Nachbarn dort liegen bei 24, 7 und 24. Vermutlich lokale Verschmutzung
oder ein Ablösefehler, nicht die Bettform.
