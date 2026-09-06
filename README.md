# Fan Controller

Vierkanal-Lüftersteuerung für 4-polige PC-Lüfter, gesteuert über WLAN von einem
Seeed XIAO ESP32-C3. KiCad-Projekt, Platine 72,9 × 25,0 mm, zweilagig.

**→ [Projektseite: der Weg von der Schaltung zur Platine](docs/build-log.html)**

## Aufbau des Repos

| Pfad | Inhalt |
|---|---|
| `fan-controller/` | KiCad-Projekt und die Skripte, die Schaltplan und Fertigungsdaten erzeugen |
| `fab/` | Fertigungspaket: Gerber, Bohrdaten, BOM und Bestückungsdaten für JLCPCB und PCBWay |
| `docs/` | Projektdokumentation |

## Schaltung

Pro Kanal geht PWM über 1 kΩ zum Lüfter, das Tachosignal über 330 Ω zurück zum
ESP, mit 10 kΩ nach 3V3 hochgezogen. Versorgung über Hohlbuchse, SS34 als
Verpolschutz, 1,5-A-Polyfuse, AMS1117-5.0 für den ESP.

GPIO-Belegung: D1/D2, D3/D4, D7/D10, D5/D6 für FAN1–FAN4. D0, D8 und D9 bleiben
frei — Strapping-Pins des ESP32-C3.

Das XIAO-Modul wird gesockelt, nicht gelötet.

## Fertigungsdaten erzeugen

```
fan-controller/make_fab.sh
```

Erzeugt Gerber, Bohrdaten, BOM und Bestückungsliste in `fab/`, jeweils in den
Formaten von JLCPCB und PCBWay, und packt alles nach
`fab/fan-controller-fab.zip`.

Der Schaltplan selbst wird aus `fan-controller/netplan.py` generiert:

```
python3 fan-controller/generate.py fan-controller/fan-controller.kicad_sch
```

Der Lauf prüft am Ende die exportierte Netzliste gegen die Planungstabelle —
ERC allein findet keine Leitung, die am falschen Pin landet.
