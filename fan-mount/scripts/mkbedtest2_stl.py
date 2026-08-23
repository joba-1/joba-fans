"""Testmuster, zweite Fassung - fuer die schwarze Messreihe.

Unterschiede zur ersten Fassung (mkbedtest_stl.py):

 * Der Punkt hinten links im mittleren Ring (x=56 y=194) faellt weg,
   samt der beiden Ringlinien, die dort zusammenstossen. Er ist der
   Tiefpunkt der Platte: um dort ueberhaupt eine messbare Schicht zu
   bekommen, braeuchte es Offset +0.37, bei dem ueberall sonst laengst
   alles zerfetzt ist. Der Kreis kaeme also in keiner Variante der
   Serie in den messbaren Bereich.
 * Der Zentralkreis ist ein normaler Kreis wie alle anderen (gefuellt,
   ohne Beschriftung) - damit auch die Plattenmitte einen Messwert
   liefert.
 * Der z-Offset steht stattdessen in groesserer Schrift auf einer
   waagrechten Linie unterhalb der Mitte. Die Linie liegt im Bereich,
   der laut Vorhersage nahe Dicke 25 druckt, also gut lesbar wird.

In FreeCAD ausfuehren:
    OFFSETS = [-0.10]
    exec(open(".../scripts/mkbedtest2_stl.py").read())
"""
import FreeCAD, Part, Draft, MeshPart, os, math

BETT = 250.0
RAND = 12.0
KREIS_D = 20.0
FUELL_D = 14.0
LINIE_B = 0.84          # zwei Bahnen a 0,42
HOEHE = 0.21            # sicher eine Lage bei 0,2 mm Schichthoehe
TEXT_H = 9.0            # groesser als in Fassung 1 (dort 5,0 im Ring)
M = BETT / 2
SCHRITT = (M - RAND - KREIS_D / 2) / 3

OUT = "/data/joachim/git/fan-stand/cad/tests"

# Punkt hinten links im mittleren Ring: Tiefpunkt der Platte, nie messbar.
AUS = (2, -1, 1)        # (Ring, dx, dy)

FONT = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
for kand in ("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"):
    if os.path.exists(kand):
        FONT = kand
        break


def punkte():
    p = []
    for ring in (3, 2, 1):
        h = ring * SCHRITT
        for dx, dy in ((-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)):
            if (ring, dx, dy) == AUS:
                continue
            p.append((M + dx*h, M + dy*h))
    return p


def balken(x0, y0, x1, y1, breite=None):
    b = breite if breite else LINIE_B
    laenge = math.hypot(x1-x0, y1-y0)
    winkel = math.degrees(math.atan2(y1-y0, x1-x0))
    q = Part.makeBox(laenge, b, HOEHE, FreeCAD.Vector(0, -b/2, 0))
    q.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), winkel)
    q.translate(FreeCAD.Vector(x0, y0, 0))
    return q


def muster(offset):
    teile = []
    aus_ring, aus_dx, aus_dy = AUS
    aus_pt = (M + aus_dx*aus_ring*SCHRITT, M + aus_dy*aus_ring*SCHRITT)

    for ring in (3, 2, 1):
        h = ring * SCHRITT
        ecken = [(M-h, M-h), (M+h, M-h), (M+h, M+h), (M-h, M+h)]
        for i in range(4):
            a, b = ecken[i], ecken[(i+1) % 4]
            # Linien, die am ausgelassenen Punkt haengen, entfallen mit ihm
            if ring == aus_ring and (
                    (abs(a[0]-aus_pt[0]) < .1 and abs(a[1]-aus_pt[1]) < .1) or
                    (abs(b[0]-aus_pt[0]) < .1 and abs(b[1]-aus_pt[1]) < .1)):
                continue
            teile.append(balken(*a, *b))

    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        teile.append(balken(M, M, M + dx*3*SCHRITT, M + dy*3*SCHRITT))

    # Alle Kreise gleich, auch der zentrale: Ring plus gefuellter Kern.
    for cx, cy in punkte() + [(M, M)]:
        teile.append(
            Part.makeCylinder(KREIS_D/2, HOEHE, FreeCAD.Vector(cx, cy, 0))
            .cut(Part.makeCylinder(KREIS_D/2 - LINIE_B, HOEHE + 2,
                                   FreeCAD.Vector(cx, cy, -1))))
        teile.append(Part.makeCylinder(FUELL_D/2, HOEHE,
                                       FreeCAD.Vector(cx, cy, 0)))

    koerper = teile[0]
    for t in teile[1:]:
        koerper = koerper.fuse(t)
    return koerper.removeSplitter()


# Beschriftungslinie: waagrecht zwischen dem inneren und dem mittleren
# Ring, unterhalb der Mitte. Dort sagt die Vorhersage Dicken um 25 - der
# Bereich, in dem Kanten am saubersten kommen.
TEXT_Y = M - 1.5 * SCHRITT
LINIE_X0 = M - 2 * SCHRITT
LINIE_X1 = M + 2 * SCHRITT   # endet auf den senkrechten Ringlinien


def mit_text(koerper, offset):
    """z-Offset auf einer waagrechten Linie, Ziffern daran haengend.

    Die Linie ersetzt den frueheren Verbindungssteg im Zentralring: sie
    traegt die Ziffern, damit beim Abloesen nichts wegfaellt und die
    Zuordnung erhalten bleibt.
    """
    koerper = koerper.fuse(balken(LINIE_X0, TEXT_Y, LINIE_X1, TEXT_Y))

    txt = "%d" % round(offset * 100)
    try:
        s = Draft.make_shapestring(String=txt, FontFile=FONT,
                                   Size=TEXT_H, Tracking=0.15 * TEXT_H)
        FreeCAD.ActiveDocument.recompute()
        f = s.Shape.copy()
        FreeCAD.ActiveDocument.removeObject(s.Name)
    except Exception as e:
        print("  Text uebersprungen: %s" % e)
        return koerper.removeSplitter()
    if not f.Faces:
        return koerper.removeSplitter()

    # Text mittig ueber der Linie, Grundlinie knapp darunter, damit
    # jede Ziffer die Linie beruehrt und daran haengt.
    bb = f.BoundBox
    f.translate(FreeCAD.Vector(M - bb.XLength/2 - bb.XMin,
                               TEXT_Y - LINIE_B/2 - bb.YMin, 0))
    koerper = koerper.fuse(f.extrude(FreeCAD.Vector(0, 0, HOEHE)))
    return koerper.removeSplitter()


os.makedirs(OUT, exist_ok=True)
d = FreeCAD.newDocument("bedtest2") if "bedtest2" not in [
    x.Name for x in FreeCAD.listDocuments().values()] else FreeCAD.getDocument("bedtest2")

try:
    OFFSETS
except NameError:
    OFFSETS = [-0.10]

basis = muster(0.0)
print("Grundmuster: %.2f cm3, %d Solids, %d Kreise" % (
    basis.Volume/1000, len(basis.Solids), len(punkte()) + 1))

for i, off in enumerate(OFFSETS):
    k = mit_text(basis.copy(), off)
    name = "Muster%+.2f" % off
    o = d.getObject("M%d" % i) or d.addObject("Part::Feature", "M%d" % i)
    o.Shape = k
    o.Label = "Testmuster z%+.2f" % off
    o.Visibility = (i == 0)
    m = MeshPart.meshFromShape(Shape=k, LinearDeflection=0.05,
                               AngularDeflection=0.5, Relative=False)
    datei = os.path.join(OUT, "bedtest2_z%+.2f.stl" % off)
    m.write(datei)
    print("  %-22s %d Solid(s), solid=%s" % (
        os.path.basename(datei), len(k.Solids), m.isSolid()))

d.recompute()
d.save() if d.FileName else d.saveAs(os.path.join(OUT, "bedtest2.FCStd"))
print("gespeichert:", d.FileName)
