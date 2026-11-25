// =====================================================================
//  Pot stirrer – motor cradle on the wooden arm + arm foot on the board
//  Motor: TOPOWER 550-18V (RS-550 class), body Ø38 mm (measured), ~57 mm long,
//  with a drill chuck (Ø55 at its thickest) on the shaft that grips the
//  6 mm input rod directly.
//
//  The wooden arm (20x40, on edge) is the spine of the whole unit; the
//  gearbox grips its top end, this part grips its bottom end.
//
//  style = "one_piece" (default): ONE print = foot plate on the board +
//  two cheeks along the arm sides + a split ring around the motor under the
//  arm. The arm end sits on the plate at 90 - shaft_angle (60°), the motor
//  sits coaxial with the gearbox input. The ring has a slit at the bottom
//  and two M4 pinch bolts; a rear lip stops the motor sliding back.
//  Insert the motor from the FRONT, rear end first (the chuck stays in
//  front of the ring – it doesn't fit through). Set how deep the chuck
//  grips the rod by sliding the rod in the chuck.
//
//  style = "three_piece": separate foot, a cradle that slides along the arm
//  and 2 clamp caps (kept as a fallback if the ring fit is a problem).
//
//  Because the motor and the gearbox are both referenced to the arm, they
//  line up by construction.
//  The arm's near face is arm_y0 = chuck_d/2 + chuck_clr (31.5 mm) from the
//  rod axis, so the spinning chuck clears it everywhere (see common.scad).
//
//  Parameters shared with the gearbox (angle, arm, chuck, cheeks, wood
//  screws) are in common.scad. No other libraries.
//
//  Hardware (one_piece)
//   - 2x M4x20 socket head screw + 2x M4 hex nut (ring pinch bolts)
//   - 8x 4 mm countersunk wood screw, ~20 mm (4 per cheek, into the arm)
//   - 4x 4 mm countersunk wood screw, ~16-20 mm (plate -> board)
//  Hardware (three_piece)
//   - 4x M4x20 socket head screw + 4x M4 hex nut (motor clamps)
//   - 8x 4 mm countersunk wood screw, ~20 mm (2 per cheek: cradle + foot)
//   - 4x 4 mm countersunk wood screw, ~16-20 mm (foot -> board)
//   - optional: 1 mm rubber/TPU strip in the cradle for grip + damping
//
//  Wood: cut the arm's bottom end 30° off square (= shaft_angle) so it sits
//  flat on the foot plate; the far (upper) face is the longer one.
//
//  Printing: PETG/ASA/nylon (not PLA – it sits next to the stove).
//   - one_piece (part = "mount"): plate down, supports from the build plate
//     only (under the rear end of the ring, the lip and the ears).
//     ~76 x 166 x 113 mm. Print a test ring first if unsure of hole sizing
//     (ring_clr).
//   - cradle: standing on its rear end face (as exported), no supports
//   - clamps: on their ring face, no supports
//   - foot: plate down, no supports
// =====================================================================

include <common.scad>

/* [What to show / export] */
// one_piece = foot + arm cheeks + split motor ring in ONE print (default);
// three_piece = separate foot, sliding cradle and 2 clamp caps
style = "one_piece"; // [one_piece, three_piece]
// mount = the one-piece part; cradle/clamp/foot = three-piece parts
part = "assembly"; // [assembly, mount, cradle, clamp, clamps_x2, foot, print_all]

/* [Motor] */
motor_d    = 38;     // measured body diameter
motor_len  = 57;     // body length without shaft (RS-550 ≈ 57)
motor_clr  = 0.3;    // diametral clearance in the bore
rear_clear = 12;     // space behind the motor for terminals + wires
// drill head in front of the can (ghost only; estimated from a photo – measure)
head_gb_d    = 44;   // beige planetary gearbox housing incl. screw ribs
head_gb_len  = 40;
head_col_len = 20;   // clutch collar (Ø chuck_d, the thickest part)
head_ch_d    = 44;   // chuck body
head_ch_len  = 43;

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

/* [One-piece: split ring (pinch clamp) around the motor] */
ring_clr    = 0.4;   // diametral clearance of the ring bore (tune to your printer)
ring_t      = 5;     // ring wall
// The ring grips only the FRONT part of the can: the rear vent slots
// (~8-13 mm from the rear face) and the end cap stay open for cooling.
// The motor can't slide back: the drill gearbox housing in front of the can
// is wider than the bore and sits against the ring's front face.
ring_z0     = 18;    // ring starts this far in front of the motor rear face
ring_len    = motor_len - ring_z0;   // ... and ends flush with the can front
slit_w      = 3;     // pinch slit at the bottom (closing it by 3 mm squeezes Ø by ~1 mm)
lip_w       = 0;     // optional inward lip at the ring's rear end (0 = none)
lip_t       = 2.5;
ear_hw      = 11;    // pinch ears: half width (across, bolt direction)
ear_drop    = 12;    // how far the ears reach below the bore
pinch_z     = [0.25, 0.75];  // pinch bolt positions as fractions of the ring length
pinch_cb    = 4;     // head counterbore depth (+x ear)
pinch_nut_d = 4;     // nut trap depth (-x ear)
plate_hw1   = 38;    // one-piece plate half width (board screws clear of the ring)

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
Rr = (motor_d + ring_clr)/2;     // one-piece ring bore radius
low_pts = style == "one_piece" ? [
    [-R,                -rear_clear],                // terminals / wires
    [-R,                 0],                         // bare rear end of the can
    [-(Rr + ring_t),    ring_z0 - lip_t],            // ring rear bottom edge
    [-(Rr + ear_drop),  ring_z0 - lip_t]             // pinch ears, rear bottom edge
] : [
    [-R,              -rear_clear],                 // terminals / wires
    [-R,               0],                          // rear edge of the motor body
    [-(R + clamp_t),   clamp_z[0] - clamp_w/2],     // rear clamp ring
    [-(R + squeeze_gap/2 + ear_t), clamp_z[0] - clamp_w/2] // clamp ears (at |x| = hw, still under)
];
function z_for(p) = (board_clear - base_t - (p[0] - arm_y0)*sa)/ca - p[1];
motor_z = motor_z_set > 0 ? motor_z_set
        : style == "one_piece" ? max([for (p = low_pts) z_for(p)])
        : max(max([for (p = low_pts) z_for(p)]), foot_len + 2);  // cradle must clear the foot cheeks

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
// One piece: foot plate + continuous arm cheeks + split ring (world frame)
// ---------------------------------------------------------------------
op_top   = motor_z + ring_z0 + ring_len;       // cheeks end with the ring (arm frame z)
pinch_y  = -(Rr + ear_drop/2);                 // pinch bolt axis, below the bore

module ring_2d() {
    union() {
        // ring + web up to the arm seat, narrowing to the cheek width
        hull() {
            circle(r = Rr + ring_t);
            translate([-cw, 0]) square([2*cw, arm_y0]);
        }
        // cheeks along both sides of the arm
        for (sx = [-1, 1])
            translate([sx > 0 ? cheek_x : -cw, arm_y0 - eps]) square([cheek_t, arm_t + arm_clr/2 + eps]);
        // pinch ears under the slit
        translate([-ear_hw, -(Rr + ear_drop)]) square([2*ear_hw, ear_drop + 2]);
    }
}

module one_piece() {
    difference() {
        union() {
            translate([-plate_hw1, plate_y0, 0]) rounded_box([2*plate_hw1, plate_y1 - plate_y0, base_t], 5);
            intersection() {
                ARM() {
                    // cheeks from below the plate up to the motor
                    for (sx = [-1, 1])
                        translate([sx > 0 ? cheek_x : -cw, arm_y0, -2*arm_t])
                            cube([cheek_t, arm_t + arm_clr/2, 2*arm_t + op_top]);
                    // ring + web, incl. the rear lip
                    translate([0, 0, motor_z + ring_z0 - (lip_w > 0 ? lip_t : 0)])
                        linear_extrude(ring_len + (lip_w > 0 ? lip_t : 0)) ring_2d();
                }
                translate([-150, -300, 0]) cube([300, 600, 400]);
            }
        }
        ARM() translate([0, 0, motor_z + ring_z0]) {
            // motor bore, open at the front (and at the rear unless there's a lip)
            translate([0, 0, lip_w > 0 ? 0 : -1]) cylinder(r = Rr, h = ring_len + 2);
            if (lip_w > 0) translate([0, 0, -lip_t - 1]) cylinder(r = Rr - lip_w, h = lip_t + 2);
            // pinch slit through the bottom wall, the ears and the lip
            translate([-slit_w/2, -(Rr + ear_drop + 1), -lip_t - 1]) cube([slit_w, ear_drop + lip_w + 2, ring_len + lip_t + 2]);
            // pinch bolts across the slit: head counterbore on +x, nut trap on -x
            for (f = pinch_z) translate([0, pinch_y, ring_len*f]) {  // (z relative to ring start)
                rotate([0, 90, 0]) cylinder(d = bolt_d, h = 2*ear_hw + 2, center = true, $fn = 24);
                translate([ear_hw - pinch_cb, 0, 0]) rotate([0, 90, 0]) cylinder(d = head_d, h = pinch_cb + 1, $fn = 32);
                translate([-ear_hw - 1, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, 30])
                    cylinder(d = nut_w/cos(30), h = pinch_nut_d + 1, $fn = 6);
            }
        }
        // wood screws into the arm: the shared pattern on each half of the cheeks
        ARM() for (sx = [-1, 1], seg = [0, 1], p = arm_screw_yz(sx, arm_y0, seg*op_top/2, op_top/2))
            arm_screw_cut(sx, p[0], p[1]);
        // countersunk board screws, 2 at each end of the plate, outside the ring
        for (y = [plate_y0 + plate_extra/2, plate_y1 - plate_extra/2], sx = [-1, 1])
            translate([sx*(plate_hw1 - 7), y, 0]) {
                translate([0, 0, -1]) cylinder(d = board_screw_d, h = base_t + 2, $fn = 24);
                translate([0, 0, base_t - (board_head_d - board_screw_d)/2 + eps])
                    cylinder(d1 = board_screw_d, d2 = board_head_d + 0.5, h = (board_head_d - board_screw_d)/2, $fn = 32);
            }
    }
}

// ---------------------------------------------------------------------
// Ghosts for the assembly view (arm frame)
// ---------------------------------------------------------------------
head_len = head_gb_len + head_col_len + head_ch_len;
module motor_ghost() {
    color("silver") cylinder(d = motor_d, h = motor_len);
    color("black") for (a = [0, 180]) rotate(a) translate([-5, -(motor_d/2 + 0.2), 8]) cube([10, 1, 5]); // vent slots
    color("goldenrod") translate([-5, -2.5, -6]) cube([10, 5, 6]);                    // terminals
    translate([0, 0, motor_len]) {
        color("tan", 0.9) cylinder(d = head_gb_d, h = head_gb_len);                    // planetary gearbox
        color("darkorange", 0.8) translate([0, 0, head_gb_len]) cylinder(d = chuck_d, h = head_col_len);  // clutch collar
        color("dimgray") translate([0, 0, head_gb_len + head_col_len]) cylinder(d1 = head_ch_d, d2 = head_ch_d - 10, h = head_ch_len);
        color("silver") translate([0, 0, head_len - 25]) cylinder(d = 6, h = 150, $fn = 24);   // input rod
    }
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
    if (style == "one_piece") {
        color("lightsteelblue") one_piece();
    } else {
        color("lightsteelblue") foot();
        ARM() translate([0, 0, motor_z]) {
            color("lightsteelblue") cradle();
            for (z = clamp_z) color("tomato") translate([0, 0, z - clamp_w/2]) clamp();
        }
    }
    ARM() translate([0, 0, motor_z]) motor_ghost();
    arm_ghost();
    board_ghost();
}
else if (part == "mount")     one_piece();
else if (part == "cradle")    cradle();
else if (part == "clamp")     clamp();
else if (part == "clamps_x2") { clamp(); translate([0, -(R + clamp_t + 10), 0]) clamp(); }
else if (part == "foot")      foot();
else if (part == "print_all" && style == "one_piece") one_piece();
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
chuck_end = motor_z + motor_len + head_len;
echo(str("Arm at ", 90 - shaft_angle, "° to the board, near face ", arm_y0, " mm from the rod axis"));
echo(str("Chuck clearance to the arm: ", arm_y0 - chuck_d/2, " mm"));
echo(str("Motor rear face at ", motor_z, " mm along the arm (near face, from the foot plate); lowest point ",
         low_world, " mm above the board"));
echo(str("Chuck front at ", chuck_end, " mm along the arm"));
if (style == "one_piece") echo(str("Ring grips the can from ", ring_z0, " to ", ring_z0 + ring_len,
    " mm (of ", motor_len, "); rear ", ring_z0, " mm open for the vents"));
echo(str("Foot plate ", 2*(style == "one_piece" ? plate_hw1 : plate_hw), " x ", plate_y1 - plate_y0, " mm (", style, ")"));
