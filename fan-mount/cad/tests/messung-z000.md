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

**Das Bett hat eine Senke, keine Kuppel.** Die frühere gegenteilige
Annahme stammte von einem 132 mm breiten Teil, das den echten
Plattenrand nie erreicht hat.

Die Farbkarte (`bettkarte-z000.png`, erzeugt mit
`scripts/bettkarte.py`) zeigt die Form deutlicher als die Tabelle: es
ist **keine zentrierte Delle, sondern eine diagonale Senke** von
hinten-links über die Mitte nach vorn. Die Tiefpunkte liegen bei
90/160, 125/160 und 125/125, also gegenüber der Plattenmitte nach
hinten-links versetzt. Der Wert 0 bei hinten-links (x=22, y=228) ist
damit **kein Ausreisser**, sondern das Ende derselben Senke — die 7
direkt daneben stützt das.

Die Hochpunkte bilden das Gegenstück: rechts aussen (194/125 = 28,
228/125 = 30), links aussen (22/125 = 28) und vorn rechts
(194/56 = 26). Der gesamte vordere Rand liegt im Sollbereich.

Folge für die Justage: Eine diagonale Senke hat eine **Kipp-Komponente**,
und Kippen können die drei Schrauben unter dem Bett — die Achse verläuft
etwa hinten-links nach vorn-rechts. Ob danach ein Restverzug bleibt, den
nur Unterlegen behebt, zeigt erst die Messung nach dem Nachstellen.
