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
    n = int(za / rast)
    x = (za - (n * rast - (rast - stb))) / 2
    while x + stb <= za:
        teile.append(Part.makeBox(stb, aussen, sd,
                                  FreeCAD.Vector(x, x0, z_streben)))
        x += rast

    r = teile[0]
    for t in teile[1:]:
        r = r.fuse(t)
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
