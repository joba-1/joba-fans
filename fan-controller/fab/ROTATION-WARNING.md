# Check part rotation in the fab's assembly preview

**Always go through the assembly preview before ordering.** In a first pass several parts showed up
rotated there, although our CPL is correct.

## Why

Not because of our files. The rotation values in `fan-controller-cpl.csv` match the board exactly —
checked part by part.

The cause is a known discrepancy between KiCad and JLCPCB: **they use different zero orientations for the
same packages.** It mainly affects SOT packages and polarised parts. The KiCad community maintains
correction tables for this (for example in the plugin `Bouni/kicad-jlcpcb-tools`) that add an offset on
export.

Those correction values are deliberately **not** built in here: they depend on the exact catalogue part
chosen, and a wrong value turns a part by 180°. For D1 and U2 that would make the board unusable.

## What to check

The preview shows every part at its position. The three polarised or asymmetric parts are the critical
ones — for the resistors the rotation is electrically irrelevant:

| Part | What to look for |
|---|---|
| **U2** AMS1117-5.0, SOT-223 | The wide tab must sit on the large pad. Pin 1 (GND) bottom left, pin 3 (VI) right. Rotated = regulator destroyed. |
| **D1** SS34, SMA | The cathode stripe must point to the marked side. The wrong way round, the diode blocks the supply. |
| **C2** 10 µF, 0805 | Ceramic, unpolarised — rotation not critical. |
| **F1** polyfuse, 1812 | Unpolarised — rotation not critical. |
| **R1–R12** 0603 | Not critical. |

In practice only **U2 and D1** are really dangerous. Both can be rotated individually in the preview.

## Why not correct automatically

We could hard-code an offset, but:

* the right value depends on the chosen catalogue part, not only on the package
* a wrong assumption only shows on the finished board
* the preview shows the result directly anyway

Correcting in the web interface is therefore the safer way — there you see immediately what happens.

## PCBWay

The same applies there. PCBWay usually reworks the assembly data manually and asks when something is
unclear, but you should not rely on that.
