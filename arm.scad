// =====================================================================
//  Pot stirrer – printed arm (the spine), one piece
//
//  20x40 bar standing on edge, arm_len (400) long along its near face. The
//  bottom end is cut parallel to the board and sits on the motor mount's
//  plate; the square top end rests against the gearbox cap. Exported as ONE
//  piece lying on a side face (~423 x 40 x 20.4). It's longer than a 220 bed:
//  the user cuts it in the slicer (cut tool + connectors/dowels) to fit their
//  printer – keep the cut away from the pilot holes (echo lists them).
//
//  Fit: the arm prints arm_fit_clr (0.2) narrower than the cheek gaps of the
//  motor mount and the gearbox (arm_w + arm_clr = 20.6) -> 20.4 wide, 0.1 mm
//  per side. Pilot holes sit exactly where the cheek wood screws go – their
//  positions are read from motor_mount.scad and angled_gearbox.scad, so they
//  follow any change there.
//
//  Shared parameters (angle, arm size, length): common.scad.
//  Uses motor_mount.scad and angled_gearbox.scad (needs BOSL2).
//
//  Hardware
//   - the 4 mm countersunk screws of the motor mount (8) and gearbox (4) go into
//     the pilot holes; ~20 mm long
//   - if cut in the slicer: whatever joint the cut tool adds (dowels, glue)
//
//  Printing: PETG/ASA/nylon. Lying on a side face as exported, no supports,
//  5+ perimeters, 40%+ infill (it carries the gearbox out over the pot).
//  Note: a printed arm is softer than wood and PETG creeps when warm – keep it
//  out of the steam; wood stays the stiffer option.
// =====================================================================

include <common.scad>
use <motor_mount.scad>      // ARM(), mm_arm_screws(), mm_assembly(), one_piece()
use <angled_gearbox.scad>   // gb_arm_top(), gb_arm_screws(), gb_from_input(), gb_assembly(), housing()

/* [What to show / export] */
// assembly = the whole unit; print = the arm lying on its side, print-ready
part = "assembly"; // [assembly, arm, print]

/* [Fit] */
arm_fit_clr = 0.2;   // printed arm is this much narrower than the cheek gap (total)

/* [Pilot holes for the 4 mm wood screws] */
pilot_d     = 3.3;   // into PETG
pilot_depth = 16;    // from the arm face (screw ~20 minus the 6 mm cheek, + 2)

$fn = 48;

// ---------------------------------------------------------------------
// Derived (arm frame, see common.scad: near face at y = arm_y0, z = 0 where
// the near face meets the foot plate, z = arm_len at the top end)
// ---------------------------------------------------------------------
aw      = arm_w + arm_clr - arm_fit_clr;        // printed width (20.4)
cut_dz  = arm_t*tan(shaft_angle);               // far face reaches this far below z = 0

// pilot holes: motor mount (z from the plate) + gearbox (z relative to the top end)
pilots = concat(
    mm_arm_screws(),
    [for (p = gb_arm_screws()) [p[0], p[1], arm_len + (p[2] - gb_arm_top())]]
);

// ---------------------------------------------------------------------
// The arm
// ---------------------------------------------------------------------
// keep everything above the board plane (the plane the bottom end is cut in)
module above_board(off = 0) {
    translate([0, arm_y0, 0]) rotate([-shaft_angle, 0, 0])
        translate([-100, -300, off]) cube([200, 600, arm_len + 300]);
}

// full arm; shrink > 0 makes it slightly smaller on the contact faces (fit checks)
module arm_bar(shrink = 0) {
    intersection() {
        translate([-aw/2, arm_y0 + shrink, -cut_dz - 1])
            cube([aw, arm_t - 2*shrink, arm_len + cut_dz + 1 - shrink]);
        above_board(shrink);
    }
}

module pilot_holes() {
    for (p = pilots)
        translate([p[0]*aw/2, p[1], p[2]]) rotate([0, p[0] > 0 ? -90 : 90, 0])
            translate([0, 0, -1]) cylinder(d = pilot_d, h = pilot_depth + 1, $fn = 24);
}

module arm(shrink = 0) {
    difference() { arm_bar(shrink); pilot_holes(); }
}

// print orientation: lying on its -x side face, centred, length along x
module arm_print() {
    translate([0, 0, aw/2]) rotate([0, 0, 90]) rotate([0, -90, 0])
        translate([0, -(arm_y0 + arm_t/2), -(arm_len - cut_dz)/2]) arm();
}

// ---------------------------------------------------------------------
// Fit checks – run by `make check` (tools/check_fit.py). Each must be EMPTY.
// The arm is shrunk 0.01 on its contact faces (seat, plate, cap).
// ---------------------------------------------------------------------
module arm_check(what) {
    if (what == "arm_vs_mount")
        intersection() { one_piece(); ARM() arm(0.01); }
    if (what == "arm_vs_gearbox")
        intersection() { housing(); in_frame_inv_arm() arm(0.01); }
    // Ø3 pins out of every pilot hole must pass through the cheeks' Ø4.5 screw
    // holes without touching -> pilot holes and cheek holes line up (±0.75 mm)
    if (what == "pilots_vs_mount")
        intersection() { one_piece(); ARM() pilot_pins(); }
    if (what == "pilots_vs_gearbox")
        intersection() { housing(); in_frame_inv_arm() pilot_pins(); }
}
module pilot_pins() {
    for (p = pilots)
        translate([p[0]*aw/2, p[1], p[2]]) rotate([0, p[0] > 0 ? 90 : -90, 0])
            cylinder(d = 3, h = cheek_t + 5, $fn = 24);
}

// arm frame -> gearbox frame: input frame shifted so the arm's top end
// (z = arm_len) lands on the cap face (gb_arm_top); in_frame() is the gearbox's
module in_frame_inv_arm() {
    in_frame() translate([0, 0, gb_arm_top() - arm_len]) children();
}

// ---------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------
// whole unit: board, motor mount + motor, arm, gearbox
module unit() {
    mm_assembly();
    ARM() {
        color("burlywood") arm();
        // the gearbox: arm frame -> input frame -> gearbox frame
        translate([0, 0, arm_len - gb_arm_top()]) gb_from_input() gb_assembly(true, false);
    }
}

if (part == "assembly")       unit();
else if (part == "arm")       arm();
else if (part == "print")     arm_print();

echo(str("Arm ", arm_len, " mm (near face), ", arm_len + cut_dz, " mm (far face); printed ", aw, " x ", arm_t));
echo(str("Pilot holes (side, y, z): ", pilots));
