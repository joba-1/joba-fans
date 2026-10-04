// ===========================================================================
//  Housing for the 4-channel fan controller (Seeed XIAO ESP32-C3)
//
//  Snap-fit, no screws: four spring tabs on the lid latch into pockets in the
//  tray. To open, press the long walls outward a little at the latch points.
//
//  All board dimensions come from board_params.scad, which
//  extract_geometry.py generates from the .kicad_pcb - do not change them here.
//
//  Parts to print:
//    part = "tray"   tray           (cream PETG)
//    part = "lid"    lid            (cream PETG)
//    part = "guide"  light guide    (transparent PETG)
//    part = "all"    assembly for visual inspection
// ===========================================================================

include <board_params.scad>

part = "all";
$fn  = 48;

// Colours for the views only - cream PETG, clear light guide
col_case  = "antiquewhite";
col_guide = "lightcyan";

// ---------------------------------------------------------------- Material
wall     = 2.4;   // side walls
floor_t  = 2.0;   // tray floor
lid_t    = 3.1;   // lid. Deliberately thicker than the walls: cream PETG is
                  // still slightly translucent at 2.4mm, so an LED right
                  // underneath would show as a blotch.
                  //
                  // 3.1 and not 3.0: the layer boundaries sit at
                  // 0.3 + n*0.2, i.e. 2.9 and 3.1. At 3.0 the top of the
                  // lid falls in the MIDDLE of a layer, and the collar of
                  // the light guide claims the same one - the slicer then
                  // aborts with "found slicing result conflict".
                  // Found on the printed part on 2026-09-09: the window sat
                  // one layer too far back on the inside.
fit      = 0.4;   // clearance between board and inner wall (left, right, front, back)
ledge    = 1.2;   // width of the shoulder the board rests on
standoff = 2.5;   // space under the board for the solder joints
pcb_t    = 1.6;
inner_h  = 19.0;  // space above the top of the board. 15 + 4: the socketed XIAO
                  // sits 4mm higher than the catalogue values (see h_socket).
                  // The margin above the tallest part absorbs a 1mm error.
outer_r  = 4.9;   // outside corner radius (plan view). The inside is sharp-cornered
                  // like the board.

// ------------------------------------------------- component heights above PCB
// Not derivable from the .kicad_pcb - footprints carry no height.
h_socket   = 12.5;  // socketed XIAO: board underside above the PCB. Measured on the
                  // real assembly, 4mm more than the 8.5mm of a plain header.
h_xiao_pcb =  1.0;  // XIAO circuit board
h_usbc     =  3.3;  // USB-C receptacle above the XIAO board
h_fan      = 12.0;  // plugged-in fan connector (figure supplied by the owner)
h_jack     = 11.0;  // PJ-102AH body

h_xiao     = h_socket + h_xiao_pcb + h_usbc;   // 16.8 - tallest component

// The plugged-in fan connector is larger than the header underneath. The
// courtyard in the .kicad_pcb only describes the pin header, not its mating
// part - but for collisions the mating part is what counts.
fan_grow_x = 0.8;
fan_grow_y = 0.7;

// ---------------------------------------------------------------- options
usb_opening    = true;   // window for re-flashing without opening
usb_h          = 4.0;    // height of that window, centred on the USB-C receptacle
jack_trim      = 1.4;    // the jack opening is this much narrower than the jack, per side
ears           = true;   // 'mouse ears': thin discs at the four bottom corners that hold
                         // the tray down while it cools. Cut them off after printing.
ear_r          = 8.0;    // radius of an ear, centred on the outer corner
ear_t          = 0.3;    // thickness = one first layer
vents          = true;   // slots above the voltage regulator
light_window   = true;   // window + light guide above the XIAO
guide_loose    = false;  // true: clearance for inserting the guide afterwards,
                         // false: exact fit, printed together in one go
guide_collar_h = 1.0;    // height of the collar (0 = none)
guide_collar_o = 2.4;    // overhang beyond the window, total

// ------------------------------------------------------------------ levels
// Z = 0 is the underside of the board.
z_floor_out = -standoff - floor_t;
z_floor_in  = -standoff;
z_pcb_top   = pcb_t;
z_rim       = pcb_t + inner_h;      // top of the tray, where the lid sits
z_lid_top   = z_rim + lid_t;

// ------------------------------------------------------------- footprint
ox0 = -(fit + wall);   oy0 = -(fit + wall);
outer_l = board_l + 2*(fit + wall);
outer_w = board_w + 2*(fit + wall);

// --------------------------------------------------------------- latches
// Positions along the length: free on both walls of components taller than
// the tab (fan connectors, XIAO, electrolytic cap, barrel jack).
snap_x     = [27.5, 67];
snap_len   = 9;
// Geometry of the spring tab. What matters is the outer-fibre strain at the
// root: eps = 3*t*d / (2*L^2). With t=1.4, d=0.6, L=8 that is about 2%;
// PETG yields at roughly 4-5%. The first design (t=1.6, L=6, d=0.7) came to
// 4.7% - the tab would have snapped off the first time the case was opened.
snap_t     = 1.4;        // thickness
snap_h     = 8.0;        // free length from the underside of the lid
snap_proud = 0.6;        // how far the nose protrudes
snap_gap   = 0.15;       // clearance between tab and inner wall
snap_pk_d  = 0.9;        // depth of the pocket in the wall (out of 2.4mm)

// ------------------------------------------------------- cable exits
notch_w     = 8.0;   // width of the slots for the fan cables
notch_depth = 1.0;   // depth below the top edge of the tray: the cable only just fits
                     // between tray and lid

fan_x = [ (J2_x[0]+J2_x[1])/2, (J3_x[0]+J3_x[1])/2 ];   // lower long wall
fan_o = [ (J4_x[0]+J4_x[1])/2, (J5_x[0]+J5_x[1])/2 ];   // upper long wall

// ------------------------------------------------------------- light window
// Above the USB-C end of the XIAO - that is where the charge LED sits, and
// where a retrofitted status LED would make the most sense.
win_cx = (U1_x[0] + U1_x[1]) / 2;
win_w  = 12;
win_d  =  6;
win_cy = U1_y[0] + 5.6;   // behind the USB-C receptacle, the tallest part
                          // of the module - a foot in front of it would collide

// ===========================================================================
//  helper shapes
// ===========================================================================

module rrect(w, h, r) {
    hull() for (x = [r, w-r], y = [r, h-r]) translate([x, y]) circle(r = r);
}

// Cuboid from two corner points, handier than translate+cube
module box(x0, y0, z0, x1, y1, z1) {
    translate([x0, y0, z0]) cube([x1-x0, y1-y0, z1-z0]);
}

// ===========================================================================
//  Tray
// ===========================================================================

// Mouse ears: one-layer discs at the four bottom corners. A long, tall tray
// shrinks while it cools and peels up at its ends; the ears add bed contact
// exactly there. They are cut off after printing.
module mouse_ears() {
    for (x = [ox0, ox0 + outer_l], y = [oy0, oy0 + outer_w])
        translate([x, y, z_floor_out]) cylinder(r = ear_r, h = ear_t, $fn = 64);
}

module tray() {
    union() {
    difference() {
        translate([ox0, oy0, z_floor_out])
            linear_extrude(z_rim - z_floor_out)
                rrect(outer_l, outer_w, outer_r);

        // Interior above the underside of the board: the board drops in
        // from above
        translate([-fit, -fit, 0])
            linear_extrude(z_rim - 0 + 1)
                square([board_l + 2*fit, board_w + 2*fit]);

        // Space under the board. The difference to the interior above is the
        // shoulder the board rests on.
        translate([-fit + ledge, -fit + ledge, z_floor_in])
            linear_extrude(0 - z_floor_in + 0.01)
                square([board_l + 2*fit - 2*ledge,
                        board_w + 2*fit - 2*ledge]);

        cable_notches();
        jack_opening();
        if (usb_opening) usb_notch();
        snap_pockets();
        if (vents) side_vents();
    }
    if (ears && part == "tray") mouse_ears();   // only in the print export, not in the views
    }
}

// Slots for the fan cables, open towards the top edge: the cable is laid in
// during assembly instead of threaded through - the fan connector does not
// fit through a closed opening.
module cable_notches() {
    for (x = fan_x)
        box(x - notch_w/2, oy0 - 1, z_rim - notch_depth,
            x + notch_w/2, 1,       z_rim + 1);
    for (x = fan_o)
        box(x - notch_w/2, board_w - 1,  z_rim - notch_depth,
            x + notch_w/2, oy0 + outer_w + 1, z_rim + 1);
}

// Cut-out for the barrel jack. It overhangs the board edge anyway and so
// sticks out of the wall.
module jack_opening() {
    box(board_l - 1,               J1_y[0] - 0.5 + jack_trim, z_pcb_top - 0.6,
        ox0 + outer_l + 1,         J1_y[1] + 0.5 - jack_trim, z_pcb_top + h_jack + 0.6);
}

// USB-C: a window usb_h high, centred on the receptacle of the socketed XIAO.
module usb_notch() {
    w  = 13;
    zc = z_pcb_top + h_socket + h_xiao_pcb + h_usbc/2;
    box(win_cx - w/2, oy0 - 1, zc - usb_h/2,
        win_cx + w/2, 1,       zc + usb_h/2);
}

// Pockets the lid's latch noses snap into.
// A recess in the inner face, NOT a through-cut: it may only mill into the
// wall, otherwise you can see into the housing from outside.
module snap_pockets() {
    for (x = snap_x) {
        box(x - snap_len/2 - 0.5, -fit - snap_pk_d,          z_rim - 3.8,
            x + snap_len/2 + 0.5, -fit + 0.5,                z_rim - 1.6);
        box(x - snap_len/2 - 0.5, board_w + fit - 0.5,       z_rim - 3.8,
            x + snap_len/2 + 0.5, board_w + fit + snap_pk_d, z_rim - 1.6);
    }
}

// The AMS1117 dissipates about 0.7W at a 12V input. Slots in the left end
// wall and in the lid give that heat a way out.
module side_vents() {
    for (i = [0:3])
        box(ox0 - 1,   6 + i*4, z_pcb_top + 3,
            -fit + 1,  8 + i*4, z_pcb_top + 10);
}

// ===========================================================================
//  Lid
// ===========================================================================

module lid() {
    difference() {
        union() {
            translate([ox0, oy0, z_rim])
                linear_extrude(lid_t)
                    rrect(outer_l, outer_w, outer_r);
            snap_tabs();
        }
        if (light_window) light_hole();
        if (vents) lid_vents();
    }
}

module snap_tabs() {
    for (x = snap_x) {
        // lower long wall
        translate([x - snap_len/2, -fit + snap_gap, z_rim - snap_h])
            snap_tab();
        // upper long wall, mirrored
        translate([x + snap_len/2, board_w + fit - snap_gap, z_rim - snap_h])
            rotate([0, 0, 180]) snap_tab();
    }
}

// Tab with a chamfered nose. The chamfer points downward so that the lid
// pushes the tab in by itself when pressed on.
module snap_tab() {
    cube([snap_len, snap_t, snap_h]);
    // Dimensioned from the top of the tab, not from its foot: otherwise the
    // nose moves along when snap_h changes and no longer hits its pocket.
    // Nose z_rim-3.5..z_rim-1.9 in pocket z_rim-3.8..z_rim-1.6.
    hull() {
        translate([0, 0, snap_h - 5.0])
            cube([snap_len, 0.01, 0.01]);
        translate([0, -snap_proud, snap_h - 3.5])
            cube([snap_len, snap_proud, 1.6]);
    }
}

module light_hole() {
    // Through-hole for the head
    translate([win_cx, win_cy, z_rim - 1])
        linear_extrude(lid_t + 2)
            rrect_c(win_w, win_d, 1.2);
    // Recess for the collar on the inside of the lid. Without it the collar
    // does not rest against the lid but sits INSIDE it: it is wider than the
    // window, and the slicer aborts with "found slicing result conflict"
    // (measured 2026-09-08: up to 1.0 mm overhang works, 2.4 mm does not).
    // The recess works since lid_t sits on a layer boundary - see there.
    if (!guide_loose && guide_collar_h > 0)
        translate([win_cx, win_cy, z_rim - 0.01])
            linear_extrude(guide_collar_h + 0.01)
                rrect_c(win_w + guide_collar_o, win_d + guide_collar_o, 1.4);
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
//  Light guide - print in transparent material
// ===========================================================================

module guide() {
    // Head flush in the lid opening. No clearance: in a two-colour print the
    // two materials fuse at the joint like two adjacent lines of the same
    // material, and that is exactly what is meant to hold it. A gap is only
    // needed if the guide is inserted afterwards - then set guide_loose = true.
    translate([win_cx, win_cy, z_rim])
        linear_extrude(lid_t)
            rrect_c(win_w - (guide_loose ? 0.3 : 0),
                    win_d - (guide_loose ? 0.3 : 0), 1.2);
    // Collar: keeps the guide in the lid. It always sits UNDER the head,
    // i.e. below z_rim. When printed together, the recess in the lid
    // (see light_hole) takes it up; when inserted afterwards, it rests
    // against the inner face. Starting it at z_rim was wrong - that is where
    // the head is, and in print orientation the collar vanished entirely.
    // Without the recess the collar would be wider than the window and rest
    // on the lid, which the slicer rejects as an overlap
    // ("found slicing result conflict", 2026-09-08).
    translate([win_cx, win_cy, z_rim - guide_collar_h])
        linear_extrude(guide_collar_h)
            rrect_c(win_w + guide_collar_o - (guide_loose ? 0 : 0.3),
                    win_d + guide_collar_o - (guide_loose ? 0 : 0.3), 1.4);
    // Deliberately no foot down to the board: the heights of the socketed
    // XIAO are estimates, and a foot that comes out 0.5mm too long would
    // push the lid open.
}

// ===========================================================================
//  Visual inspection
// ===========================================================================

// Thin slice across one latch. Simply cutting away one half lets you look
// too far into the part - you then see more material behind the cut face
// and can no longer tell what belongs to what.
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

// Printable orientation: lid and light guide are turned by 180 degrees
// together so that their position RELATIVE to each other is kept. Exported
// individually and each placed on Z=0, the height relationships are lost and
// the parts overlap in the window area.
// Both are shifted by the same amount so the relationships stay: in print
// orientation the head of the guide sits at Z 0..3 in the window hole and its
// collar at Z 3..4 above it. If each part were put on Z=0 on its own, both
// would end up at 0..3 and overlap.
if      (part == "lid_print")
    translate([0, 0, z_lid_top]) rotate([180, 0, 0]) lid();
else if (part == "guide_print")
    translate([0, 0, z_lid_top]) rotate([180, 0, 0]) guide();
else if (part == "tray")  color(col_case)
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
    // Spring tabs as cuboids, including the nose
    for (x = snap_x) {
        echo(str("TAB ", x - snap_len/2, " ", x + snap_len/2,
                 " ", -fit + snap_gap - snap_proud, " ", -fit + snap_gap + snap_t,
                 " ", z_rim - snap_h, " ", z_rim));
        echo(str("TAB ", x - snap_len/2, " ", x + snap_len/2,
                 " ", board_w + fit - snap_gap - snap_t,
                 " ", board_w + fit - snap_gap + snap_proud,
                 " ", z_rim - snap_h, " ", z_rim));
    }
    // Components that reach higher than the foot of the spring tabs
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
    // For viewing only: lid in print orientation with the light guide lifted
    // off. Not for STL export - the two parts are printed separately and in
    // different materials.
    color("wheat")
        translate([0, 0, z_lid_top]) rotate([180, 0, 0]) lid();
    color(col_guide, 0.65)
        translate([0, 0, z_lid_top + 15]) rotate([180, 0, 0]) guide();
}
else if (part == "latch") {
    // Move the latch to the origin so the camera only has to point at
    // (0,0,0) - aiming in model coordinates is guesswork in an oblique view.
    translate([-snap_x[0], 0.5, -(z_rim - 2.7)]) {
        color("steelblue")  intersection() { tray(); cutbox(); }
        color("sandybrown") intersection() { lid();  cutbox(); }
    }
}
else if (part == "section") {
    // Section across one latch. Deliberately coloured unrealistically - in
    // two shades of cream you cannot tell which part is which in the section.
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
