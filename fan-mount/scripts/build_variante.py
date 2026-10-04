"""Build the mount (Halter) in the document named by ZIEL (set from outside).

Run inside FreeCAD with the document already open, e.g.
    ZIEL = "RadiatorFanLarge"
    exec(open(".../fan-mount/scripts/build_variante.py").read())
STL and FCStd are written next to the opened document (fan-mount/cad/);
set the environment variable FAN_MOUNT_CAD to write somewhere else.

Uses the same functions as scripts/passprobe.py, but against the spreadsheet of
the new document - there the fan sits centred (no wall offset) and the ribs lie
on the unperforated edge strips without an offset.

German names are kept for the spreadsheet aliases (Masse) and local variables
- see the glossary in docs/design-notes.md.
"""
import FreeCAD, Part, MeshPart, os

d = FreeCAD.getDocument(ZIEL)
sh = d.getObject("Masse")
g = lambda a: float(sh.get(a))
out = os.environ.get("FAN_MOUNT_CAD") or os.path.dirname(d.FileName) or os.getcwd()

nase_h = 1.5


def halter(tiefe, hinten_ueber, rand, x0=0.0):
    zi, za, zd = g("z_innen"), g("z_aussen"), g("z_dicke")
    zh, ah, al = g("z_hoehe"), g("z_auflage"), g("z_ecke")
    xk = x0 - zd

    teile = [Part.makeBox(za, za, zh, FreeCAD.Vector(xk, -hinten_ueber - zd, 0)).cut(
                 Part.makeBox(zi, zi, zh + 2, FreeCAD.Vector(x0, -hinten_ueber, -1)))]
    for dx, dy2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
        teile.append(Part.makeBox(al, al, ah, FreeCAD.Vector(
            x0 + (zi - al) * dx, -hinten_ueber + (zi - al) * dy2, 0)))
    rb, dy = g("rippe_b"), g("rippe_dy")
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, dy, 0)))
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, tiefe - rb + dy, 0)))
    # Sheet C has TWO perforated fields with an unperforated centre web
    # between them. It carries a third rib without covering any air outlet -
    # exactly what the web is there for.
    try:
        ms = g("stegmitte")
    except Exception:
        ms = 0.0
    if ms > 0:
        mitte_von = g("a_rand") + g("a_lochfeld")
        teile.append(Part.makeBox(za, ms, ah,
                                  FreeCAD.Vector(xk, mitte_von + dy, 0)))
    bb_ = g("blende_b")
    teile.append(Part.makeBox(bb_, tiefe, ah, FreeCAD.Vector(xk - bb_, 0, 0)))
    teile.append(Part.makeBox(bb_, tiefe, ah, FreeCAD.Vector(xk + za, 0, 0)))

    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)

    rad = g("kanten_r")

    def _kandidat(shape):
        b = shape.BoundBox
        for e in shape.Edges:
            try:
                if e.Curve.__class__.__name__ != "Line":
                    continue
            except TypeError:
                continue
            eb = e.BoundBox
            senk = eb.ZLength > rad and eb.XLength < 1e-6 and eb.YLength < 1e-6
            randk = (abs(eb.XMin - b.XMin) < 1e-6 or abs(eb.XMax - b.XMax) < 1e-6
                     or abs(eb.YMin - b.YMin) < 1e-6 or abs(eb.YMax - b.YMax) < 1e-6)
            oben = (abs(eb.ZMin - b.ZMax) < 1e-6 and eb.ZLength < 1e-6
                    and e.Length > rad)
            auf_hoehe = (abs(eb.ZMin - g("z_auflage")) < 1e-6
                         and eb.ZLength < 1e-6 and e.Length > rad)
            laengs = abs(eb.XLength) > 1e-6 and (
                abs(eb.YMin - b.YMin) < 1e-6 or abs(eb.YMax - b.YMax) < 1e-6
                or abs(eb.YMin) < 1e-6 or abs(eb.YMax - g("a_tiefe")) < 1e-6)
            stirn = (abs(eb.XLength) < 1e-6
                     and (abs(eb.XMin - b.XMin) < 1e-6
                          or abs(eb.XMax - b.XMax) < 1e-6))
            if (senk and randk) or oben or (auf_hoehe and (laengs or stirn)):
                yield e

    gerundet, versucht = 0, set()
    for _ in range(60):
        ziel = marke = None
        for e in _kandidat(r):
            kennung = (round(e.BoundBox.XMin, 2), round(e.BoundBox.YMin, 2),
                       round(e.BoundBox.ZMin, 2), round(e.Length, 2))
            if kennung not in versucht:
                ziel, marke = e, kennung
                break
        if ziel is None:
            break
        versucht.add(marke)
        try:
            r = r.makeFillet(rad, [ziel])
            gerundet += 1
        except Exception:
            pass
    print("  edges rounded: %d" % gerundet)

    kr = g("kehle_r")
    if kr > 0:
        for _ in range(8):
            ziel = None
            for e in r.Edges:
                try:
                    if e.Curve.__class__.__name__ != "Line":
                        continue
                except TypeError:
                    continue
                eb = e.BoundBox
                senkrecht_in_y = (abs(eb.XLength) < 1e-6 and abs(eb.ZLength) < 1e-6
                                  and eb.YLength > kr)
                am_uebergang = (abs(eb.ZMin - g("z_auflage")) < 1e-6
                                and (abs(eb.XMin - xk) < 1e-6
                                     or abs(eb.XMin - (xk + za)) < 1e-6))
                if senkrecht_in_y and am_uebergang:
                    ziel = e
                    break
            if ziel is None:
                break
            try:
                r = r.makeFillet(kr, [ziel])
            except Exception:
                break

    sp = g("z_spiel") / 2
    lx0, ly0 = x0 + sp, -hinten_ueber + sp
    off = (g("lueftergroesse") - g("schraub_lk")) / 2
    for dx, dy2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
        c = FreeCAD.Vector(lx0 + off + g("schraub_lk") * dx,
                           ly0 + off + g("schraub_lk") * dy2, -1)
        r = r.cut(Part.makeCylinder(g("schraub_d") / 2, ah + 2, c))
    for cx in (xk - bb_ / 2, xk + za + bb_ / 2):
        r = r.cut(Part.makeCylinder(g("blende_sd") / 2, ah + 2,
                                    FreeCAD.Vector(cx, tiefe / 2, -1)))
    return r.removeSplitter()


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
    # Funnel at BOTH ends: the screw finds the start without tipping over.
    # It begins at the former mid-range diameter (2.5 mm) and tapers to the
    # core hole. On both sides because the peg has to stay usable turned
    # over.
    td, tt = g("trichter_d"), g("trichter_t")
    if td > sd:
        koerper = koerper.cut(Part.makeCone(td / 2, sd / 2, tt,
                                            FreeCAD.Vector(cx, cy, h - tt)))
        koerper = koerper.cut(Part.makeCone(sd / 2, td / 2, tt,
                                            FreeCAD.Vector(cx, cy, 0)))
    return koerper.removeSplitter()


o = d.getObject("Halter") or d.addObject("Part::Feature", "Halter")
o.Shape = halter(g("a_tiefe"), g("a_hinten"), g("a_rand"))
o.Label = "Halter %s" % ZIEL
d.recompute()
bb = o.Shape.BoundBox
print("  mount %.0fx%.0fx%.0f mm  %.2f cm3" % (
    bb.XLength, bb.YLength, bb.ZLength, o.Shape.Volume / 1000))

zi = g("z_innen")
zb, zl = g("zapfen_b"), g("zapfen_l")
# For PRINTING the pegs lie where the mount is open. On a sheet with two
# perforated fields the middle is occupied (rib on the centre web), so move
# to the first field.
try:
    _ms = g("stegmitte")
except Exception:
    _ms = 0.0
if _ms > 0:
    # Peg length = width of the perforated field, so they would otherwise
    # butt flush against the adjacent ribs and merge into one body on fuse.
    # Moving them 3 mm forward makes room on both sides.
    # Centre them in the FREE area between rib 1 and the centre rib, not in
    # the middle of the field: the ribs cover its edges.
    _frei_von = g("rippe_b")
    _frei_bis = g("a_rand") + g("a_lochfeld")
    ymid = _frei_von + (_frei_bis - _frei_von - zl) / 2
else:
    ymid = g("a_tiefe") / 2 - zl / 2
# Two pegs are enough - both core-hole sizes have proven themselves, the
# new value lies in between.
saetze = [g("zapfen_sd"), g("zapfen_sd")]
n = len(saetze)
if _ms > 0 and n > 2:
    # Two perforated fields: spread the pegs over both. In a single row they
    # would touch at 7.8 mm width and merge on fuse. With only two pegs there
    # is plenty of room for that.
    # Row 2 likewise centred in its free area: between the centre rib and the
    # rear rib.
    _f2_von = g("a_rand") + g("a_lochfeld") + _ms
    _f2_bis = g("a_tiefe") - g("rippe_b")
    reihe2 = _f2_von + (_f2_bis - _f2_von - zl) / 2
    proreihe = n // 2
    luecke = (zi - proreihe * zb) / (proreihe + 1)
    stueck = []
    for i, k in enumerate(saetze):
        x = luecke + (i % proreihe) * (zb + luecke)
        y = ymid if i < proreihe else reihe2
        stueck.append(zapfen(x, y, k))
else:
    luecke = (zi - n * zb) / (n + 1)
    stueck = [zapfen(luecke + i * (zb + luecke), ymid, k) for i, k in enumerate(saetze)]

oz = d.getObject("Zapfen") or d.addObject("Part::Feature", "Zapfen")
gz = stueck[0]
for t in stueck[1:]:
    gz = gz.fuse(t)
oz.Shape = gz
oz.Label = "Zapfen (pegs, 2x each M2/M3/M4)"
d.recompute()

ges = o.Shape.fuse(oz.Shape)
mg = MeshPart.meshFromShape(Shape=ges, LinearDeflection=0.05,
                            AngularDeflection=0.5, Relative=False)
mg.write(os.path.join(out, ZIEL + ".stl"))
print("  complete: %d bodies, %.2f cm3, solid=%s" % (
    len(ges.Solids), ges.Volume / 1000, mg.isSolid()))

d.saveAs(os.path.join(out, ZIEL + ".FCStd"))
print("  saved:", d.FileName)
