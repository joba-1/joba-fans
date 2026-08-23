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

# Welche Kreise ausgelassen werden, wechselt mit dem Offset: die Senke
# hinten links braucht viel Material, die Ecke vorn rechts wenig. Bei
# einem Offset, der hinten links gerade traegt, laeuft vorn rechts
# laengst ueber - und umgekehrt. Ausgelassen wird also jeweils die
# Seite, die bei diesem Offset ohnehin keinen brauchbaren Wert liefert.
#
# Stand fuer die Serie ab 0.00: vorn rechts faellt weg, hinten links ist
# wieder dabei (Beobachtung des Nutzers an den Drucken -0.10 und -0.05,
# 2026-08-23). Einzige Ausnahme hinten links ist (2,2): dort ist die
# Steigung mit 0,35 Hundertstel pro 0,01 Offset so flach, dass der Punkt
# in keiner Variante messbar wird.
#
# Koordinaten sind (Spalte, Zeile), beide von 1 bis 7:
#   erste Zahl  links -> rechts   (1 = x 22 mm,  7 = x 228 mm)
#   zweite Zahl hinten -> vorn    (1 = y 228 mm, 7 = y 22 mm)
# also (1,1) hinten links, (7,7) vorn rechts, (4,4) die Mitte.
AUS = {
    (2, 2),     # hinten links, Steigung nur 0,35 - nie messbar
    (7, 7),     # vorn rechts, Ecke
    (7, 4),     # rechts Mitte
    (4, 7),     # vorn Mitte
    (6, 4),     # rechts, mittlerer Ring
    (4, 6),     # vorn, mittlerer Ring
    (6, 6),     # vorn rechts, mittlerer Ring
}

FONT = "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
for kand in ("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"):
    if os.path.exists(kand):
        FONT = kand
        break


# Welche Punkte das Muehlebrett traegt, als (Spalte, Zeile) von 1 bis 7.
# Drei ineinanderliegende Quadrate; nur die Mittelzeile und die
# Mittelspalte tragen alle sieben Positionen.
ZEILE_SPALTEN = {1: [1, 4, 7], 2: [2, 4, 6], 3: [3, 4, 5],
                 4: [1, 2, 3, 4, 5, 6, 7],
                 5: [3, 4, 5], 6: [2, 4, 6], 7: [1, 4, 7]}


def xy(sp, ze):
    """(Spalte, Zeile) 1-7  ->  Plattenkoordinate in mm.

    Spalte 1 ist links (x=22), Zeile 1 ist hinten (y=228).
    """
    return (M + (sp - 4) * SCHRITT, M - (ze - 4) * SCHRITT)


def alle_punkte():
    return [(sp, ze) for ze, spalten in ZEILE_SPALTEN.items() for sp in spalten]


def naechster(sp, ze, dsp, dze, vorhanden):
    """Naechster vorhandener Punkt in Richtung (dsp, dze), sonst None."""
    sp, ze = sp + dsp, ze + dze
    while 1 <= sp <= 7 and 1 <= ze <= 7:
        if (sp, ze) in vorhanden:
            return (sp, ze)
        sp, ze = sp + dsp, ze + dze
    return None


def alle_linien():
    """Kanten zwischen BENACHBARTEN Punkten, waagrecht und senkrecht.

    Bewusst als Graph formuliert: Punkte und Kanten, sonst nichts. Faellt
    ein Punkt weg, fallen alle Kanten mit, die ihn beruehren - das ist
    eine Zeile Code statt Sonderfaellen je Quadratseite und Speiche.

    Die frueheren "Speichen" vom Zentrum bis zum Aussenring waren zudem
    falsch: sie verbanden (1,4)-(4,4)-(7,4) in einem Zug und liefen damit
    quer durch Punkte hindurch, statt Nachbarn zu verbinden.
    """
    vorhanden = set(alle_punkte())
    kanten = []
    for sp, ze in vorhanden:
        for dsp, dze in ((1, 0), (0, 1)):      # nach rechts und nach vorn
            nachbar = naechster(sp, ze, dsp, dze, vorhanden)
            if nachbar:
                kanten.append(((sp, ze), nachbar))
    return kanten


def balken(x0, y0, x1, y1, breite=None):
    b = breite if breite else LINIE_B
    laenge = math.hypot(x1 - x0, y1 - y0)
    winkel = math.degrees(math.atan2(y1 - y0, x1 - x0))
    q = Part.makeBox(laenge, b, HOEHE, FreeCAD.Vector(0, -b / 2, 0))
    q.rotate(FreeCAD.Vector(0, 0, 0), FreeCAD.Vector(0, 0, 1), winkel)
    q.translate(FreeCAD.Vector(x0, y0, 0))
    return q


def muster(offset):
    teile = []
    behalten = [p for p in alle_punkte() if p not in AUS]

    # Kanten: nur zwischen zwei behaltenen Punkten. Beruehrt eine Kante
    # einen ausgelassenen Punkt, entfaellt sie mit ihm.
    for a, b in alle_linien():
        if a in AUS or b in AUS:
            continue
        teile.append(balken(*xy(*a), *xy(*b)))

    # Kreise: Aussenring plus gefuellter Kern, fuer jeden behaltenen Punkt.
    for sp, ze in behalten:
        cx, cy = xy(sp, ze)
        teile.append(
            Part.makeCylinder(KREIS_D / 2, HOEHE, FreeCAD.Vector(cx, cy, 0))
            .cut(Part.makeCylinder(KREIS_D / 2 - LINIE_B, HOEHE + 2,
                                   FreeCAD.Vector(cx, cy, -1))))
        teile.append(Part.makeCylinder(FUELL_D / 2, HOEHE,
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
# Kandidaten sind die waagrechten Kanten des Musters, die breit genug
# fuer die Zahl sind. Sie kommen aus derselben Kantenliste wie die
# Geometrie, also entfaellt ein Kandidat automatisch mit seinem Punkt.
TEXTLINIEN = []
for _a, _b in alle_linien():
    if _a in AUS or _b in AUS:
        continue
    if _a[1] != _b[1]:              # nur waagrechte Kanten: gleiche Zeile
        continue
    _x1, _y1 = xy(*_a)
    _x2, _y2 = xy(*_b)
    if _x2 - _x1 - KREIS_D < TEXT_H * 2.2:     # zu eng fuer die Zahl
        continue
    TEXTLINIEN.append((_a, _b, _y1, (_x1 + _x2) / 2,
                       "Zeile %d, Spalten %d-%d" % (_a[1], _a[0], _b[0])))

# Messreihen fuer die Vorhersage (1/100 mm). Die Rohdaten stehen zeilenweise
# von hinten nach vorn, je Zeile von links nach rechts - also in derselben
# Reihenfolge, in der der Nutzer sie am Teil abliest.
def _lade(roh):
    g = {}
    for _ze, grp in enumerate(roh.split(", "), start=1):
        werte = [int(v) for v in grp.strip().split(",")]
        for _sp, v in zip(ZEILE_SPALTEN[_ze], werte):
            g[(_sp, _ze)] = v
    return g


_W0 = _lade("0,24,17, 7,24,25, 0,0,18, 28,24,9,0,11,28,30, 14,10,17, 24,22,26, 18,22,24")
_W2 = _lade("28,55,33, 14,50,45, 30,33,45, 43,45,35,30,34,45,48, 42,42,41, 44,46,48, 46,50,48")
_SW = _lade("26,50,39, 9,44,35, 26,27,34, 35,34,27,31,34,49,39, 33,28,35, 41,36,39, 23,40,40")
_STEIG = {k: (_W2[k] - _W0[k]) / 0.20 for k in _W0}
_BASIS = {k: _SW[k] - _STEIG[k] * 0.02 for k in _W0}


def waehle_linie(offset):
    """Linie, deren Nachbarkreise am naechsten an ZIEL_DICKE liegen."""
    best = None
    for a, b, y, x, name in TEXTLINIEN:
        d1 = _BASIS[a] + _STEIG[a] * offset
        d2 = _BASIS[b] + _STEIG[b] * offset
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
print("Grundmuster: %.2f cm3, %d Solids, %d Kreise (%d ausgelassen)" % (
    basis.Volume / 1000, len(basis.Solids),
    len([p for p in alle_punkte() if p not in AUS]), len(AUS)))

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
