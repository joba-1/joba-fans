"""Haengt eine Abkuehlphase an das Ende eines Gcodes.

Nach dem Druck laeuft der Zusatzluefter (M106 P2 - der mittlere, der ueber
die Druckplatte blaest, identifiziert 2026-08-23) weiter, bis das Bett
unter ZIEL Grad gefallen ist. Danach schaltet er ab.

Warum nicht einfach M190 R<ziel>:
Dieser Drucker heizt ueber den herstellereigenen G9111, nicht ueber
Standard-Marlin-Befehle. Ob er die Marlin-Form "M190 R" (warten, auch
beim Abkuehlen) ueberhaupt kennt, ist ungeprueft - und wenn nicht, laeuft
der Gcode einfach weiter und der naechste Befehl schaltet den Luefter
wieder aus, ohne dass man es merkt.

Deshalb zweigleisig:
  1. M190 R<ziel> versuchen - wenn der Drucker es kennt, wartet er genau
     bis zur Zieltemperatur.
  2. Danach zusaetzlich eine feste Nachlaufzeit. Kennt der Drucker M190 R
     nicht, wirkt nur diese; kennt er es, ist sie ein kurzer Nachlauf.

So kuehlt es in beiden Faellen, und die Funktion faellt nicht stumm aus.

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
; %(ziel)d C ist. M190 R wartet auch beim ABkuehlen - falls diese
; Firmware es nicht kennt, faengt die feste Nachlaufzeit darunter das
; ab, damit die Funktion nicht stumm ausfaellt.
M140 S0            ; Bett aus, sonst haelt es die Temperatur
M106 %(fan)s S255  ; Zusatzluefter volle Leistung
M190 R%(ziel)d     ; warten bis %(ziel)d C erreicht (auch von oben)
G4 S%(nach)d       ; Nachlauf, falls M190 R nicht unterstuetzt wird
M106 %(fan)s S0    ; Luefter aus
; --- Ende Abkuehlung ----------------------------------------------
""" % {"fan": LUEFTER, "ziel": ziel, "nach": nachlauf}


def main(pfad, ziel=50, nachlauf=600):
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
         int(sys.argv[3]) if len(sys.argv) > 3 else 600)
