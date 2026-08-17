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


# ---------------------------------------------------------------------------
# Halter: Passprobe + Zarge (Luefteraufnahme) in einem Teil
# ---------------------------------------------------------------------------

def halter(tiefe, hinten_ueber, x0=0.0):
    """Klammer + Zarge.

    Koordinaten: y=0 ist die Blech-HINTERKANTE (Wandseite), y=tiefe die
    Vorderkante. hinten_ueber sagt, wie weit der Luefter ueber die
    Hinterkante hinausragt - daraus ergibt sich der asymmetrische Sitz.

    Wichtig: der Verbindungssteg liegt OBERHALB des Blechs (z >= 0).
    Liegt er im Maul, passt das Blech nicht hinein.
    """
    bd, maul = g("backendicke"), g("maulweite")
    zi, za, zd = g("z_innen"), g("z_aussen"), g("z_dicke")
    zh, ah, al = g("z_hoehe"), g("z_auflage"), g("z_ecke")
    h, br, xk = maul + nase_h, za, x0 - zd

    teile = [Part.makeBox(za, za, zh, FreeCAD.Vector(xk, -hinten_ueber - zd, 0)).cut(
                 Part.makeBox(zi, zi, zh + 2, FreeCAD.Vector(x0, -hinten_ueber, -1)))]
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):           # Auflageecken
        teile.append(Part.makeBox(al, al, ah, FreeCAD.Vector(
            x0 + (zi - al) * dx, -hinten_ueber + (zi - al) * dy, 0)))
    teile.append(Part.makeBox(br, bd, h, FreeCAD.Vector(xk, -bd, -h)))       # Backe hinten
    teile.append(Part.makeBox(br, bd, h, FreeCAD.Vector(xk, tiefe, -h)))     # Backe vorne
    teile.append(Part.makeBox(br, nase_l, nase_h, FreeCAD.Vector(xk, 0, -h)))
    teile.append(Part.makeBox(br, nase_l, nase_h, FreeCAD.Vector(xk, tiefe - nase_l, -h)))
    teile.append(Part.makeBox(br, tiefe + 2 * bd, ah, FreeCAD.Vector(xk, -bd, 0)))  # Steg

    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)
    return r.removeSplitter()


def pruefe_halter(s, tiefe, hinten_ueber):
    """Vier Bedingungen, die das Teil erfuellen muss."""
    maul, zi, ah = g("maulweite"), g("z_innen"), g("z_auflage")
    x = s.BoundBox.XMin + g("z_aussen") / 2
    ins = lambda xx, yy, zz: s.isInside(FreeCAD.Vector(xx, yy, zz), 1e-6, True)
    hi = hinten_ueber
    return {
        "Maul frei":       all(not ins(x, y, z) for y in (0.5, tiefe / 2, tiefe - 0.5)
                               for z in (-0.3, -maul / 2, -maul + 0.3)),
        "Nasen greifen":   ins(x, 0.7, -maul - 0.75) and not ins(x, tiefe / 2, -maul - 0.75),
        "Luefterraum":     all(not ins(xx, yy, ah + 3) for xx, yy
                               in ((30, -hi + 30), (60, -hi + 60), (90, -hi + 90))),
        "Auflagen tragen": all(ins(xx, yy, ah / 2) for xx, yy
                               in ((3, -hi + 3), (zi - 3, -hi + 3),
                                   (3, -hi + zi - 3), (zi - 3, -hi + zi - 3))),
    }


if __name__ != "nicht_ausfuehren":
    o = d.getObject("Halter_A") or d.addObject("Part::Feature", "Halter_A")
    o.Shape = halter(g("a_tiefe"), g("a_hinten"))
    o.Label = "Halter A (Buero, %.0f-mm-Luefter)" % g("luefterhoehe")
    d.recompute()
    res = pruefe_halter(o.Shape, g("a_tiefe"), g("a_hinten"))
    for k, v in res.items():
        print("  %-16s %s" % (k, "OK" if v else "FEHLER"))
    m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05,
                               AngularDeflection=0.5, Relative=False)
    m.write(os.path.join(out, "halter_A.stl"))
    bb = o.Shape.BoundBox
    print("  Halter A %.0fx%.0fx%.0f mm  %.1f cm3  solid=%s  %s" % (
        bb.XLength, bb.YLength, bb.ZLength, o.Shape.Volume / 1000, m.isSolid(),
        "BESTANDEN" if all(res.values()) else "FEHLGESCHLAGEN"))
