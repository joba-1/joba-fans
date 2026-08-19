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
| davon nach hinten (Wandseite) | 14 |
| davon nach vorne (in den Raum) | 41 |
| Luft zur Wand | 8 |

`a_hinten = z_ecke` — der hintere Überstand ist an die Ecklänge der
Auflagen gekoppelt. Dadurch ist `rippe_dy = 0` und **beide Rippen liegen
vollständig auf den ungelochten Randstreifen** des Blechs, während die
vordere Auflage nahtlos in Rippe 1 übergeht.

Der Wandabstand ist damit nicht mehr die bestimmende Größe, sondern
Kontrollwert: `wandluft_ist = wandabstand − a_hinten − z_dicke` = 8 mm,
Vorgabe mindestens 5 mm. Wird der Halter für einen Heizkörper mit weniger
Wandabstand abgeleitet, ist diese Zelle die Stelle, an der es auffällt.

### Bauhöhe

Auflage 2 mm + Lüfter 25 mm = 27 mm. Bei ~55 mm Freiraum im Büro bleiben
**28 mm Ansaugraum** — knapp unter den ~30 mm, die ein 120-mm-Lüfter gern
hätte, aber brauchbar. Wird es zu laut, sind 15-mm-Slim-Lüfter der Hebel;
`luefterhoehe` in der Tabelle ändern, neu erzeugen.

### Drucklage

`halter_A.stl` wird **flach gedruckt, ohne Drehen und ohne Sonderflags** —
das Teil endet bei z=0 und jede Fläche wird von unten getragen.

**Material: weißes PETG** (Slot 2). PETG statt PLA, weil PLA schon bei etwa
60 °C erweicht und der Halter auf einem Heizkörper sitzt. Weiß passt zur
Farbe der Heizkörper.

```
kobra-slice halter_A_komplett.stl -o /tmp/halter_A.gcode \
    --filament "eSUN PETG" --layer 0.2 --max-speed 60 --timelapse 0
```

140 Lagen, 3 h 07 min, 60 g — Halter und beide Zapfen zusammen.
Düse 265 °C, Bett 75 °C.

### Zargenhöhe und Sichtschutz

`zarge_innen` = 26 mm **ab Lüfterauflage** gemessen, also `z_hoehe` = 28 mm
ab Blech. Die Lüfteroberkante liegt bei 2 + 25 = 27 mm — der schwarze Lüfter
verschwindet damit vollständig hinter der Zarge, mit 1 mm Überstand.

Mit `kanten_r` = 1,5 mm gebrochen sind: alle senkrechten Außenkanten, die
obere Umlaufkante der Zarge und die **drei freien Oberkanten je Blende**
(zwei Längsseiten, eine Stirnseite).

Die vierte Blendenkante — der Übergang zur Zarge — bekommt stattdessen eine
**Kehle** (`kehle_r` = 1,5 mm). Das ist eine *Innenkante*: die Rundung läuft
andersherum als an den Außenkanten und **fügt Material hinzu**, statt es
wegzunehmen. Sie versteift die 2 mm dünne Blende genau dort, wo sie an der
28 mm hohen Zargenwand hängt.

Die Kehle muss **nach** den Außenkanten gesetzt werden: die Längsrundungen
der Blende laufen sonst bis an den Übergang durch und fressen sie weg.

Preis dafür ist Ansaugraum. Bei einem 120-mm-Lüfter wären ~30 mm ideal:

| | Freiraum | über der Zarge |
|---|---|---|
| A — Büro | ~55 mm | 27 mm |
| B — Wohnzimmer | 100 mm | 72 mm |
| C — Esszimmer | 50 mm | **22 mm** |

Im Esszimmer wird es damit eng — der Lüfter wird dort lauter und liefert
weniger. Falls das stört, ist `zarge_innen` die Stellschraube. Fertiger Gcode liegt auf job6 unter
`~/halter_A.gcode` (PLA schwarz, Slot 3).

### Verschraubung

Vier Bohrungen **⌀6 mm** in den Auflageecken, Lochabstand **105 × 105 mm** —
das Normmaß für 120-mm-Lüfter (Lochmitte 7,5 mm von jeder Lüfterkante).

Der Bezug ist die Lüfterecke, nicht die Auflage: ändert sich `z_spiel` oder
die Lüfterlage, wandern die Löcher korrekt mit. Für andere Lüftergrößen ist
`schraub_lk` die Stellschraube (92 mm beim 92er, 71,5 mm beim 80er).

Zwischen Lochrand und Auflagekante bleiben **3,2 mm** stehen. Das ist dünn —
Lüfterschrauben sind normalerweise M4, für die ein 4,5-mm-Loch reichen würde
und 4,0 mm Steg bliebe. Bei ⌀6 hat eine M4-Schraube Spiel; mit Unterlegscheibe
oder Mutter von unten ist das kein Problem, für eine selbstschneidende
Verschraubung direkt ins PLA wäre 3,5 mm richtig.

### Blende gegen Kurzschlussströmung

Links und rechts schließen je **50 mm Bodenfläche** an (`blende_b`). Sie decken
die Nachbarschlitze ab, damit die Luft nicht durch sie zurück nach oben
kurzschließt, statt durch die Konvektorbleche nach unten zu gehen.

Die Blende reicht nur über die Blechtiefe (y = 0…65), nicht über die volle
Zargentiefe — sonst hingen 62 mm frei in der Luft. Dicke wie die Auflagen,
2 mm.

Damit wird das Teil **226,6 mm breit** bei 230 mm nutzbarem Bett: nur 3,4 mm
Reserve. Die Zelle `bett_rest` in der Tabelle rechnet das mit, und die
Prüfung `passt aufs Bett` schlägt an, bevor ein zu breites Teil im Slicer
landet. Für Heizkörper B und C, die breitere Bleche haben, muss die Blende
in Segmenten gedruckt und aneinandergereiht werden.

### Befestigung — Zapfen (2× im Komplett-STL enthalten)

**Massiver** Quader mit gerundeten Kanten, der **formschlüssig in einen
Heizungsschlitz** fasst. Außenmaß 7,4 × 39 mm — Schlitzbreite minus 0,2 mm
Spiel mal die volle Lochfeldbreite. Er kann sich damit weder drehen noch
wandern.

| | mm |
|---|---|
| Außen | 7,4 × 39,0 |
| Höhe | 7,0 |
| Kantenradius (4 senkrechte Kanten) | 2,0 |
| Kernloch M3, selbstschneidend | ⌀2,5, **durchgehend** |

Der Zapfen wird von unten durch den Schlitz gesteckt und mit **einer M3 durch
die Blende** in sein Kernloch geschraubt.

Die zwei Durchmesser gehören zusammen und dürfen nicht gleich sein:

| | ⌀ | Funktion |
|---|---|---|
| Blende (`blende_sd`) | 3,4 mm | Durchgang — die Schraube läuft frei durch |
| Zapfen (`zapfen_sd`) | 2,5 mm | Kernloch — die Schraube schneidet ihr Gewinde |

Wäre das Blendenloch ebenso eng, würde die Schraube auch dort schneiden und
die beiden Teile nicht zusammenziehen.

Das Kernloch geht **durch den ganzen Zapfen**: lässt das geschnittene Gewinde
auf einer Seite nach, wird der Zapfen umgedreht und die andere Seite genutzt.

Das zugehörige Loch in jeder Blende sitzt mittig zur Heizungstiefe
(y = 32,5) und mittig in der Blende — beide fluchten.

**Montage vs. Druck:** montiert werden die Zapfen unter den Blenden. Für den
Druck liegen sie in `halter_A_komplett.stl` frei in der Lüfteröffnung, wo der
Halter ohnehin leer ist — ein STL darf mehrere getrennte Volumenkörper
enthalten, der Slicer behandelt sie als eigene Objekte.

Der ursprüngliche Randumgriff (Backen und Nasen unterhalb z=0) ist entfernt:
er machte das Teil druckunfreundlich, und die Fixierung übernehmen jetzt
diese zwei Teile.

**Zu prüfen beim ersten Anhalten:** ob 7,4 mm wirklich in den Schlitz gehen.
Gedruckte Außenmaße fallen in PLA gern 0,1–0,2 mm zu groß aus; `zapfen_spiel`
in der Tabelle ist die Stellschraube.

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
