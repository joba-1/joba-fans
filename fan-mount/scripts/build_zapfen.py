"""Only the pegs (Zapfen, the screw blocks) of a mount, as a separate file.

The pegs are printed separately when nothing on the mount itself needs to
change - for example after a dimension correction to zapfen_l. Uses the same
geometry function as build_variante.py so that funnels, roundings and core
hole stay identical; the mount in the target document is not touched.

Run inside FreeCAD with the document open, setting ZIEL first:
    ZIEL = "RadiatorFanLarge"
    exec(open(".../fan-mount/scripts/build_zapfen.py").read())
The STL is written next to the opened document (set FAN_MOUNT_CAD to override).
"""
import FreeCAD, Part, MeshPart, os

d = FreeCAD.getDocument(ZIEL)
sh = d.getObject("Masse")
g = lambda a: float(sh.get(a))
out = os.environ.get("FAN_MOUNT_CAD") or os.path.dirname(d.FileName) or os.getcwd()


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


# For single printing, side by side in a row with a gap: they do not have to
# lie where there is room in the mount.
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
oz.Label = "Zapfen, separate (%dx)" % ANZ
d.recompute()

bb = gz.BoundBox
mg = MeshPart.meshFromShape(Shape=gz, LinearDeflection=0.05,
                            AngularDeflection=0.5, Relative=False)
stl = os.path.join(out, name + ".stl")
mg.write(stl)
print("  %s: %d bodies, %.1f x %.1f x %.1f mm, %.2f cm3, solid=%s" % (
    name, len(gz.Solids), bb.XLength, bb.YLength, bb.ZLength,
    gz.Volume / 1000, mg.isSolid()))
print("  peg length now: %.1f mm" % zl)
print("  written:", stl)
