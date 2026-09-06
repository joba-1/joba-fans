#!/usr/bin/env python3
"""Passungen des Gehaeuses rechnerisch pruefen.

Aufruf: python3 enclosure/check_fit.py

Das Modell rechnet seine eigenen Quader aus und gibt sie ueber echo() aus;
hier werden sie nur noch geprueft. Damit gibt es keine zweite Stelle, an
der Masse stehen - eine Aenderung in case.scad schlaegt sofort durch.

Geprueft wird, was ein Render nicht zeigt: ob die Rastnase ihre Tasche
trifft, ob die Zunge das aushaelt, und ob Federzungen in Bauteile ragen.
Genau das war schon zweimal falsch (Tasche durch die Wand, Nase 2mm unter
ihrer Tasche) und in beiden Faellen am Bild nicht zu erkennen.
"""
import os
import shutil
import subprocess
import sys

SCAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "case.scad")
def _openscad():
    """OpenSCAD liegt hier als AppImage - Arch liefert das Paket zwar, der
    Index war aber veraltet und ein -Syu nur fuer ein CAD ist zu viel."""
    for c in (os.path.expanduser("~/.local/opt/openscad.AppImage"),
              "openscad"):
        if os.path.isfile(c) or shutil.which(c):
            return c
    sys.exit("OpenSCAD nicht gefunden")

OSC = _openscad()
ECHO = "/tmp/case_report.echo"

subprocess.run([OSC, "-o", ECHO, "-D", 'part="report"', SCAD],
               capture_output=True, check=True)

tabs, parts, v = [], [], {}
for line in open(ECHO):
    f = line.replace("ECHO:", "").replace('"', "").split()
    if not f:
        continue
    if f[0] == "TAB":
        tabs.append(tuple(map(float, f[1:7])))
    elif f[0] == "PART":
        parts.append((f[1], tuple(map(float, f[2:8]))))
    else:
        v[f[0]] = list(map(float, f[1:]))

fails = []
def check(ok, msg):
    print(("  ok   " if ok else "  FEHL ") + msg)
    if not ok:
        fails.append(msg)

def overlap(a, b):
    """Ueberschneiden sich zwei Quader (x0,x1,y0,y1,z0,z1)?"""
    return all(a[i] < b[i+1] and b[i] < a[i+1] for i in (0, 2, 4))

snap_t, snap_h, proud, gap, pk_d, fit = v["SNAP"]
wall_in = -fit
nose_tip = -fit + gap - proud
pocket_out = -fit - pk_d
engage = wall_in - nose_tip
defl = engage
strain = 3 * snap_t * defl / (2 * snap_h ** 2) * 100

print("Rastverbindung")
check(engage > 0.3, f"Nase greift {engage:.2f} mm hinter die Wandinnenflaeche "
                    f"(mindestens 0.30)")
check(nose_tip > pocket_out, f"Nase endet {nose_tip - pocket_out:.2f} mm vor dem "
                             f"Taschengrund")
check(strain < 3.0, f"Randfaserdehnung beim Oeffnen {strain:.2f} % "
                    f"(PETG fliesst ab etwa 4 %)")
n0, n1 = v["NOSEZ"]; p0, p1 = v["POCKZ"]
check(p0 < n0 and n1 < p1,
      f"Nase z {n0:.1f}..{n1:.1f} liegt in Tasche z {p0:.1f}..{p1:.1f}")

print("\nFreigang der Federzungen")
for name, pb in parts:
    hit = [i for i, t in enumerate(tabs) if overlap(t, pb)]
    check(not hit, f"{name} kollidiert mit keiner Zunge"
                   + (f" - Treffer: Zunge {hit}" if hit else ""))

print("\nBauhoehe")
head = v["HEAD"][0]
for name, pb in parts:
    clear = head + 1.6 - pb[5]
    check(clear > 1.0, f"{name} laesst {clear:.1f} mm Luft unter dem Deckel")

print(f"\nAussenmass {v['OUTER'][0]:.1f} x {v['OUTER'][1]:.1f} x "
      f"{v['OUTER'][2]:.1f} mm")
print(f"{'ALLE PRUEFUNGEN BESTANDEN' if not fails else str(len(fails)) + ' FEHLER'}")
sys.exit(1 if fails else 0)
