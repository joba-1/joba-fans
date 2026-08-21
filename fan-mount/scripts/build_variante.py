"""Halter im Dokument ZIEL erzeugen (Variable von aussen gesetzt).

Nutzt dieselben Funktionen wie scripts/passprobe.py, aber gegen die
Tabelle des neuen Dokuments - dort sitzt der Luefter mittig (kein
Wandversatz) und die Rippen liegen ohne Versatz auf den Randstreifen.
"""
import FreeCAD, Part, MeshPart, os

d = FreeCAD.getDocument(ZIEL)
sh = d.getObject("Masse")
g = lambda a: float(sh.get(a))
out = "/data/joachim/git/fan-stand/cad"

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
    # Blech C hat ZWEI Lochfelder mit einem ungelochten Mittelsteg dazwischen.
    # Der traegt eine dritte Rippe, ohne Luftaustritt zu verdecken - genau
    # das, wofuer der Steg da ist.
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
    print("  Kanten gerundet: %d" % gerundet)

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
    # Trichter an BEIDEN Enden: die Schraube findet den Anfang, ohne
    # wegzukippen. Beginnt beim frueheren mittleren Durchmesser (2,5 mm)
    # und laeuft auf das Kernloch zu. Beidseitig, weil der Zapfen
    # umgedreht verwendbar bleiben soll.
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
print("  Halter %.0fx%.0fx%.0f mm  %.2f cm3" % (
    bb.XLength, bb.YLength, bb.ZLength, o.Shape.Volume / 1000))

zi = g("z_innen")
zb, zl = g("zapfen_b"), g("zapfen_l")
# Die Zapfen liegen fuer den DRUCK dort, wo der Halter offen ist. Bei einem
# Blech mit zwei Lochfeldern ist die Mitte belegt (Rippe auf dem Mittelsteg),
# also auf das erste Lochfeld ausweichen.
try:
    _ms = g("stegmitte")
except Exception:
    _ms = 0.0
if _ms > 0:
    # Zapfenlaenge = Lochfeldbreite, also stossen sie sonst bündig an die
    # angrenzenden Rippen und verschmelzen beim fuse zu einem Koerper.
    # 3 mm nach vorne ruecken schafft beidseitig Luft.
    # mittig in den FREIEN Bereich zwischen Rippe 1 und Mittelrippe legen,
    # nicht mittig ins Lochfeld: die Rippen ueberdecken dessen Raender.
    _frei_von = g("rippe_b")
    _frei_bis = g("a_rand") + g("a_lochfeld")
    ymid = _frei_von + (_frei_bis - _frei_von - zl) / 2
else:
    ymid = g("a_tiefe") / 2 - zl / 2
# Zwei Zapfen genuegen - beide Kernlochgroessen haben sich bewaehrt,
# der neue Wert liegt dazwischen.
saetze = [g("zapfen_sd"), g("zapfen_sd")]
n = len(saetze)
if _ms > 0 and n > 2:
    # Zwei Lochfelder: die Zapfen auf beide verteilen. In einer Reihe
    # stossen sie bei 7,8 mm Breite sonst aneinander und verschmelzen
    # beim fuse. Bei nur zwei Zapfen ist dafuer reichlich Platz.
    # Reihe 2 ebenso mittig in ihren freien Bereich: zwischen Mittelrippe
    # und hinterer Rippe.
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
oz.Label = "Zapfen (je 2x M2/M3/M4)"
d.recompute()

ges = o.Shape.fuse(oz.Shape)
mg = MeshPart.meshFromShape(Shape=ges, LinearDeflection=0.05,
                            AngularDeflection=0.5, Relative=False)
mg.write(os.path.join(out, ZIEL + ".stl"))
print("  Komplett: %d Koerper, %.2f cm3, solid=%s" % (
    len(ges.Solids), ges.Volume / 1000, mg.isSolid()))

d.saveAs(os.path.join(out, ZIEL + ".FCStd"))
print("  gespeichert:", d.FileName)
