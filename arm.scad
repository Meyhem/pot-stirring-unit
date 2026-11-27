// =====================================================================
//  Pot stirrer – printed arm (the spine) in two halves
//
//  20x40 bar standing on edge, arm_len (400) long along its near face. The
//  bottom end is cut parallel to the board and sits on the motor mount's
//  plate; the square top end rests against the gearbox cap. Too long for a
//  220 mm bed, so it prints as two halves joined by a half-lap in the middle
//  (3x M4 bolts, optionally glued). Each half prints lying on a side face,
//  diagonally on the bed, no supports.
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
//   - 3x M4x16 socket head screw + 3x M4 hex nut (lap joint)
//   - the 4 mm countersunk screws of the motor mount (8) and gearbox (4) go into
//     the pilot holes; ~20 mm long
//   - optional: epoxy / CA glue on the lap faces (PETG: epoxy holds best)
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
// assembly = the whole unit; lower/upper = print-ready halves
part = "assembly"; // [assembly, arm, lower, upper, print_all]

/* [Fit] */
arm_fit_clr = 0.2;   // printed arm is this much narrower than the cheek gap (total)

/* [Pilot holes for the 4 mm wood screws] */
pilot_d     = 3.3;   // into PETG
pilot_depth = 16;    // from the arm face (screw ~20 minus the 6 mm cheek, + 2)

/* [Lap joint between the halves] */
lap_len    = 80;     // overlap length
lap_bolt_d = 4.4;    // M4 clearance
lap_head_d = 8;      // counterbore (upper half, outer face)
lap_head_h = 3;
lap_nut_w  = 7.2;    // M4 nut across flats + clearance (lower half, outer face)
lap_nut_h  = 3.5;
lap_bolts  = [[-0.35, 0.3], [0, 0.7], [0.35, 0.3]];  // [along the lap, across arm_t] fractions

/* [Print bed] */
bed = 220;

$fn = 48;

// ---------------------------------------------------------------------
// Derived (arm frame, see common.scad: near face at y = arm_y0, z = 0 where
// the near face meets the foot plate, z = arm_len at the top end)
// ---------------------------------------------------------------------
aw      = arm_w + arm_clr - arm_fit_clr;        // printed width (20.4)
cut_dz  = arm_t*tan(shaft_angle);               // far face reaches this far below z = 0
z_split = (arm_len - cut_dz)/2;                 // lap centre: both halves equally long
z_lap0  = z_split - lap_len/2;
z_lap1  = z_split + lap_len/2;
half_len = z_lap1 + cut_dz;                     // longest edge of each half
// both halves lie diagonally: their footprint (length + depth)/sqrt(2) must fit the bed
assert((half_len + arm_t)/sqrt(2) <= bed - 4, "arm halves don't fit the bed – shorten arm_len or lap_len");

// pilot holes: motor mount (z from the plate) + gearbox (z relative to the top end)
pilots = concat(
    mm_arm_screws(),
    [for (p = gb_arm_screws()) [p[0], p[1], arm_len + (p[2] - gb_arm_top())]]
);
for (p = pilots) assert(p[2] < z_lap0 - 10 || p[2] > z_lap1 + 10, "a pilot hole falls into the lap joint");

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

module lap_bolt_holes(head) {   // head = true: counterbore on +x, else nut trap on -x
    for (b = lap_bolts) translate([0, arm_y0 + arm_t*b[1], z_split + lap_len*b[0]]) {
        rotate([0, 90, 0]) cylinder(d = lap_bolt_d, h = aw + 2, center = true, $fn = 24);
        if (head) translate([aw/2 - lap_head_h, 0, 0]) rotate([0, 90, 0]) cylinder(d = lap_head_d, h = lap_head_h + 1, $fn = 32);
        else translate([-aw/2 - 1, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, 30])
            cylinder(d = lap_nut_w/cos(30), h = lap_nut_h + 1, $fn = 6);
    }
}

// half = -1: lower (bottom end + tongue on the -x side), +1: upper (tongue on +x)
module arm_half(half, shrink = 0) {
    difference() {
        intersection() {
            arm_bar(shrink);
            union() {
                // full section on its own side of the lap
                if (half < 0) translate([-50, -100, -100]) cube([100, 300, z_lap0 + 100]);
                else          translate([-50, -100, z_lap1]) cube([100, 300, arm_len]);
                // tongue: half the width across the lap
                translate([half < 0 ? -50 : 0, -100, z_lap0]) cube([50, 300, lap_len]);
            }
        }
        pilot_holes();
        lap_bolt_holes(head = half > 0);
    }
}

module arm(shrink = 0) { arm_half(-1, shrink); arm_half(1, shrink); }

// print orientation: lying on the outer face of its tongue side, centred,
// turned 45° to lie diagonally on the bed
module arm_half_print(half, diagonal = true) {
    zc = half < 0 ? (z_lap1 - cut_dz)/2 : (z_lap0 + arm_len)/2;
    rotate([0, 0, diagonal ? 45 : 0]) translate([0, 0, aw/2])
        rotate([0, half < 0 ? -90 : 90, 0])
            translate([0, -(arm_y0 + arm_t/2), -zc]) arm_half(half);
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
    // the two halves only touch on the lap faces
    if (what == "arm_halves")
        intersection() { arm_half(-1); translate([0.01, 0, 0.01]) arm_half(1); }  // off the lap plane + both shoulders
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
else if (part == "lower")     arm_half_print(-1);
else if (part == "upper")     arm_half_print(1);
// preview of both halves side by side (each one is a separate, full-bed print)
else if (part == "print_all") { translate([0, 35, 0]) arm_half_print(-1, false); translate([0, -35, 0]) arm_half_print(1, false); }

echo(str("Arm ", arm_len, " mm (near face), ", arm_len + cut_dz, " mm (far face); printed ", aw, " x ", arm_t,
         "; halves ", half_len, " mm long, lap ", lap_len, " mm at ", z_lap0, "..", z_lap1));
echo(str("Pilot holes (side, y, z): ", pilots));
