# Bauteildrehung in JLCPCBs Vorschau prüfen

**Vor dem Bestellen unbedingt die Bestückungsvorschau durchsehen.** In einem
ersten Durchlauf saßen dort mehrere Bauteile verdreht, obwohl unsere CPL
korrekt ist.

## Woran es liegt

Nicht an unseren Dateien. Die Rotationswerte in `fan-controller-cpl.csv`
stimmen exakt mit der Platine überein — nachgeprüft, Bauteil für Bauteil.

Ursache ist eine bekannte Unstimmigkeit zwischen KiCad und JLCPCB:
**beide verwenden für dieselben Gehäuse unterschiedliche Nullstellungen.**
Betroffen sind vor allem SOT-Gehäuse und polarisierte Bauteile. Die
KiCad-Community pflegt dafür Korrekturtabellen (etwa im Plugin
`Bouni/kicad-jlcpcb-tools`), die beim Export einen Versatz aufaddieren.

Diese Korrekturwerte sind hier bewusst **nicht** eingebaut: sie hängen vom
konkret gewählten Katalogteil ab, und ein falscher Wert dreht ein Bauteil um
180°. Bei D1 und U2 wäre die Platine damit unbrauchbar.

## Was zu prüfen ist

Die Vorschau zeigt jedes Bauteil an seiner Position. Kritisch sind die drei
polarisierten bzw. unsymmetrischen Teile — bei den Widerständen ist die
Drehung elektrisch belanglos:

| Bauteil | Worauf achten |
|---|---|
| **U2** AMS1117-5.0, SOT-223 | Die breite Kühlfahne muss auf dem großen Pad liegen. Pin 1 (GND) links unten, Pin 3 (VI) rechts. Verdreht = Regler zerstört. |
| **D1** SS34, SMA | Kathodenstrich muss zur markierten Seite zeigen. Verkehrt herum sperrt die Diode die Versorgung. |
| **C2** 10 µF, 0805 | Keramik, unpolarisiert — Drehung unkritisch. |
| **F1** Polyfuse, 1812 | Unpolarisiert — Drehung unkritisch. |
| **R1–R12** 0603 | Unkritisch. |

Faktisch sind also nur **U2 und D1** wirklich gefährlich. Beide lassen sich
in der Vorschau einzeln drehen.

## Warum nicht automatisch korrigieren

Wir könnten einen Versatz fest eintragen, aber:

* der richtige Wert hängt vom gewählten Katalogteil ab, nicht nur vom
  Gehäuse
* eine falsche Annahme fällt erst an der fertigen Platine auf
* die Vorschau zeigt das Ergebnis ohnehin direkt an

Die Korrektur im Web-Interface ist daher der sicherere Weg — dort siehst du
unmittelbar, was passiert.

## PCBWay

Dort ist dasselbe zu prüfen. PCBWay arbeitet die Bestückungsdaten
üblicherweise manuell nach und fragt bei Unklarheiten zurück, aber verlassen
sollte man sich darauf nicht.
