"""Erstlagen-Testmuster als STL, eine Lage hoch.

Gegenueber der handgeschriebenen Gcode-Fassung: die Bahnfuehrung
uebernimmt der Slicer. Der kennt Kurvengeschwindigkeit, Beschleunigung und
Bahnplanung besser als ein selbstgebautes Muster, und die 90-Grad-Ecken
ergeben sich beim Uebergang von den geraden Verbindungen auf die Kreise
mehrfach von selbst.

Der Zentralkreis bleibt ungefuellt und traegt stattdessen den z-Offset als
Text - so ist jeder Ausdruck der Reihe eindeutig zuzuordnen.

In FreeCAD ausfuehren:
    exec(open('.../mkbedtest_stl.py').read())
"""
import FreeCAD, Part, Draft, MeshPart, os, math

BETT     = 250.0
RAND     = 12.0
KREIS_D  = 20.0
FUELL_D  = 14.0
ZENTRUM_D = 24.0        # Zentralkreis: traegt die Beschriftung ("-10")
LINIE_B  = 0.84          # zwei Bahnen a 0,42
HOEHE    = 0.21          # sicher eine Lage bei 0,2 mm Schichthoehe
TEXT_H   = 5.0          # kleiner ist bei 0,8 mm Bahnbreite unlesbar

OUT = "/data/joachim/git/fan-stand/cad/tests"
M = BETT / 2
SCHRITT = (M - RAND - KREIS_D / 2) / 3


def punkte():
    p = []
    for ring in (3, 2, 1):
        h = ring * SCHRITT
        for dx, dy in ((-1,-1),(0,-1),(1,-1),(1,0),(1,1),(0,1),(-1,1),(-1,0)):
            p.append((M + dx*h, M + dy*h))
    return p


def balken(x0, y0, x1, y1):
    """Verbindung als flacher Quader, LINIE_B breit."""
    laenge = math.hypot(x1-x0, y1-y0)
    winkel = math.degrees(math.atan2(y1-y0, x1-x0))
    b = Part.makeBox(laenge, LINIE_B, HOEHE,
                     FreeCAD.Vector(0, -LINIE_B/2, 0))
    b.rotate(FreeCAD.Vector(0,0,0), FreeCAD.Vector(0,0,1), winkel)
    b.translate(FreeCAD.Vector(x0, y0, 0))
    return b


def muster(offset):
    teile = []

    # drei Ringe - ihre zwoelf Ecken sind die 90-Grad-Wechsel
    for ring in (3, 2, 1):
        h = ring * SCHRITT
        ecken = [(M-h, M-h), (M+h, M-h), (M+h, M+h), (M-h, M+h)]
        for i in range(4):
            teile.append(balken(*ecken[i], *ecken[(i+1) % 4]))

    # Speichen vom Zentrum nach aussen
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        teile.append(balken(M, M, M + dx*3*SCHRITT, M + dy*3*SCHRITT))

    # 24 Kreise: Aussenring plus gefuellter Kern
    for cx, cy in punkte():
        ring = (Part.makeCylinder(KREIS_D/2, HOEHE, FreeCAD.Vector(cx, cy, 0))
                .cut(Part.makeCylinder(KREIS_D/2 - LINIE_B, HOEHE + 2,
                                       FreeCAD.Vector(cx, cy, -1))))
        teile.append(ring)
        teile.append(Part.makeCylinder(FUELL_D/2, HOEHE,
                                       FreeCAD.Vector(cx, cy, 0)))

    # Zentrum: nur Ring, innen der z-Offset als Text. Der Ring ist
    # groesser als die anderen, damit die Beschriftung lesbar wird -
    # bei 20 mm und 0,8 mm Bahnbreite blieben je Strich zwei Bahnen.
    zr = ZENTRUM_D / 2
    teile.append(
        Part.makeCylinder(zr, HOEHE, FreeCAD.Vector(M, M, 0))
        .cut(Part.makeCylinder(zr - LINIE_B, HOEHE + 2,
                               FreeCAD.Vector(M, M, -1))))

    koerper = teile[0]
    for t in teile[1:]:
        koerper = koerper.fuse(t)
    return koerper.removeSplitter()


def mit_text(koerper, offset):
    """z-Offset als Ziffern im Zentralkreis, mit dem Ring verbunden.

    Der ganze String wird in EINEM Zug erzeugt - zeichenweise zu setzen
    ging schief, weil Punkt und Minus andere Boundboxen liefern als die
    Ziffern und die Breitenrechnung sie dann falsch verschiebt.

    Die Ziffern haengen sonst frei im Ring und fielen beim Abloesen
    heraus - damit waere die Zuordnung des Offsets verloren. Ein Steg
    durch den Text verbindet sie untereinander und mit dem Ring.
    """
    # Kurzform: -0.10 wird "-10", +0.05 wird "5". Ohne Punkt und
    # fuehrende Null bleibt bei gleicher Ringgroesse mehr Luft, und
    # ohne Dezimalpunkt genuegt ein einziger Verbindungssteg.
    txt = "%d" % round(offset * 100)
    try:
        s = Draft.make_shapestring(String=txt, FontFile=FONT,
                                   Size=TEXT_H, Tracking=0.15 * TEXT_H)
        FreeCAD.ActiveDocument.recompute()
        f = s.Shape.copy()
        FreeCAD.ActiveDocument.removeObject(s.Name)
    except Exception as e:
        print("  Text uebersprungen: %s" % e)
        return koerper
    if not f.Faces:
        return koerper
    bb = f.BoundBox
    f.translate(FreeCAD.Vector(M - bb.XLength / 2 - bb.XMin,
                               M - bb.YLength / 2 - bb.YMin, 0))
    koerper = koerper.fuse(f.extrude(FreeCAD.Vector(0, 0, HOEHE)))

    # Ein Steg quer durch den Text auf halber Zeichenhoehe. Er haelt
    # Ziffern und Minuszeichen am Ring fest, damit die Zuordnung des
    # Offsets beim Abloesen nicht verloren geht. Ein zweiter Steg auf
    # Grundlinie war nur noetig, solange der Text einen Dezimalpunkt
    # unterhalb der Mitte hatte.
    zr = ZENTRUM_D / 2
    for dy in (0.0,):
        koerper = koerper.fuse(
            Part.makeBox(2 * zr, LINIE_B, HOEHE,
                         FreeCAD.Vector(M - zr, M + dy - LINIE_B / 2, 0))
            .common(Part.makeCylinder(zr, HOEHE, FreeCAD.Vector(M, M, 0))))
    return koerper.removeSplitter()


FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
for kand in ("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"):
    if os.path.exists(kand):
        FONT = kand
        break

os.makedirs(OUT, exist_ok=True)
d = FreeCAD.newDocument("bedtest") if "bedtest" not in [
    x.Name for x in FreeCAD.listDocuments().values()] else FreeCAD.getDocument("bedtest")

basis = muster(0.0)
print("Grundmuster: %.2f cm3, %d Solids" % (basis.Volume/1000, len(basis.Solids)))

for i in range(9):
    off = -0.10 + i * 0.05
    k = mit_text(basis.copy(), off)
    o = d.getObject("Muster%d" % i) or d.addObject("Part::Feature", "Muster%d" % i)
    o.Shape = k
    o.Label = "Testmuster z%+.2f" % off
    o.Visibility = (i == 0)          # nur das erste zeigen, sonst ueberlagern sie sich
    d.recompute()
    m = MeshPart.meshFromShape(Shape=k, LinearDeflection=0.05,
                               AngularDeflection=0.5, Relative=False)
    name = "bedtest_z%+.2f.stl" % off
    m.write(os.path.join(OUT, name))
    print("  %-22s solid=%s" % (name, m.isSolid()))
print("fertig")
