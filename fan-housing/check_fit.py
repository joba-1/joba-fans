#!/usr/bin/env python3
"""Check the fits of the housing numerically.

Usage: python3 fan-housing/check_fit.py

The model works out its own cuboids and prints them via echo(); this script only
checks them. That leaves no second place where dimensions live - a change in
fan-housing.scad shows up immediately.

It checks what a render does not show: whether the latch nose hits its pocket,
whether the tab withstands the deflection, and whether spring tabs poke into
components. Exactly these were wrong twice already (pocket cut through the wall,
nose 2mm below its pocket) and neither was visible in the picture.
"""
import os
import shutil
import subprocess
import sys
import tempfile

SCAD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fan-housing.scad")
OSC = shutil.which("openscad")
if not OSC:
    sys.exit("openscad not found in PATH")
ECHO = os.path.join(tempfile.mkdtemp(), "report.echo")

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
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)

def overlap(a, b):
    """Do two cuboids (x0,x1,y0,y1,z0,z1) overlap?"""
    return all(a[i] < b[i+1] and b[i] < a[i+1] for i in (0, 2, 4))

snap_t, snap_h, proud, gap, pk_d, fit = v["SNAP"]
wall_in = -fit
nose_tip = -fit + gap - proud
pocket_out = -fit - pk_d
engage = wall_in - nose_tip
defl = engage
strain = 3 * snap_t * defl / (2 * snap_h ** 2) * 100

print("Snap-fit")
check(engage > 0.3, f"Nose engages {engage:.2f} mm behind the inner wall face "
                    f"(minimum 0.30)")
check(nose_tip > pocket_out, f"Nose ends {nose_tip - pocket_out:.2f} mm short of the "
                             f"bottom of the pocket")
check(strain < 3.0, f"Outer-fibre strain when opening {strain:.2f} % "
                    f"(PETG yields from about 4 %)")
n0, n1 = v["NOSEZ"]; p0, p1 = v["POCKZ"]
check(p0 < n0 and n1 < p1,
      f"Nose z {n0:.1f}..{n1:.1f} lies within pocket z {p0:.1f}..{p1:.1f}")

print("\nClearance of the spring tabs")
for name, pb in parts:
    hit = [i for i, t in enumerate(tabs) if overlap(t, pb)]
    check(not hit, f"{name} collides with no tab"
                   + (f" - hit: tab {hit}" if hit else ""))

print("\nHeight")
head = v["HEAD"][0]
for name, pb in parts:
    clear = head + 1.6 - pb[5]
    check(clear > 1.0, f"{name} leaves {clear:.1f} mm of air under the lid")

print(f"\nOuter size {v['OUTER'][0]:.1f} x {v['OUTER'][1]:.1f} x "
      f"{v['OUTER'][2]:.1f} mm")
print(f"{'ALL CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED'}")
sys.exit(1 if fails else 0)
