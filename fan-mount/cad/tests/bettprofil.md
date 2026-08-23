# Plattenprofil — die bisher zuverlässigste Messung

Gemessen 2026-08-23, schwarzes PETG, Muster `bedtest2`.

## Verfahren

Anders als bei den früheren Messreihen wurde **nicht** je Offset die
ganze Platte vermessen. Statt dessen liefert jeder Punkt genau **einen**
Wert: den aus dem Druck, bei dem der Kreis gut aussah, zusammen mit dem
Offset dieses Drucks.

    Betthöhe = Offset - Schichtdicke

Herleitung: die Schichtdicke ist der Spalt zwischen Düse und Bett, also
`Dicke = (Nennhöhe + Offset) - Betthöhe`. Nach der Betthöhe aufgelöst
fällt die konstante Nennhöhe weg.

Ein Punkt, der erst bei +0.05 gut kam, brauchte eine höher stehende Düse
— dort liegt das Bett also **tief**.

> **Korrektur 2026-08-23:** Hier stand zunächst `Dicke - Offset`, also
> das falsche Vorzeichen. Alle daraus erzeugten Karten und Schablonen
> waren punktgespiegelt. Der Nutzer bemerkte es daran, dass die Karte
> hinten links eine Senke zeigte, obwohl dort die Düse zu nah war.

Damit gehen **nur zuverlässig messbare Werte** ein. Die früheren Karten
enthielten Nullstellen und zerfetzte Bereiche, deren Werte nicht
reproduzierbar waren.

## Genauigkeit

Vier Punkte kamen bei zwei verschiedenen Offsets gut heraus. Ihre daraus
berechneten Bettlagen müssen übereinstimmen — eine unabhängige Probe auf
das Verfahren:

| Punkt | Messung 1 | Messung 2 | Lagen | Differenz |
|---|---|---|---|---|
| (4,1) | 23 @ -0.10 | 28 @ -0.05 | 33 / 33 | **0** |
| (1,4) | 25 @ -0.10 | 28 @ -0.05 | 35 / 33 | 2 |
| (2,4) | 21 @ -0.10 | 25 @ -0.05 | 31 / 30 | 1 |
| (4,5) | 20 @ -0.05 | 25 @ 0.00 | 25 / 25 | **0** |

Mittlere Abweichung **0,8 Hundertstel**. Zum Vergleich: die frühere
Methode streute je Punkt um 16 Hundertstel — das neue Verfahren ist
rund zwanzigmal genauer.

## Ergebnis

```
        Spalte 1    2    3    4    5    6    7
  Zeile 1   +11              -3             +2
  Zeile 2        +12         -2        -3
  Zeile 3              +9  +12   +5
  Zeile 4     -5   -1  +12  +14   +4   -3   -6
  Zeile 5               +0   +5   +1
  Zeile 6         +0        -6        -5
  Zeile 7     +2            -10             -4
```

Positiv heißt: das Bett liegt dort **hoch**, die Düse kommt ihm zu nahe.

 * **Spanne 24 Hundertstel** (-10 bis +14)
 * Höchste Zone: die Mitte und der Bereich dahinter-links,
   (4,4) = +14, (4,3), (3,4) und (2,2) = +12, (1,1) = +11
 * Tiefste Stellen: vorn Mitte (4,7) = -10 und (4,6) = -6,
   dazu die rechte Seite (7,4) = -6 und (6,6) = -5

Die Form ist eine **Beule, die sich diagonal von der Mitte nach
hinten-links zieht**, mit abfallenden Rändern vorn und rechts.

## Für die Justage

Eine Ausgleichsebene durch alle 25 Punkte reduziert die Spanne nur von
24 auf 23 Hundertstel — die **Kippung macht 6 % aus**. Die drei
Schrauben unter dem Bett können also praktisch nichts ausrichten; das
Bett ist nicht schief, sondern verzogen.

Das bestätigt den früheren Befund (damals 7 %) mit deutlich besseren
Daten und stützt den Shimming-Ansatz.

## Praktische Folgerung

Der Nutzer beobachtete, dass alle guten Kreise zwischen Offset -0.05 und
+0.05 lagen, also in einem Bereich von 15 Hundertsteln. Die gemessene
Spanne von 24 liegt etwas darüber, weil auch die Randwerte -0.10 und
+0.05 einzelne gute Kreise lieferten.

Mit einem Offset in der Mitte des Bandes bleibt das Bett etwa
±12 Hundertstel um den Zielwert. Das ist deutlich besser als die frühere
Schätzung von 33 Hundertsteln, reicht für ein grosses Teil mit perfektem
Boden aber noch nicht aus.
