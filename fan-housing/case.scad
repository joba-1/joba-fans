// ===========================================================================
//  Gehaeuse fuer den 4-Kanal-Luefterregler (Seeed XIAO ESP32-C3)
//
//  Zum Zusammenstecken, ohne Schrauben: vier federnde Nasen am Deckel
//  rasten in Taschen der Wanne. Zum Oeffnen die Laengswaende an den
//  Rastpunkten leicht nach aussen druecken.
//
//  Alle Platinenmasse kommen aus board_params.scad und werden von
//  extract_geometry.py aus der .kicad_pcb erzeugt - nicht hier aendern.
//
//  Teile drucken:
//    part = "tray"   Wanne          (cremefarbenes PETG)
//    part = "lid"    Deckel         (cremefarbenes PETG)
//    part = "guide"  Lichtleiter    (transparentes PETG)
//    part = "all"    Zusammenbau zur Sichtkontrolle
// ===========================================================================

include <board_params.scad>

part = "all";
$fn  = 48;

// Farben nur fuer die Ansichten - PETG cremefarben, Lichtleiter klar
col_case  = "antiquewhite";
col_guide = "lightcyan";

// ---------------------------------------------------------------- Material
wall     = 2.4;   // Seitenwaende
floor_t  = 2.0;   // Boden der Wanne
lid_t    = 3.0;   // Deckel. Bewusst dicker als die Waende: cremefarbenes
                  // PETG ist bei 2.4mm noch leicht transluzent, eine LED
                  // direkt darunter zeichnet sich sonst als Fleck ab.
fit      = 0.3;   // Spiel Platine gegen Innenwand
ledge    = 1.2;   // Breite der Auflageschulter
standoff = 2.5;   // Luft unter der Platine fuer die Loetstellen
pcb_t    = 1.6;
inner_h  = 15.0;  // Luft ueber der Platinenoberseite. Die Bauteilhoehen
                  // unten sind Katalogwerte, keine Messungen - der
                  // Zuschlag faengt ab, wenn eine davon 1mm daneben liegt.
corner_r = 2.5;

// ------------------------------------------------- Bauteilhoehen ueber PCB
// Nicht aus der .kicad_pcb ableitbar - Footprints tragen keine Hoehe.
h_socket   =  8.5;  // Buchsenleiste 2.54mm, uebliche Bauhoehe
h_xiao_pcb =  1.0;  // Platine des XIAO
h_usbc     =  3.3;  // USB-C-Buchse ueber der XIAO-Platine
h_fan      = 12.0;  // gesteckter Luefterstecker (deine Angabe)
h_jack     = 11.0;  // PJ-102AH Korpus

h_xiao     = h_socket + h_xiao_pcb + h_usbc;   // 12.8 - hoechstes Bauteil

// Der gesteckte Luefterstecker ist groesser als der Header darunter. Der
// Courtyard in der .kicad_pcb beschreibt nur die Stiftleiste, nicht das
// Gegenstueck - fuer Kollisionen zaehlt aber das Gegenstueck.
fan_grow_x = 0.8;
fan_grow_y = 0.7;

// ---------------------------------------------------------------- Optionen
usb_opening   = true;   // Schlitz zum Nachflashen ohne Oeffnen
vents         = true;   // Schlitze ueber dem Spannungsregler
light_window  = true;   // Fenster + Lichtleiter ueber dem XIAO

// ------------------------------------------------------------------ Ebenen
// Z = 0 ist die Unterseite der Platine.
z_floor_out = -standoff - floor_t;
z_floor_in  = -standoff;
z_pcb_top   = pcb_t;
z_rim       = pcb_t + inner_h;      // Oberkante Wanne, hier liegt der Deckel
z_lid_top   = z_rim + lid_t;

// ------------------------------------------------------------- Grundflaeche
ox0 = -(fit + wall);   oy0 = -(fit + wall);
outer_l = board_l + 2*(fit + wall);
outer_w = board_w + 2*(fit + wall);

// --------------------------------------------------------------- Rastnasen
// Laengspositionen: an beiden Waenden frei von Bauteilen, die hoeher als
// die Zunge reichen (Luefterstecker, XIAO, Elko, Hohlbuchse).
snap_x     = [27.5, 67];
snap_len   = 9;
// Geometrie der Federzunge. Massgebend ist die Randfaserdehnung an der
// Einspannung: eps = 3*t*d / (2*L^2). Mit t=1.4, d=0.6, L=8 sind das rund
// 2%, PETG fliesst ab etwa 4-5%. Die erste Auslegung (t=1.6, L=6, d=0.7)
// lag bei 4.7% - das haette beim ersten Oeffnen die Zunge abgerissen.
snap_t     = 1.4;        // Dicke
snap_h     = 8.0;        // freie Laenge ab Deckelunterseite
snap_proud = 0.6;        // Ueberstand der Nase
snap_gap   = 0.15;       // Spiel Zunge gegen Innenwand
snap_pk_d  = 0.9;        // Tiefe der Tasche in der Wand (von 2.4mm)

// ------------------------------------------------------- Kabelausgaenge
notch_w     = 8.0;   // Breite der Schlitze fuer die Luefterkabel
notch_depth = 6.0;   // Tiefe ab Oberkante Wanne

fan_x = [ (J2_x[0]+J2_x[1])/2, (J3_x[0]+J3_x[1])/2 ];   // untere Laengswand
fan_o = [ (J4_x[0]+J4_x[1])/2, (J5_x[0]+J5_x[1])/2 ];   // obere Laengswand

// ------------------------------------------------------------- Lichtfenster
// Ueber dem USB-C-Ende des XIAO - dort sitzt die Ladeanzeige, und dort
// waere auch eine nachgeruestete Status-LED am sinnvollsten.
win_cx = (U1_x[0] + U1_x[1]) / 2;
win_w  = 12;
win_d  =  6;
win_cy = U1_y[0] + 5.6;   // hinter der USB-C-Buchse, dem hoechsten Teil
                          // des Moduls - ein Fuss davor wuerde anstossen

// ===========================================================================
//  Hilfsformen
// ===========================================================================

module rrect(w, h, r) {
    hull() for (x = [r, w-r], y = [r, h-r]) translate([x, y]) circle(r = r);
}

// Quader ueber zwei Eckpunkte, bequemer als translate+cube
module box(x0, y0, z0, x1, y1, z1) {
    translate([x0, y0, z0]) cube([x1-x0, y1-y0, z1-z0]);
}

// ===========================================================================
//  Wanne
// ===========================================================================

module tray() {
    difference() {
        translate([ox0, oy0, z_floor_out])
            linear_extrude(z_rim - z_floor_out)
                rrect(outer_l, outer_w, corner_r + wall);

        // Innenraum oberhalb der Platinenunterseite: die Platine faellt
        // von oben hinein
        translate([-fit, -fit, 0])
            linear_extrude(z_rim - 0 + 1)
                rrect(board_l + 2*fit, board_w + 2*fit, corner_r);

        // Raum unter der Platine. Das Delta zum Innenraum darueber ist die
        // Schulter, auf der die Platine aufliegt.
        translate([-fit + ledge, -fit + ledge, z_floor_in])
            linear_extrude(0 - z_floor_in + 0.01)
                rrect(board_l + 2*fit - 2*ledge,
                      board_w + 2*fit - 2*ledge, corner_r);

        cable_notches();
        jack_opening();
        if (usb_opening) usb_notch();
        snap_pockets();
        if (vents) side_vents();
    }
}

// Schlitze fuer die Luefterkabel, von der Oberkante nach unten offen:
// so legt man das Kabel beim Zusammenbau ein, statt es einzufaedeln -
// der Luefterstecker passt durch keine geschlossene Oeffnung.
module cable_notches() {
    for (x = fan_x)
        box(x - notch_w/2, oy0 - 1, z_rim - notch_depth,
            x + notch_w/2, 1,       z_rim + 1);
    for (x = fan_o)
        box(x - notch_w/2, board_w - 1,  z_rim - notch_depth,
            x + notch_w/2, oy0 + outer_w + 1, z_rim + 1);
}

// Durchbruch fuer die Hohlbuchse. Sie steht ohnehin ueber die
// Platinenkante hinaus und schaut damit aus der Wand heraus.
module jack_opening() {
    box(board_l - 1,               J1_y[0] - 0.5, z_pcb_top - 0.6,
        ox0 + outer_l + 1,         J1_y[1] + 0.5, z_pcb_top + h_jack + 0.6);
}

// USB-C: von oben offen, weil der Kabelknick sonst nicht hineinreicht.
module usb_notch() {
    w = 13; 
    box(win_cx - w/2, oy0 - 1, z_pcb_top + h_socket - 1.0,
        win_cx + w/2, 1,       z_rim + 1);
}

// Taschen, in die die Rastnasen des Deckels einschnappen
// Mulde in der Innenflaeche, KEIN Durchbruch: sie darf die Wand nur
// anfraesen, sonst sieht man von aussen in das Gehaeuse.
module snap_pockets() {
    for (x = snap_x) {
        box(x - snap_len/2 - 0.5, -fit - snap_pk_d,          z_rim - 3.8,
            x + snap_len/2 + 0.5, -fit + 0.5,                z_rim - 1.6);
        box(x - snap_len/2 - 0.5, board_w + fit - 0.5,       z_rim - 3.8,
            x + snap_len/2 + 0.5, board_w + fit + snap_pk_d, z_rim - 1.6);
    }
}

// Der AMS1117 verheizt bei 12V Eingang rund 0.7W. Schlitze in der linken
// Stirnwand und im Deckel geben dem einen Weg nach draussen.
module side_vents() {
    for (i = [0:3])
        box(ox0 - 1,   6 + i*4, z_pcb_top + 3,
            -fit + 1,  8 + i*4, z_pcb_top + 10);
}

// ===========================================================================
//  Deckel
// ===========================================================================

module lid() {
    difference() {
        union() {
            translate([ox0, oy0, z_rim])
                linear_extrude(lid_t)
                    rrect(outer_l, outer_w, corner_r + wall);
            snap_tabs();
        }
        if (light_window) light_hole();
        if (vents) lid_vents();
    }
}

module snap_tabs() {
    for (x = snap_x) {
        // untere Laengswand
        translate([x - snap_len/2, -fit + snap_gap, z_rim - snap_h])
            snap_tab();
        // obere Laengswand, gespiegelt
        translate([x + snap_len/2, board_w + fit - snap_gap, z_rim - snap_h])
            rotate([0, 0, 180]) snap_tab();
    }
}

// Zunge mit angeschraegter Nase. Die Schraege zeigt nach unten, damit der
// Deckel sich beim Aufdruecken selbst eindrueckt.
module snap_tab() {
    cube([snap_len, snap_t, snap_h]);
    // Von der Zungenoberkante aus bemassen, nicht vom Fuss: sonst wandert
    // die Nase mit, sobald man snap_h aendert, und trifft ihre Tasche nicht
    // mehr. Nase z_rim-3.5..z_rim-1.9 in Tasche z_rim-3.8..z_rim-1.6.
    hull() {
        translate([0, 0, snap_h - 5.0])
            cube([snap_len, 0.01, 0.01]);
        translate([0, -snap_proud, snap_h - 3.5])
            cube([snap_len, snap_proud, 1.6]);
    }
}

module light_hole() {
    translate([win_cx, win_cy, z_rim - 1])
        linear_extrude(lid_t + 2)
            rrect_c(win_w, win_d, 1.2);
}

module rrect_c(w, h, r) {
    translate([-w/2, -h/2]) rrect(w, h, r);
}

module lid_vents() {
    for (i = [0:4])
        translate([U2_x[0] + 1 + i*2.2, U2_y[0] + 1, z_rim - 1])
            cube([1.3, 6.5, lid_t + 2]);
}

// ===========================================================================
//  Lichtleiter - transparent drucken
// ===========================================================================

module guide() {
    // Kopf buendig in der Deckeloeffnung
    translate([win_cx, win_cy, z_rim])
        linear_extrude(lid_t)
            rrect_c(win_w - 0.3, win_d - 0.3, 1.1);
    // Bund innen: verhindert, dass der Leiter nach aussen durchfaellt
    translate([win_cx, win_cy, z_rim - 1.0])
        linear_extrude(1.0)
            rrect_c(win_w + 2.4, win_d + 2.4, 1.4);
    // Bewusst ohne Fuss bis zur Platine: die Bauhoehen des gesockelten
    // XIAO sind Schaetzwerte, und ein Fuss, der 0.5mm zu lang geraet,
    // drueckt den Deckel auf.
}

// ===========================================================================
//  Sichtkontrolle
// ===========================================================================

// Duenne Scheibe quer durch eine Rastung. Ein blosses Wegschneiden der
// einen Haelfte laesst zu weit in das Bauteil hinein sehen - man sieht
// dann hinter der Schnittflaeche weiter Material und kann nichts mehr
// zuordnen.
slab = 5;
module cutbox() {
    translate([snap_x[0] - slab/2, -80, -80]) cube([slab, 160, 160]);
}

module board_mock() {
    color("darkgreen") translate([0, 0, 0]) cube([board_l, board_w, pcb_t]);
    color("gray")   box(U1_x[0], U1_y[0], z_pcb_top,
                        U1_x[1], U1_y[1], z_pcb_top + h_xiao);
    color("white")  for (j = [[J2_x, J2_y], [J3_x, J3_y], [J4_x, J4_y], [J5_x, J5_y]])
                        box(j[0][0] - fan_grow_x, j[1][0] - fan_grow_y, z_pcb_top,
                            j[0][1] + fan_grow_x, j[1][1] + fan_grow_y,
                            z_pcb_top + h_fan);
    color("black")  box(J1_x[0], J1_y[0], z_pcb_top,
                        J1_x[1], J1_y[1], z_pcb_top + h_jack);
    color("silver") box(C1_x[0], C1_y[0], z_pcb_top,
                        C1_x[1], C1_y[1], z_pcb_top + 12.5);
}

if      (part == "tray")  color(col_case)
                             translate([0, 0, -z_floor_out]) tray();
else if (part == "lid")   color("wheat")
                             translate([0, 0, z_lid_top]) rotate([180, 0, 0]) lid();
else if (part == "guide") color(col_guide)
                             translate([0, 0, z_lid_top]) rotate([180, 0, 0]) guide();
else if (part == "explode") {
    color(col_case) tray();
    board_mock();
    translate([0, 0, 20]) {
        color("wheat") lid();
        color(col_guide) guide();
    }
}
else if (part == "report") {
    echo(str("OUTER ", outer_l, " ", outer_w, " ", z_lid_top - z_floor_out));
    echo(str("SNAP ", snap_t, " ", snap_h, " ", snap_proud, " ", snap_gap,
             " ", snap_pk_d, " ", fit));
    echo(str("NOSEZ ", z_rim - 3.5, " ", z_rim - 1.9));
    echo(str("POCKZ ", z_rim - 3.8, " ", z_rim - 1.6));
    echo(str("HEAD ", z_rim - z_pcb_top));
    // Federzungen als Quader, inklusive Nase
    for (x = snap_x) {
        echo(str("TAB ", x - snap_len/2, " ", x + snap_len/2,
                 " ", -fit + snap_gap - snap_proud, " ", -fit + snap_gap + snap_t,
                 " ", z_rim - snap_h, " ", z_rim));
        echo(str("TAB ", x - snap_len/2, " ", x + snap_len/2,
                 " ", board_w + fit - snap_gap - snap_t,
                 " ", board_w + fit - snap_gap + snap_proud,
                 " ", z_rim - snap_h, " ", z_rim));
    }
    // Bauteile, die hoeher reichen als der Fuss der Federzungen
    echo(str("PART U1 ", U1_x[0], " ", U1_x[1], " ", U1_y[0], " ", U1_y[1],
             " ", z_pcb_top, " ", z_pcb_top + h_xiao));
    echo(str("PART J1 ", J1_x[0], " ", J1_x[1], " ", J1_y[0], " ", J1_y[1],
             " ", z_pcb_top, " ", z_pcb_top + h_jack));
    for (j = [["J2", J2_x, J2_y], ["J3", J3_x, J3_y],
              ["J4", J4_x, J4_y], ["J5", J5_x, J5_y]])
        echo(str("PART ", j[0], " ", j[1][0] - fan_grow_x, " ", j[1][1] + fan_grow_x,
                 " ", j[2][0] - fan_grow_y, " ", j[2][1] + fan_grow_y,
                 " ", z_pcb_top, " ", z_pcb_top + h_fan));
    echo(str("PART C1 ", C1_x[0], " ", C1_x[1], " ", C1_y[0], " ", C1_y[1],
             " ", z_pcb_top, " ", z_pcb_top + 12.5));
}
else if (part == "lid_guide") {
    // Nur zum Ansehen: Deckel in Drucklage mit abgehobenem Lichtleiter.
    // Nicht fuer den STL-Export - die beiden Teile werden getrennt und aus
    // verschiedenem Material gedruckt.
    color("wheat")
        translate([0, 0, z_lid_top]) rotate([180, 0, 0]) lid();
    color(col_guide, 0.65)
        translate([0, 0, z_lid_top + 15]) rotate([180, 0, 0]) guide();
}
else if (part == "latch") {
    // Rastung in den Ursprung schieben, damit die Kamera nur noch auf
    // (0,0,0) zeigen muss - Zielen in Modellkoordinaten ist bei schraeger
    // Ansicht Raterei.
    translate([-snap_x[0], 0.5, -(z_rim - 2.7)]) {
        color("steelblue")  intersection() { tray(); cutbox(); }
        color("sandybrown") intersection() { lid();  cutbox(); }
    }
}
else if (part == "section") {
    // Schnitt quer durch eine Rastung. Bewusst unrealistisch eingefaerbt -
    // in zwei Cremetoenen ist im Schnitt nicht zu erkennen, welches Teil
    // welches ist.
    color("steelblue")  intersection() { tray(); cutbox(); }
    color("sandybrown") intersection() { lid();  cutbox(); }
}
else if (part == "closed") {
    color(col_case)  tray();
    color("wheat") lid();
    color(col_guide) guide();
}
else {
    tray();
    board_mock();
    color("ivory",   0.55) lid();
    color("skyblue", 0.75) guide();
}
