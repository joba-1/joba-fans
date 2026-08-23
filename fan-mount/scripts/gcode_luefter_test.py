"""Haengt einen Luefter-Kanaltest an das Ende eines Gcodes.

Hintergrund: der Drucker hat drei Luefterkanaele (M106 P1/P2/P3) und
meldet ueber MQTT drei Felder - fan_speed_pct (Bauteil), aux_fan_speed_pct
(Zusatz, blaest ueber die Platte) und box_fan_level (Gehaeuse). Welcher
Gcode-Kanal welchem Feld entspricht, ist nicht dokumentiert, und ueber
MQTT liessen sich die Luefter nicht setzen: set/auto/control/adjust
antworten alle code 200 und aendern nichts.

Also am Druckende testen. Jeder Kanal laeuft 20 s allein, dazwischen
5 s Stille - so ist am Gehoer zuzuordnen, welcher Kanal der Plattenluefter
ist. Kostet gut eine Minute und keinen eigenen Testlauf.

    python3 gcode_luefter_test.py datei.gcode
"""
import sys
import re

TEST = """
; --- Luefter-Kanaltest (angehaengt) -------------------------------
; Jeder Kanal 20 s allein, dazwischen 5 s Stille.
; Zuhoeren: welcher blaest ueber die Druckplatte?
M106 P1 S255 ; Kanal 1 an
G4 S20
M106 P1 S0
G4 S5
M106 P2 S255 ; Kanal 2 an
G4 S20
M106 P2 S0
G4 S5
M106 P3 S255 ; Kanal 3 an
G4 S20
M106 P3 S0
; --- Ende Luefter-Kanaltest ---------------------------------------
"""


def main(pfad):
    with open(pfad, "r", errors="replace") as f:
        text = f.read()

    # Vor "M84" einhaengen: danach sind die Motoren stromlos, aber die
    # Luefter laufen weiter. Der Test soll aber vor dem Konfigblock stehen.
    m = re.search(r"^M84.*$", text, re.M)
    if not m:
        sys.exit("kein M84 gefunden - Endblock nicht erkannt")

    neu = text[:m.start()] + TEST.lstrip("\n") + text[m.start():]
    with open(pfad, "w") as f:
        f.write(neu)
    print("Luefter-Kanaltest eingefuegt vor Zeile %d (M84)"
          % (text[:m.start()].count("\n") + 1))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
