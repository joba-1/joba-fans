"""Fingerschutz-Haube fuer den Luefter.

Stuelpt sich ueber die Zarge und laesst sich abziehen. Der Halt kommt aus
einer Schuerze mit Untermass, die auf der ganzen Umfangslaenge klemmt -
kein Spiel, also kein Vibrationsgeraeusch.

Die Streben laufen laengs zu den Heizungsschlitzen und uebernehmen deren
Raster (Strebe = Blechsteg, Luecke = Schlitz), damit sich das Blechmuster
optisch nach oben fortsetzt.

NULLPUNKT: z=0 ist die OBERKANTE DER ZARGE, also dort, wo die Haube
aufsitzt. Die Schuerze laeuft von da nach unten (negativ), Streben und
Deckel liegen darueber.
"""
import FreeCAD, Part, MeshPart, os

# ZIEL ist der Name der HALTER-Variante; der Schutz kommt in ein eigenes
# Dokument RadiatorFanGuard*, damit die Halter-Dateien unberuehrt bleiben.
quelle = FreeCAD.getDocument(ZIEL)
GUARD = ZIEL.replace("RadiatorFan", "RadiatorFanGuard")
try:
    d = FreeCAD.getDocument(GUARD)
except NameError:
    d = FreeCAD.newDocument(GUARD)
sh = d.getObject("Masse") or quelle.getObject("Masse")
g = lambda a: float(sh.get(a))
out = "/data/joachim/git/fan-stand/cad"


def schutz():
    za, zh, ah, lh = g("z_aussen"), g("z_hoehe"), g("z_auflage"), g("luefterhoehe")
    sb, su, sd = g("schutz_schuerze"), g("schutz_unter"), g("schutz_dicke")
    std = g("strebe_dicke")          # Streben duenner als die Wand
    ab, stb, rast = g("schutz_abstand"), g("strebe_b"), g("strebe_raster")

    # Unterkante der Streben, relativ zur Zargenoberkante
    z_streben = (ah + lh + ab) - zh
    if z_streben < 0:
        raise SystemExit("Streben laegen unter der Zargenoberkante")

    aussen = za + 2 * sd            # Aussenmass der Haube
    x0 = -sd                        # linke Aussenkante (Zarge beginnt bei 0)

    teile = []

    # 1) Schuerze: Kasten nach unten, innen mit Untermass -> klemmt
    teile.append(
        Part.makeBox(aussen, aussen, sb, FreeCAD.Vector(x0, x0, -sb)).cut(
            Part.makeBox(za - 2 * su, za - 2 * su, sb + 2,
                         FreeCAD.Vector(su, su, -sb - 1))))

    # 2) Senkrechter Ring von der Schuerze hoch zur Strebenebene
    if z_streben > 0:
        teile.append(
            Part.makeBox(aussen, aussen, z_streben,
                         FreeCAD.Vector(x0, x0, 0)).cut(
                Part.makeBox(za, za, z_streben + 2,
                             FreeCAD.Vector(0, 0, -1))))

    # 3) Deckelrahmen auf Strebenhoehe
    rb = sd + 2.0
    teile.append(
        Part.makeBox(aussen, aussen, sd,
                     FreeCAD.Vector(x0, x0, z_streben)).cut(
            Part.makeBox(aussen - 2 * rb, aussen - 2 * rb, sd + 2,
                         FreeCAD.Vector(x0 + rb, x0 + rb, z_streben - 1))))

    # 4) Streben laengs (in Y), im Heizungsraster, mittig ausgerichtet
    # Die Streben werden gleich gerundet erzeugt: eine Box hinterher zu
    # suchen und zu fillen kostet bei ~11 Streben zu viel Rechenzeit.
    # Gerundet werden die vier Laengskanten, also oben UND unten.
    rs = g("strebe_r")
    n = int(za / rast)
    x = (za - (n * rast - (rast - stb))) / 2
    while x + stb <= za:
        st = Part.makeBox(stb, aussen, std, FreeCAD.Vector(x, x0, z_streben))
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

    # Kanten brechen. Zwei Radien, weil die Streben duenner sind als die
    # Aussenwand: kanten_r wuerde eine 2,5 mm dicke Strebe halbieren.
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

    # 1) Aussenkanten der Haube: die vier senkrechten Ecken UND die
    #    umlaufenden waagerechten Kanten oben und unten. Zuletzt fehlten
    #    die waagerechten, dadurch war die Haube nur an den Ecken gebrochen.
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
o.Label = "Fingerschutz %s" % ZIEL.replace("RadiatorFan", "")
d.recompute()
d.saveAs(os.path.join(out, GUARD + ".FCStd")) if not d.FileName else d.save()
s = o.Shape
bb = s.BoundBox
print("  Schutz %.1f x %.1f x %.1f mm  %.2f cm3  solids %d  gueltig %s" % (
    bb.XLength, bb.YLength, bb.ZLength, s.Volume / 1000, len(s.Solids), s.isValid()))

gedreht = s.copy()
gedreht.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(1, 0, 0), 180)
gedreht.translate(FreeCAD.Vector(0, 0, -gedreht.BoundBox.ZMin))
m = MeshPart.meshFromShape(Shape=gedreht, LinearDeflection=0.05,
                           AngularDeflection=0.5, Relative=False)
m.write(os.path.join(out, GUARD + ".stl"))
print("  %s.stl (auf dem Kopf gedruckt)  solid=%s  Abw %.4f%%" % (
    GUARD, m.isSolid(), abs(m.Volume - s.Volume) / s.Volume * 100))
