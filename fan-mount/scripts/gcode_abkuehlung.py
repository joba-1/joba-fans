"""Haengt eine Abkuehlphase an das Ende eines Gcodes.

Nach dem Druck laeuft der Zusatzluefter (M106 P2 - der mittlere, der ueber
die Druckplatte blaest, identifiziert 2026-08-23) weiter, bis das Bett
unter ZIEL Grad gefallen ist. Danach schaltet er ab.

M190 R kennt diese Firmware NICHT (gemessen 2026-08-23): das Bett fiel
mit laufendem Luefter von 45 auf 38 Grad, also weit unter die Schwelle
von 50, ohne dass der Gcode weiterlief. Der Befehl wird stillschweigend
uebergangen - der Drucker heizt ueber den herstellereigenen G9111 statt
ueber Standard-Marlin-Befehle.

Es traegt also allein die feste Nachlaufzeit. M190 R bleibt trotzdem im
Block stehen: es kostet nichts und wuerde nach einem Firmware-Update
sofort greifen.

Gemessene Abkuehlung mit Luefter, Bett von 76 Grad:
    nach ~1 min   59 C     (17 Grad/min - anfangs sehr schnell)
    nach ~4 min   49 C     Ziel 50 erreicht
    danach         2,8 Grad/min - deutlich langsamer

Daraus die Vorgabe von 300 s: nach 5 Minuten ist das Bett von jeder
ueblichen Drucktemperatur unter 50 Grad. Laenger zu blasen bringt wenig,
weil die Rate dann auf unter 3 Grad/min faellt.

    python3 gcode_abkuehlung.py datei.gcode [ziel_grad] [nachlauf_s]
"""
import sys
import re

# Der Zusatzluefter. Vom Nutzer am Kanaltest identifiziert: der mittlere.
LUEFTER = "P2"


def block(ziel, nachlauf):
    return """
; --- Abkuehlung (angehaengt) --------------------------------------
; Zusatzluefter %(fan)s blaest ueber die Platte, bis das Bett unter
; %(ziel)d C ist. Diese Firmware kennt M190 R nicht (gemessen), es
; traegt also die feste Nachlaufzeit darunter. M190 R bleibt stehen,
; damit es nach einem Firmware-Update sofort greift.
M140 S0            ; Bett aus, sonst haelt es die Temperatur
M106 %(fan)s S255  ; Zusatzluefter volle Leistung
M190 R%(ziel)d     ; wirkungslos auf dieser Firmware, siehe oben
G4 S%(nach)d       ; das ist der wirksame Teil: %(nach)d s blasen
M106 %(fan)s S0    ; Luefter aus
; --- Ende Abkuehlung ----------------------------------------------
""" % {"fan": LUEFTER, "ziel": ziel, "nach": nachlauf}


def main(pfad, ziel=50, nachlauf=300):
    with open(pfad, "r", errors="replace") as f:
        text = f.read()

    # Vor M84 einhaengen: danach sind die Motoren stromlos. Der Block muss
    # aber noch vor den Konfig-Kommentarblock, sonst steht er im Nirgendwo.
    m = re.search(r"^M84.*$", text, re.M)
    if not m:
        sys.exit("kein M84 gefunden - Endblock nicht erkannt")

    neu = text[:m.start()] + block(ziel, nachlauf).lstrip("\n") + text[m.start():]
    with open(pfad, "w") as f:
        f.write(neu)
    print("Abkuehlung eingefuegt: Luefter %s bis %d C, Nachlauf %d s"
          % (LUEFTER, ziel, nachlauf))


if __name__ == "__main__":
    if not 2 <= len(sys.argv) <= 4:
        sys.exit(__doc__)
    main(sys.argv[1],
         int(sys.argv[2]) if len(sys.argv) > 2 else 50,
         int(sys.argv[3]) if len(sys.argv) > 3 else 300)
