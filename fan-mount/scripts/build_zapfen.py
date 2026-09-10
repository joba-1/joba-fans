"""Nur die Zapfen (Verschraubungsklötze) eines Halters als eigene Datei.

Die Zapfen werden separat gedruckt, wenn am Halter selbst nichts zu
aendern ist - etwa nach einer Massekorrektur an zapfen_l. Nutzt dieselbe
Geometriefunktion wie build_variante.py, damit Trichter, Rundungen und
Kernloch identisch bleiben; der Halter im Zieldokument wird nicht
angefasst.

In FreeCAD ausfuehren, ZIEL vorher setzen:
    ZIEL = "RadiatorFanLarge"
    exec(open(".../scripts/build_zapfen.py").read())
"""
import FreeCAD, Part, MeshPart, os

d = FreeCAD.getDocument(ZIEL)
sh = d.getObject("Masse")
g = lambda a: float(sh.get(a))
out = "/data/joachim/git/fan-stand/cad"


def zapfen(x0=0.0, y0=0.0, sd=None):
    b, l = g("zapfen_b"), g("zapfen_l")
    h, rad = g("zapfen_h"), g("zapfen_r")
    if sd is None:
        sd = g("zapfen_sd")
    aussen = Part.makeBox(b, l, h, FreeCAD.Vector(x0, y0, 0))
    senk = [e for e in aussen.Edges
            if abs(e.Vertexes[0].Point.z - e.Vertexes[-1].Point.z) > h - 1e-6]
    koerper = aussen.makeFillet(rad, senk)
    cx, cy = x0 + b / 2, y0 + l / 2
    koerper = koerper.cut(Part.makeCylinder(sd / 2, h + 2,
                                           FreeCAD.Vector(cx, cy, -1)))
    td, tt = g("trichter_d"), g("trichter_t")
    if td > sd:
        koerper = koerper.cut(Part.makeCone(td / 2, sd / 2, tt,
                                            FreeCAD.Vector(cx, cy, h - tt)))
        koerper = koerper.cut(Part.makeCone(sd / 2, td / 2, tt,
                                            FreeCAD.Vector(cx, cy, 0)))
    return koerper.removeSplitter()


# Fuer den Einzeldruck nebeneinander in einer Reihe, mit Abstand: sie
# muessen nicht dort liegen, wo im Halter Platz ist.
ANZ = 4
LUFT = 6.0
zb, zl = g("zapfen_b"), g("zapfen_l")
stueck = [zapfen(i * (zb + LUFT), 0.0) for i in range(ANZ)]

gz = stueck[0]
for t in stueck[1:]:
    gz = gz.fuse(t)

name = "ZapfenLarge"
oz = d.getObject(name) or d.addObject("Part::Feature", name)
oz.Shape = gz
oz.Label = "Zapfen einzeln (%dx)" % ANZ
d.recompute()

bb = gz.BoundBox
mg = MeshPart.meshFromShape(Shape=gz, LinearDeflection=0.05,
                            AngularDeflection=0.5, Relative=False)
stl = os.path.join(out, name + ".stl")
mg.write(stl)
print("  %s: %d Koerper, %.1f x %.1f x %.1f mm, %.2f cm3, solid=%s" % (
    name, len(gz.Solids), bb.XLength, bb.YLength, bb.ZLength,
    gz.Volume / 1000, mg.isSolid()))
print("  Zapfenlaenge jetzt: %.1f mm" % zl)
print("  geschrieben:", stl)
