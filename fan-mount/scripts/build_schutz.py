"""Finger-guard hood (Schutz) for the fan - ONE variant for all mounts.

Slips over the collar (Zarge) and can be pulled off. The hold comes from a
skirt with undersize that clamps along the whole circumference - no play, so
no vibration noise.

The struts run lengthwise to the radiator slots and take over their pitch
(strut = sheet web, gap = slot), so the sheet pattern continues visually
upwards.

ORIGIN: z=0 is the TOP EDGE OF THE COLLAR, i.e. where the hood sits. The skirt
runs downwards from there (negative); struts and top frame lie above.

Run inside FreeCAD with a mount document open (ZIEL = its name, e.g.
"RadiatorFanLarge"); the result goes into the document RadiatorFanGuard and
into fan-mount/cad/ (set FAN_MOUNT_CAD to override).
"""
import FreeCAD, Part, MeshPart, os

# ZIEL is the name of the MOUNT variant; the guard goes into a document of its
# own, RadiatorFanGuard, so the mount files stay untouched.
quelle = FreeCAD.getDocument(ZIEL)
# A single variant: the hood only depends on the collar, and that is the same
# for Small, Medium and Large (126.6 mm). Since the struts no longer follow the
# sheet pitch, there is no difference any more.
GUARD = "RadiatorFanGuard"
try:
    d = FreeCAD.getDocument(GUARD)
except NameError:
    d = FreeCAD.newDocument(GUARD)
sh = d.getObject("Masse") or quelle.getObject("Masse")
g = lambda a: float(sh.get(a))
out = os.environ.get("FAN_MOUNT_CAD") or os.path.dirname(d.FileName) or os.getcwd()


def schutz():
    za, zh, ah, lh = g("z_aussen"), g("z_hoehe"), g("z_auflage"), g("luefterhoehe")
    sb, su, sd = g("schutz_schuerze"), g("schutz_unter"), g("schutz_dicke")
    std = g("strebe_dicke")          # struts thinner than the wall
    ab, stb, rast = g("schutz_abstand"), g("strebe_b"), g("strebe_raster")

    # Lower edge of the struts, relative to the top of the collar
    z_streben = (ah + lh + ab) - zh
    if z_streben < 0:
        raise SystemExit("struts would lie below the top of the collar")

    aussen = za + 2 * sd            # outer size of the hood
    x0 = -sd                        # left outer edge (the collar starts at 0)

    teile = []

    # 1) Skirt: box going down, undersized inside -> clamps
    teile.append(
        Part.makeBox(aussen, aussen, sb, FreeCAD.Vector(x0, x0, -sb)).cut(
            Part.makeBox(za - 2 * su, za - 2 * su, sb + 2,
                         FreeCAD.Vector(su, su, -sb - 1))))

    # 2) Vertical ring from the skirt up to the strut level
    if z_streben > 0:
        teile.append(
            Part.makeBox(aussen, aussen, z_streben,
                         FreeCAD.Vector(x0, x0, 0)).cut(
                Part.makeBox(za, za, z_streben + 2,
                             FreeCAD.Vector(0, 0, -1))))

    # 3) Top frame at strut height
    rb = sd + 2.0
    teile.append(
        Part.makeBox(aussen, aussen, sd,
                     FreeCAD.Vector(x0, x0, z_streben)).cut(
            Part.makeBox(aussen - 2 * rb, aussen - 2 * rb, sd + 2,
                         FreeCAD.Vector(x0 + rb, x0 + rb, z_streben - 1))))

    # 4) Struts lengthwise (in Y), on the radiator pitch, centred
    # The struts are created already rounded: finding and filleting a box
    # afterwards costs too much computing time with ~11 struts.
    # The four lengthwise edges are rounded, i.e. top AND bottom.
    rs = g("strebe_r")
    n = int(za / rast)
    x = (za - (n * rast - (rast - stb))) / 2
    while x + stb <= za:
        # Flush with the TOP of the top frame, not with the underside: it is
        # printed upside down, and this face then lies on the bed. If the
        # thinner struts were flush at the bottom, they would start 0.9 mm
        # above the bed and would have to be printed as bridges over 129 mm.
        st = Part.makeBox(stb, aussen, std,
                          FreeCAD.Vector(x, x0, z_streben + sd - std))
        if rs > 0:
            laengs = [e for e in st.Edges
                      if e.BoundBox.YLength > aussen - 1e-6]
            try:
                st = st.makeFillet(rs, laengs)
            except Exception:
                pass
        teile.append(st)
        x += rast

    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)

    # Break edges. Two radii, because the struts are thinner than the outer
    # wall: kanten_r would halve a 2.5 mm thick strut.
    def _runden(shape, radius, waehle):
        versucht = set()
        for _ in range(200):
            ziel = marke = None
            for e in shape.Edges:
                try:
                    if e.Curve.__class__.__name__ != "Line":
                        continue
                except TypeError:
                    continue
                eb = e.BoundBox
                k = (round(eb.XMin, 2), round(eb.YMin, 2), round(eb.ZMin, 2),
                     round(e.Length, 2))
                if k in versucht:
                    continue
                if waehle(e, shape.BoundBox):
                    ziel, marke = e, k
                    break
            if ziel is None:
                break
            versucht.add(marke)
            try:
                shape = shape.makeFillet(radius, [ziel])
            except Exception:
                pass
        return shape

    rad_a = g("kanten_r")
    b0 = r.BoundBox

    # 1) Outer edges of the hood: the four vertical corners AND the
    #    circumferential horizontal edges at top and bottom. Lastly the
    #    horizontal ones were missing, so the hood was only broken at the
    #    corners.
    def _senkrecht(e, b):
        eb = e.BoundBox
        senk = eb.ZLength > rad_a and eb.XLength < 1e-6 and eb.YLength < 1e-6
        randk = (abs(eb.XMin - b.XMin) < 1e-6 or abs(eb.XMax - b.XMax) < 1e-6
                 or abs(eb.YMin - b.YMin) < 1e-6 or abs(eb.YMax - b.YMax) < 1e-6)
        return senk and randk
    r = _runden(r, rad_a, _senkrecht)

    def _waagerecht(e, b):
        eb = e.BoundBox
        flach = eb.ZLength < 1e-6 and e.Length > rad_a
        aussen_xy = (abs(eb.XMin - b.XMin) < 1e-6 or abs(eb.XMax - b.XMax) < 1e-6
                     or abs(eb.YMin - b.YMin) < 1e-6 or abs(eb.YMax - b.YMax) < 1e-6)
        ganz_oben  = abs(eb.ZMin - b.ZMax) < 1e-6
        ganz_unten = abs(eb.ZMin - b.ZMin) < 1e-6
        return flach and aussen_xy and (ganz_oben or ganz_unten)
    r = _runden(r, min(rad_a, sd / 2 - 0.05), _waagerecht)

    return r.removeSplitter()


o = d.getObject("Schutz") or d.addObject("Part::Feature", "Schutz")
o.Shape = schutz()
o.Label = "Finger guard %s" % ZIEL.replace("RadiatorFan", "")
d.recompute()
d.saveAs(os.path.join(out, GUARD + ".FCStd")) if not d.FileName else d.save()
s = o.Shape
bb = s.BoundBox
print("  guard %.1f x %.1f x %.1f mm  %.2f cm3  solids %d  valid %s" % (
    bb.XLength, bb.YLength, bb.ZLength, s.Volume / 1000, len(s.Solids), s.isValid()))

gedreht = s.copy()
gedreht.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), 180)
gedreht.translate(FreeCAD.Vector(0, 0, -gedreht.BoundBox.ZMin))
m = MeshPart.meshFromShape(Shape=gedreht, LinearDeflection=0.05,
                           AngularDeflection=0.5, Relative=False)
m.write(os.path.join(out, GUARD + ".stl"))
print("  %s.stl (printed upside down)  solid=%s  deviation %.4f%%" % (
    GUARD, m.isSolid(), abs(m.Volume - s.Volume) / s.Volume * 100))
