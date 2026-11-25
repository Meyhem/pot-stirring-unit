// =====================================================================
//  Pot stirrer – motor cradle on the wooden arm + arm foot on the board
//  Motor: TOPOWER 550-18V (RS-550 class), body Ø38 mm (measured), ~57 mm long,
//  with a drill chuck (Ø55 at its thickest) on the shaft that grips the
//  6 mm input rod directly.
//
//  The wooden arm (20x40, on edge) is the spine of the whole unit:
//   - the FOOT holds the arm's bottom end on the board at 90 - shaft_angle
//     (60° for the default 30° input),
//   - the CRADLE grips the arm with two cheeks + wood screws and holds the
//     motor underneath it, coaxial with the gearbox input,
//   - the gearbox grips the top end of the arm the same way.
//  Because the motor and the gearbox are both referenced to the arm, they
//  line up by construction. The cradle can slide along the arm before the
//  screws go in, to set how deep the chuck grips the rod.
//  The arm's near face is arm_y0 = chuck_d/2 + chuck_clr (31.5 mm) from the
//  rod axis, so the spinning chuck clears it everywhere (see common.scad).
//
//  Parameters shared with the gearbox (angle, arm, chuck, cheeks, wood
//  screws) are in common.scad. No other libraries.
//
//  Hardware
//   - 4x M4x20 socket head screw + 4x M4 hex nut (motor clamps)
//   - 8x 4 mm countersunk wood screw, ~20 mm (2 per cheek: cradle + foot)
//   - 4x 4 mm countersunk wood screw, ~16-20 mm (foot -> board)
//   - optional: 1 mm rubber/TPU strip in the cradle for grip + damping
//
//  Wood: cut the arm's bottom end 30° off square (= shaft_angle) so it sits
//  flat on the foot plate; the far (upper) face is the longer one.
//
//  Printing: PETG/ASA/nylon (not PLA – it sits next to the stove).
//   - cradle: standing on its rear end face (as exported), no supports
//   - clamps: on their ring face, no supports
//   - foot: plate down, no supports
// =====================================================================

include <common.scad>

/* [What to show / export] */
part = "assembly"; // [assembly, cradle, clamp, clamps_x2, foot, print_all]

/* [Motor] */
motor_d    = 38;     // measured body diameter
motor_len  = 57;     // body length without shaft (RS-550 ≈ 57)
motor_clr  = 0.3;    // diametral clearance in the bore
rear_clear = 12;     // space behind the motor for terminals + wires
chuck_gap  = 3;      // motor front face -> back of the chuck

/* [Cradle (hangs under the arm)] */
cradle_len  = 54;    // along the motor axis, from the motor's rear face
side_w      = 11.5;  // material beside the bore at the split line
squeeze_gap = 1.5;   // gap between cradle and clamp faces (clamping travel)

/* [Clamps] */
clamp_w    = 12;     // width along the motor axis
clamp_t    = 5;      // ring thickness under the motor
ear_t      = 6;      // ear thickness under the bolt head
clamp_z    = [12, 42]; // clamp centres, measured from the motor rear face

/* [Clamp bolts] */
bolt_d     = 4.4;    // M4 clearance
bolt_off   = 6;      // bolt axis distance outside the bore
bolt_depth = 16;     // how deep the bolt hole goes into the cradle
head_d     = 8;      // counterbore for M4 socket head
nut_w      = 7.2;    // M4 nut across flats + clearance
nut_h      = 3.4;
nut_depth  = 7;      // nut slot depth above the cradle face

/* [Foot (arm end on the board)] */
foot_len    = 50;    // how far the cheeks run up the arm (on its near face)
base_t      = 6;     // plate thickness
plate_extra = 16;    // plate beyond the cheeks, front and back (board screws)
plate_side  = 14;    // plate beyond the cheeks, left and right
board_screw_d = 4.5; // 4 mm wood screw
board_head_d  = 8.5;

/* [Placement in the assembly] */
board_clear = 10;    // minimum air between motor/clamps/terminals and the board
// motor rear face position along the arm, measured on the arm near face from
// the foot plate; 0 = lowest position that respects board_clear and the foot
motor_z_set = 0;
arm_len     = 420;   // only for the ghost

$fn = 96;
eps = 0.01;

// ---------------------------------------------------------------------
// Derived
// ---------------------------------------------------------------------
R  = (motor_d + motor_clr)/2;
hw = R + side_w;                 // half width of cradle at the split line / clamps
W  = 2*hw;
yb = R + bolt_off;               // bolt position (±x)
sa = sin(shaft_angle);
ca = cos(shaft_angle);
cw = cheek_x + cheek_t;          // half width over the cheeks

assert(arm_y0 >= chuck_d/2 + 1, "arm would touch the drill chuck");
assert(arm_y0 >= R + squeeze_gap/2 + 6, "no room for the cradle between motor and arm");

// arm frame -> world. Arm frame: see common.scad (motor axis = z, arm on +y).
// World: board top = z 0, the arm near face meets the foot plate at the origin.
module ARM() { translate([0, 0, base_t]) rotate([shaft_angle, 0, 0]) translate([0, -arm_y0, 0]) children(); }
function arm2world(p) = let(q = [p[0], p[1] - arm_y0, p[2]])
    [q[0], q[1]*ca - q[2]*sa, base_t + q[1]*sa + q[2]*ca];

// lowest motor_z so that nothing below the arm comes closer than board_clear
// to the board. Candidates (y, z offset from the motor rear face):
low_pts = [
    [-R,              -rear_clear],                 // terminals / wires
    [-R,               0],                          // rear edge of the motor body
    [-(R + clamp_t),   clamp_z[0] - clamp_w/2],     // rear clamp ring
    [-(R + squeeze_gap/2 + ear_t), clamp_z[0] - clamp_w/2] // clamp ears (at |x| = hw, still under)
];
function z_for(p) = (board_clear - base_t - (p[0] - arm_y0)*sa)/ca - p[1];
motor_z = motor_z_set > 0 ? motor_z_set
        : max(max([for (p = low_pts) z_for(p)]), foot_len + 2);

// ---------------------------------------------------------------------
// Cradle (arm frame, motor rear face at z = 0)
// ---------------------------------------------------------------------
module cradle_2d() {
    difference() {
        union() {
            hull() {
                // full width at the split line: room for the clamp bolts + nuts
                translate([-hw, squeeze_gap/2]) square([W, bolt_depth + 3]);
                // narrows to the cheek width at the arm seat
                translate([-cw, squeeze_gap/2]) square([2*cw, arm_y0 - squeeze_gap/2]);
            }
            // cheeks along both sides of the arm
            for (sx = [-1, 1])
                translate([sx > 0 ? cheek_x : -cw, arm_y0 - eps]) square([cheek_t, arm_t + arm_clr/2 + eps]);
        }
        circle(r = R);
    }
}

module cradle_bolt_cuts() {
    for (z = clamp_z, sx = [-1, 1]) translate([sx*yb, 0, z]) {
        // bolt hole, from the split face into the cradle (+y)
        translate([0, squeeze_gap/2 - 1, 0]) rotate([-90, 0, 0]) cylinder(d = bolt_d, h = bolt_depth + 1, $fn = 24);
        // nut slot, open to the side
        translate([0, squeeze_gap/2 + nut_depth, 0]) {
            rotate([-90, 0, 0]) cylinder(d = nut_w/cos(30), h = nut_h, center = true, $fn = 6);
            translate([sx > 0 ? 0 : -(hw - yb + 2), -nut_h/2, -nut_w/2]) cube([hw - yb + 2, nut_h, nut_w]);
        }
    }
}

module cradle() {
    difference() {
        linear_extrude(cradle_len) cradle_2d();
        cradle_bolt_cuts();
        for (sx = [-1, 1], p = arm_screw_yz(sx, arm_y0, 0, cradle_len)) arm_screw_cut(sx, p[0], p[1]);
    }
}

// ---------------------------------------------------------------------
// Clamp cap (under the motor, -y side). 2D in the XY plane, extruded along z.
// ---------------------------------------------------------------------
module clamp_2d() {
    difference() {
        hull() {
            circle(r = R + clamp_t);
            translate([-hw, -squeeze_gap/2 - ear_t]) square([W, ear_t]);
        }
        circle(r = R);
        translate([-100, -squeeze_gap/2]) square([200, 100]);
    }
}

// print orientation = as modelled: ring face down, extruded along +z
module clamp() {
    difference() {
        linear_extrude(clamp_w) clamp_2d();
        for (sx = [-1, 1]) translate([sx*yb, 0, clamp_w/2]) {
            translate([0, -100, 0]) rotate([-90, 0, 0]) cylinder(d = bolt_d, h = 200, $fn = 24);
            // counterbore from the ear's outer face outwards
            translate([0, -squeeze_gap/2 - ear_t, 0]) rotate([90, 0, 0]) cylinder(d = head_d, h = 100, $fn = 32);
        }
    }
}

// ---------------------------------------------------------------------
// Foot (world frame, plate on the board)
// ---------------------------------------------------------------------
// world-Y extent of the cheeks (near face top .. far face bottom)
foot_y0 = arm2world([0, arm_y0, foot_len])[1];          // front (pot side), top of near face
foot_y1 = arm2world([0, arm_y0 + arm_t, -arm_t*tan(shaft_angle)])[1];  // back, far face on the plate
plate_y0 = foot_y0 - plate_extra;
plate_y1 = foot_y1 + plate_extra;
plate_hw = cw + plate_side;

module rounded_box(size, r) {
    hull() for (x = [r, size[0] - r], y = [r, size[1] - r])
        translate([x, y, 0]) cylinder(r = r, h = size[2], $fn = 32);
}

module foot() {
    difference() {
        union() {
            translate([-plate_hw, plate_y0, 0]) rounded_box([2*plate_hw, plate_y1 - plate_y0, base_t], 5);
            // cheeks: the arm's side silhouette from the plate up to foot_len
            intersection() {
                ARM() for (sx = [-1, 1])
                    translate([sx > 0 ? cheek_x : -cw, arm_y0, -2*arm_t])
                        cube([cheek_t, arm_t + arm_clr/2, 2*arm_t + foot_len]);
                translate([-100, -300, 0]) cube([200, 600, 300]);
            }
        }
        // wood screws into the arm
        ARM() for (sx = [-1, 1], p = arm_screw_yz(sx, arm_y0, 0, foot_len)) arm_screw_cut(sx, p[0], p[1]);
        // countersunk board screws, 2 at each end of the plate
        for (y = [plate_y0 + plate_extra/2, plate_y1 - plate_extra/2], sx = [-1, 1])
            translate([sx*(plate_hw - 8), y, 0]) {
                translate([0, 0, -1]) cylinder(d = board_screw_d, h = base_t + 2, $fn = 24);
                translate([0, 0, base_t - (board_head_d - board_screw_d)/2 + eps])
                    cylinder(d1 = board_screw_d, d2 = board_head_d + 0.5, h = (board_head_d - board_screw_d)/2, $fn = 32);
            }
    }
}

// ---------------------------------------------------------------------
// Ghosts for the assembly view (arm frame)
// ---------------------------------------------------------------------
module motor_ghost() {
    color("dimgray") cylinder(d = motor_d, h = motor_len);
    color("silver") translate([0, 0, motor_len]) cylinder(d = 3.175, h = chuck_gap + 2, $fn = 24);
    color("goldenrod") translate([-5, -2.5, -6]) cube([10, 5, 6]);                    // terminals
    color("darkorange", 0.8) translate([0, 0, motor_len + chuck_gap]) cylinder(d = chuck_d, h = chuck_len);
    color("silver") translate([0, 0, motor_len + chuck_gap + chuck_len - 30]) cylinder(d = 6, h = 150, $fn = 24);
}
module arm_ghost() {
    // bottom end cut parallel to the board
    %intersection() {
        ARM() translate([-arm_w/2, arm_y0, -2*arm_t]) cube([arm_w, arm_t, arm_len]);
        translate([-100, -500, base_t]) cube([200, 1000, 1000]);
    }
}
module board_ghost() {
    %translate([-60, plate_y0 - 140, -18]) cube([120, plate_y1 - plate_y0 + 200, 18]);
}

// ---------------------------------------------------------------------
// Output
// ---------------------------------------------------------------------
if (part == "assembly") {
    color("lightsteelblue") foot();
    ARM() translate([0, 0, motor_z]) {
        color("lightsteelblue") cradle();
        for (z = clamp_z) color("tomato") translate([0, 0, z - clamp_w/2]) clamp();
        motor_ghost();
    }
    arm_ghost();
    board_ghost();
}
else if (part == "cradle")    cradle();
else if (part == "clamp")     clamp();
else if (part == "clamps_x2") { clamp(); translate([0, -(R + clamp_t + 10), 0]) clamp(); }
else if (part == "foot")      foot();
else if (part == "print_all") {
    foot();
    translate([plate_hw + hw + 15, 0, 0]) cradle();
    translate([plate_hw + hw + 15, -(R + clamp_t) - arm_y0 - 25, 0]) {
        clamp(); translate([0, -(R + clamp_t + 10), 0]) clamp();
    }
}

// ---------------------------------------------------------------------
// Report
// ---------------------------------------------------------------------
low_world = min([for (p = low_pts) arm2world([0, p[0], motor_z + p[1]])[2]]);
chuck_end = motor_z + motor_len + chuck_gap + chuck_len;
echo(str("Arm at ", 90 - shaft_angle, "° to the board, near face ", arm_y0, " mm from the rod axis"));
echo(str("Chuck clearance to the arm: ", arm_y0 - chuck_d/2, " mm"));
echo(str("Motor rear face at ", motor_z, " mm along the arm (near face, from the foot plate); lowest point ",
         low_world, " mm above the board"));
echo(str("Chuck front at ", chuck_end, " mm along the arm"));
echo(str("Foot plate ", 2*plate_hw, " x ", plate_y1 - plate_y0, " mm"));
