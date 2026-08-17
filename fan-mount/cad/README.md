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

**`halter_A_gedreht.stl` ist die Druckdatei**, nicht `halter_A.stl`. Auf den
Kopf gedreht liegt die Zargenoberseite auf dem Bett, die Klammernasen zeigen
nach oben und werden getragen. In der Konstruktionslage hingen sie in der
Luft und bräuchten Stützmaterial.

Mit `--no-orient` slicen — der Auto-Orienter stellt das Teil sonst hochkant
(126 mm hoch, 633 Lagen statt 74).

```
kobra-slice halter_A_gedreht.stl -o /tmp/halter_A.gcode \
    --filament "Amazon Basics PLA" --layer 0.2 --max-speed 60 \
    --timelapse 0 --no-orient
```

74 Lagen, 1 h 57 min, 36 g. Fertiger Gcode liegt auf job6 unter
`~/halter_A.gcode` (PLA schwarz, Slot 3).

### Vor dem Druck zu prüfen

Die Klammer setzt eine **freie Blechkante** voraus. Geht das Gitter vorne
oder hinten in eine Sicke oder ein Seitenblech über, greift die Backe ins
Leere — dann wäre das Zapfenprinzip nötig, wofür die Schlitzlänge fehlt.
Die kleine Passprobe `passprobe_A.stl` klärt das in 45 min statt in 2 h.

### Mögliche Nebenwirkung

Der Lüfter liegt über die Auflageecken am Blech an und überträgt Vibration
in ein großes dünnes Blech. Wenn es brummt: `z_auflage` erhöhen und einen
Streifen Moosgummi unterlegen.
