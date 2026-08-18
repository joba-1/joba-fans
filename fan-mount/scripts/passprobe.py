"""Passproben-Rahmen aus der Tabelle 'Masse' erzeugen.

In FreeCAD ausfuehren (Ansicht -> Panels -> Python-Konsole):
    exec(open('/data/joachim/git/fan-stand/scripts/passprobe.py').read())

Erzeugt/aktualisiert Rahmen_A/B/C und schreibt die STLs nach cad/.
Alle Masse kommen aus der Tabelle, keine Zahl steht hier fest ausser der
Nasengeometrie (nase_h/nase_l) und der Teilelucke im Layout.
"""
import FreeCAD, Part, MeshPart, os

# Der interne Dokumentname kommt beim Oeffnen aus dem Dateinamen und ist
# dann klein geschrieben; beim Neuanlegen gross. Beide zulassen.
d = None
for _n in ("Passprobe", "passprobe"):
    try:
        d = FreeCAD.getDocument(_n)
        break
    except NameError:
        pass
if d is None:
    raise RuntimeError("Dokument Passprobe nicht offen")
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

def halter(tiefe, hinten_ueber, rand, x0=0.0):
    """Flache Zarge, liegt lose auf dem Blech (Befestigung: eigenes Teil).

    Koordinaten: y=0 ist die Blech-HINTERKANTE (Wandseite), y=tiefe die
    Vorderkante. hinten_ueber sagt, wie weit der Luefter ueber die
    Hinterkante hinausragt - daraus ergibt sich der asymmetrische Sitz.

    Das Teil endet bei z=0 und steht damit ohne Drehen ueberhangfrei auf
    dem Bett.
    """
    zi, za, zd = g("z_innen"), g("z_aussen"), g("z_dicke")
    zh, ah, al = g("z_hoehe"), g("z_auflage"), g("z_ecke")
    xk = x0 - zd

    teile = [Part.makeBox(za, za, zh, FreeCAD.Vector(xk, -hinten_ueber - zd, 0)).cut(
                 Part.makeBox(zi, zi, zh + 2, FreeCAD.Vector(x0, -hinten_ueber, -1)))]
    # Auflagen reichen in Y bis an die jeweilige Rippe heran. Eine feste
    # Ecklaenge liess schmale Spalte stehen (3,0 mm vorne, 24,6 mm hinten),
    # die sich weder drucken noch nutzen lassen.
    ev, eh = g("ecke_v"), g("ecke_h")
    for dx in (0, 1):
        ex = x0 + (zi - al) * dx
        teile.append(Part.makeBox(al, ev, ah, FreeCAD.Vector(ex, -hinten_ueber, 0)))
        teile.append(Part.makeBox(al, eh, ah, FreeCAD.Vector(ex, tiefe, 0)))
    # RIPPEN statt eines durchgehenden Stegs: nur auf den ungelochten
    # Randstreifen. Ein Vollsteg ueber die ganze Tiefe verdeckt 64 % des
    # Luefteraustritts - genau den Teil, der ueber dem Lochfeld liegt.
    rb = g("rippe_b")
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, 0, 0)))
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, tiefe - rb, 0)))

    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)
    return r.removeSplitter()


def pruefe_halter(s, tiefe, hinten_ueber, rand):
    """Vier Bedingungen an die flache Zarge (Teil endet bei z=0)."""
    zi, ah, zd = g("z_innen"), g("z_auflage"), g("z_dicke")
    ins = lambda xx, yy, zz: s.isInside(FreeCAD.Vector(xx, yy, zz), 1e-6, True)
    hi, x = hinten_ueber, s.BoundBox.XMin + 3.0

    def durchgehend(y0, y1):
        return all(ins(x, y0 + (y1 - y0) * (i + 0.5) / 40, ah / 2) for i in range(40))

    return {
        "flach ab z=0":    abs(s.BoundBox.ZMin) < 1e-6,
        "keine Ueberhaenge": not any(
            f.Surface.__class__.__name__ == "Plane"
            and f.normalAt(0.5, 0.5).z <= -0.9 and f.BoundBox.ZMin > 0.01
            for f in s.Faces),
        # Der Weg vom Luefter zum Lochfeld muss frei sein. Fehlt diese
        # Pruefung, faellt ein Boden unter dem Luefter nicht auf.
        "Lochfeld offen": not any(
            ins(s.BoundBox.XMin + zd + zi * (i + 0.5) / 9,
                rand + (tiefe - 2 * rand) * (j + 0.5) / 11, ah / 2)
            for i in range(9) for j in range(11)),
        # Auflagen muessen bis an die Rippen reichen, sonst bleiben Spalte.
        "keine Spalte":   durchgehend(-hi, 0.0) and durchgehend(tiefe, -hi + zi),
    }


if __name__ != "nicht_ausfuehren":
    o = d.getObject("Halter_A") or d.addObject("Part::Feature", "Halter_A")
    o.Shape = halter(g("a_tiefe"), g("a_hinten"), g("a_rand"))
    o.Label = "Halter A (Buero, %.0f-mm-Luefter)" % g("luefterhoehe")
    d.recompute()
    res = pruefe_halter(o.Shape, g("a_tiefe"), g("a_hinten"), g("a_rand"))
    for k, v in res.items():
        print("  %-16s %s" % (k, "OK" if v else "FEHLER"))
    m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05,
                               AngularDeflection=0.5, Relative=False)
    m.write(os.path.join(out, "halter_A.stl"))   # flach, keine Drehung noetig
    bb = o.Shape.BoundBox
    print("  Halter A %.0fx%.0fx%.0f mm  %.1f cm3  solid=%s  %s" % (
        bb.XLength, bb.YLength, bb.ZLength, o.Shape.Volume / 1000, m.isSolid(),
        "BESTANDEN" if all(res.values()) else "FEHLGESCHLAGEN"))
