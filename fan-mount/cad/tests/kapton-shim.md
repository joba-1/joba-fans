# Kapton-Shims unter der PEI-Platte

> **Korrektur 2026-08-23:** Die erste Fassung beruhte auf einem
> Vorzeichenfehler im Profil und war punktgespiegelt — das Band wäre
> auf die Beule statt in die Senke gekommen. Schwellen und Flächen sind
> neu gerechnet.

## Warum Kapton, nicht Alufolie

An den tiefen Stellen liegt die Platte ohnehin **nicht auf** — dort ist
ein Luftspalt. Kapton füllt also einen Isolator, statt einen Wärmeleiter
zu ersetzen:

| Füllung des Spalts (0,18 mm) | Wärmeleitfähigkeit | Temperaturabfall |
|---|---|---|
| Luft (Ist-Zustand) | 0,026 W/(m·K) | ~11 K |
| **Kapton** | 0,12 W/(m·K) | **~2 K** |
| Alufolie | 237 W/(m·K) | ~0 K |

Kapton verbessert die Wärmeleitung an diesen Stellen also um etwa das
Fünffache. Die verbleibenden 2 K liegen innerhalb der normalen
Regelschwankung des Betts; Alufolie wäre thermisch besser, hält aber
nicht von selbst.

*(Der Temperaturabfall ist mit 25 % der Heizleistung als Verlustleistung
gerechnet — die Größenordnung stimmt, nicht die zweite Stelle.)*

## Stufen

Kapton trägt **0,06 mm** je Bahn auf. Damit sind drei Lagen nötig:

| Lage | Bereich unter | Fläche | Ausdehnung |
|---|---|---|---|
| 1 | +8/100 mm | | |
| 2 | +2/100 mm | | |
| 3 | −4/100 mm | | |

**Restspanne danach: 6 statt 24 Hundertstel.**

Jede Lage ist **eine** Bahn dick — anders als beim frueheren
Alufolien-Entwurf, wo dieselbe Form mehrfach gestapelt werden musste
(bis zu 22 Lagen a 0,01 mm). Die Stufen entstehen hier dadurch, dass
die drei Flaechen ineinanderliegen:

| Ort | liegt in | Gesamtauftrag |
|---|---|---|
| aeusserer Rand | keiner | 0 mm |
| unter +8 | Lage 1 | 0,06 mm |
| unter +2 | Lage 1+2 | 0,12 mm |
| unter −4 | Lage 1+2+3 | 0,18 mm |

Reihenfolge: Lage 1 zuerst direkt aufs Hotbed, dann die jeweils
kleinere Flaeche darauf.

Zwei Lagen kämen nur auf 12 und würden das Ziel von 10 verfehlen.

## Bahnen

| Bandbreite | Lage 1 | Lage 2 | Lage 3 | gesamt |
|---|---|---|---|---|
| 40 mm | 7 | 5 | 4 | 16 Bahnen |
| 20 mm | 13 | 9 | 7 | 29 Bahnen |

Die Bahnen werden mit **0,5 mm Lücke** verlegt, nicht auf Stoß:
überlappt das Band, trägt es dort doppelt auf und macht die Stelle
schlimmer als vorher. Eine schmale Lücke ist dagegen harmlos, weil das
PEI-Blech darüber Sprünge weitgehend ausgleicht.

## Ausdrucke

`kapton-schablonen-40mm.pdf` und `kapton-schablonen-20mm.pdf`:
Seite 1 Übersicht mit Profil und Stufengrenzen, danach je Stufe eine
Seite mit Umriss und Bahngrenzen.

**Die Seiten sind verkleinert** (Maßstab etwa 1:1,344) — 250 mm passen
nicht 1:1 auf A4. Jede Seite trägt eine Kontrollstrecke mit dem
umgerechneten Maß zum Nachmessen.
