# CAD — Passproben (test frames)

## Was hier liegt

| Datei | Inhalt |
|---|---|
| `lochblech.csv` | Gemessene Lochblech-Geometrie der drei Heizkörper. Quelle der Wahrheit. |
| `passprobe.FCStd` | FreeCAD-Dokument mit Tabelle `Masse` und den drei Rahmen. |
| `passprobe_A.stl` … `_C.stl` | Druckfertige Passproben. |

## Zweck der Passprobe

Kein Funktionsteil. Sie beantwortet vier Fragen in einem Druck:

1. Stimmt die gemessene Tiefe?
2. Greift der **Randumgriff** (edge grip) über die Blechkante, oder endet
   das Gitter in einer Sicke / einem Seitenblech, wo keine freie Kante ist?
3. Ist die **Maulweite** (jaw opening) richtig — klemmt es, oder wackelt es?
4. Wie stark verzieht der Schrumpf die Breite über 141 mm (Teil C)?

## Aufbau des Teils

Querschnitt, quer zur Wand:

```
        ┌───────────────────────────────┐   Grundplatte 3 mm
        │                               │
        █ ▁▁                       ▁▁ █     Maul 1,4 mm = Blech 1,0 + Spiel 0,4
        █ ██                       ██ █     Nase 1,5 mm greift unter das Blech
        └──┘                       └──┘     Backe 2,5 mm, außen
          ↑                         ↑
          └──── Blechtiefe (65/101/136) ────┘
```

Das Teil wird **von vorne auf die Blechkante geschoben**. Die Mitte unter
dem Blech ist frei — es klemmt nur an den beiden Rändern.

## Annahmen, die beim Anhalten zu prüfen sind

| Annahme | Wert | Wenn falsch |
|---|---|---|
| Blechdicke | 1,0 mm | `blechdicke` in der Tabelle ändern |
| Freie Blechkante vorhanden | ja | Randumgriff scheitert → Zapfenprinzip nötig |
| Backentiefe reicht | 6 mm | `backentiefe` ändern |

## Neu erzeugen

Maß in `lochblech.csv` und in der Tabelle `Masse` ändern, dann
`scripts/passprobe.py` in FreeCAD ausführen. Die Tiefe ist **abgeleitet**
(Summe der Teilstücke) — weicht sie von der Messung ab, zeigt Spalte E der
Tabelle die Differenz, statt sie stillschweigend zu verteilen.

## Druckhinweise

PLA, 0,2 mm Schicht, 3 Perimeter. Liegend drucken (Grundplatte auf dem Bett,
Nasen nach oben) — dann braucht keine Stützstruktur ins Maul. Zusammen
~60 cm³, gut 3 Stunden.

---

## Halter A (Passprobe + Zarge)

`halter_A.stl` — Klammer und **Zarge** (Lüfteraufnahme) in einem Teil, für
einen 25-mm-Lüfter. Der Lüfter fällt hinein und liegt auf vier Auflageecken
von 2 mm; unter ihm ist **kein Boden**, er bläst direkt aufs Blech. Eine
Grundplatte mit Durchlass wäre eine Drosselstelle unmittelbar an der
Druckseite — genau dort, wo ein Axiallüfter am empfindlichsten ist.

### Rippen statt Boden

Zarge und Klammer sind durch **zwei Rippen** verbunden, die auf den
ungelochten Randstreifen (13 mm bei A) sitzen. Ein durchgehender Steg ueber
die volle Blechtiefe verdeckte in der ersten Fassung **64 % des
Luefteraustritts** — und zwar genau den Teil ueber dem Lochfeld, also den
einzigen, der etwas nuetzt. Mit Rippen sind es 25 %, alles davon Zargenwand
und Auflageecken am Rand; **ueber dem Lochfeld ist es zu 100 % offen**.

Die Pruefung `Lochfeld offen` im Skript testet das an 99 Punkten. Sie fehlte
zunaechst, weshalb der Boden erst am Bild auffiel.

### Asymmetrischer Sitz

Ein 120-mm-Lüfter auf 65 mm Blechtiefe steht 55 mm über. Bei nur ~25 mm
Wandabstand muss er nach vorne ausweichen:

| | mm |
|---|---|
| Überstand gesamt | 55 |
| davon nach hinten (Wandseite) | 17 |
| davon nach vorne (in den Raum) | 38 |
| Luft zur Wand | 5 |

Die Tabelle rechnet das selbst aus (`a_hinten = wandabstand − wandluft −
z_dicke`). Ändert sich der Wandabstand, wandert der Lüfter mit.

### Bauhöhe

Auflage 2 mm + Lüfter 25 mm = 27 mm. Bei ~55 mm Freiraum im Büro bleiben
**28 mm Ansaugraum** — knapp unter den ~30 mm, die ein 120-mm-Lüfter gern
hätte, aber brauchbar. Wird es zu laut, sind 15-mm-Slim-Lüfter der Hebel;
`luefterhoehe` in der Tabelle ändern, neu erzeugen.

### Drucklage

`halter_A.stl` wird **flach gedruckt, ohne Drehen und ohne Sonderflags** —
das Teil endet bei z=0 und jede Fläche wird von unten getragen.

```
kobra-slice halter_A.stl -o /tmp/halter_A.gcode \
    --filament "Amazon Basics PLA" --layer 0.2 --max-speed 60 --timelapse 0
```

60 Lagen, 1 h 19 min, 23 g. Fertiger Gcode liegt auf job6 unter
`~/halter_A.gcode` (PLA schwarz, Slot 3).

### Befestigung

Der Halter **liegt lose auf** dem Blech. Der ursprüngliche Randumgriff
(Backen und Nasen unterhalb z=0) ist entfernt: er machte das Teil
druckunfreundlich, und die Befestigung übernimmt ein eigenes zweites Teil.

### Mögliche Nebenwirkung

Der Lüfter liegt über die Auflageecken am Blech an und überträgt Vibration
in ein großes dünnes Blech. Wenn es brummt: `z_auflage` erhöhen und einen
Streifen Moosgummi unterlegen.

---

## Druckbarkeit

Geprueft an der gedrehten Drucklage (`halter_A_gedreht.stl`). Massgeblich ist
nicht die **Flaeche** eines Ueberhangs, sondern seine **Spannweite** — und ob
er frei in der Luft beginnt oder als Bruecke zwischen zwei Waenden spannt.

| Stelle | z | Spannweite | Art |
|---|---|---|---|
| Rippen (2×) | 10,0 mm | **12 mm** | Bruecke zwischen den Zargenwaenden |
| Auflageecken (4×) | 10,0 mm | **14 mm** | haengen an der Zargenwand |
| Klammernasen (2×) | 13,4 mm | **2 mm** | Bruecke |

Alle unter der 20-mm-Grenze, alle beidseitig angebunden. **Kein
Stuetzmaterial noetig**, keine Flaeche beginnt frei in der Luft.

### Warum einteilig

Eine zweiteilige Variante (Zarge + aufschiebbare Klammern mit
Schwalbenschwanz) wurde durchgerechnet und wieder verworfen. Der Grund ist
strukturell: die Zarge ist 127 mm breit, das Blech nur 65 mm. Jede Verbindung
zwischen beiden ueberbrueckt 31 mm je Seite — die Bruecke verschwindet nicht,
sie wandert nur. Getrennte Teile brachten in Summe **mehr** Ueberhang
(2538 mm² statt 4179 mm² bei groesserer Spannweite) und zusaetzlich eine
Fuegestelle.

Einteilig bleibt es, solange die Spannweiten unter 20 mm liegen. Wuerde die
Zarge einmal deutlich hoeher (dickerer Luefter), sind die Rippen die Stelle,
die zuerst kritisch wird.
