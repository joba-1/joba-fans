"""Generate the fit-test frames (Passproben) from the 'Masse' spreadsheet.

Run inside FreeCAD with fan-mount/cad/passprobe.FCStd open
(View -> Panels -> Python console):
    exec(open('<repo>/fan-mount/scripts/passprobe.py').read())

Creates/updates Rahmen_A/B/C and writes the STLs next to the opened document
(fan-mount/cad/). All dimensions come from the spreadsheet; nothing is
hard-coded here except the nose geometry (nase_h/nase_l) and the gap between
parts in the layout.

The second half of this file builds "Halter A", the first design of the mount
for radiator A (halter_A.stl, halter_A_komplett.stl). It is kept for
reference; the current mounts are built by build_variante.py
(RadiatorFanSmall/Medium/Large).

German names are kept for the spreadsheet aliases (Masse) and local variables
- see the glossary in docs/design-notes.md.
"""
import FreeCAD, Part, MeshPart, os

# The internal document name comes from the file name when opened and is then
# lower case; when newly created it is capitalised. Allow both.
d = None
for _n in ("Passprobe", "passprobe"):
    try:
        d = FreeCAD.getDocument(_n)
        break
    except NameError:
        pass
if d is None:
    raise RuntimeError("document Passprobe is not open")
sh  = d.getObject("Masse")
g   = lambda a: float(sh.get(a))

nase_h, nase_l, luecke = 1.5, 1.5, 12.0


def rahmen(tiefe, x0):
    """Edge-grip clamp. Layout along y: jaw | sheet | jaw."""
    pd, bd, maul, L = g("plattendicke"), g("backendicke"), g("maulweite"), g("probelaenge")
    breite = tiefe + 2 * bd
    h = maul + nase_h
    teile = [
        Part.makeBox(L, breite, pd, FreeCAD.Vector(x0, 0, 0)),                  # plate
        Part.makeBox(L, bd, h,      FreeCAD.Vector(x0, 0, -h)),                 # jaw front
        Part.makeBox(L, bd, h,      FreeCAD.Vector(x0, bd + tiefe, -h)),        # jaw back
        Part.makeBox(L, nase_l, nase_h, FreeCAD.Vector(x0, bd, -h)),            # nose front
        Part.makeBox(L, nase_l, nase_h, FreeCAD.Vector(x0, bd + tiefe - nase_l, -h)),
    ]
    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)
    return r.removeSplitter()


def pruefe(shape, tiefe):
    """The jaw must be free over the full sheet depth, the noses must grip.

    x is chosen relative to the part - in the layout the parts stand offset
    next to each other, an absolute x would only hit the first one.
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
    print("%s %3.0fx%3.0fx%.0f  jaw free=%s  nose grips=%s  solid=%s  bed=%s" % (
        hk, bb.XLength, bb.YLength, bb.ZLength, frei, greift, m.isSolid(),
        "OK" if max(bb.XLength, bb.YLength) <= bett else "TOO LARGE"))
    x += g("probelaenge") + luecke

d.recompute()
print("errors:", [o.Name for o in d.Objects if o.isValid() is False])


# ---------------------------------------------------------------------------
# Halter (mount): fit-test frame + collar (fan seat) in one part
# ---------------------------------------------------------------------------

def halter(tiefe, hinten_ueber, rand, x0=0.0):
    """Flat collar, rests loosely on the sheet (fastening: a part of its own).

    Coordinates: y=0 is the REAR edge of the sheet (wall side), y=tiefe the
    front edge. hinten_ueber says how far the fan projects beyond the rear
    edge - that gives the asymmetric seat.

    The part ends at z=0 and therefore stands on the bed without turning and
    without overhangs.
    """
    zi, za, zd = g("z_innen"), g("z_aussen"), g("z_dicke")
    zh, ah, al = g("z_hoehe"), g("z_auflage"), g("z_ecke")
    xk = x0 - zd

    teile = [Part.makeBox(za, za, zh, FreeCAD.Vector(xk, -hinten_ueber - zd, 0)).cut(
                 Part.makeBox(zi, zi, zh + 2, FreeCAD.Vector(x0, -hinten_ueber, -1)))]
    # Four square fan rests in the collar corners.
    for dx, dy2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
        teile.append(Part.makeBox(al, al, ah, FreeCAD.Vector(
            x0 + (zi - al) * dx, -hinten_ueber + (zi - al) * dy2, 0)))
    # RIBS instead of a continuous web: only on the unperforated edge strips.
    # A solid web across the full depth covers 64 % of the fan outlet - exactly
    # the part above the perforated field.
    # Both ribs are shifted by rippe_dy so that rib 1 joins the front rest
    # seamlessly; the distance between them stays the same.
    rb, dy = g("rippe_b"), g("rippe_dy")
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, dy, 0)))
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, tiefe - rb + dy, 0)))
    # BLENDE (baffle): covers the neighbouring slots left and right so the air
    # does not short-circuit back up through them instead of going down
    # through the convector fins. Only over the sheet depth, so nothing hangs
    # free in the air.
    bb_ = g("blende_b")
    teile.append(Part.makeBox(bb_, tiefe, ah, FreeCAD.Vector(xk - bb_, 0, 0)))
    teile.append(Part.makeBox(bb_, tiefe, ah, FreeCAD.Vector(xk + za, 0, 0)))

    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)

    # Break outer edges - fuse first, then round, otherwise the radius hits
    # edges that disappear later anyway. Only vertical edges on the outer
    # contour and the upper circumferential edge of the collar; rest faces and
    # the underside stay flat.
    rad = g("kanten_r")
    bb = r.BoundBox
    kanten = []
    for e in r.Edges:
        eb = e.BoundBox
        senkrecht = eb.ZLength > 1e-6 and eb.XLength < 1e-6 and eb.YLength < 1e-6
        aussen = (abs(eb.XMin - bb.XMin) < 1e-6 or abs(eb.XMax - bb.XMax) < 1e-6
                  or abs(eb.YMin - bb.YMin) < 1e-6 or abs(eb.YMax - bb.YMax) < 1e-6)
        oben = abs(eb.ZMin - bb.ZMax) < 1e-6 and abs(eb.ZLength) < 1e-6
        if (senkrecht and aussen) or oben:
            kanten.append(e)
    # Break outer edges. Only STRAIGHT vertical edges on the outer contour and
    # the upper circumferential edge - rest faces and underside stay flat.
    # Round one at a time: OCCT fails on the whole list, almost never on single
    # edges. Search again after each fillet, because the indices move.
    rad = g("kanten_r")

    def _kandidat(shape):
        b = shape.BoundBox
        for e in shape.Edges:
            try:
                if e.Curve.__class__.__name__ != "Line":
                    continue                    # already rounded
            except TypeError:
                continue                        # edge type without a Curve
            eb = e.BoundBox
            senk = eb.ZLength > rad and eb.XLength < 1e-6 and eb.YLength < 1e-6
            rand = (abs(eb.XMin - b.XMin) < 1e-6 or abs(eb.XMax - b.XMax) < 1e-6
                    or abs(eb.YMin - b.YMin) < 1e-6 or abs(eb.YMax - b.YMax) < 1e-6)
            oben = (abs(eb.ZMin - b.ZMax) < 1e-6 and eb.ZLength < 1e-6
                    and e.Length > rad)
            # The THREE free top edges of each baffle: two long sides and the
            # outer end. They lie at rest height, not at BoundBox.ZMax. The
            # fourth edge - the transition to the collar - stays sharp: a
            # reinforcement of material is wanted there.
            auf_hoehe = (abs(eb.ZMin - g("z_auflage")) < 1e-6
                         and eb.ZLength < 1e-6 and e.Length > rad)
            laengs = abs(eb.XLength) > 1e-6 and (
                abs(eb.YMin - b.YMin) < 1e-6 or abs(eb.YMax - b.YMax) < 1e-6
                or abs(eb.YMin) < 1e-6 or abs(eb.YMax - g("a_tiefe")) < 1e-6)
            stirn = (abs(eb.XLength) < 1e-6
                     and (abs(eb.XMin - b.XMin) < 1e-6
                          or abs(eb.XMax - b.XMax) < 1e-6))
            blende = auf_hoehe and (laengs or stirn)
            if (senk and rand) or oben or blende:
                yield e

    gerundet, versucht = 0, set()
    for _ in range(60):                         # upper limit against endless loops
        ziel = marke = None
        for e in _kandidat(r):
            kennung = (round(e.BoundBox.XMin, 2), round(e.BoundBox.YMin, 2),
                       round(e.BoundBox.ZMin, 2), round(e.Length, 2))
            if kennung not in versucht:
                ziel, marke = e, kennung
                break
        if ziel is None:
            break
        versucht.add(marke)                     # note it even on failure,
        try:                                    # otherwise a single edge that
            r = r.makeFillet(rad, [ziel])       # cannot be rounded blocks all
            gerundet += 1                       # the following ones
        except Exception:
            pass                                # edge too short for the radius
    print("  edges rounded: %d" % gerundet)

    # FILLET (Kehle) at the transition baffle -> collar wall. This is an inner
    # edge: the rounding runs the other way than on the outer edges and adds
    # material instead of removing it. It stiffens the 2 mm thin baffle exactly
    # where it hangs on the 28 mm high collar wall.
    #
    # Must come AFTER the outer edges: otherwise the lengthwise roundings of the
    # baffle run through to the transition and eat the fillet away.
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

    # Screw holes to the fan standard: hole spacing schraub_lk (105 mm for a
    # 120 mm fan), i.e. (lueftergroesse - schraub_lk)/2 from every fan edge.
    # The reference is the fan corner, not the rest - so the holes move
    # correctly with the fan position or collar clearance.
    sp = g("z_spiel") / 2
    lx0, ly0 = x0 + sp, -hinten_ueber + sp
    off = (g("lueftergroesse") - g("schraub_lk")) / 2
    for dx, dy2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
        c = FreeCAD.Vector(lx0 + off + g("schraub_lk") * dx,
                           ly0 + off + g("schraub_lk") * dy2, -1)
        r = r.cut(Part.makeCylinder(g("schraub_d") / 2, ah + 2, c))

    # One screw hole per baffle for the peg underneath: centred on the radiator
    # depth (y) and centred in the baffle (x).
    bb_ = g("blende_b")
    for cx in (xk - bb_ / 2, xk + za + bb_ / 2):
        r = r.cut(Part.makeCylinder(g("blende_sd") / 2, ah + 2,
                                    FreeCAD.Vector(cx, tiefe / 2, -1)))
    return r.removeSplitter()


def _loecher_ok(s, hinten_ueber):
    """All four bores open, and material remains all around."""
    sp, ah, zi, al = g("z_spiel") / 2, g("z_auflage"), g("z_innen"), g("z_ecke")
    lk, dm = g("schraub_lk"), g("schraub_d")
    off = (g("lueftergroesse") - lk) / 2
    ins = lambda p: s.isInside(p, 1e-6, True)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        cx, cy = sp + off + lk * dx, -hinten_ueber + sp + off + lk * dy
        if ins(FreeCAD.Vector(cx, cy, ah / 2)):
            return False                       # hole not through
        for ex, ey in ((dm / 2 + 1.2, 0), (-dm / 2 - 1.2, 0),
                       (0, dm / 2 + 1.2), (0, -dm / 2 - 1.2)):
            if not ins(FreeCAD.Vector(cx + ex, cy + ey, ah / 2)):
                return False                   # edge broken out
    return True


def pruefe_halter(s, tiefe, hinten_ueber, rand):
    """Checks on the flat collar (the part ends at z=0)."""
    zi, ah, zd = g("z_innen"), g("z_auflage"), g("z_dicke")
    ins = lambda xx, yy, zz: s.isInside(FreeCAD.Vector(xx, yy, zz), 1e-6, True)
    # The reference is the COLLAR at x=0, not the BoundBox - that grows with the
    # baffle and would otherwise shift all test points.
    hi, x = hinten_ueber, 3.0

    def durchgehend(y0, y1):
        return all(ins(x, y0 + (y1 - y0) * (i + 0.5) / 40, ah / 2) for i in range(40))

    return {
        "flat from z=0":   abs(s.BoundBox.ZMin) < 1e-6,
        "fits the bed":   max(s.BoundBox.XLength, s.BoundBox.YLength) <= g("druckbett"),
        "no overhangs":   not any(
            f.Surface.__class__.__name__ == "Plane"
            and f.normalAt(0.5, 0.5).z <= -0.9 and f.BoundBox.ZMin > 0.01
            for f in s.Faces),
        # The path from the fan to the perforated field must be free. Without
        # this check a floor under the fan goes unnoticed.
        "field open":     not any(
            ins(zi * (i + 0.5) / 9,
                rand + (tiefe - 2 * rand) * (j + 0.5) / 11, ah / 2)
            for i in range(9) for j in range(11)),
        # Rib 1 must join the front rest seamlessly.
        "front seam":    durchgehend(-hi, g("rippe_dy") + g("rippe_b")),
        # The four screw holes must be free and lie within the rests.
        "screw holes":    _loecher_ok(s, hinten_ueber),
    }


if __name__ != "do_not_run":
    o = d.getObject("Halter_A") or d.addObject("Part::Feature", "Halter_A")
    o.Shape = halter(g("a_tiefe"), g("a_hinten"), g("a_rand"))
    o.Label = "Halter A (office, %.0f mm fan)" % g("luefterhoehe")
    d.recompute()
    res = pruefe_halter(o.Shape, g("a_tiefe"), g("a_hinten"), g("a_rand"))
    for k, v in res.items():
        print("  %-16s %s" % (k, "OK" if v else "FAIL"))
    m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=0.05,
                               AngularDeflection=0.5, Relative=False)
    m.write(os.path.join(out, "halter_A.stl"))   # flat, no turning needed
    bb = o.Shape.BoundBox
    print("  Halter A %.0fx%.0fx%.0f mm  %.1f cm3  solid=%s  %s" % (
        bb.XLength, bb.YLength, bb.ZLength, o.Shape.Volume / 1000, m.isSolid(),
        "PASSED" if all(res.values()) else "FAILED"))


# ---------------------------------------------------------------------------
# Zapfen (pegs): blocks that engage the radiator slots with a positive fit
# ---------------------------------------------------------------------------

def zapfen(x0=0.0, y0=0.0, sd=None):
    """Solid block with rounded edges that engages a radiator slot with a
    positive fit.

    Outer size = slot width minus clearance x width of the perforated field,
    so it sits in the slot with a positive fit and can neither turn nor
    wander. It is screwed from above through the baffle; zapfen_sd is the
    CORE hole for a self-tapping M3, not a clearance hole.
    """
    b, l = g("zapfen_b"), g("zapfen_l")
    h, rad = g("zapfen_h"), g("zapfen_r")
    if sd is None:
        sd = g("zapfen_sd")

    aussen = Part.makeBox(b, l, h, FreeCAD.Vector(x0, y0, 0))
    # Round only the four VERTICAL edges - the top face stays flat to rest
    # against the baffle, at the bottom the edge for insertion.
    senk = [e for e in aussen.Edges
            if abs(e.Vertexes[0].Point.z - e.Vertexes[-1].Point.z) > h - 1e-6]
    koerper = aussen.makeFillet(rad, senk)
    # Core hole THROUGH, so the peg is usable on both sides: if the thread
    # gives way on one side, it is turned over.
    koerper = koerper.cut(Part.makeCylinder(
        sd / 2, h + 2, FreeCAD.Vector(x0 + b / 2, y0 + l / 2, -1)))
    return koerper.removeSplitter()


if __name__ != "do_not_run":
    # For PRINTING the pegs are placed in the fan opening - the mount is empty
    # there anyway, so it costs no bed area. They are installed under the
    # baffles, at their existing holes.
    zi = g("z_innen")
    zb, zl = g("zapfen_b"), g("zapfen_l")
    ymid = g("a_tiefe") / 2 - zl / 2                  # centred on the sheet depth

    # Two pegs each for M2, M3 and M4 - which screws are at hand only shows
    # during assembly. Evenly distributed across the opening.
    saetze = [("M2", g("kern_m2")), ("M3", g("zapfen_sd")), ("M4", g("kern_m4"))]
    stueck, n = [], 2 * len(saetze)
    luecke = (zi - n * zb) / (n + 1)
    for i, (_, kern) in enumerate([s for s in saetze for _ in range(2)]):
        x = luecke + i * (zb + luecke)
        stueck.append(zapfen(x, ymid, kern))

    oz = d.getObject("Zapfen_A") or d.addObject("Part::Feature", "Zapfen_A")
    ges_z = stueck[0]
    for t in stueck[1:]:
        ges_z = ges_z.fuse(t)
    oz.Shape = ges_z
    oz.Label = "Zapfen A (2x each M2/M3/M4)"
    d.recompute()
    bbz = oz.Shape.BoundBox
    print("  Zapfen A %.1fx%.1fx%.1f mm  %.2f cm3  (%d pieces: 2x each M2/M3/M4)" % (
        bbz.XLength, bbz.YLength, bbz.ZLength, oz.Shape.Volume / 1000, n))

    # One file with all bodies: mount + pegs. An STL may contain several
    # separate volumes; the slicer treats them as objects of their own.
    ges = d.getObject("Halter_A").Shape.fuse(oz.Shape)
    mg = MeshPart.meshFromShape(Shape=ges, LinearDeflection=0.05,
                                AngularDeflection=0.5, Relative=False)
    mg.write(os.path.join(out, "halter_A_komplett.stl"))
    print("  complete: %d solids, %.2f cm3, solid=%s" % (
        len(ges.Solids), ges.Volume / 1000, mg.isSolid()))
