"""Passproben-Rahmen aus der Tabelle 'Masse' erzeugen.

In FreeCAD ausfuehren (Ansicht -> Panels -> Python-Konsole):
    exec(open('/data/joachim/git/fan-stand/scripts/passprobe.py').read())

Erzeugt/aktualisiert Rahmen_A/B/C und schreibt die STLs nach cad/.
Alle Masse kommen aus der Tabelle, keine Zahl steht hier fest ausser der
Nasengeometrie (nase_h/nase_l) und der Teilelucke im Layout.
"""
import FreeCAD, Part, MeshPart, os

DOC = "Passprobe"
d   = FreeCAD.getDocument(DOC)
sh  = d.getObject("Masse")
g   = lambda a: float(sh.get(a))

nase_h, nase_l, luecke = 1.5, 1.5, 12.0


def rahmen(tiefe, x0):
    """Randumgriff-Klammer. y-Aufbau: Backe | Blech | Backe."""
    pd, bd, maul, L = g("plattendicke"), g("backendicke"), g("maulweite"), g("probelaenge")
    breite = tiefe + 2 * bd
    h = maul + nase_h
    teile = [
        Part.makeBox(L, breite, pd, FreeCAD.Vector(x0, 0, 0)),                  # Platte
        Part.makeBox(L, bd, h,      FreeCAD.Vector(x0, 0, -h)),                 # Backe vorne
        Part.makeBox(L, bd, h,      FreeCAD.Vector(x0, bd + tiefe, -h)),        # Backe hinten
        Part.makeBox(L, nase_l, nase_h, FreeCAD.Vector(x0, bd, -h)),            # Nase vorne
        Part.makeBox(L, nase_l, nase_h, FreeCAD.Vector(x0, bd + tiefe - nase_l, -h)),
    ]
    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)
    return r.removeSplitter()


def pruefe(shape, tiefe):
    """Maul muss ueber die volle Blechtiefe frei sein, Nasen muessen greifen.

    x wird relativ zum Teil gewaehlt - die Teile stehen im Layout nebeneinander
    versetzt, ein absolutes x trifft nur das erste.
    """
    bd, maul = g("backendicke"), g("maulweite")
    x = shape.BoundBox.XMin + g("probelaenge") / 2
    frei = all(not shape.isInside(FreeCAD.Vector(x, y, z), 1e-6, True)
               for y in (bd + 0.2, bd + tiefe / 2, bd + tiefe - 0.2)
               for z in (-0.3, -maul / 2, -maul + 0.3))
    u = -maul - nase_h / 2
    greift = (shape.isInside(FreeCAD.Vector(x, bd + 0.5, u), 1e-6, True) and
              not shape.isInside(FreeCAD.Vector(x, bd + tiefe / 2, u), 1e-6, True))
    return frei, greift


out = os.path.join(os.path.dirname(d.FileName) or ".", "")
x, bett = 0.0, g("druckbett")
for hk, alias in (("A", "a_tiefe"), ("B", "b_tiefe"), ("C", "c_tiefe")):
    tiefe = g(alias)
    o = d.getObject("Rahmen_%s" % hk) or d.addObject("Part::Feature", "Rahmen_%s" % hk)
    o.Shape = rahmen(tiefe, x)
    o.Label = "Passprobe %s (%.0f mm tief)" % (hk, tiefe)
    frei, greift = pruefe(o.Shape, tiefe)
    bb = o.Shape.BoundBox
    m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05,
                               AngularDeflection=0.5, Relative=False)
    m.write(os.path.join(out, "passprobe_%s.stl" % hk))
    print("%s %3.0fx%3.0fx%.0f  Maul frei=%s  Nase greift=%s  solid=%s  Bett=%s" % (
        hk, bb.XLength, bb.YLength, bb.ZLength, frei, greift, m.isSolid(),
        "OK" if max(bb.XLength, bb.YLength) <= bett else "ZU GROSS"))
    x += g("probelaenge") + luecke

d.recompute()
print("Fehler:", [o.Name for o in d.Objects if o.isValid() is False])
