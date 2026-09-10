# Fan Controller

Vierkanal-Lüftersteuerung für 4-polige PC-Lüfter, gesteuert über WLAN von einem
Seeed XIAO ESP32-C3. KiCad-Projekt, Platine 72,9 × 25,0 mm, zweilagig.

**→ [Projektseite: der Weg von der Schaltung zur Platine](docs/build-log.html)**

## Aufbau des Repos

| Pfad | Inhalt |
|---|---|
| `fan-controller/` | KiCad-Projekt und die Skripte, die Schaltplan und Fertigungsdaten erzeugen |
| `fab/` | Fertigungspaket: Gerber, Bohrdaten, BOM und Bestückungsdaten für JLCPCB und PCBWay |
| `enclosure/` | Gehäuse um die Platine, parametrisch in OpenSCAD |
| `fan-stand/` | Lüfterhalterungen am Heizkörper — die Lüfter, die diese Platine ansteuert |
| `docs/` | Projektdokumentation |

### Die Historie von `fan-stand/`

`fan-stand/` kam am 2026-09-10 aus einem eigenen Repo hierher, als
Subtree-Merge — seine 61 Commits sind also erhalten, liegen aber unter den
**alten Pfaden ohne das `fan-stand/`-Präfix**. Ein `git log -- fan-stand/x`
zeigt darum nur den Merge selbst. So kommt man an die echte Historie:

```sh
git log --oneline e5e0e0c              # der alte Zweigkopf, 61 Commits
git log --oneline e5e0e0c -- MEASUREMENTS.md
git log --follow --full-history --all -- MEASUREMENTS.md
```

Nicht im Repo, und zwar mit Absicht:

* **Die Fotos der Halterungen** — 26 HEIC-Originale (40 MB) und ihre
  JPEG-Fassungen. Sie liegen unter `/data/joachim/git/fan-stand/doc/` und waren
  auch dort nie versioniert.
* **Gcode.** Am 2026-09-10 aus der Historie entfernt: 62 MB und damit der
  größte Posten im Repo, dabei aus den STL- und FreeCAD-Dateien jederzeit neu
  zu erzeugen. Die zuletzt gedruckten Fassungen liegen unter
  `/data/joachim/gcode-rette/`, die Historie davor im Bundle
  `/data/joachim/fan-speed-vor-rewrite-20260910.bundle`.

## Schaltung

Pro Kanal geht PWM über 1 kΩ zum Lüfter, das Tachosignal über 330 Ω zurück zum
ESP, mit 10 kΩ nach 3V3 hochgezogen. Versorgung über Hohlbuchse, SS34 als
Verpolschutz, 1,5-A-Polyfuse, AMS1117-5.0 für den ESP.

GPIO-Belegung: D1/D2, D3/D4, D7/D10, D5/D6 für FAN1–FAN4. D0, D8 und D9 bleiben
frei — Strapping-Pins des ESP32-C3.

Das XIAO-Modul wird gesockelt, nicht gelötet.

## Fertigungsdaten erzeugen

```sh
fan-controller/make_fab.sh
```

Erzeugt Gerber, Bohrdaten, BOM und Bestückungsliste in `fab/`, jeweils in den
Formaten von JLCPCB und PCBWay, und packt alles nach
`fab/fan-controller-fab.zip`.

Der Schaltplan selbst wird aus `fan-controller/netplan.py` generiert:

```sh
python3 fan-controller/generate.py fan-controller/fan-controller.kicad_sch
```

Der Lauf prüft am Ende die exportierte Netzliste gegen die Planungstabelle —
ERC allein findet keine Leitung, die am falschen Pin landet.
