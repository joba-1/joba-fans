"""Reinigungsmuster: dasselbe Raster, aber breiter und dicker.

Zweck ist nicht Messen, sondern Putzen. Nach vielen Testdrucken steckt
Filament in den Taelern der PEI-Struktur, das sich nicht mehr abziehen
laesst. Ein Druck mit doppelter Bahnbreite holt es heraus: die Duese
fasst breiter an und nimmt beim Abloesen mit, was in den Taelern sitzt.

Drei Aenderungen gegenueber dem Messmuster (mkbedtest2_stl.py):

 * LINIE_B doppelt - vier Bahnen statt zwei, also mehr Kontaktflaeche;
 * der Kreisring bekommt eine Bahn mehr, wird also breiter - es ist
   derselbe Ring, kein zusaetzlicher daneben;
 * drei Lagen statt einer, damit sich das Ergebnis in einem Stueck
   abziehen laesst statt in Fetzen zu reissen.

Ohne Beschriftung: es gibt nichts zuzuordnen.

In FreeCAD ausfuehren:
    exec(open(".../scripts/mkreinigung_stl.py").read())
"""
import FreeCAD, Part, MeshPart, os, math

BETT = 250.0
RAND = 12.0
KREIS_D = 20.0
FUELL_D = 14.0
BAHN = 0.42             # eine Extrusionsbahn
LINIE_B = 4 * BAHN      # doppelt so breit wie im Messmuster
RING_B = 5 * BAHN       # der Kreisring eine Bahn breiter als die Linien
LAGEN = 3
LAGENHOEHE = 0.20
HOEHE = LAGEN * LAGENHOEHE + 0.01
M = BETT / 2
SCHRITT = (M - RAND - KREIS_D / 2) / 3

OUT = "/data/joachim/git/fan-stand/cad/tests"

ZEILE_SPALTEN = {1: [1, 4, 7], 2: [2, 4, 6], 3: [3, 4, 5],
                 4: [1, 2, 3, 4, 5, 6, 7],
                 5: [3, 4, 5], 6: [2, 4, 6], 7: [1, 4, 7]}


def xy(sp, ze):
    return (M + (sp - 4) * SCHRITT, M - (ze - 4) * SCHRITT)


def alle_punkte():
    return [(sp, ze) for ze, spalten in ZEILE_SPALTEN.items() for sp in spalten]


def naechster(sp, ze, dsp, dze, vorhanden):
    sp, ze = sp + dsp, ze + dze
    while 1 <= sp <= 7 and 1 <= ze <= 7:
        if (sp, ze) in vorhanden:
            return (sp, ze)
        sp, ze = sp + dsp, ze + dze
    return None


def alle_linien():
    vorhanden = set(alle_punkte())
    kanten = []
    for sp, ze in vorhanden:
        for dsp, dze in ((1, 0), (0, 1)):
            n = naechster(sp, ze, dsp, dze, vorhanden)
            if n:
                kanten.append(((sp, ze), n))
    return kanten


def balken(x0, y0, x1, y1):
    laenge = math.hypot(x1 - x0, y1 - y0)
    winkel = math.degrees(math.atan2(y1 - y0, x1 - x0))
    q = Part.makeBox(laenge, LINIE_B, HOEHE,
                     FreeCAD.Vector(0, -LINIE_B / 2, 0))
    q.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), winkel)
    q.translate(FreeCAD.Vector(x0, y0, 0))
    return q


def ring(cx, cy, aussen, breite):
    return (Part.makeCylinder(aussen / 2, HOEHE, FreeCAD.Vector(cx, cy, 0))
            .cut(Part.makeCylinder(aussen / 2 - breite, HOEHE + 2,
                                   FreeCAD.Vector(cx, cy, -1))))


def muster():
    teile = []
    for a, b in alle_linien():
        teile.append(balken(*xy(*a), *xy(*b)))
    for sp, ze in alle_punkte():
        cx, cy = xy(sp, ze)
        teile.append(ring(cx, cy, KREIS_D, RING_B))
        teile.append(Part.makeCylinder(FUELL_D / 2, HOEHE,
                                       FreeCAD.Vector(cx, cy, 0)))
    k = teile[0]
    for t in teile[1:]:
        k = k.fuse(t)
    return k.removeSplitter()


os.makedirs(OUT, exist_ok=True)
d = (FreeCAD.getDocument("reinigung")
     if "reinigung" in [x.Name for x in FreeCAD.listDocuments().values()]
     else FreeCAD.newDocument("reinigung"))
for o in list(d.Objects):
    d.removeObject(o.Name)

k = muster()
o = d.addObject("Part::Feature", "Reinigung")
o.Shape = k
o.Label = "Reinigungsmuster %d Lagen" % LAGEN
d.recompute()

m = MeshPart.meshFromShape(Shape=k, LinearDeflection=0.05,
                           AngularDeflection=0.5, Relative=False)
datei = os.path.join(OUT, "reinigung.stl")
m.write(datei)
bb = k.BoundBox
print("Reinigungsmuster: %.2f cm3, %d Solid(s), solid=%s" % (
    k.Volume / 1000, len(k.Solids), m.isSolid()))
print("  Linien %.2f mm (%d Bahnen), Kreisring %.2f mm (%d Bahnen)" % (
    LINIE_B, round(LINIE_B / BAHN), RING_B, round(RING_B / BAHN)))
print("  %d Lagen a %.2f mm = %.2f mm hoch" % (LAGEN, LAGENHOEHE, HOEHE))
print("  %.0f x %.0f mm, %d Kreise" % (bb.XLength, bb.YLength,
                                       len(alle_punkte())))
print("  geschrieben:", datei)
d.saveAs(os.path.join(OUT, "reinigung.FCStd")) if not d.FileName else d.save()
