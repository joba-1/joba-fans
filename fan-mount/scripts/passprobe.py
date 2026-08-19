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
    # Vier quadratische Luefterauflagen in den Zargenecken.
    for dx, dy2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
        teile.append(Part.makeBox(al, al, ah, FreeCAD.Vector(
            x0 + (zi - al) * dx, -hinten_ueber + (zi - al) * dy2, 0)))
    # RIPPEN statt eines durchgehenden Stegs: nur auf den ungelochten
    # Randstreifen. Ein Vollsteg ueber die ganze Tiefe verdeckt 64 % des
    # Luefteraustritts - genau den Teil, der ueber dem Lochfeld liegt.
    # Beide Rippen um rippe_dy verschoben, damit Rippe 1 nahtlos an die
    # vordere Auflage anschliesst; ihr gegenseitiger Abstand bleibt gleich.
    rb, dy = g("rippe_b"), g("rippe_dy")
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, dy, 0)))
    teile.append(Part.makeBox(za, rb, ah, FreeCAD.Vector(xk, tiefe - rb + dy, 0)))
    # BLENDE: deckt links und rechts die Nachbarschlitze ab, damit die Luft
    # nicht durch sie zurueck nach oben kurzschliesst, statt durch die
    # Konvektorbleche nach unten zu gehen. Nur ueber der Blechtiefe, damit
    # nichts frei in der Luft haengt.
    bb_ = g("blende_b")
    teile.append(Part.makeBox(bb_, tiefe, ah, FreeCAD.Vector(xk - bb_, 0, 0)))
    teile.append(Part.makeBox(bb_, tiefe, ah, FreeCAD.Vector(xk + za, 0, 0)))

    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)

    # Aussenkanten brechen - erst verschmelzen, dann runden, sonst trifft der
    # Radius Kanten, die spaeter ohnehin verschwinden. Nur senkrechte Kanten
    # am Aussenumriss und die obere Umlaufkante der Zarge; Auflageflaechen
    # und die Unterseite bleiben plan.
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
    # Aussenkanten brechen. Nur GERADE senkrechte Kanten am Aussenumriss und
    # die obere Umlaufkante - Auflageflaechen und Unterseite bleiben plan.
    # Einzeln runden: OCCT scheitert an der ganzen Liste, an einzelnen Kanten
    # fast nie. Nach jedem Fillet neu suchen, denn die Indizes wandern.
    rad = g("kanten_r")

    def _kandidat(shape):
        b = shape.BoundBox
        for e in shape.Edges:
            try:
                if e.Curve.__class__.__name__ != "Line":
                    continue                    # schon gerundet
            except TypeError:
                continue                        # Kantentyp ohne Curve
            eb = e.BoundBox
            senk = eb.ZLength > rad and eb.XLength < 1e-6 and eb.YLength < 1e-6
            rand = (abs(eb.XMin - b.XMin) < 1e-6 or abs(eb.XMax - b.XMax) < 1e-6
                    or abs(eb.YMin - b.YMin) < 1e-6 or abs(eb.YMax - b.YMax) < 1e-6)
            oben = (abs(eb.ZMin - b.ZMax) < 1e-6 and eb.ZLength < 1e-6
                    and e.Length > rad)
            # Die DREI freien Oberkanten je Blende: zwei Laengsseiten und die
            # Stirnseite aussen. Sie liegen auf Auflagehoehe, nicht auf
            # BoundBox.ZMax. Die vierte Kante - der Uebergang zur Zarge -
            # bleibt scharf: dort ist eine Materialverstaerkung erwuenscht.
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
    for _ in range(60):                         # Obergrenze gegen Endlosschleife
        ziel = marke = None
        for e in _kandidat(r):
            kennung = (round(e.BoundBox.XMin, 2), round(e.BoundBox.YMin, 2),
                       round(e.BoundBox.ZMin, 2), round(e.Length, 2))
            if kennung not in versucht:
                ziel, marke = e, kennung
                break
        if ziel is None:
            break
        versucht.add(marke)                     # auch bei Misserfolg vermerken,
        try:                                    # sonst blockiert eine einzelne
            r = r.makeFillet(rad, [ziel])       # unrundbare Kante alle weiteren
            gerundet += 1
        except Exception:
            pass                                # Kante zu kurz fuer den Radius
    print("  Kanten gerundet: %d" % gerundet)

    # KEHLE am Uebergang Blende -> Zargenwand. Das ist eine Innenkante: die
    # Rundung laeuft andersherum als an den Aussenkanten und fuegt Material
    # hinzu statt es wegzunehmen. Sie versteift die 2 mm duenne Blende genau
    # dort, wo sie an der 28 mm hohen Zargenwand haengt.
    #
    # Muss NACH den Aussenkanten kommen: die Laengsrundungen der Blende
    # laufen sonst bis an den Uebergang durch und fressen die Kehle weg.
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

    # Verschraubungsloecher nach Luefternorm: Lochabstand schraub_lk (105 mm
    # beim 120er), also (lueftergroesse - schraub_lk)/2 von jeder Luefterkante.
    # Bezug ist die Luefterecke, nicht die Auflage - so wandern die Loecher
    # korrekt mit, wenn sich Luefterlage oder Zargenspiel aendert.
    sp = g("z_spiel") / 2
    lx0, ly0 = x0 + sp, -hinten_ueber + sp
    off = (g("lueftergroesse") - g("schraub_lk")) / 2
    for dx, dy2 in ((0, 0), (1, 0), (0, 1), (1, 1)):
        c = FreeCAD.Vector(lx0 + off + g("schraub_lk") * dx,
                           ly0 + off + g("schraub_lk") * dy2, -1)
        r = r.cut(Part.makeCylinder(g("schraub_d") / 2, ah + 2, c))

    # Je ein Schraubloch pro Blende fuer den Zapfen darunter: mittig zur
    # Heizungstiefe (y) und mittig in der Blende (x).
    bb_ = g("blende_b")
    for cx in (xk - bb_ / 2, xk + za + bb_ / 2):
        r = r.cut(Part.makeCylinder(g("blende_sd") / 2, ah + 2,
                                    FreeCAD.Vector(cx, tiefe / 2, -1)))
    return r.removeSplitter()


def _loecher_ok(s, hinten_ueber):
    """Alle vier Bohrungen offen, und rundum bleibt Material stehen."""
    sp, ah, zi, al = g("z_spiel") / 2, g("z_auflage"), g("z_innen"), g("z_ecke")
    lk, dm = g("schraub_lk"), g("schraub_d")
    off = (g("lueftergroesse") - lk) / 2
    ins = lambda p: s.isInside(p, 1e-6, True)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        cx, cy = sp + off + lk * dx, -hinten_ueber + sp + off + lk * dy
        if ins(FreeCAD.Vector(cx, cy, ah / 2)):
            return False                       # Loch nicht durchgehend
        for ex, ey in ((dm / 2 + 1.2, 0), (-dm / 2 - 1.2, 0),
                       (0, dm / 2 + 1.2), (0, -dm / 2 - 1.2)):
            if not ins(FreeCAD.Vector(cx + ex, cy + ey, ah / 2)):
                return False                   # Rand ausgebrochen
    return True


def pruefe_halter(s, tiefe, hinten_ueber, rand):
    """Vier Bedingungen an die flache Zarge (Teil endet bei z=0)."""
    zi, ah, zd = g("z_innen"), g("z_auflage"), g("z_dicke")
    ins = lambda xx, yy, zz: s.isInside(FreeCAD.Vector(xx, yy, zz), 1e-6, True)
    # Bezug ist die ZARGE bei x=0, nicht die BoundBox - die waechst mit der
    # Blende und verschiebt sonst alle Pruefpunkte.
    hi, x = hinten_ueber, 3.0

    def durchgehend(y0, y1):
        return all(ins(x, y0 + (y1 - y0) * (i + 0.5) / 40, ah / 2) for i in range(40))

    return {
        "flach ab z=0":    abs(s.BoundBox.ZMin) < 1e-6,
        "passt aufs Bett": max(s.BoundBox.XLength, s.BoundBox.YLength) <= g("druckbett"),
        "keine Ueberhaenge": not any(
            f.Surface.__class__.__name__ == "Plane"
            and f.normalAt(0.5, 0.5).z <= -0.9 and f.BoundBox.ZMin > 0.01
            for f in s.Faces),
        # Der Weg vom Luefter zum Lochfeld muss frei sein. Fehlt diese
        # Pruefung, faellt ein Boden unter dem Luefter nicht auf.
        "Lochfeld offen": not any(
            ins(zi * (i + 0.5) / 9,
                rand + (tiefe - 2 * rand) * (j + 0.5) / 11, ah / 2)
            for i in range(9) for j in range(11)),
        # Rippe 1 muss nahtlos an die vordere Auflage anschliessen.
        "Naht vorne":     durchgehend(-hi, g("rippe_dy") + g("rippe_b")),
        # Die vier Schraubloecher muessen frei sein und in den Auflagen liegen.
        "Schraubloecher": _loecher_ok(s, hinten_ueber),
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


# ---------------------------------------------------------------------------
# Zapfen: hohle Quader, die formschluessig in die Heizungsschlitze fassen
# ---------------------------------------------------------------------------

def zapfen(x0=0.0, y0=0.0):
    """Massiver Quader mit gerundeten Kanten, der formschluessig in einen
    Heizungsschlitz fasst.

    Aussenmass = Schlitzbreite minus Spiel x Lochfeldbreite, sitzt also
    formschluessig im Schlitz und kann sich weder drehen noch wandern.
    Wird von oben durch die Blende verschraubt; zapfen_sd ist das KERNLOCH
    fuer eine selbstschneidende M3, kein Durchgangsloch.
    """
    b, l = g("zapfen_b"), g("zapfen_l")
    h, rad, sd = g("zapfen_h"), g("zapfen_r"), g("zapfen_sd")

    aussen = Part.makeBox(b, l, h, FreeCAD.Vector(x0, y0, 0))
    # Nur die vier SENKRECHTEN Kanten runden - oben bleibt die Flaeche plan
    # zur Anlage an der Blende, unten die Kante zum Einfuehren.
    senk = [e for e in aussen.Edges
            if abs(e.Vertexes[0].Point.z - e.Vertexes[-1].Point.z) > h - 1e-6]
    koerper = aussen.makeFillet(rad, senk)
    # Kernloch DURCHGEHEND, damit der Zapfen beidseitig verwendbar ist:
    # laesst das Gewinde auf einer Seite nach, wird er umgedreht.
    koerper = koerper.cut(Part.makeCylinder(
        sd / 2, h + 2, FreeCAD.Vector(x0 + b / 2, y0 + l / 2, -1)))
    return koerper.removeSplitter()


if __name__ != "nicht_ausfuehren":
    # Die beiden Zapfen werden fuer den DRUCK in die Luefteroeffnung gelegt -
    # dort ist der Halter ohnehin leer, also kostet es keine Bettflaeche.
    # Montiert werden sie unter den Blenden, an deren vorhandenen Loechern.
    zi = g("z_innen")
    zb, zl = g("zapfen_b"), g("zapfen_l")
    ymid = g("a_tiefe") / 2 - zl / 2                  # mittig zur Blechtiefe
    zapfen_paar = [zapfen(zi * f - zb / 2, ymid) for f in (1 / 3, 2 / 3)]

    oz = d.getObject("Zapfen_A") or d.addObject("Part::Feature", "Zapfen_A")
    oz.Shape = zapfen_paar[0].fuse(zapfen_paar[1])
    oz.Label = "Zapfen A (2x, in der Luefteroeffnung platziert)"
    d.recompute()
    bbz = oz.Shape.BoundBox
    print("  Zapfen A %.1fx%.1fx%.1f mm  %.2f cm3  (2 Stueck)" % (
        bbz.XLength, bbz.YLength, bbz.ZLength, oz.Shape.Volume / 1000))

    # Eine Datei mit allen drei Koerpern: Halter + 2 Zapfen. Ein STL darf
    # mehrere getrennte Volumen enthalten, der Slicer behandelt sie als
    # eigene Objekte.
    ges = d.getObject("Halter_A").Shape.fuse(oz.Shape)
    mg = MeshPart.meshFromShape(Shape=ges, LinearDeflection=0.05,
                                AngularDeflection=0.5, Relative=False)
    mg.write(os.path.join(out, "halter_A_komplett.stl"))
    print("  Komplett: %d Volumenkoerper, %.2f cm3, solid=%s" % (
        len(ges.Solids), ges.Volume / 1000, mg.isSolid()))
