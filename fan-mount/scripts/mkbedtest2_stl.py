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

# Zwei Punkte in der Ecke hinten links fallen weg - dort ist die Platte
# so tief, dass sie in keiner Variante der Serie messbar werden:
#   Ring 2 (x=56 y=194): Steigung nur 0,35 Hundertstel pro 0,01 Offset,
#       braeuchte Offset +0,37 fuer eine messbare Schicht.
#   Ring 3 (x=22 y=228): kam bei Weiss mit Offset 0 ganz ohne Material.
AUS = {(2, -1, 1), (3, -1, 1)}      # Menge von (Ring, dx, dy)

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
            if (ring, dx, dy) in AUS:
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
    aus_pt = {(M + dx*r*SCHRITT, M + dy*r*SCHRITT) for r, dx, dy in AUS}

    def ist_aus(p):
        return any(abs(p[0]-q[0]) < .1 and abs(p[1]-q[1]) < .1 for q in aus_pt)

    for ring in (3, 2, 1):
        h = ring * SCHRITT
        ecken = [(M-h, M-h), (M+h, M-h), (M+h, M+h), (M-h, M+h)]
        for i in range(4):
            a, b = ecken[i], ecken[(i+1) % 4]
            # Linien, die an einem ausgelassenen Punkt haengen, entfallen mit ihm
            if ist_aus(a) or ist_aus(b):
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


# Die Beschriftung haengt an einer LINIE DES MUSTERS, nicht an einer
# eigens dafuer gezogenen: eine Extralinie waere zusaetzliches Material
# ohne Messwert.
#
# WELCHE Linie, haengt vom Offset ab. Sitzt die Zahl in einer Zone, die
# bei diesem Offset zerfetzt oder gar nicht mehr kommt, ist die
# Zuordnung des Offsets verloren - genau das, was die Beschriftung
# verhindern soll. Also wird je Offset die Linie gewaehlt, deren beiden
# Nachbarkreise am naechsten an der gut druckbaren Dicke 25 liegen.
#
# Die Vorhersage stammt aus den bisherigen Messreihen: punktweise
# Steigung aus den beiden Weiss-Drucken, Niveau aus dem Schwarz-Druck
# bei 0.02. Sie ist eine Naeherung - deshalb faellt die Wahl bei
# Gleichstand auf die Linie mit dem groesseren Abstand zum Plattenrand.

ZIEL_DICKE = 25.0

# Kandidaten sind alle waagrechten Abschnitte zwischen zwei benachbarten
# Kreisen einer Zeile, die breit genug fuer die Zahl sind. Es genuegt
# nicht, je Quadratseite nur einen festen Abschnitt anzubieten: eine
# Quadratseite hat zwei oder mehr davon, und welcher davon gut druckt,
# haengt vom Offset ab. (Die Mittellinie ist in der Praxis nie die beste
# Wahl, wird aber der Vollstaendigkeit halber mitgeprueft.)
_ZEILEN_Y = [M + 3*SCHRITT, M + 2*SCHRITT, M + SCHRITT, M,
             M - SCHRITT, M - 2*SCHRITT, M - 3*SCHRITT]
_SPALTEN_X = [M - 3*SCHRITT, M - 2*SCHRITT, M - SCHRITT, M,
              M + SCHRITT, M + 2*SCHRITT, M + 3*SCHRITT]
_ZEILEN_SPALTEN = {0: [0,3,6], 1: [1,3,5], 2: [2,3,4], 3: list(range(7)),
                   4: [2,3,4], 5: [1,3,5], 6: [0,3,6]}

TEXTLINIEN = []
for _r, _cols in _ZEILEN_SPALTEN.items():
    for _i in range(len(_cols) - 1):
        _c1, _c2 = _cols[_i], _cols[_i+1]
        # ein ausgelassener Punkt kann keinen Text tragen
        _AUSRC = {(1, 1), (0, 0)}       # Rasterkoordinaten der AUS-Punkte
        if (_r, _c1) in _AUSRC or (_r, _c2) in _AUSRC:
            continue
        _luecke = _SPALTEN_X[_c2] - _SPALTEN_X[_c1] - KREIS_D
        if _luecke < TEXT_H * 2.2:      # zu eng fuer die Zahl
            continue
        TEXTLINIEN.append((_r, _c1, _c2, _ZEILEN_Y[_r],
                           (_SPALTEN_X[_c1] + _SPALTEN_X[_c2]) / 2,
                           "Zeile %d, Spalten %d-%d" % (_r, _c1, _c2)))

# Messreihen fuer die Vorhersage (1/100 mm), Raster wie im Muster.
_SP = {0:[0,3,6], 1:[1,3,5], 2:[2,3,4], 4:[2,3,4], 5:[1,3,5], 6:[0,3,6]}


def _lade(roh):
    g = {}
    for r, grp in enumerate(roh.split(", ")):
        vals = [int(v) for v in grp.strip().split(",")]
        cols = list(range(7)) if r == 3 else _SP[r]
        for c, v in zip(cols, vals):
            g[(r, c)] = v
    return g


_W0 = _lade("0,24,17, 7,24,25, 0,0,18, 28,24,9,0,11,28,30, 14,10,17, 24,22,26, 18,22,24")
_W2 = _lade("28,55,33, 14,50,45, 30,33,45, 43,45,35,30,34,45,48, 42,42,41, 44,46,48, 46,50,48")
_SW = _lade("26,50,39, 9,44,35, 26,27,34, 35,34,27,31,34,49,39, 33,28,35, 41,36,39, 23,40,40")
_STEIG = {k: (_W2[k] - _W0[k]) / 0.20 for k in _W0}
_BASIS = {k: _SW[k] - _STEIG[k] * 0.02 for k in _W0}


def waehle_linie(offset):
    """Linie, deren Nachbarkreise am naechsten an ZIEL_DICKE liegen."""
    best = None
    for r, c1, c2, y, x, name in TEXTLINIEN:
        d1 = _BASIS[(r, c1)] + _STEIG[(r, c1)] * offset
        d2 = _BASIS[(r, c2)] + _STEIG[(r, c2)] * offset
        fehler = (abs(d1 - ZIEL_DICKE) + abs(d2 - ZIEL_DICKE)) / 2
        if best is None or fehler < best[0]:
            best = (fehler, y, x, name, d1, d2)
    return best


def mit_text(koerper, offset):
    """z-Offset an eine vorhandene Musterlinie gehaengt.

    Die Ziffern sitzen auf der unteren Waagrechten des mittleren
    Quadrats. Sie beruehren die Linie, haengen also daran fest und
    fallen beim Abloesen nicht heraus - die Zuordnung des Offsets
    bleibt erhalten, ohne dass eine Extralinie noetig waere.
    """
    fehler, text_y, text_x, name, d1, d2 = waehle_linie(offset)
    print("  Text auf Linie '%s' (y=%.0f), Nachbarkreise erwartet %.0f/%.0f"
          % (name, text_y, d1, d2))
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

    # Text ueber der Linie, Grundlinie knapp darunter, damit jede Ziffer
    # die Linie beruehrt und daran haengt.
    bb = f.BoundBox
    f.translate(FreeCAD.Vector(text_x - bb.XLength/2 - bb.XMin,
                               text_y - LINIE_B/2 - bb.YMin, 0))
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
