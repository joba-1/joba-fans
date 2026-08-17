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
