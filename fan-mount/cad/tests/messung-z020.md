# Erste Lage, gemessen — Testmuster bei z-Offset 0.20

Gemessen 2026-08-22, Werte in 1/100 mm, Sollhöhe der Lage 0,20 mm.
Ablesung hinten-links nach vorne-rechts.

```
            links ------------------> rechts
hinten      28    ·    ·   55    ·    ·   33
             ·   14    ·   50    ·   45    ·
             ·    ·   30   33   45    ·    ·
MITTE       43   45   35   30   34   45   48
             ·    ·   42   42   41    ·    ·
             ·   44    ·   46    ·   48    ·
vorn        46    ·    ·   50    ·    ·   48
```

## Qualitätseichung durch den Nutzer

Am gedruckten Teil beurteilt — damit werden aus Zahlen Urteile:

| Wert | Beurteilung |
|---|---|
| 14 | gequetscht, eindeutig zu dünn |
| **28** | **perfekt** |
| 30 | leicht zu hoch, Lücken zwischen den Linien |
| ab 40 | mehr oder weniger zerfetzt |

**Das gute Band reicht von 20 bis 28**, nicht nur bis zur theoretischen
Lagenhöhe 20 — der Nutzer beurteilt auch alle 20er-Werte des ersten
Tests als gut. Auf strukturiertem PEI muss das Material die Textur
füllen, deshalb liegt das Optimum über der Sollhöhe.

## Vergleich mit z-Offset 0.00

| | 0.00 | 0.20 |
|---|---|---|
| Minimum | 0 | 14 |
| Median | 18 | 44 |
| Nullstellen | 4 | 0 |
| Zentrum (r<40) | 10,0 | 34,8 |
| Rand (r>70) | 22,3 | 41,8 |
| Zentrum-Rand-Differenz | 12,3 | **7,0** |

**Die Senke war grösstenteils kein Bettverzug.** Wäre die Bettform starr,
müsste überall genau +20 dazukommen. Tatsächlich schwankt der Zuwachs
zwischen +7 und +33, und zwar systematisch: wo es tief war, wuchs es
stark (Korrelation Ausgangshöhe/Zuwachs r = -0,41). Wo die Düse zu tief
stand, kam schlicht kein Material heraus — das sah aus wie eine Senke.

Übrig bleibt ein einzelner echter Tiefpunkt bei x=55 y=195 (Wert 14).

## Folgerung für den Arbeitswert

Ein Offset-Schritt von 0,20 mm brachte im Mittel +24 Hundertstel,
der Median bei Offset 0 war 18:

| Ziel | Offset |
|---|---|
| 20 (unteres Bandende) | 0.02 |
| **24 (Bandmitte)** | **0.05** |
| 28 (oberes Bandende) | 0.08 |

**0.05** legt die Bandmitte auf den Median und lässt nach beiden Seiten
gleich viel Luft — deutlich unter dem bisher benutzten 0.15.

Bei Offset 0.00 lagen bereits **11 von 25 Punkten (44 %) im guten Band**;
4 Punkte hatten gar kein Material, 4 waren zu dünn, 5 knapp, 1 zu hoch.

Das verbleibende Problem ist nicht der Offset, sondern die **Streuung**:
bei einer Spanne von rund 20 Hundertsteln und einem guten Band von 8
Hundertsteln Breite passt nicht alles gleichzeitig hinein. Dafür ist die
mechanische Justage der drei Schrauben da.

## Nebenbefund: die Ziffern werden gedruckt

Im 0.20-Muster ist die "20" im Zentralring gut lesbar. Die frühere
Vermutung, kurze freistehende Bahnen könnten grundsätzlich nicht haften,
war falsch — beim 0.00-Muster fehlten sie schlicht, weil die Düse dort
zu tief stand. Eine Ersatzcodierung durch Striche wird nicht gebraucht.

## Nachtrag: Test bei 0.02 (2026-08-22, schwarzes PETG)

Das rechnerische Optimum 0.02 wurde gedruckt und vom Nutzer beurteilt:

 * die meisten Kreise haben **Lücken zwischen den Bahnen**,
 * vorne rechts und hinten Mitte sogar **unrunde Kreise** durch zu viel
   Abstand,
 * dagegen **schabte** die Stelle, die bei 0.20 den Wert 14 hatte
   (zweite Reihe von hinten, links), schon auf dem PEI — der Druck lief
   aber weiter.

**Fazit des Nutzers: 0.02 ist ein möglicher Kompromiss für grosse Teile,
aber nicht wirklich gut.** Der einzige Kreis, der ohne Abstriche gut
aussieht, ist der mit **23** (vorne links).

### Die Messwerte widerlegen die Prognose — anderes Filament

Gemessen (schwarzes PETG):

```
            links ------------------> rechts
hinten      26    ·    ·   50    ·    ·   39
             ·    9    ·   44    ·   35    ·
             ·    ·   26   27   34    ·    ·
MITTE       35   34   27   31   34   49   39
             ·    ·   33   28   35    ·    ·
             ·   41    ·   36    ·   39    ·
vorn        23    ·    ·   40    ·    ·   40
```

| | 0.00 weiss | 0.02 **schwarz** | 0.20 weiss |
|---|---|---|---|
| Median | 18 | **35** | 44 |
| gut (20-29) | 11 | 6 | 1 |
| >= 30 sichtbar | 1 | **18** | 23 |

Prognostiziert war für 0.02 ein Median von 21, gemessen sind **35** — der
Druck verhält sich, als wäre er mit Offset **0.136** entstanden.

**Ursache: es ist ein anderes Filament.** Schwarzes statt weisses PETG,
gleiche Firma und gleicher Typ, aber offenbar nicht gleiches
Fliessverhalten. Damit sind die drei Messreihen **nicht direkt
vergleichbar**, und die aus zwei Weiss-Messungen abgeleitete Steigung
gilt für Schwarz nicht.

Auch die Qualitätseichung verschiebt sich: bei Weiss war **28** perfekt,
bei Schwarz ist es **23**.

Lehre: eine Offset-Kalibrierung gilt **pro Filament**, nicht pro Drucker.
Beim Materialwechsel neu bestimmen, auch wenn Hersteller und Typ
übereinstimmen.

Damit ist die zentrale Aussage dieser Messreihe: **bei der derzeitigen
Bettstreuung lässt sich ein grosses Objekt nicht mit einwandfreiem Boden
drucken.** Die Spanne von rund 20 Hundertsteln ist breiter als das
brauchbare Fenster — an einem Ende schabt die Düse, am anderen klaffen
Lücken. Ein Offset verschiebt nur, wo das Problem auftritt, er löst es
nicht. Der Weg führt über die mechanische Justage.

Kleine Teile in der Plattenmitte sind davon nicht betroffen: dort ist
die lokale Streuung klein.
