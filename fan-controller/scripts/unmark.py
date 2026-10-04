#!/usr/bin/env python3
"""Remove the temporary narrowed-track markers from User.Eco1.

Usage: python3 unmark.py [board.kicad_pcb]

Markers are placed by the widening pass to show where a power or ground trace
could not reach its target width. They live on User.Eco1 so they never reach
a fab output, but clear them once the spots have been reviewed.
"""
import os
import sys

import pcbnew

path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "fan-controller.kicad_pcb")
b = pcbnew.LoadBoard(path)

n = 0
for d in list(b.GetDrawings()):
    if d.GetLayer() == pcbnew.Eco1_User:
        b.Remove(d)
        n += 1

b.Save(path)
print(f"removed {n} marker items from User.Eco1")
